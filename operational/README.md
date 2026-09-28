# Operational data

Measurements from RV Gunnerus in service: ship motion, position, machinery and the sea around her. Each folder is one case, tied to a published study that describes it.

| Case | Date | What | Study |
| --- | --- | --- | --- |
| [`wave-shielding-2023/`](wave-shielding-2023/README.md) | 31 Oct 2023 | Seven headings on DP in Breisundet: ship motion, crane-tip motion, incident and sheltered waves | Wang et al. (2025), *Ocean Engineering* 320, 120189 |

## Conventions

- **Time** is UTC, ISO 8601 (`2023-10-31T10:00:00.000Z`), in a `time_utc` column.
- **Units** are in the column names (`_deg`, `_m`, `_ms2`, `_kn`, …) and described in each case's `channels.csv`.
- **Files** are CSV, gzipped when large. Empty cells are missing values.
- **Cases** carry a `case` column linking every row to the case table (`cases.csv`).
- **Raw data** is not stored here; each case has the script that produced its files from the raw data.

## Credit and licence

Each case README names the study the case comes from, and that study is the reference for the experiment and its results. The datasets in this folder are organised by Jisang Ha and Henrique M. Gaspar (NTNU).

Licensed [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/), like the rest of the repository.
