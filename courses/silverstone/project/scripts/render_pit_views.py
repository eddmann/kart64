"""Current pit entry, garage lane and merge preview cameras."""
from pathlib import Path
import bpy,json
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'silverstone-hd-preview.blend'))
s=bpy.data.scenes['Silverstone — Complete Course'];c=s.camera;s.cycles.samples=12;s.cycles.use_denoising=False
s.render.resolution_x=1600;s.render.resolution_y=1000;s.render.threads_mode='FIXED';s.render.threads=3
for name,pos,target,lens in [('pit-shortcut-entry',(281,-220,60),(170,-123,1),30),('pit-shortcut-lane',(36,-100,5),(40,130,4),28),('pit-shortcut-exit',(73,245,26),(16,293,2),32)]:
 c.location=Vector(pos)*.06;c.rotation_euler=(Vector(target)*.06-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='PERSP';c.data.lens=lens;c.data.clip_end=500
 s.render.filepath=str(R/'previews'/f'{name}.png');bpy.ops.render.render(write_still=True,scene=s.name);print('PIT_VIEW_READY',name,flush=True)
