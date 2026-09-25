# Derived files

Files made by NTNU from the material published in this repository. They are conversions and simplifications, not new engineering data. For accurate values, always go back to the source files named below.

| File | Made from | Purpose |
| --- | --- | --- |
| [`3d/gunnerus.glb`](3d/gunnerus.glb) | [`extended/CJOB/3d models/Gunnerus 3D Model Rev0.3dm`](<../extended/CJOB/3d models/README.md>) (C-JOB) | Lightweight 3D model for web viewers, visualisation and teaching. Used by the [website](https://shiplab.github.io/gunnerus/#model). |

## 3d/gunnerus.glb

A simplified glTF 2.0 binary of the C-JOB 3D model, **3.5 MB** instead of 396 MB.

| Property | Value |
| --- | --- |
| Format | glTF 2.0 binary (`.glb`) |
| Triangles | ~1.59 million (source render meshes: ~3.98 million) |
| Units and axes | Metres, Y up (glTF convention). The source is in millimetres, Z up. |
| Origin | Same as the source model. The keel is at y ≈ 0, so y = 2.50 is the operating draught. |
| Materials | 21 flat colours, one per display colour in the source. No textures. |
| Required extensions | `EXT_meshopt_compression`, `KHR_mesh_quantization` |

### How it was made

1. Read the Rhino 8 file with [rhino3dm](https://github.com/mcneel/rhino3dm) and collected the render meshes stored on every surface and extrusion (about 3.98 million triangles). Curves and text were skipped. The one block instance sits at identity, so its members were taken once.
2. Grouped the meshes by display colour. Three CAD highlight colours (black, magenta, pure green) were remapped to the hull grey (RGB 151, 170, 174).
3. Converted millimetres to metres and Z-up to Y-up.
4. Simplified to about 40 % of the triangles and compressed with [gltfpack](https://github.com/zeux/meshoptimizer) (`gltfpack -si 0.4 -cc`).

### What is lost

- Exact geometry. The source is NURBS surfaces; this file is a simplified triangle mesh with quantised vertex positions. Do not take dimensions from it.
- Object structure. The source layers are unnamed leftovers from an IGES import, so the file carries no part names; parts are only grouped by colour.
- Curves, text and hidden objects.

### Opening it

Web viewers built on three.js or Babylon.js, and most online glTF viewers, read the compressed file directly. Some desktop tools do not support `EXT_meshopt_compression`. For those, make an uncompressed copy (about 21 MB) with gltfpack:

```sh
gltfpack -i gunnerus.glb -o gunnerus-uncompressed.glb -noq
```

gltfpack re-optimises the mesh while doing this, so the triangle count drops slightly (merged duplicate vertices and degenerate triangles).

## Licence

Derivative works of the repository material, under the same terms: **CC BY-NC 4.0**. See the main [README](../README.md#licence) and [LICENSE](../LICENSE). When you use `gunnerus.glb`, credit the source:

> Gunnerus open data, courtesy of polarkonsult, published by NTNU. 3D model by C-JOB; simplified glTF by NTNU.
> Licensed under CC BY-NC 4.0 — https://creativecommons.org/licenses/by-nc/4.0/
