# Changelog

Notable changes to the Gunnerus Open Data Set. Versions follow the tagged [releases](https://github.com/shiplab/gunnerus/releases); each release is archived on [Zenodo](https://doi.org/10.5281/zenodo.22983657) (concept DOI 10.5281/zenodo.22983657, all versions) with its own version DOI.

## [Unreleased]

### Added

- `metadata/signals/`: a crosswalk of 53 signals of the ship (engine 1, power management, thrusters, navigation, crane) across the engine vendor list, HEMOS, the 2023 logger and the 2019 asset model, with quantity, canonical unit, SFI code and status; two extracts from the 2019 logs (engine, 1-minute; docking, 10-second); and the inputs, answers, key and grading script of a blind translator test.
- Website: a signals page, `pages/signals.html` (data in `pages/assets/signals/signals.json`, made by `metadata/signals/scripts/build_page_data.py`): coverage, signal inspector, conventions and documents against data, translator test, and an illustration of the same facts stored as a wide table, a long table, a hierarchy, a graph and a self-describing record.
- README: the signals folder in At a glance, Other material and Metadata; link to the ship explorer.
- Website: the top menu of the main page now links to the Energy and Sensors pages (the Licence and Cite links are removed from the menu; the sections stay on the page), and the two pages link to each other.

## [1.0.3] – 2026-10-20

Adds a second operational case, a power and energy profile of the cruise week.

### Added

- `operational/power-energy-2023/`: a power and energy profile of the cruise week, 30 October – 3 November 2023, from the ship's own NUC logger. One row per minute (7,200) with speed over ground, GPS position, the three main engines (load in kW, fuel consumption in L/h, speed), the two azimuth drives and the tunnel thruster, and an operating mode (stationary, station-keeping, manoeuvring, transit) set by documented thresholds. Includes `cases.csv` (consecutive operating periods), `profile.csv` (shares of time, energy and fuel), `summary.csv` (hours, energy, fuel and a tank-to-wake CO₂ estimate per mode, day and week), `channels.csv` with a measured / derived / assumed label for every column, an overview figure, and the extraction script. Under 1 MB. No published study anchors this case; the README says what is ours. Data from Robert Skulstad (NTNU), organised by Henrique M. Gaspar.
- Website: a power and energy page, `pages/power-energy.html` (data in `pages/assets/operational/power-energy-2023.json`, made by the case's `extract.py web`): operating-mode timeline by day, load sharing between engines, fuel against load, a summary by mission, operational profile, operational states and performance (time, energy and fuel by state, speed band and engine combination; each engine's share of the output and load factor), a GPS track on Kartverket's open map linked to the charts (the track alone if the map cannot be loaded), a power-chain diagram that marks what is measured, and the assumptions. A card in the *Operational* section links to it.

## [1.0.2] – 2026-10-10

Adds operational data measured at sea, a ship explorer page, and a citable DOI.

### Added

- `operational/`, for data measured on board in service: one folder per case, each tied to a published study, with UTC times, units in the column names, a data dictionary and the extraction script.
- `operational/wave-shielding-2023/`: the wave-shielding experiment of 31 October 2023 in Breisundet, from Wang et al. (2025), *Ocean Engineering* 320, 120189, [doi:10.1016/j.oceaneng.2024.120189](https://doi.org/10.1016/j.oceaneng.2024.120189). Seven heading cases (10:00–12:10 UTC) with ship motion and position (1 and 2 Hz), crane angles and a crane-hook accelerometer, azimuth and tunnel thrusters, engines, Miros wave radar spectra, air gap and a 50 Hz wave buoy on the sheltered side. Includes `cases.csv`, the paper's reported values (`results.csv`), `channels.csv` (132 columns) and an overview figure. About 16 MB. Data set organised by Jisang Ha and Henrique M. Gaspar.
- Website: an *Operational* section with a chart of the seven cases, a case table and the data files (`pages/assets/operational/wave-shielding-2023.json`, made by the case's `extract.py web`).
- Website: a ship explorer, `pages/explorer.html`. *Ship* view: the 3D model with a detail panel per part, SFI group, equipment item or weight group (equipment-list rows with the matching specification line, drawing evidence, GA metadata, measured channels from the wave-shielding case, known issues), weight centres from the C-JOB weight calculation, and deep links (`#part=`, `#group=`, `#item=`, `#weight=`). *Coverage* view: all 127 items of the C-JOB list of main equipment against 3D model, specification, drawings, GA metadata and measurements. Data in `pages/assets/explorer/explorer.json`, built by `pages/tools/build_explorer_data.py`.
- Website: a *Cite* panel with the data set citation and BibTeX, and the citation for the operational study.
- README: an *Operational data* section, a DOI badge, and a header image showing drawings, 3D model and operational data (`images/gunnerus-header.png`, built by `images/make_header.py`).
- Concept DOI [10.5281/zenodo.22983657](https://doi.org/10.5281/zenodo.22983657) in the README, `CITATION.cff` and `.zenodo.json`.

### Changed

- Citation: the data set is cited as Ha, J. and Gaspar, H. M. polarkonsult, C-JOB and NTNU are credited in the README and on Zenodo as rights holder, producer and hosting institution. The title now includes operational data.
- `polarkonsult/Profile and Plan Rev0.pdf` re-issued.

## [1.0.1] – 2026-09-27

### Added

- `derived/`, a folder for files made by NTNU from the published material or brought in from earlier NTNU Shiplab projects, with a README giving source, method, limitations and licence for each file.
- `derived/3d/gunnerus.glb`: a 3.6 MB simplified glTF of the C-JOB 3D model, with parts grouped by SFI group and 17 equipment items matched to the C-JOB list of main equipment; `derived/3d/gunnerus-parts.json` describes each part.
- Website viewer: colour and filter by SFI group, presets, section cuts (from the bow, and at the centreline) and click-to-identify.
- `derived/3d/gunnerus-visual.glb`: the textured visual model from vessel.js (2020), with textures compressed to WebP (31.8 MB → 10.9 MB).
- `derived/vesseljs/gunnerus.json`: the vessel.js ship specification (hull offsets, decks, bulkheads, compartments and tanks), and `derived/vesseljs/offsets.csv` with the offsets in metres.
- A *Related projects* section in the README, linking the vessel.js Gunnerus examples and the OpenBridge simulator demo.
- A photo of the vessel (2014, Fredrik Skoglund) in the README, and a render of the visual model in `derived/3d/`.

### Changed

- The website now takes its 3D model from `derived/3d/gunnerus.glb`; the duplicate `pages/assets/gunnerus.glb` was removed.

## [1.0.0] – 2026-09-26

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

[Unreleased]: https://github.com/shiplab/gunnerus/compare/v1.0.3...HEAD
[1.0.3]: https://github.com/shiplab/gunnerus/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/shiplab/gunnerus/compare/V1.0.1...v1.0.2
[1.0.1]: https://github.com/shiplab/gunnerus/compare/v1.0.0...V1.0.1
[1.0.0]: https://github.com/shiplab/gunnerus/releases/tag/v1.0.0
