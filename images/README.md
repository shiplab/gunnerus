# Images

Images used in the main [README](../README.md). Not production drawings — see [`../polarkonsult/`](../polarkonsult/README.md) and [`../extended/CJOB/`](../extended/CJOB/README.md) for those.

| File | Used for |
| --- | --- |
| `gunnerus-header.png` | The banner at the top of the main README: the general arrangement (profile and 1-deck, from `polarkonsult/GA Gunnerus Rev1.pdf`), the 3D model coloured by SFI group (from [`../derived/3d/gunnerus.glb`](../derived/README.md), colours as on the website) and heading, roll and wave height from the [wave-shielding case](../operational/wave-shielding-2023/README.md). Built by `make_header.py`. |
| `make_header.py` | Rebuilds `gunnerus-header.png` from the repository: `python3 images/make_header.py` from the repository root. Needs Pillow, pandas, matplotlib, Playwright with Chromium and poppler (`pdftoppm`); see the script header. |
| `gunnerus-3d.png` | The earlier 3D model render (no longer at the top of the main README). Rendered from the simplified web copy in [`../derived/3d/gunnerus.glb`](../derived/README.md), itself derived from the C-JOB 3D model. |
| `gunnerus-photo-2014.jpg` | Photo of R/V Gunnerus from starboard, in the *The vessel* section of the main README. Taken in 2014 (camera date), before the lengthening. Photo: Fredrik Skoglund. From the vessel.js repository. |
| `ga-preview.png` | An excerpt of the general arrangement drawing. |

This folder replaces the old `docs/images/` path used in earlier revisions of this repository; update any bookmarked links accordingly.

## License

Same terms as the rest of the repository — CC BY-NC 4.0 — except `gunnerus-photo-2014.jpg`, which stays with its photographer, Fredrik Skoglund, and must be credited to him. It is not covered by the CC licence. See the main [README](../README.md#licence) and [LICENSE](../LICENSE).
