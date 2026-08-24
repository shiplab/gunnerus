# Gunnerus metadata

Machine-readable metadata for R/V Gunnerus, extracted from the general arrangement drawing in [`../polarkonsult/`](../polarkonsult/).

| File | Contents |
| --- | --- |
| [`gunnerus_metadata.json`](gunnerus_metadata.json) | Vessel identity, main dimensions, capacities, tank list, deck-by-deck space list and equipment inventory, each entry classified by SFI group and where possible cross-referenced to DNV VIS/GMOD |

## Where the data comes from

Everything in the file is read off **GA drawing 165821B7** — its title block, deck plans, inboard profile and section views. Nothing is taken from class documents, the stability book or the yard's specification, so the file is a structured index of one drawing, not an authoritative description of the ship. Check any value against the current ship documents before relying on it operationally.

The published sheet is the open-data issue based on `165821B7 Rev1`, and it does not print a revision table. Accordingly `vessel_identity.revision_history` holds a single entry — `Rev1`, *Publish*, 2026-08-21 — rather than the production drawing's earlier revision history.

Provenance is tracked inside the file: each top-level block carries a `_source` field naming the part of the drawing it came from, and individual equipment entries carry their own `source`.

## Structure

| Key | Contents |
| --- | --- |
| `_schema_note` | How the file was built and which classification schemes it uses |
| `vessel_identity` | Name, call sign, owner, port of registry, designer, drawing reference and the revision entry for the published issue |
| `classification_regulatory` | Flag authority, class society and class notation |
| `main_dimensions` | Lengths, breadth, depths, draughts, gross tonnage, frame spacing and frame numbering convention |
| `capacities` | Aggregate fuel oil, fresh water, ballast, cargo hold and deadweight figures from the title block |
| `tanks` | 26 tank entries — number, content, capacity, SFI subgroup and location |
| `general_arrangement` | 5 decks (Wheelhouse, A-Deck, 1-Deck, Below 1-Deck, Tank Top) holding 38 spaces, each with area where the drawing prints one |
| `equipment_inventory` | 14 distinctly labelled or identifiable items — A-frame, deck crane, stern gantry, winch, hatches, propulsion, engines, switchboards, mast, funnels, lifeboat, bridge console |
| `vis_gmod_top_level_reference` | Lookup table for the VIS/GMOD top-level nodes used in `vis_gmod_ref` fields |

## Classification schemes

Entries are classified primarily by the **SFI Group System**, the standard maritime cost and technical classification, through `sfi_maingroup` / `sfi_group` / `sfi_subgroup` fields with a plain-language `sfi_desc`.

Where the mapping is unambiguous, a cross-reference to the **DNV VIS/GMOD v3.10a** top-level node is added as `vis_gmod_ref` (with `vis_gmod_ref_desc`). These are top-level nodes only — 100 Main structure, 400 Propulsion and steering, 600 Machinery and piping, and so on — not full GMOD paths. See <https://docs.vista.dnv.com/docs/resources/vis/v3-10a>.

## Conventions

- Units are named in the key: `_m`, `_mm`, `_m3`, `_m2`, `_t`, `_deg`. Dates are ISO `YYYY-MM-DD`.
- `null` means *the drawing does not state this value* — it is not zero and not "not applicable".
- Frame numbering runs 0 at the aft perpendicular to 60 at the forward perpendicular, at 500 mm spacing, with lettered sub-frames amidships.

## Known limitations

These are recorded in the file itself as well; they are repeated here so they are visible before anyone loads the data.

- **The tank list does not reconcile with the capacity totals, and is superseded by the tank plan.** Some tanks appear twice — once numbered on the tank top plan, once generically in the inboard profile — and 7 of the 26 entries carry no tank number. They were flagged rather than merged, so the itemised capacities will not sum to the rounded system totals in `capacities`. Tank plan `166151A3` in [`../polarkonsult/`](../polarkonsult/) settles this: it numbers every tank 1–15, gives each one a frame range, net volume and mass per fluid type, and totals 180.03 m³. Use it, not this array, when the tank data matters.
- **The propulsion units are inferred, not confirmed.** They are identified as cycloidal (Voith-Schneider type) from the wheel geometry in the aft view; the drawing never names them. The entry carries `"confidence": "inferred_from_geometry"`.
- **The equipment inventory is not a full outfit list.** Unlabelled items with no unambiguous visual identity — small deck fittings, valves — were left out rather than guessed at.
- **Some figures disagree with the other two drawings.** Deadweight is 164 t here against 169 t on the lines plan in [`../extended/CJOB/`](../extended/CJOB/), and depth to A-deck is 6.60 m against the lines plan's 6.687 m. Every value in this file matches the GA sheet, which is its source; the main [README](../README.md) tabulates the differences across all three drawings.

## License

Same terms as the rest of the repository — CC BY-NC 4.0, see the main [README](../README.md#credit--license) and [LICENSE](../LICENSE).
