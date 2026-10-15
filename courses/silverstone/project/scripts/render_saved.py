"""Render an existing exported source scene without regenerating its game assets."""
import argparse,json,sys,shutil
from pathlib import Path
import bpy
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;sys.path.insert(0,str(HERE))
parser=argparse.ArgumentParser();parser.add_argument('--fast64',type=Path,default=ROOT.parents[2]/'.cache/course-tools/fast64')
parser.add_argument('--samples',type=int,default=24)
parser.add_argument('--hd',action='store_true')
opts=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
sys.path.insert(0,str(opts.fast64.resolve().parent))
import fast64
fast64.register()
from render_course import render_previews
main=bpy.data.scenes['Silverstone — Complete Course'];library=bpy.data.scenes['Silverstone — Asset Library']
root=bpy.data.objects['Silverstone — Track Root'];kit=bpy.data.objects['Reusable Silverstone models']
materials={m.name:m for m in bpy.data.materials if m.is_f3d}
manifest=json.loads((ROOT/'textures/manifest.json').read_text())
textures={name:bpy.data.images['silverstone_'+name] for name in manifest}
if opts.hd:
 textures={name:bpy.data.images.load(str(ROOT/'textures/hd'/info['file']),check_existing=True) for name,info in manifest.items()}
if opts.hd:
 for image in textures.values():image.use_fake_user=True;image.pack()
data=json.loads((ROOT/'source/geometry.json').read_text())
render_previews(main,root,library,kit,materials,textures,data,ROOT,samples=opts.samples)

if opts.hd:
 shutil.copyfile(ROOT/'silverstone-preview.blend',ROOT/'silverstone-hd-preview.blend')
