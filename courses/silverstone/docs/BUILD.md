# Building Silverstone

[Back to Silverstone](../README.md)

## Files

| Path under `project/` | Purpose |
| --- | --- |
| `silverstone.blend` | Main editable Fast64 course, with Complete Course and Asset Library scenes |
| `silverstone-hd-preview.blend` | Render-ready course with all 50 original HD images packed |
| `silverstone-fast64-assets.blend` | Library of the 24 reusable models |
| `silverstone-hd-assets.blend` | The same models with HD materials |
| `textures/`, `textures/hd/` | Original logical and HD source PNGs, with manifests |
| `scripts/` | Geometry, artwork, export, packaging and validation |
| `source/silverstone-layout.geojson` | GP outline, derived from MIT-licensed circuit data |
| `source/geometry.json`, `source/pit-shortcut.json` | Prepared centreline, widths, elevation, and pit floors and walls |
| `source/scene-defaults.json` | Scene template from upstream's Harbour track |

The Blender images are packed, so the projects open without a ROM or reference photos.

## Pipeline

`../build.py` copies the scripts, source data and textures into the ignored
`../build/work/project/` and works only there, using the Fast64 checkout from
`courses/setup_fast64.py`.

1. `prepare_pit_lane.py` generates the GP and pit geometry from the outline.
2. `build_course.py` builds the course scene (road, collision, waypoints, sky
   and scenery), saves a working `silverstone.blend` and exports it with Fast64.
3. `package_course.py` stabilises materials, draws the minimap, applies scene
   defaults and item positions, and packages the course.
4. `package_hd_course.py` swaps in the HD PNGs, keeping geometry, collision and AI.
5. `validate_course.py`, `validate_blend.py` and `check_clearance.py` check the
   result before it is copied to `../build/silverstone-v1.9.o2r`.

`--regenerate-textures` also runs `make_textures.py` and `make_hd_textures.py`,
whose fixed seeds reproduce the original designs. Otherwise the checked-in PNGs
are used, so edits to them are kept; update the HD manifest hashes when you
change one. `--from-blend` exports your saved edits to the **Silverstone —
Complete Course** scene instead of regenerating the meshes. The validators
expect the current road, sky and textures, so large layout changes need matching
input and validator changes. Edit runtime geometry in the main project, not the
HD one.

Keep source and resource names distinct on case-insensitive filesystems:
ground slabs use `concrete.png`, while barriers and buildings use
`structural_concrete.png`.

## Units and engine constraints

Source coordinates are metres, exported at six game units per metre (Fast64
scale 100). The 5.89 km GP outline is resampled into 842 waypoints. The road is
36 metres wide, narrowed at tight bends so the offset edges don't fold.
Elevation is a shallow synthetic profile, not surveyed.

HD textures are 16× the logical tiles on each axis, at the logical resource path
plus `.png`.

**Collision walls must sort before floor meshes in `data_track_sections`.** The
pinned engine keeps collision-filter state between mesh loads, and floors first
discards valid pit triangles. The **Barrier pit collision** object name keeps
that order. Keep `stabilize_materials.py` in any manual export.

Most runoff beyond the race barriers is scenery; the pit shortcut is the one
extra physical route.

## Renders and model libraries

To regenerate the HD project and model libraries after a build, from
`courses/silverstone/build/work/project/`:

```sh
blender --factory-startup -b silverstone.blend -t 4 --python-exit-code 1 --python scripts/render_saved.py -- --fast64 /absolute/path/to/fast64 --hd --samples 12
blender --factory-startup -b --python-exit-code 1 --python scripts/copy_hd_preview.py
blender --factory-startup -b --python-exit-code 1 --python scripts/export_reusable_library.py
```

Review the new files before copying them into `project/`, and keep preview
renders out of Git.

The libraries hold the 24 models with local origins:
- buildings: Wing modules, National garages, control tower and marshal hut
- stands: covered and open stands, the grouped stand module and spectator bank
- trackside: tyre barrier, Armco, gantry, advertising gantry and event display
- pit and paddock: pit trolley, pit boom, service vehicle, tent, concession
  kiosk, picnic table and camera platform
- scenery: tree, flagpole, lighting mast and windsock

Reuse them for future courses at the same scale, and credit any new third-party
inputs.
