# 3D model

A 3D CAD model of the hull and superstructure, built by C-JOB from the same source data as the drawings in [`../`](../README.md). Corresponds to `25.1142-000-113 3D model` in the C-JOB project document list ([`../docs/`](../docs/README.md)).

| File | Size | Format |
| --- | --- | --- |
| `Gunnerus 3D Model Rev0.3dm` | ~396 MB | Rhinoceros 3D native format |
| `Gunnerus 3D Model STEP Rev0.stp` | ~728 MB | STEP (ISO 10303) neutral CAD exchange format |

## ⚠️ Before you clone, add to, or push this folder

Both files are far past GitHub's plain-git limits: GitHub **blocks any push containing a file over 100 MB** outright, and warns starting at 50 MB. Neither file will currently push over a normal `git push` — they need to be handled with **[Git LFS](https://git-lfs.com/)** (`git lfs track "*.3dm" "*.stp"`) or hosted outside the git repository (e.g. a release asset or external file store) before they can be committed. If you're seeing these files already tracked in git history without LFS, the repository will be slow to clone and may be rejected by GitHub on push — this is worth fixing before publishing.

## License

Same terms as the rest of the repository — CC BY-NC 4.0 — unless a licence notice embedded in the model itself says otherwise (not machine-checked here, since these are binary CAD formats). See the main [README](../../../README.md#credit--license) and [LICENSE](../../../LICENSE).
