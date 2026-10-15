# Silverstone

[Back to courses](../README.md)

An original, stylised Silverstone GP circuit for Kart64 and native SpaghettiKart:
the full GP route with every named corner, the Wing and National pit buildings,
grandstands, spectator banks and an optional Wing pit shortcut that bypasses
Vale and Club. CPU racers follow the GP route. The scenery uses 50 original
texture designs and 24 reusable models.

The editable Blender projects, original textures, generators and geographic
input are here, along with one compressed runtime archive and a small viewing
gallery. No ROM, extracted Nintendo assets or texture pack is included.

## Play it

In Kart64, choose Grand Prix or Time Trials and a driver, then press **Up** from
the cup row to open **Custom** and confirm Silverstone with **A** twice. **B**
returns to the original courses. See the [playing guide](../../docs/playing.md#custom-courses).

For native SpaghettiKart (tested against
`aedcf9ada627f4f8e861f12d8b48f587de521e6b`), copy
`runtime/silverstone-v1.9.o2r` into the game's `mods/` directory, restart, enable
Debug Mode and choose **Silverstone** in the title-screen track selector.

## Build it

Tested with Blender **4.3.2**, Python **3.12** and HarbourMasters Fast64
`0f7a80a6b40c73a8d65dd2dab37310c163f54c68`. The texture generators expect DejaVu
Sans Bold at `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf`; Linux is
the validated build environment. From the repository root:

```sh
python3.12 -m venv courses/.venv
courses/.venv/bin/python -m pip install -r courses/requirements.txt
courses/.venv/bin/python courses/setup_fast64.py
courses/.venv/bin/python courses/silverstone/build.py --blender /path/to/blender
```

The build writes `build/silverstone-v1.9.o2r`; all output is ignored by Git.
Add `--regenerate-textures` to regenerate the procedural art, or `--from-blend`
to export your edits to `project/silverstone.blend` instead of regenerating the
meshes. Once a rebuild is tested, update the committed archive and
`web/courses.json` with:

```sh
python courses/silverstone/bundle_runtime.py
```

[How it is built](docs/BUILD.md) covers the pipeline, files and reusable models;
[validation](docs/VALIDATION.md) covers what has been tested and what remains.

## Media

The [gallery](media/README.md) has 24 screenshots and overview renders, a
complete native lap as Mario, and a side-by-side comparison with Max
Verstappen's 2025 British GP pole lap from the official Formula 1 onboard. The
native footage uses AI-assisted driving and the separate MK64 Reloaded pack for
the stock characters and HUD.

## Credits

The geographic outline is derived from
[bacinger/f1-circuits](https://github.com/bacinger/f1-circuits) under the included
[MIT licence](project/source/circuit-data-LICENSE.txt). Road widths, elevation,
landscape, models and textures are artistic approximations, not a surveyed or
licensed reconstruction. Reference photos informed the design; their pixels are
not redistributed. [sources.json](references/sources.json) lists them.
