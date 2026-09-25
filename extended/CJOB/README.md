# Drawings

The drawings are derivative works made by **C-JOB (<https://c-job.com/contact-us/nikolayev/>)** and **NTNU**, based on polarkonsult drawings of the vessel, and published by NTNU under the terms below.

| Drawing | Scale | Sheet date | Formats |
| --- | --- | --- | --- |
| `Engine Room Arrangement Rev0` (`25.1142-052-100`) | 1:100 | 2026-08-31 | `.dwg`, `.dxf`, `.pdf` (A0) |
| `Construction Plan Deck and Double Bottom Rev0` (`25.1142-100-120`) | 1:50 | 2026-09-11 | `.dwg`, `.dxf`, `.pdf` (A0) |
| `Construction Plan Longitudinal Section Rev0` (`25.1142-100-121`) | 1:50 | 2026-09-25 | `.dwg`, `.dxf`, `.pdf` (A0) |
| `Construction Plan Transverse Section Rev0` (`25.1142-100-122`) | 1:50 | 2026-09-25 | `.dwg`, `.dxf`, `.pdf` (A0) |
| `Draught and Hullmarks Rev0` (`25.1142-650-102`) | 1:50 (marking details 1:10) | 2026-09-11 | `.dwg`, `.dxf`, `.pdf` (A0) |
| `Freeboard Plan Rev0` (`25.1142-000-019`) | 1:150 | 2026-09-25 | `.dwg`, `.dxf`, `.pdf` (A0) |
| `Retractable Telescopic Diver's Platform Arrangement Rev0` (`25.1142-560-000`) | 1:25 | 2026-09-25 | `.dwg`, `.dxf`, `.pdf` (A0) |
| `Safety Fire Zone Plan Rev0` (`25.1142-570-100`) | 1:100 | 2026-09-11 | `.dwg`, `.dxf`, `.pdf` (A0) |
| `Tank Arrangement Rev0` (`25.1142-000-009`) | 1:100 | 2026-09-11 | `.dwg`, `.dxf`, `.pdf` (A0) |

Document numbers are C-JOB's own, per `25.1142-080-001-REV0-LIST OF PROJECT DOCUMENTS.pdf` in [`docs/`](docs/README.md).

## Engine room arrangement

The sheet shows the machinery spaces as a section at the centreline, a plan under 1st deck, a plan of the engine room, and three  section views (frames 0, 18 and 26).

Its main content is a **numbered equipment list of 43 items**, keyed to balloons on the plans, with quantity and capacity for each. Among them:

- 3 × main engine, 475 kW at 1800 rpm, and 3 × generator, 556 kVA at 1800 rpm
- PM azimuth drives port and starboard, with their steering gear and central shaft tanks
- 2 × frequency converter at 500 kW, one of them for the bow thruster, plus main switchboard, transformers, battery boxes and a tuned filter
- ballast, bilge, fire, fuel oil transfer and hydrophore pumps, box coolers, sewage treatment plant and oily water separator

The sheet also repeats the vessel's main particulars and tank capacities.

## Construction plan

The structural framing plan, issued as three sheets at 1:50 (an earlier single-sheet `Construction Plan Rev0` at 1:100 has been superseded and removed):

- **Deck and double bottom** — 1-deck, tanktop/single-bottom and A-deck framing plans, plus the wheelhouse-top and superstructure-top structure.
- **Longitudinal section** — the structural section at the centreline, keel to wheelhouse top, with scantling callouts.
- **Transverse section** — numbered frame sections along the length (including the transom), plus stringer, floor and connection details.

None of the three carries an equipment list or main-particulars table.

## Draught and hullmarks

Draft mark and hull-marking details: full profile with draft mark locations (aft, midships and forward), templates for the "GUNNERUS" name and "TRONDHEIM" homeport lettering, the bow marking, deck marking, the centre-of-bowthruster marking, and the underwater search-equipment markings (transducers "T" and HiPAP unit "H"), each with cutting/welding notes and scale.

## Freeboard plan

Freeboard-related openings and closing appliances: profile and deck plans (A-deck, 1-deck, below 1-deck), with schedules for air pipes, windows and scuttles, doors, hatches, ventilators and freeing ports, plus the sea inlet/outlet and sanitary discharge arrangement and a typical guardrail section. Carries its own main particulars table — see [Notes](#notes) for a data mismatch on this sheet.

## Retractable telescopic diver's platform arrangement

The stern-mounted diving platform: side, plan and end views in both stored and launched position, the main frame and movable platform frame details, and a parts/materials list.

## Safety fire zone plan

Fire safety arrangement and equipment: profile, wheelhouse and deck plans (A-deck, 1-deck, below 1-deck) with fire-fighting equipment symbols (CO₂ bottles, fire pumps, portable extinguishers, escape routes, defibrillators) and a numbered equipment/legend table. Carries its own main particulars table — see [Notes](#notes) for a data mismatch on this sheet.

## Tank arrangement

Tank arrangement in profile, below-1-deck and below-tank-top plans, with a tank schedule giving location/frame range, net volume and mass per fluid type (water ballast, fresh water, fuel oil and miscellaneous) plus the dry/cargo compartments.

## Other material in this folder

| Folder | Contents |
| --- | --- |
| [`3d models/`](<3d models/README.md>) | 3D CAD model of the hull and superstructure. ⚠️ Very large files — read that README before cloning or pushing. |
| [`docs/`](docs/README.md) | Supporting C-JOB documents: weight calculation, GT/NT calculation, specification, and the project document/equipment lists. **Licensed CC BY-SA 4.0**, not CC BY-NC 4.0 — see that folder's README. |

## Notes

Known gaps and inconsistencies in this batch, kept here for traceability rather than silently corrected (the PDFs are plotted sheets, not editable at the README level):

- **Freeboard Plan Rev0**'s main-particulars table states `BUILT YEAR 2005`, while **Safety Fire Zone Plan Rev0**'s main-particulars table states `BUILT YEAR: 2006` — the two sheets disagree, and only 2006 matches the main [README](../../README.md#vessel)'s "in service since 2006".
- `Safety Fire Zone Plan Rev0.dwg` and `Construction Plan Deck and Double Bottom Rev0.dwg` were both originally exported with a filename that didn't match their `.dxf`/`.pdf` siblings (missing the `Rev0` suffix, and a stray trailing space, respectively); both have been renamed here for consistency.
- The C-JOB project document list (`25.1142-080-001`, in [`docs/`](docs/README.md)) also lists `25.1142-000-020 Freeboard Calculation` and a `25.1142-100-123 Shell Expansion` deliverable; neither is included in this repository under those numbers (a Shell Expansion drawing does exist, but as the polarkonsult original in [`../../polarkonsult/`](../../polarkonsult/README.md)).

## License

Same terms as the rest of the repository — CC BY-NC 4.0, and the sheets themselves carry the wording *open use for research/teaching and other non-commercial activities, commercial use is not permitted without approval*. See the main [README](../../README.md#credit--license) and [LICENSE](../../LICENSE).
