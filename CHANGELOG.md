# Changelog

Notable changes to the Gunnerus Open Data Set. Versions follow the tagged [releases](https://github.com/shiplab/gunnerus/releases); each release is archived on Zenodo with its own DOI.

## [Unreleased] – planned as 1.1.0

### Added

- `derived/`, a folder for files made by NTNU from the published material or brought in from earlier NTNU Shiplab projects, with a README giving source, method, limitations and licence for each file.
- `derived/3d/gunnerus.glb`: a 3.5 MB simplified glTF of the C-JOB 3D model.
- `derived/3d/gunnerus-visual.glb`: the textured visual model from vessel.js (2020), with textures compressed to WebP (31.8 MB → 10.9 MB).
- `derived/vesseljs/gunnerus.json`: the vessel.js ship specification (hull offsets, decks, bulkheads, compartments and tanks), and `derived/vesseljs/offsets.csv` with the offsets in metres.
- A *Related projects* section in the README, linking the vessel.js Gunnerus examples and the OpenBridge simulator demo.
- A photo of the vessel (2014, Fredrik Skoglund) in the README, and a render of the visual model in `derived/3d/`.

### Changed

- The website now takes its 3D model from `derived/3d/gunnerus.glb`; the duplicate `pages/assets/gunnerus.glb` was removed.

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

[Unreleased]: https://github.com/shiplab/gunnerus/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/shiplab/gunnerus/releases/tag/v1.0.0
