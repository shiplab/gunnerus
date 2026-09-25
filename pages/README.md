# Showcase page

Source for the GitHub Pages site that presents this repository, <https://shiplab.github.io/gunnerus/>. It is deployed by [`.github/workflows/pages.yml`](../.github/workflows/pages.yml), which assembles the site from three places:

| Site path | Copied from |
| --- | --- |
| `/` (page, thumbnails, logo) | this folder, `pages/` |
| `/metadata/gunnerus_metadata.json` | [`metadata/gunnerus_metadata.json`](../metadata/README.md) |
| `/assets/gunnerus.glb` | [`derived/3d/gunnerus.glb`](../derived/README.md) |

## Files in this folder

| Path | Contents |
| --- | --- |
| `index.html` | The page itself: 3D viewer, drawing gallery, documents, metadata explorer, credits and licence. Loads three.js from jsDelivr and fonts from Google Fonts. |
| `assets/thumbs/*.webp` | First-sheet previews of the 15 drawings, rendered from the PDFs and trimmed. |
| `assets/ntnu-logo.svg` | NTNU logo (colour, horizontal). |

The 3D model is kept in [`derived/`](../derived/README.md), not here, so there is only one copy. That folder's README explains how it was made.

## Local preview

Serve the repository root and open `/pages/`:

```sh
python3 -m http.server 8000   # then http://localhost:8000/pages/
```

When a file is not next to the page, the page falls back to the repository copy: `../derived/3d/gunnerus.glb` for the 3D model, and `../metadata/` then raw.githubusercontent.com for the metadata.
