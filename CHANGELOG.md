# Changelog

Notable changes to the Gunnerus Open Data Set. Versions follow the tagged [releases](https://github.com/shiplab/gunnerus/releases); each release is archived on Zenodo with its own DOI.

## [1.0.0] – unreleased

First public release.

### Added

- Six polarkonsult drawings in `polarkonsult/`: general arrangement (Rev1), tank plan (Rev1), lines plan, profile and plan, midship section and shell expansion (Rev0), each as DWG, DXF and A0 PDF.
- Nine C-JOB/NTNU derivative drawings in `extended/CJOB/`: engine room arrangement, construction plan (deck and double bottom, longitudinal section, transverse section), draught and hullmarks, freeboard plan, diver's platform arrangement, safety fire zone plan and tank arrangement.
- 3D CAD model in `extended/CJOB/3d models/` (Rhino `.3dm` and STEP), stored with Git LFS.
- Five C-JOB engineering documents in `extended/CJOB/docs/` (CC BY-SA 4.0).
- `metadata/gunnerus_metadata.json`: the general arrangement as structured data, coded by SFI group and DNV VIS/GMOD v3.10a.
- Website at <https://shiplab.github.io/gunnerus/>, built from `pages/`, with a browser 3D viewer.
- `CITATION.cff`, `.zenodo.json`, this changelog and a data error issue template.

### Changed

- The single-sheet `Construction Plan Rev0` (1:100) was replaced by three 1:50 sheets.
- Preview images moved from `docs/images/` to `images/`.
- `Safety Fire Zone Plan Rev0.dwg` and `Construction Plan Deck and Double Bottom Rev0.dwg` were renamed to match their DXF and PDF siblings.

[1.0.0]: https://github.com/shiplab/gunnerus/releases/tag/v1.0.0
