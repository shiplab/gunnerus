# R/V Gunnerus 3D model from one image of the GA

This model was built from **one raster image**: `GA_Gunnerus_Rev1_300dpi.png`, a 9934 × 14042 px grayscale render of `GA Gunnerus Rev1.pdf`. The PDF was opened once to make this PNG and never again. No vector data, no other drawings and no other models were used. All geometry comes from pixels.

The earlier models (the GA-only model built from the PDF's vectors, and the Lines Plan model) appear only in the checks at the end.

## 1. Image to ship coordinates

| Quantity | How it was found in the image | Value |
| --- | --- | --- |
| Scale | Frame ruler under the outboard profile: 74 ticks found as short vertical ink runs and fitted to a line (residual 0.42 px) | **81.200 px per 500 mm frame**, i.e. 6.158 mm per px |
| Frame 0 (AP) | 4th tick, under the "0" label and the AP line | px x = 1089.8 |
| Outboard profile baseline | Long dashed horizontal ink run labelled "BL" | px y = 3427 |
| Inboard profile baseline | Same method | px y = 6042 |
| Plan centrelines | Long dash-dot horizontal runs | A-deck 7425, 1-deck 9253, below 1-deck 11143, tank top 12899 |
| Section Fr. 17 and view from aft centreline | Long vertical dash-dot run | px x = 8167 |
| Wheelhouse plan | Its own frame ruler (frame 25 at px x = 7502) and centreline at px y = 7225 | — |

These pixel distances confirm the scale and origins:

| Check | Expected | Measured |
| --- | --- | --- |
| Draught marks above the inboard BL | 2.613 m and 2.787 m | 2.617 m and 2.789 m |
| A-deck line | 6.687 m | 6.693 m |
| Frame 60 | x = 35.0 m | on the "60" label |
| Transom position | — | x = −1.005 m |

Coordinates: metres, x forward from AP (frame 0), y to port, z up from baseline.

## 2. Tracing from pixels

All tracing works on the image resampled into a ship-coordinate window (5–10 mm per sample). Ink is any pixel darker than 170/255.

| Item | Image method | Result |
| --- | --- | --- |
| Centreline bottom aft (line A) | Column scan, snapped to the nearest ink run along a rough seed line | −0.10 m at x = 13.8 rising to 1.81 m at the transom |
| Rake-of-keel line (B) | Column scan, then a straight-line fit | z = 0.0346 x − 0.584 |
| Skeg bottom (E) | Column scan | −0.79 m at the skeg's aft end (x = 1.61) to 0.21 m at x = 14 |
| Bulb and stem | 26 points, each snapped to the nearest ink pixel within 0.12 m | Bulb nose at x = 34.22 m, stem top at 35.26 m |
| Waterline at the tank-top level | Tank top plan, solid outline, column-scanned every 50 mm | 482 samples |
| 1-deck edge | Tank top plan, dash-dot outline | 136 samples |
| A-deck edge | 1-deck plan, outer outline | 214 samples |
| Bulwark top | A-deck plan, outer outline | 452 samples |
| Section Fr. 17 | Lowest ink per column (bottom), outermost ink per row (side) | Deadrise 0.122; skeg from y = 1.83 to 3.51 m, bottom 0.75 m below the centreline |
| Thruster ducts | Circles fitted by least squares to ink pixels in the view from aft | Centre (±2.70, 0.556) m; radii 1.228 / 0.947 m; hub 0.256 m |
| Decks and bulwark (aft) | Horizontal pixel projections | Aft deck 4.115 m, bulwark top 5.11 m |
| Deck step | Vertical pixel projection in the A-deck plan | x = 12.305 m |

### Waterline heights

The 1-deck, A-deck and bulwark-top outlines take their heights from the depths in the image's main dimensions table (4.287 m and 6.687 m) and from the stem top (7.52 m). The tank-top waterline's height was found where its half-breadth at Fr. 17 (4.114 m) meets the traced Fr. 17 bilge, which gives **1.167 m**.

The Fr. 17 contour was shifted 0.07 m so that its centreline bottom matches the profile's line A at x = 8.5 m.

Seed lines were placed by eye on crops of the image, only to say which line to follow. Every stored coordinate is the position of an ink pixel. Snapping moved the bow seeds by at most 0.045 m.

## 3. Building the model

### Hull

1. **Aft and midbody stations:** each one uses the Fr. 17 shape, shifted to that station's keel height and scaled vertically so that it passes through the 1.167 m waterline.
2. **Fore-body stations:** each one is a smooth curve through the keel and the 1.167 m, 4.287 m, 6.687 m and 7.52 m waterlines.
3. **Blend:** the two section families are blended between x = 21 m and x = 26 m.
4. **Skegs:** added from x = 1.61 m to about 16 m, with their bottom on line E.
5. **Bow:** trimmed to the traced centreline profile. This cut is what forms the bulb and its neck.
6. **Decks and bulwarks:** deck 4.115 m aft of x = 12.305 m and 6.687 m forward of it. Bulwarks are 120 mm thick.
7. **Meshing:** every 50 mm slice was turned into a signed-distance field, the slices were meshed with marching cubes, and the mesh was mirrored about the centreline.

### Superstructure

Each tier is the overlap of its outline in the outboard profile with its outline in the deck or wheelhouse plan. The main sizes were measured by pixel projections:

| Part | Measured from the image |
| --- | --- |
| A-deck house | Aft wall x = 14.5 m, front x = 26.71 m, sides y = ±3.50 m, roof z = 9.085 m |
| Wheelhouse | x 13.415 → 21.22 m, y ±3.50 m; window band z 10.15 → 11.39 m; roof up to 11.665 m |
| Hangar | x 8.25 → 12.295 m, y −2.77 → +3.23 m, top z = 6.985 m |
| Thrusters | From the fitted duct circles |

Mast, radar, funnel, cranes, boats, liferafts, rails and windows were read from ship-coordinate crops of the image.

## 4. Checks

Only the GA column below comes from the image. The other two columns are earlier models, shown for comparison only.

| Quantity | GA (image) | Image model | GA vector model | Lines Plan model |
| --- | --- | --- | --- | --- |
| LOA | 36.25 m | 36.25 m | 36.26 m | 36.26 m |
| Breadth | 9.60 m | 9.66 m | 9.66 m | 9.66 m |
| Displacement, d = 2.50 m | – | 528 t | 504 t | 506 t |
| Displacement, d = 2.787 m | – | 614 t | 589 t | 589 t |

For the hull-surface deviation, 4 000 points were sampled on the image hull and measured to each reference hull:

| Reference | Median | Mean | 90th percentile |
| --- | --- | --- | --- |
| Lines Plan model | 24 mm | 75 mm | 0.19 m |
| GA vector model | 3 mm | 28 mm | 0.10 m |

The image hull sits closer to the Lines Plan hull through the midbody than the GA vector hull did. In the vector build, the bilge-scaling step capped the section heights; computing them from the bilge curve fixed that here. The image hull still carries about 4 % more displacement, mostly because the fore body between the keel and the 1.167 m waterline comes out too full. The GA has no information there. `Hull_comparison_image_vector_lines.png` overlays all three hulls.

## 5. Limitations

- The fore body below 1.2 m and the bulb's width at its neck are interpolated, because the image has no waterlines there.
- The blend between the aft and fore section families (x = 21–26 m) is an assumption, not something read from the image.
- Equipment and masts are simple blocks. No interior is modelled.
- At 300 dpi, one pixel is 6.2 mm at full scale. Lines are traced to about ±1 px.

## 6. Files

| File | Contents |
| --- | --- |
| `GA_Gunnerus_Rev1_300dpi.png` | The only input |
| `Gunnerus_GA_image.glb` / `.obj` + `.mtl` / `.stl` | Full model |
| `Gunnerus_GA_image_hull.stl` | Hull with decks and bulwarks only |
| `Gunnerus_GA_image_viewer.html` | Four-view viewer with the image overlaid on each view |
| `Hull_comparison_image_vector_lines.png` | Hull check against the two earlier models |
| `scripts/` | `rimg.py` (image loading and calibration), `rtrace.py` (tracing), `hull_img.py`, `hullmesh_img.py`, `super_img.py`, `assemble_img.py`, `calib.json`, `decks.json` |
