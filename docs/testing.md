# Testing Kart64

[Back to Kart64](../README.md) · [Local build setup](development.md)

The Playwright harnesses cover the startup page, layouts, ROM extraction,
phone controls, and custom courses. Install the test dependencies and Playwright's Chromium
from the repository root:

```sh
make deps
```

`make can-release` runs the checks that need neither a build nor a ROM: script
syntax, a check that no ROM-derived files are tracked, a dependency audit, and
the startup gate test.

## Startup and layout

```sh
make test
make test/layout
```

The gate check needs no engine build. The layout check needs a local build
from `make build` but no ROM.

## ROM, races and custom courses

```sh
make test/rom ROM=~/roms/mk64.z64
make test/race ROM=~/roms/mk64.z64
make test/course ROM=~/roms/mk64.z64
```

Use the path to your own ROM for `ROM`.

| Harness | Coverage |
|---|---|
| `rom-test.mjs` | ROM selection, extraction, reload from cache, and reset |
| `race-test.mjs` | Phone touch input through menus, racing, pause, rotation, and results |
| `course-test.mjs` | Silverstone from the in-game Custom menu: a standalone race, Change Course, and Time Trial saves |

The ROM is read from your disk and fed to the page's file input; it is never
copied into the repository or served over HTTP.

The [phone showcase](../media/mario-raceway/README.md) contains simulator
recordings with automated steering. They illustrate the layouts and textures;
the race harness covers touch interaction. Silverstone's more detailed course
validation is in [its validation notes](../courses/silverstone/docs/VALIDATION.md).
