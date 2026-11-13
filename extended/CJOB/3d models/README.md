# 3D model

A 3D CAD model of the hull and superstructure, built by C-JOB from the same source data as the drawings in [`../`](../README.md). Corresponds to `25.1142-000-113 3D model` in the C-JOB project document list ([`../docs/`](../docs/README.md)).

## Files

The models are stored **compressed as 7-Zip archives** to keep the repository small. The original, uncompressed CAD files are not committed (they are listed in the repository's [`.gitignore`](../../../.gitignore)).

| Archive (in this repo) | Archive size | Contains | Uncompressed size | Format |
| --- | --- | --- | --- | --- |
| `Gunnerus 3D Model Rev0.7z` | ~65 MB | `Gunnerus 3D Model Rev0.3dm` | ~274 MB | Rhinoceros 3D native format |
| `Gunnerus 3D Model STEP Rev0.7z` | ~158 MB | `Gunnerus 3D Model STEP Rev0.stp` | ~728 MB | STEP (ISO 10303-21) neutral CAD exchange format |

The `.3dm` file was re-saved without render meshes ("save small"), which reduces it from ~396 MB to ~274 MB with no loss of geometry. Rhino regenerates the render meshes when the model is opened, so the first display may take a little longer.

SHA-256 checksums of the archives:

```
8bd4a0b4b23b8fb370ec9364b220b54e4fff14fba96f6acb5310a5ff874f1145  Gunnerus 3D Model Rev0.7z
7512363bce23eefd99e94de0cabe6ae387812095fdd03554359f121f27eaff53  Gunnerus 3D Model STEP Rev0.7z
```

## Getting and extracting the models

The archives are stored with **[Git LFS](https://git-lfs.com/)** (the STEP archive is over GitHub's 100 MB per-file limit). Install Git LFS before cloning, otherwise you will get small text pointer files instead of the archives:

```bash
git lfs install
git clone https://github.com/shiplab/gunnerus.git
# or, in an existing clone without the archives:
git lfs pull --include="extended/CJOB/3d models/*.7z"
```

Then extract with [7-Zip](https://www.7-zip.org/) (Windows: right-click → *7-Zip → Extract Here*), or from the command line:

```bash
7z x "Gunnerus 3D Model Rev0.7z"
7z x "Gunnerus 3D Model STEP Rev0.7z"
```

On macOS/Linux, `7z` is provided by the `p7zip` / `7zip` package (e.g. `brew install sevenzip`, `apt install 7zip`).

Which file to use:

- **`.3dm`**: open in Rhinoceros 3D (v7 or later recommended); keeps Rhino layers and object structure.
- **`.stp`**: import into most CAD tools (SolidWorks, Siemens NX, CATIA, FreeCAD, Fusion, etc.). Large and slow to import; expect several minutes.

## Contributing an updated model

Do not commit the uncompressed `.3dm`/`.stp` files; `.gitignore` will skip them. Instead compress the new revision and commit the archive:

```bash
7z a -t7z -mx=9 "Gunnerus 3D Model RevN.7z" "Gunnerus 3D Model RevN.3dm"
```

`.7z` files in this folder are routed to Git LFS automatically by [`.gitattributes`](../../../.gitattributes). Update the table and checksums above when doing so.

> Earlier commits of this repository contain the uncompressed Rev0 `.3dm` and `.stp` files in Git LFS. They remain available through the git history but are no longer in the current tree.

## License

Same terms as the rest of the repository — CC BY-NC 4.0 — unless a licence notice embedded in the model itself says otherwise (not machine-checked here, since these are binary CAD formats). See the main [README](../../../README.md#credit--license) and [LICENSE](../../../LICENSE).
