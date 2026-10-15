- `web/`: Browser page, service worker and icons.
- `patches/`: Emscripten changes to upstream SpaghettiKart and libultraship.
- `scripts/`: Build, serve, publish, patch regeneration and texture-pack trimming.
- `tests/`: Playwright harnesses.
- `media/`: Phone showcase screenshots and videos.
- `courses/`: Editable custom courses and their runtime archives.
- `docs/`: Playing, development, testing and deployment guides.

Keep changes focused and as simple as possible: no gold plating, over-architecting, over-engineering or over-testing.

Prefer `make` targets over direct commands - run `make help` for targets.
Run `make can-release` after any changes to validate; it needs no build or ROM. `make test/layout`, `test/rom`, `test/race` and `test/course` need `make build`, and the last three `ROM=`.
Edit engine code in the patched tree under `$WORK/SpaghettiKart`, keep it under `#ifdef __EMSCRIPTEN__`, then run `make patches`. Never hand-edit `patches/`.

Never commit or deploy ROMs or anything extracted from them (`*.z64`, `*.o2r`, `baserom*`).
The one tracked `.o2r` is `courses/silverstone/runtime/silverstone-v1.9.o2r`: original course assets, nothing from the ROM.
