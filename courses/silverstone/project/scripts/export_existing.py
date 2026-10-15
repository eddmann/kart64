"""Export the current Complete Course scene of an already-open Blender project."""
import argparse
import json
import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--fast64', type=Path, required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
sys.path.insert(0, str(args.fast64.resolve().parent))
import fast64
fast64.register()

scene = bpy.data.scenes['Silverstone — Complete Course']
bpy.context.window.scene = scene
scene.hm64_mk64_export_path = str(ROOT / 'export')
scene.hm64_mk64_export_name = 'silverstone'
root = scene.objects['Silverstone — Track Root']
bpy.ops.object.select_all(action='DESELECT')
root.select_set(True)
bpy.context.view_layer.objects.active = root
result = bpy.ops.scene.mk64_export_course()
if result != {'FINISHED'}:
    raise RuntimeError('Fast64 export failed: ' + str(result))
meshes = [obj for obj in root.children if obj.type == 'MESH']
report = {'edition': '1.9.0', 'triangle_budget': 72000,
          'mesh_triangles': sum(len(obj.data.polygons) for obj in meshes),
          'mesh_objects': len(meshes), 'runtime_tested': False}
(ROOT / 'source/build-report.json').write_text(json.dumps(report, indent=2) + '\n')
print('EDITED_COURSE_EXPORT_SUCCESS')
