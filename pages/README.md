# Showcase page

Source for the GitHub Pages site that presents this repository. It is deployed by [`.github/workflows/pages.yml`](../.github/workflows/pages.yml), which copies this folder plus `metadata/gunnerus_metadata.json` to the site root.

| Path | Contents |
| --- | --- |
| `index.html` | The page itself: 3D viewer, drawing gallery, documents, metadata explorer, credits and licence. Loads three.js from jsDelivr and fonts from Google Fonts. |
| `assets/gunnerus.glb` | Simplified web copy of `extended/CJOB/3d models/Gunnerus 3D Model Rev0.3dm` (see below). |
| `assets/thumbs/*.webp` | First-sheet previews of the 15 drawings, rendered from the PDFs and trimmed. |
| `assets/ntnu-logo.svg` | NTNU logo (colour, horizontal). |

## How `gunnerus.glb` was made

1. Read the Rhino 8 file with `rhino3dm` and collected the render meshes cached on every Brep face and extrusion (≈4.0 M triangles). Curves and text were skipped; the one block instance sits at identity, so its members were taken once.
2. Grouped meshes by display colour, remapped three CAD highlight colours (black, magenta, green) to the hull grey, converted mm → m and Z-up → Y-up.
3. Simplified to ~40 % and compressed with `gltfpack -si 0.4 -cc` (meshopt + quantisation), giving about 3.5 MB.

The original model is by C-JOB; the web copy is a derivative and carries the same CC BY-NC 4.0 licence as the rest of the repository.

## Local preview

Serve the repository root and open `/pages/`:

```sh
python3 -m http.server 8000   # then http://localhost:8000/pages/
```

The page falls back to `../metadata/` and then to raw.githubusercontent.com if the metadata file is not next to it.
