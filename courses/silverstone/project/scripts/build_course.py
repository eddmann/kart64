"""Generate Silverstone art, a reusable asset library and Fast64 resources."""
import argparse,json,math,random,shutil,sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(HERE))
from geometry import make_geometry
from assets import Collector,Frame,wing,grandstand,old_pits,control_tower,marshal_post,tree,tyre_stack,service_vehicle,tent,gantry
from assets import flagpole,light_mast,pit_trolley,concession,picnic_table,windsock
from scenery import add_details,sky_geometry
from terrain import HeightField,grass_tint,foliage_tint
from grounds import add_ground_surfaces
from detail_assets import add_detail_passes,pit_boom,camera_platform,armco_module
from onboard_surfaces import kerb_materials, add_exit_paint, runoff_profile
from pit_lane import add_pit_details, build_pit_collision
from spectator_scenery import add_spectator_pass, compact_stand, spectator_bank, overhead_gantry, event_display
parser=argparse.ArgumentParser();parser.add_argument('--fast64',type=Path,default=ROOT.parents[2]/'.cache/course-tools/fast64')
parser.add_argument('--render',action='store_true')
opts=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
sys.path.insert(0,str(opts.fast64.resolve().parent))
import fast64
fast64.register()
from fast64.fast64_internal.f3d.f3d_material import createF3DMat
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.name='Silverstone — Complete Course'
scene.gameEditorMode='MK64';scene.f3d_type='F3DEX/LX';scene.hm64_mk64_feature_set='HM64'
scene.fast64.mk64.scale=100;scene.fast64.settings.dont_ask_color_management=True
scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
scene.hm64_mk64_export_name='silverstone';scene.hm64_mk64_export_path='//export'
scene.exportInlineF3D=False;scene.fullTraceback=True
scene.ignoreTextureRestrictions=False
data=make_geometry();P=np.array(data['points']);N=np.array(data['normals']);HW=np.array(data['half_width'])
SH=np.array(data['shoulder']);COUNT=len(P);S=data['metres_to_blender'];rng=random.Random(642026)
height=HeightField(data)
pit=json.loads((ROOT/'source/pit-shortcut.json').read_text())
pit_openings=set(pit['right_opening_segments'])
distance=np.arange(COUNT)*data['lap_metres']/COUNT
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1/S
root=bpy.data.objects.new('Silverstone — Track Root',None);scene.collection.objects.link(root)
root.hm64_mk64_obj_type='Track Root'
root['description']='Silverstone N64 art edition. Geographic GP layout; original stylised assets.'
root['game_units_per_metre']=data['game_units_per_metre'];root['runtime_tested']=False
root['source']='https://github.com/bacinger/f1-circuits — MIT'
palette={'Ivory':(.78,.81,.79,1),'Silver':(.44,.52,.57,1),'structural_concrete':(.45,.49,.47,1),
 'Roof':(.19,.24,.28,1),'Navy':(.025,.055,.085,1),'Glass dark':(.04,.11,.14,1),
 'White':(.92,.92,.86,1),'Black':(.018,.022,.028,1),'Red':(.70,.025,.04,1),
 'Blue':(.025,.17,.44,1),'Yellow':(.93,.64,.025,1),'Orange':(.92,.22,.025,1),
 'Green paint':(.025,.40,.22,1),'Bark':(.17,.10,.055,1),'Rubber':(.025,.028,.033,1),
 'Grass warm':(.22,.31,.095,1),'Grass cool':(.16,.29,.12,1),'Runway':(.23,.25,.22,1),
 'Tyre wear':(.17,.19,.20,1),'Sky':(1,1,1,1)}
materials={};textures={}
manifest=json.loads((ROOT/'textures/manifest.json').read_text())
for name,color in palette.items():
 if name in manifest:continue
 m=createF3DMat(None,preset='Shaded Solid');m.name=name;m.diffuse_color=color;m.f3d_mat.prim_color=color
 m.f3d_mat.rdp_settings.g_lighting=False
 for comb in (m.f3d_mat.combiner1,m.f3d_mat.combiner2):
  comb.A='PRIMITIVE';comb.B='0';comb.C='SHADE';comb.D='0'
  comb.A_alpha='0';comb.B_alpha='0';comb.C_alpha='0';comb.D_alpha='1'
 m.f3d_mat.set_prim=True;m.f3d_mat.rdp_settings.g_fog=False;m.f3d_mat.rdp_settings.g_cull_back=False
 materials[name]=m
manifest=json.loads((ROOT/'textures/manifest.json').read_text())
for name,info in manifest.items():
 image=bpy.data.images.load(str(ROOT/'textures'/info['file']),check_existing=True)
 image.name='silverstone_'+name;image.pack();textures[name]=image
 cutout=name in ('fence','cloud','spectators')
 m=createF3DMat(None,preset='unlit_texture_cutout' if cutout else 'unlit_texture')
 m.name=name;m.diffuse_color=(.75,.75,.75,1)
 m.f3d_mat.tex0.tex=image;m.f3d_mat.tex0.tex_format='RGBA16';m.f3d_mat.tex1.tex_set=False
 m.f3d_mat.tex0.S.clamp=name.startswith('sign_');m.f3d_mat.tex0.T.clamp=name.startswith('sign_')
 m.f3d_mat.tex0.autoprop=False
 for field,dimension in ((m.f3d_mat.tex0.S,image.size[0]),(m.f3d_mat.tex0.T,image.size[1])):
  field.low=0;field.high=dimension-1;field.mask=0 if name.startswith('sign_') else int(math.log2(dimension))
 m.f3d_mat.rdp_settings.g_lighting=False;m.f3d_mat.rdp_settings.g_fog=False;m.f3d_mat.rdp_settings.g_cull_back=False
 for comb in (m.f3d_mat.combiner1,m.f3d_mat.combiner2):
  comb.A='TEXEL0';comb.B='0';comb.C='SHADE';comb.D='0'
  comb.A_alpha='0';comb.B_alpha='0';comb.C_alpha='0';comb.D_alpha='TEXEL0' if cutout else '1'
 materials[name]=m

def make_mesh(name,verts,faces,face_materials,uvs,parent=root,collection=None,surface='ASPHALT',clip='CLIP_NONE',draw='DRAW_OPAQUE'):
 verts=np.asarray(verts,dtype=float).copy()
 if parent==root and not name.startswith('Sky'):
  verts[:,2]+=height(verts[:,:2])
 mesh=bpy.data.meshes.new(name);mesh.from_pydata([tuple(np.array(p)*S) for p in verts],[],faces);mesh.update()
 obj=bpy.data.objects.new(name,mesh);(collection or scene.collection).objects.link(obj);obj.parent=parent
 obj.hm64_mk64_surface_type=surface;obj.hm64_mk64_clip_type=clip;obj.hm64_mk64_section_id=255
 obj.hm64_mk64_draw_layer=draw
 if draw=='DRAW_INVISIBLE':obj.hide_render=True
 names=list(dict.fromkeys(face_materials));lookup={n:i for i,n in enumerate(names)}
 for n in names:mesh.materials.append(materials[n])
 mesh.uv_layers.new(name='UVMap');mesh.color_attributes.new(name='Col',type='FLOAT_COLOR',domain='CORNER')
 # Fill each attribute in one pass. Interleaved RNA writes can invalidate layer data
 # in Blender 4.3, corrupting early vertex colours with UV components.
 uv_values=np.zeros((len(mesh.loops),2),dtype=np.float32)
 color_values=np.ones((len(mesh.loops),4),dtype=np.float32)
 light=Vector((-.5,-.7,1)).normalized()
 grass_colours=grass_tint(verts[:,:2]) if 'grass' in face_materials else None
 foliage_colours=foliage_tint(verts[:,:2]) if 'leaves' in face_materials else None
 for poly,mat,uv in zip(mesh.polygons,face_materials,uvs):
  poly.material_index=lookup[mat];shade=.60+.40*max(0,poly.normal.dot(light))
  if mat.startswith('sign_') or mat in ('cloud','spectators','garage_numbers'):shade=1
  for loop,coord in zip(poly.loop_indices,uv):
   uv_values[loop]=coord
   if mat=='Sky':
    sky_height=max(0,verts[mesh.loops[loop].vertex_index][2]);t=min(1,(sky_height/2300)**.65)
    horizon=np.array([.74,.87,.94]);zenith=np.array([.21,.49,.77])
    color_values[loop]=(*tuple(horizon*(1-t)+zenith*t),1)
   elif mat=='grass':
    tint=grass_colours[mesh.loops[loop].vertex_index]
    color_values[loop]=(*tuple(tint*shade),1)
   elif mat=='leaves':
    tint=foliage_colours[mesh.loops[loop].vertex_index]
    color_values[loop]=(*tuple(tint*shade),1)
   else:color_values[loop]=(shade,shade,shade,1)
 mesh.uv_layers['UVMap'].data.foreach_set('uv',uv_values.ravel())
 mesh.color_attributes['Col'].data.foreach_set('color',color_values.ravel())
 if collection is None:
  bpy.context.view_layer.objects.active=obj;obj.select_set(True)
  mod=obj.modifiers.new('Game triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name);obj.select_set(False)
 else:
  import bmesh
  bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
 return obj

def from_collector(c,parent=root,collection=None):
 objects={}
 for name,g in c.groups.items():objects[name]=make_mesh(name,g['vertices'],g['faces'],g['materials'],g['uv'],parent,collection)
 return objects

def strip(name,lo,hi,mats,surface='ASPHALT',clip='CLIP_SURFACE',z=0,skip=()):
 verts=[];faces=[];uvs=[]
 for i in range(COUNT):
  for offset in (lo[i],hi[i]):verts.append((*tuple(P[i]+N[i]*offset),z))
  if i in skip:continue
  k=(i+1)%COUNT;faces.append((2*i,2*i+1,2*k+1,2*k))
  tile=2.5 if mats[i]=='asphalt' else 5
  v=(distance[i]/tile)%1;dv=data['lap_metres']/COUNT/tile
  uvs.append([(0,v),((hi[i]-lo[i])/tile,v),((hi[k]-lo[k])/tile,v+dv),(0,v+dv)])
 return make_mesh(name,verts,faces,[m for i,m in enumerate(mats) if i not in skip],uvs,surface=surface,clip=clip)

strip('Road',-HW,HW,['asphalt']*COUNT)
for side in (-1,1):
 a=side*HW;b=side*(HW+1.5);edge=side*(HW+1.5+SH)
 kerbs=kerb_materials(data,side)
 strip('Kerbs '+str(side),np.minimum(a,b),np.maximum(a,b),kerbs,skip=pit_openings if side==1 else ())
 strip('Grass shoulders '+str(side),np.minimum(b,edge),np.maximum(b,edge),['grass']*COUNT,'GRASS',skip=pit_openings if side==1 else ())
 verts=[];faces=[]
 for i in range(COUNT):
  pos=P[i]+N[i]*edge[i];verts.extend([(*pos,0),(*pos,3)])
  if side==1 and i in pit_openings:continue
  k=(i+1)%COUNT;faces.append((2*i,2*k,2*k+1,2*i+1))
 make_mesh('Barrier '+str(side),verts,faces,['structural_concrete']*len(faces),[[(0,0),(1,0),(1,1),(0,1)]]*len(faces),
           surface='STONE',clip='CLIP_DOUBLE_SIDED_WALL',draw='DRAW_INVISIBLE')
 # The collision envelope stays three metres high; render a lower concrete base.
 visual=[(x,y,min(z,1.25)) for x,y,z in verts]
 uv=[]
 for i in range(COUNT):
  if side==1 and i in pit_openings:continue
  u=(distance[i]/8)%1;du=data['lap_metres']/COUNT/8
  uv.append([(u,0),(u+du,0),(u+du,1),(u,1)])
 make_mesh('Barrier visible '+str(side),visual,faces,['structural_concrete']*len(faces),uv,surface='STONE')
 aa=side*(HW-.42);bb=side*(HW-.20)
 strip('Edge line '+str(side),np.minimum(aa,bb),np.maximum(aa,bb),['White']*COUNT,clip='CLIP_NONE',z=.22)
build_pit_collision(pit,make_mesh)
c=Collector()
onboard_report=add_exit_paint(c,data)
def frame_at(group,index,side=1,distance=0,face_road=False):
 i=index%COUNT;p=P[i]+N[i]*side*distance;angle=math.atan2(N[i,1],N[i,0])
 if face_road and side<0:angle+=math.pi
 return Frame(c,group,(*p,0),angle)

xs=P[:,0];ys=P[:,1];lo=(xs.min()-520,ys.min()-520);hi=(xs.max()+520,ys.max()+520)
for x in np.arange(lo[0],hi[0],70):
 for y in np.arange(lo[1],hi[1],70):
  f=Frame(c,'Airfield terrain');mat='grass'
  f.quad([(x,y,-.5),(x+70,y,-.5),(x+70,y+70,-.5),(x,y+70,-.5)],mat,(7,7))
centre=P.mean(axis=0)
# Extend the ground into the horizon with coarse, non-overlapping outer tiles.
inner_hi=(lo[0]+math.ceil((hi[0]-lo[0])/70)*70,lo[1]+math.ceil((hi[1]-lo[1])/70)*70)
outer_lo=centre-3700;outer_hi=centre+3700
rectangles=[(outer_lo[0],outer_lo[1],lo[0],outer_hi[1]),(inner_hi[0],outer_lo[1],outer_hi[0],outer_hi[1]),
            (lo[0],outer_lo[1],inner_hi[0],lo[1]),(lo[0],inner_hi[1],inner_hi[0],outer_hi[1])]
for x0,y0,x1,y1 in rectangles:
 f=Frame(c,'Airfield terrain horizon')
 for x in np.arange(x0,x1,250):
  for y in np.arange(y0,y1,250):
   xx=min(x+250,x1);yy=min(y+250,y1)
   f.quad([(x,y,-.5),(xx,y,-.5),(xx,yy,-.5),(x,yy,-.5)],'grass',((xx-x)/10,(yy-y)/10))
def subtract_convex(polygon,cutter):
 # Partition an outside polygon into convex pieces, discarding the shared interior.
 remaining=polygon;outside=[]
 for a,b in zip(cutter,cutter[1:]+cutter[:1]):
  if not remaining:break
  def signed(p):return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
  def half(keep_inside):
   result=[]
   for p,q in zip(remaining,remaining[1:]+remaining[:1]):
    dp,dq=signed(p),signed(q);ip=dp>=0 if keep_inside else dp<=0;iq=dq>=0 if keep_inside else dq<=0
    if ip:result.append(p)
    if ip!=iq:
     t=dp/(dp-dq);result.append(tuple(p[k]+t*(q[k]-p[k]) for k in range(3)))
   return result
  piece=half(False)
  if len(piece)>=3:
   area=sum(p[0]*q[1]-q[0]*p[1] for p,q in zip(piece,piece[1:]+piece[:1]))
   if abs(area)>1e-6:outside.append(piece)
  remaining=half(True)
 return outside
runway_cutters=[]
for j,(angle,length) in enumerate(((.22,860),(-.62,760),(1.13,700))):
 # Remove shared interiors; height offsets would collapse when game positions round to integers.
 f=Frame(c,'Historic runway remnants',(*centre,-.33),angle)
 for y in np.arange(-length/2,length/2,50):
  pieces=[[f.point(p) for p in [(-13,y,0),(13,y,0),(13,y+50,0),(-13,y+50,0)]]]
  for cutter in runway_cutters:pieces=[part for piece in pieces for part in subtract_convex(piece,cutter)]
  for piece in pieces:c.add(f.group,piece,[tuple(range(len(piece)))],'Runway')
  if j==0:f.quad([(-.5,y+8,.13),(.5,y+8,.13),(.5,y+28,.13),(-.5,y+28,.13)],'White')
 end=-length/2+math.ceil(length/50)*50
 runway_cutters.append([f.point(p) for p in [(-13,-length/2,0),(13,-length/2,0),(13,end,0),(-13,end,0)]])
wing(Frame(c,'Wing complex',(64,65,0)),length=250)
control_tower(Frame(c,'Wing control tower',(85,-80,0)))
f=Frame(c,'Hamilton pit lane')
# The physical pit floor is generated above; avoid a coplanar decorative floor.
for x in (29,45):f.quad([(x,-110,.30),(x+.25,-110,.30),(x+.25,205,.30),(x,205,.30)],'White')
for y in range(-100,200,15):f.quad([(36,y,.30),(36.3,y,.30),(36.3,y+8,.30),(36,y+8,.30)],'Yellow')
add_pit_details(c,pit)
for j in range(7):tent(Frame(c,'Paddock tents',(110,-50+j*30,0)))
for j in range(4):service_vehicle(Frame(c,'Paddock vehicles',(92,-35+j*55,0)))
gantry(Frame(c,'Hamilton start gantry'))
f=Frame(c,'Starting grid')
for row in range(2):
 for col in range(18):f.quad([(-18+2*col,-1.2+row*1.2,.22),(-16+2*col,-1.2+row*1.2,.22),
                            (-16+2*col,row*1.2,.22),(-18+2*col,row*1.2,.22)],'White' if (row+col)%2 else 'Black')
for row in range(4):
 for side in (-1,1):
  x=side*7;y=-12-row*12
  f.quad([(x-3,y,.22),(x+3,y,.22),(x+3,y+.5,.22),(x-3,y+.5,.22)],'White')
  f.quad([(x-3,y,.22),(x-2.5,y,.22),(x-2.5,y+4,.22),(x-3,y+4,.22)],'White')
landmarks=data['landmarks']
for name,side,length,roof in [('Abbey',-1,100,True),('Village',-1,76,False),('Luffield',-1,140,True),
 ('Woodcote',-1,110,True),('Copse',-1,124,True),('Becketts',-1,155,True),('Club',-1,150,True)]:
 style='woodland' if name in ('Copse','Luffield') else ('stowe' if name=='Stowe' else ('open' if not roof else 'wing'))
 grandstand(frame_at(name+' grandstand',landmarks[name]['path_index'],side,62,True),length,roof,style)
grandstand(Frame(c,'Hamilton grandstand',(-64,60,0),math.pi),140,True)
national=landmarks['Woodcote']['path_index']+22
old_pits(frame_at('National pits',national,1,54,True),190)
control_tower(frame_at('National control tower',national-15,1,80,True))
for name,info in landmarks.items():
 index=info['path_index'];before=(index-5)%COUNT
 f=frame_at(name+' corner furniture',index-5,-1,HW[before]+SH[before]+9)
 f.sign(name.upper(),0,0,1.5,12,3)
 f.box(-5,0,0,.3,.3,1.5,'Silver');f.box(5,0,0,.3,.3,1.5,'Silver')
 marshal_post(frame_at(name+' marshal post',index+8,-1,44))
 if name in ('Village','Brooklands','Copse','Stowe','Vale'):
  for metres in (150,100,50):
   before=index-round(metres/(data['lap_metres']/COUNT))
   f=frame_at(name+' braking boards',before,1,HW[before%COUNT]+SH[before%COUNT]+6)
   f.sign(str(metres),0,0,2,3,4);f.box(0,0,0,.35,.35,2,'Silver')
for name in ('Village','Brooklands','Luffield','Copse','Maggotts','Becketts','Stowe','Vale','Club'):
 index=landmarks[name]['path_index'];previous=P[(index-5)%COUNT];nextp=P[(index+5)%COUNT]
 a=P[index]-previous;b=nextp-P[index];side=1 if a[0]*b[1]-a[1]*b[0]>0 else -1
 f=Frame(c,name+' gravel runoff')
 extent,width,bands=runoff_profile(name)
 for j in range(index-extent,index+extent):
  i=j%COUNT;k=(j+1)%COUNT;near=HW[i]+1.5+SH[i]+1;near2=HW[k]+1.5+SH[k]+1
  outer=near+width*.6+width*.4*math.sin((j-index+extent)/(2*extent)*math.pi)
  outer2=near2+width*.6+width*.4*math.sin((j-index+extent+1)/(2*extent)*math.pi)
  # Inner painted/apron strips, broad weathered tarmac and outer gravel.
  # Corner-specific painted/apron/gravel proportions from the reviewed onboard.
  for start,end,mat in bands:
   a=near+start;b=outer if end is None else near+end
   a2=near2+start;b2=outer2 if end is None else near2+end
   f.quad([(*tuple(P[i]+N[i]*side*a),-.25),(*tuple(P[i]+N[i]*side*b),-.25),
           (*tuple(P[k]+N[k]*side*b2),-.25),(*tuple(P[k]+N[k]*side*a2),-.25)],mat,((b-a)/5,1))
  f.quad([(*tuple(P[i]+N[i]*side*outer),-.25),(*tuple(P[i]+N[i]*side*(outer+4)),-.25),
          (*tuple(P[k]+N[k]*side*(outer2+4)),-.25),(*tuple(P[k]+N[k]*side*outer2),-.25)],'dirt',(1,1))
 for j in (-6,0,6):tyre_stack(frame_at(name+' tyre stacks',index+j,side,HW[(index+j)%COUNT]+SH[(index+j)%COUNT]+5))
for side in (-1,1):
 for i in range(COUNT):
  if side==1 and i in pit_openings:continue
  k=(i+1)%COUNT;group='Fence sector %d side %d'%(i//110,side);f=Frame(c,group)
  p=P[i]+N[i]*side*(HW[i]+1.5+SH[i]+.5);q=P[k]+N[k]*side*(HW[k]+1.5+SH[k]+.5)
  f.quad([(*p,1.25),(*q,1.25),(*q,4.05),(*p,4.05)],'fence')
  if i%8==0:f.box(p[0],p[1],0,.22,.22,4.15,'Silver')
  if i%16==0 and SH[i]>3 and HW[i]>14:
   tangent=P[k]-P[i];angle=math.atan2(tangent[1],tangent[0])+(math.pi if side>0 else 0)
   Frame(c,group,(*((p+q)/2),0),angle).sign('SILVERSTONE' if i%32==0 else 'KART64',0,0,.6,12,2)
for name in ('Copse','Luffield','Woodcote','Becketts','Stowe','Club'):
 idx=landmarks[name]['path_index']
 for j in range(34):
  site='Copse' if name=='Stowe' and j<18 else name
  idx=landmarks[site]['path_index']
  i=(idx+rng.randint(-25,25))%COUNT
  pos=P[i]-N[i]*rng.uniform(98,170)+np.array([rng.uniform(-25,25),rng.uniform(-25,25)])
  if np.min(np.linalg.norm(P-pos,axis=1))<78:continue
  tree(Frame(c,site+' woodland',(*pos,0),rng.uniform(0,math.tau)),rng.uniform(10,18),slender=j%4==0)
event_centre=centre+np.array([-130,30])
f=Frame(c,'Infield pavilion',(*(event_centre+np.array([-45,0])),0));f.cylinder(0,0,0,17,6,'Ivory',8);f.cylinder(0,0,6,18,4,'Glass dark',8)
f.poly([(20*math.cos(i*math.tau/8),20*math.sin(i*math.tau/8),10) for i in range(8)]+[(0,0,15)],
       [(i,(i+1)%8,8) for i in range(8)],'Roof')
for j in range(5):tent(Frame(c,'Infield event tents',(*(event_centre+np.array([45,j*22-50])),0)))
add_details(c,data,frame_at)
ground_counts=add_ground_surfaces(c,data,frame_at)
detail_report=add_detail_passes(c,data,frame_at)
spectator_report=add_spectator_pass(c,data,frame_at)
# Ground patches face upwards on both sides of the track.
for g in c.groups.values():
 for index,(face,mat) in enumerate(zip(g['faces'],g['materials'])):
  if mat not in ('gravel','dirt','service_asphalt','runoff_blue','Green paint'):continue
  v=np.asarray([g['vertices'][i] for i in face])
  if np.ptp(v[:,2])>.01:continue
  xy=v[:,:2];area=np.sum(xy[:,0]*np.roll(xy[:,1],-1)-xy[:,1]*np.roll(xy[:,0],-1))
  if area<0:g['faces'][index]=tuple(reversed(face));g['uv'][index]=list(reversed(g['uv'][index]))
# Subtle, tapered paired braking wear; original paint geometry above the road.
for name in ('Village','Brooklands','Copse','Stowe','Vale'):
 idx=landmarks[name]['path_index']
 f=Frame(c,name+' braking wear')
 for track in (-1,1):
  for j in range(-19,-4):
   i=(idx+j)%COUNT;k=(i+1)%COUNT
   width=.18*math.sin((j+19.5)/15*math.pi)
   offset=track*1.5+2.5*math.sin((j+19)/18)
   a=P[i]+N[i]*offset;b=P[k]+N[k]*offset
   f.quad([(*tuple(a-N[i]*width),.34),(*tuple(a+N[i]*width),.34),
           (*tuple(b+N[k]*width),.34),(*tuple(b-N[k]*width),.34)],'Tyre wear')
# Surface UVs share a world phase, so terrain tiles no longer restart the pattern.
grass_pixels=np.asarray(textures['grass'].pixels).reshape(-1,4)[:,:3]
grass_pixel=int(np.argmin(np.sum((grass_pixels-grass_pixels.mean(axis=0))**2,axis=1)))
grass_average_uv=((grass_pixel%32+.5)/32,(grass_pixel//32+.5)/32)
for name,g in c.groups.items():
 if not name.startswith('Airfield terrain'):continue
 for face,uv in zip(g['faces'],g['uv']):
  if 'horizon' in name:
   # Coarse distant tiles use a constant texel plus continuous vertex tint.
   # Large nearest-filtered repeats otherwise create a visible checker pattern.
   uv[:]=[grass_average_uv]*len(face)
   continue
  xy=np.asarray([g['vertices'][i][:2] for i in face])/5
  phase=np.floor(xy.min(axis=0))
  uv[:]=[tuple(p-phase) for p in xy]
from_collector(c)
sky_verts,sky_faces=sky_geometry(centre)
make_mesh('Sky dome',sky_verts,sky_faces,['Sky']*len(sky_faces),
          [[(0,0)]*len(face) for face in sky_faces])
path_curve=bpy.data.curves.new('Main racing path','CURVE');path_curve.dimensions='3D'
spline=path_curve.splines.new('BEZIER');spline.bezier_points.add(COUNT-1)
for point,p in zip(spline.bezier_points,P):
 point.co=(p[0]*S,p[1]*S,float(height(p))*S);point.handle_left_type='VECTOR';point.handle_right_type='VECTOR'
spline.use_cyclic_u=True
path=bpy.data.objects.new('Main racing path',path_curve);scene.collection.objects.link(path)
path.parent=root;path.hm64_mk64_path_type='TRACK_PATH_1';path.hide_render=True;path.show_in_front=True
library_scene=bpy.data.scenes.new('Silverstone — Asset Library')
library_scene.unit_settings.system='METRIC';library_scene.unit_settings.scale_length=1/S
library_root=bpy.data.objects.new('Reusable Silverstone models',None);library_scene.collection.objects.link(library_root)
kit=Collector();kit_origins={}
for group,function,pos in [('Wing module',lambda f:wing(f,100),(0,0,0)),
 ('Covered grandstand',lambda f:grandstand(f,65,True),(85,0,0)),('Open grandstand',lambda f:grandstand(f,65,False),(140,0,0)),
 ('National garages',lambda f:old_pits(f,90),(0,150,0)),('Control tower',control_tower,(60,135,0)),
 ('Marshal hut',marshal_post,(100,130,0)),('Broadleaf tree',tree,(130,130,0)),('Tyre barrier',tyre_stack,(150,130,0)),
 ('Service vehicle',service_vehicle,(170,130,0)),('Paddock tent',tent,(190,130,0)),('Start gantry',gantry,(90,190,0)),
 ('Flagpole',flagpole,(0,280,0)),('Lighting mast',light_mast,(35,280,0)),('Pit trolley',pit_trolley,(70,280,0)),
 ('Concession kiosk',concession,(105,280,0)),('Picnic table',picnic_table,(140,280,0)),('Airfield windsock',windsock,(180,280,0)),
 ('Pit service boom',pit_boom,(220,130,0)),('Camera platform',camera_platform,(220,210,0)),('Armco rail module',armco_module,(220,280,0)),
 ('Grouped stand module',compact_stand,(280,0,0)),('Spectator bank',spectator_bank,(330,160,0)),
 ('Overhead advertising gantry',overhead_gantry,(320,320,0)),('Event display board',event_display,(270,420,0))]:
 function(Frame(kit,group,pos))
 kit_origins[group]=pos
kit_objects=from_collector(kit,library_root,library_scene.collection)
for name,pos in kit_origins.items():
 obj=kit_objects[name];origin=Vector(pos)*S
 for vertex in obj.data.vertices:vertex.co-=origin
 obj.location=origin;obj.asset_mark()
 obj.asset_data.description='Original Silverstone low-poly '+name.lower()+'. Packed Fast64 materials; source dimensions in metres.'
(ROOT/'source/asset-library-manifest.json').write_text(json.dumps({'models':list(kit_origins),'unit_scale_metres':1/S},indent=2)+'\n')
doc=bpy.data.texts.new('START HERE');doc.write('Silverstone Spectator Edition 1.9 — Native HD Geometry and Materials\nSee README.md beside this file.\n'
 'Complete Course scene: export its Track Root. Asset Library scene: reusable original models.\n'
 'Original textures are packed. Pit shortcut is physical asphalt with wall openings. See external runtime-test-report.json for the latest native test.\n')
bpy.ops.object.select_all(action='DESELECT');root.select_set(True);bpy.context.view_layer.objects.active=root
bpy.ops.object.make_local(type='ALL');used_images=set(textures.values())
for image in list(bpy.data.images):
 if image.source=='FILE' and image not in used_images:bpy.data.images.remove(image)
bpy.ops.file.pack_all();bpy.ops.object.select_all(action='DESELECT');root.select_set(True);bpy.context.view_layer.objects.active=root
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.region_3d.view_location=Vector((centre[0]*S,centre[1]*S,0))
   area.spaces.active.region_3d.view_distance=100;area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'silverstone.blend'))
track_dir=ROOT/'export/tracks/silverstone'
if track_dir.exists():shutil.rmtree(track_dir)
result=bpy.ops.scene.mk64_export_course()
if result!={'FINISHED'}:raise RuntimeError('Fast64 export failed: '+str(result))
summary={'edition':'1.9.0','triangle_budget':72000,'mesh_triangles':sum(len(o.data.polygons) for o in root.children if o.type=='MESH'),
 'mesh_objects':sum(o.type=='MESH' for o in root.children),'path_points':COUNT,'texture_count':len(textures),
 'asset_library_models':len(kit.groups),'placed_asset_counts':dict(c.counts),'ground_surface_tiles':ground_counts,'blender':bpy.app.version_string,'runtime_tested':False}
(ROOT/'source/onboard-surface-pass.json').write_text(json.dumps(onboard_report,indent=2)+'\n')
(ROOT/'source/spectator-scenery-pass.json').write_text(json.dumps(spectator_report,indent=2)+'\n')
(ROOT/'source/build-report.json').write_text(json.dumps(summary,indent=2)+'\n')
detail_report.update(mesh_triangles=summary['mesh_triangles'],placed_assets=summary['placed_asset_counts'])
(ROOT/'source/detail-pass-report.json').write_text(json.dumps(detail_report,indent=2)+'\n')
print('COURSE_BUILD_SUCCESS',json.dumps(summary))
if opts.render:
 from render_course import render_previews
 render_previews(scene,root,library_scene,library_root,materials,textures,data,ROOT)
