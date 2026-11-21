# MapLab desktop releases

Public installer storage for MapLab desktop apps. Release tags are
`<app>-desktop-v<version>`. A release contains the platform installers and
update manifests for a single app.

Each application has a feed at `feeds/<app>/`. Its `release.json` points to the
current release and its update manifests link to those specific release assets.
Publish the complete release before updating the app's feed.
