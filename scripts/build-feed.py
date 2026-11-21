"""Build Electron's per-app generic feed from a public MapLab release."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

import yaml

REPOSITORY = "mp-lb/releases"
MANIFESTS = ("latest-linux.yml", "latest-mac.yml")


def fetch(url):
    with urlopen(Request(url, headers={"Accept": "application/vnd.github+json"}), timeout=30) as response:
        return response.read()


def build_feed(app, version, destination):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", app) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Expected an application slug and a stable desktop version")

    existing = destination / app / "release.json"
    if existing.exists():
        current = json.loads(existing.read_text(encoding="utf-8"))["version"]
        if tuple(map(int, version.split("."))) < tuple(map(int, current.split("."))):
            raise ValueError(f"Refusing to replace {current} with older version {version}")

    tag = f"{app}-desktop-v{version}"
    release = json.loads(fetch(f"https://api.github.com/repos/{REPOSITORY}/releases/tags/{tag}"))
    if release["tag_name"] != tag or release["draft"] or release["prerelease"]:
        raise ValueError(f"{tag} must already be published as a stable release")

    download_base = f"https://github.com/{REPOSITORY}/releases/download/{tag}/"
    assets = {
        asset["name"]: download_base + quote(asset["name"], safe="")
        for asset in release["assets"]
        if asset["state"] == "uploaded"
    }

    manifests = {}
    for filename in MANIFESTS:
        manifest = yaml.safe_load(fetch(assets[filename]))
        if manifest["version"] != version:
            raise ValueError(f"{filename} does not match release {tag}")
        for entry in manifest["files"]:
            entry["url"] = assets[entry["url"]]
        manifest["path"] = assets[manifest["path"]]
        manifests[filename] = yaml.safe_dump(manifest, sort_keys=False)

    output = destination / app
    output.mkdir(parents=True, exist_ok=True)
    for filename, manifest in manifests.items():
        (output / filename).write_text(manifest, encoding="utf-8")
    (output / "release.json").write_text(
        json.dumps({
            "tag": tag,
            "version": version,
            "url": f"https://github.com/{REPOSITORY}/releases/tag/{tag}",
            "assets": assets,
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app")
    parser.add_argument("version")
    parser.add_argument("--destination", type=Path, default=Path("feeds"))
    args = parser.parse_args()
    build_feed(args.app, args.version, args.destination)
