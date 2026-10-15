# Building and developing Kart64

[Back to Kart64](../README.md)

The repository holds the browser frontend, patches to the upstream engine,
and the tools needed to build them together. The game itself is not vendored:
`make build` fetches SpaghettiKart, applies the two patches, and compiles it
with Emscripten through [`scripts/build.sh`](../scripts/build.sh). Run `make`
on its own to list every target.

## Repository layout

```text
patches/   changes to upstream SpaghettiKart and libultraship
web/       ROM intake, extraction, layout, touch controls and browser assets
scripts/   build, serving, deployment, patch regeneration and pack trimming
tests/     Playwright harnesses
courses/   editable courses, original textures, generators and build notes
media/     phone-mode screenshots and complete source recordings
docs/      playing, texture packs, development, testing and deployment
```

The build pins SpaghettiKart to
`aedcf9ada627f4f8e861f12d8b48f587de521e6b` and defaults to emsdk **6.0.3**.

## Build and run locally

Requirements: Git, CMake 3.28+, Ninja, Python 3, and Node 24 (see `.nvmrc`).
The build script installs emsdk itself. Run these commands from the repository
root; `WORK` chooses the directory for the upstream checkout and toolchain, and
defaults to `~/kart64-work`.

```sh
make build
make start
```

Open `http://localhost:8099/`, press **Start**, and choose your ROM.
`make build` can be rerun after changing a patch or the page; it rebuilds what
has changed.

## Change the engine

Edit the patched tree under `$WORK/SpaghettiKart`, rebuild, then regenerate
the repository patches:

```sh
make patches
```

Keep engine changes under `#ifdef __EMSCRIPTEN__`. Use the regeneration script
to update `patches/`; extracted ROM assets can generate headers in the upstream
tree that should not enter a patch.

For frontend changes, edit `web/` and rerun `make build` to copy the page
into the build directory. For course editing and rebuilding, see
[courses/](../courses/README.md).

## Game assets stay local

ROM files and extracted game assets, including `mk64.o2r`, are never committed
or deployed. `.gitignore`, `scripts/make-dist.sh`, and `scripts/serve.py`
enforce that boundary. Each player extracts from their own ROM in their own
browser.

Next: [run the checks](testing.md) or [prepare a deployment](deployment.md).
