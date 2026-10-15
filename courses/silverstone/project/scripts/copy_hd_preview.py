"""Pack all HD library textures in the current preview, including two spare signs."""
from pathlib import Path
import json,bpy
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'silverstone-preview.blend'))
manifest=json.loads((R/'textures/hd/manifest.json').read_text())
for info in manifest.values():
 image=bpy.data.images.load(str(R/'textures/hd'/info['file']),check_existing=True);image.use_fake_user=True;image.pack()
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(R/'silverstone-hd-preview.blend'))
print('CURRENT_HD_PREVIEW_READY')
