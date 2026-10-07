# Texture packs

[Back to Kart64](../README.md)

An optional texture pack gives the familiar tracks and characters a sharper
finish. Choose **Texture pack** on the start page and load a pack made for
SpaghettiKart, such as the HD build of
[MK64 Reloaded](https://github.com/GhostlyDark/MK64-Reloaded).

Bring your own file, as with the ROM. The browser keeps it on disk until you
remove it and loads it into memory when the game starts.

## Choosing a pack for a phone

A phone needs a lighter cut of the pack. In the measured full HD build,
memory keeps growing during a race to about 1.8 GB with its kart sprites,
until Safari closes the tab.

[`scripts/trim-pack.py`](../scripts/trim-pack.py) makes a smaller copy for your
own use. At half texture resolution with karts at 96×96 — one and a half times
the game's own sprite resolution — MK64 Reloaded's HD build becomes about
133 MB. A full race peaks at about 940 MB, compared with 614 MB without a pack.
Without HD kart sprites, the pack is about 50 MB and the race peaks at about
760 MB. These are measurements of the tested build, rather than limits for
every pack or device.

## Make a lighter copy

Run from the repository root. Resizing requires Python 3 and Pillow; the
target uses `uv` to supply Pillow:

```sh
make pack/trim PACK=mk64-reloaded-v2026.04.03-sk-hd.o2r OUT=mk64-reloaded-phone.o2r
```

Use the path to your pack for `PACK`. The options default to
`--scale 0.5 --kart-scale 0.375`; set `PACK_ARGS` to choose others. The output is a
separate file; select it with **Texture pack** when starting Kart64.

- `--scale 0.5` halves the width and height of the other textures.
- `--kart-scale 0.375` keeps the kart sprites and reduces them to 96×96
  when the input uses 256×256 sprites.
- Without `--kart-scale` or `--keep-karts`, the script drops the HD kart
  sprites and the game uses its original sprites.
- `--drop <folder>` removes another folder under `textures/`; repeat the
  option to remove more than one.

The [phone showcase](../media/mario-raceway/README.md) uses a separate
**phone karts128** cut. Its complete videos and screenshots are included in
the repo; the pack itself remains a user-provided file. The pack's terms
determine whether a trimmed copy may be shared.
