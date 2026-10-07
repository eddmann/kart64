#!/usr/bin/env python3
"""Make a lighter copy of a SpaghettiKart texture pack, for phones.

Usage: trim-pack.py <pack.o2r> [out.o2r] [--keep-karts] [--kart-scale 0.375]
                    [--drop <folder> ...] [--scale 0.5]

A pack replaces the game's textures with bigger ones, and the engine keeps
every texture it has drawn. Most of an HD pack is usually kart sprites: MK64
Reloaded's HD build holds 9,513 kart frames at 256x256 (300 of its 444 MB),
and a race draws every kart from every angle, so memory climbs until a phone's
browser closes the tab. By default this drops textures/karts (the karts keep
the game's own sprites; everything else stays HD). --drop removes further
folders under textures/, such as player_selection (the large character
portraits on the menus).

--kart-scale keeps the kart sprites but shrinks them by that factor (needs
Pillow): MK64 Reloaded's at 0.375 are 96x96, one and a half times the game's
own, and cost 36 KB each instead of 256 KB.

--scale shrinks every texture by that factor (needs Pillow): at 0.5 an HD
pack's textures are still twice the game's own resolution and take a quarter
of the memory. The engine scales a replacement to its original's size, so any
size works. Otherwise entries are copied as they are.

The output is for your own use: the pack's terms decide whether you may share
it.
"""
import sys
import zipfile

args = sys.argv[1:]
keep_karts = "--keep-karts" in args


def option(name, default):
    if name not in args:
        return default
    i = args.index(name)
    value = float(args[i + 1])
    del args[i:i + 2]
    return value


scale = option("--scale", 1.0)
kart_scale = option("--kart-scale", None)
if kart_scale is not None:
    keep_karts = True
drops = []
while "--drop" in args:
    i = args.index("--drop")
    drops.append(args[i + 1].strip("/"))
    del args[i:i + 2]
args = [a for a in args if not a.startswith("--")]
if not args:
    sys.exit(__doc__)
src = args[0]
dst = args[1] if len(args) > 1 else src.rsplit(".", 1)[0] + "-phone.o2r"
if not keep_karts:
    drops.append("karts")
prefixes = tuple("textures/" + d + "/" for d in drops)
if scale != 1.0 or kart_scale is not None:
    import io
    from PIL import Image


def shrink(data, scale):
    img = Image.open(io.BytesIO(data))
    w, h = max(1, round(img.width * scale)), max(1, round(img.height * scale))
    out = io.BytesIO()
    img.resize((w, h), Image.LANCZOS).save(out, "PNG", optimize=True)
    return out.getvalue()

kept = dropped = 0
with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w") as zout:
    if "mods.toml" not in zin.namelist():
        sys.exit("no mods.toml in %s: not a SpaghettiKart pack" % src)
    for info in zin.infolist():
        if info.filename.startswith(prefixes):
            dropped += 1
            continue
        data = zin.read(info.filename)
        if info.filename.lower().endswith(".png"):
            s = kart_scale if kart_scale is not None and info.filename.startswith("textures/karts/") else scale
            if s != 1.0:
                data = shrink(data, s)
        zout.writestr(info, data, compress_type=info.compress_type)
        kept += 1

print("%s: kept %d entries, dropped %d (%s)%s%s" % (
    dst, kept, dropped, ", ".join(drops) or "none",
    ", textures scaled by %g" % scale if scale != 1.0 else "",
    ", karts by %g" % kart_scale if kart_scale is not None else ""))
