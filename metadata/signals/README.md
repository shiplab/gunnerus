# Signals: the ship as a set of sensors

Gunnerus has many sources of data (the engine vendor's Modbus list, the power management system, HEMOS, the 2023 logger, the 2019 asset model). The same quantity has a different name, unit convention and classification in each. This folder holds our crosswalk of 53 signals and a test of how well an AI model translates the names. The page [`pages/signals.html`](../../pages/signals.html) shows it.

## Files

| Path | Contents |
| --- | --- |
| `gunnerus-signal-crosswalk.csv` | One row per signal (E01–E14 engine 1, P01–P10 power management, T01–T11 thrusters and drives, N01–N12 navigation and environment, C01–C06 crane): names in each source, quantity kind, canonical unit, SFI code and name, VIS/GMOD level 1, documented unit or scaling, whether it is in the 2023 cruise-week logger, logged range, note. |
| `data/engine_2019_1min.csv.gz` | Engine log from 21 Nov 2019, 08:30–14:10, 1-minute means, 37 columns (`ME1_`, `ME2_`, `ME3_` plus `m2InsideTemp`), already in engineering units. 340 rows. |
| `data/docking_2019_10s.csv.gz` | Docking log from 9 Nov 2019, 08:20–10:30, 10-second means: position, speeds, attitude, thruster angle, rpm and force, feedback and order. 780 rows. |
| `translator-test/` | `armA_input.json`, `armB_input.json` (the blind inputs), `armA_answers.json`, `armB_answers.json`, `key.json` (item to signal id) and `grade.py`. |
| `scripts/build_page_data.py` | Builds `pages/assets/signals/signals.json` from the files above and the power and energy case. Needs pandas and numpy. |

## Things to know

- **Time.** The 2019 files have a `time_logged` column with no time zone, because the logs do not state one. The 2023 series is UTC.
- **Position.** In the 2019 docking log latitude and longitude are `ddmm.mmmm` (for example 6228.146161 is 62° 28.146161′), not decimal degrees. The 2023 series is in decimal degrees.
- **Units.** Two items are unconfirmed: the thruster feedback is documented both as a percentage and as rpm, and the surge speed unit is not confirmed. See the notes in the crosswalk.
- **SFI codes** come from the 2019 TM Master tree. The codes for wind and waves are provisional, and E13, T10 and N12 have no code.
- **Not published.** Vendor documents and PLC dumps are vendor material. Only our own crosswalk (names, meaning in our words, units, status) is published, and nothing from the third-party wave sensor beyond its existence.

## The translator test

53 signals, two arms, one run each. Arm A received only the native names. Arm B also received the source device and the vendor's documentation note. Each was asked for quantity kind, canonical unit, SFI code and whether a human must check. The answers were graded against our own crosswalk, which is not independent ground truth.

| | Arm A (names) | Arm B (names + note) |
| --- | --- | --- |
| Quantity kind right | 51 / 53 | 52 / 53 |
| Unit right, clear cases | 35 / 38 | 37 / 38 |
| Contradictions and format traps flagged | 3 / 15 | 15 / 15 |
| SFI main group right | 1 / 36 | 0 / 36 |
| Items asking for a human | 25 / 53 | 37 / 53 |

Reproduce the grading with `python3 metadata/signals/translator-test/grade.py`.

## Licence

CC BY-NC 4.0, like the rest of the repository. The 2023 data is from Robert Skulstad (NTNU); the 2019 engine and docking logs are from the NTNU Gunnerus dashboard project 2019–2020.
