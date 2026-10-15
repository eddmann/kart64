"""Prepare an original pit shortcut and clipped asphalt footprint. Requires Shapely.

Run before build_course.py. Game AI remains on the original GP path; this JSON
contains a separate guide for authoring and ordinary-keyboard native playtesting.
"""
from pathlib import Path
import json,math
import numpy as np
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union,triangulate
from geometry import make_geometry
R=Path(__file__).resolve().parents[1]
g=make_geometry();p=np.array(g['points']);norm=np.array(g['normals']);hw=np.array(g['half_width']);sh=np.array(g['shoulder']);n=len(p)
entry=770;exit=44;half=6.5

def bezier(a,b,c,d,count=30):
 t=np.linspace(0,1,count,endpoint=False)[:,None]
 return (1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d

forward=p[entry+1]-p[entry-1];forward/=np.linalg.norm(forward)
raw=[*bezier(p[entry],p[entry]+forward*38,np.array([252,-110]),np.array([218,-110])),
     *np.column_stack((np.linspace(218,66,32,endpoint=False),np.full(32,-110))),
     *np.array([[66+30*math.cos(a),-80+30*math.sin(a)] for a in np.linspace(-math.pi/2,-math.pi,25,endpoint=False)]),
     *np.column_stack((np.full(60,36),np.linspace(-80,210,60,endpoint=False))),
     *bezier(np.array([36,210]),np.array([36,254]),p[exit]-np.array([0,37]),p[exit]),p[exit]]
raw=np.asarray(raw);ds=np.linalg.norm(np.diff(raw,axis=0),axis=1);cumulative=np.r_[0,np.cumsum(ds)];distance=np.linspace(0,cumulative[-1],round(cumulative[-1]/4)+1)
route=np.column_stack([np.interp(distance,cumulative,raw[:,j]) for j in range(2)])
tan=np.gradient(route,axis=0);tan/=np.linalg.norm(tan,axis=1)[:,None];normal=np.column_stack((tan[:,1],-tan[:,0]))
lo=route-normal*half;hi=route+normal*half

def ribbon(widths):
 return unary_union([Polygon([p[i]-norm[i]*widths[i],p[i]+norm[i]*widths[i],p[(i+1)%n]+norm[(i+1)%n]*widths[(i+1)%n],p[(i+1)%n]-norm[(i+1)%n]*widths[(i+1)%n]]) for i in range(n)])
road=ribbon(hw);corridor=ribbon(hw+1.5+sh)
doors=list(range(767,783))+list(range(31,48))
shoulder=[Polygon([p[i]+norm[i]*hw[i],p[i]+norm[i]*(hw[i]+1.5+sh[i]),p[(i+1)%n]+norm[(i+1)%n]*(hw[(i+1)%n]+1.5+sh[(i+1)%n]),p[(i+1)%n]+norm[(i+1)%n]*hw[(i+1)%n]]) for i in doors]
raw_floor=unary_union([*[Polygon([lo[i],hi[i],hi[i+1],lo[i+1]]) for i in range(len(route)-1)],Polygon([(27,-110),(47,-110),(47,205),(27,205)]),*shoulder])
# A broad entry apron supports a normal kart's turning arc across the fork.
# Leaving only two narrow ribbons made the wedge between them an actual hole.
entry_apron=unary_union([*shoulder[:16],LineString(route[:29]).buffer(14,cap_style=2)]).convex_hull
raw_floor=raw_floor.union(entry_apron)
assert raw_floor.is_valid and raw_floor.geom_type=='Polygon'
floor=raw_floor.difference(road);triangles=[]
for part in ([floor] if floor.geom_type=='Polygon' else floor.geoms):
 for t in triangulate(part):
  if part.covers(t) and t.area>1e-5:triangles.append(list(map(list,list(t.exterior.coords)[:-1])))
# Bound edge length for N64 signed texture coordinates and a smooth height field.
queue=[np.array(t) for t in triangles];triangles=[]
while queue:
 t=queue.pop();lengths=[np.linalg.norm(t[(i+1)%3]-t[i]) for i in range(3)];i=int(np.argmax(lengths))
 if lengths[i]<=20:triangles.append(t.tolist());continue
 a,b,c=t[i],t[(i+1)%3],t[(i+2)%3];m=(a+b)/2
 queue.extend([np.array([a,m,c]),np.array([m,b,c])])
assert abs(sum(Polygon(t).area for t in triangles)-floor.area)<1e-4,'Floor triangulation has gaps'
# New perimeter walls stop at the original corridor, leaving both junctions open.
wall_lines=[]
exterior=list(raw_floor.exterior.coords)
for a,b in zip(exterior,exterior[1:]):
 rest=LineString([a,b]).difference(corridor.buffer(2.0))
 if rest.is_empty:continue
 lines=[rest] if rest.geom_type=='LineString' else list(rest.geoms)
 for line in lines:
  if line.length<.3:continue
  coords=list(line.coords)
  for a,b in zip(coords,coords[1:]):
   count=max(1,math.ceil(np.linalg.norm(np.array(b)-a)/6))
   q=np.linspace(a,b,count+1)
   wall_lines.extend([[q[i].tolist(),q[i+1].tolist()] for i in range(count)])
# Whole route must remain supported by the main road or new physical asphalt.
physical=road.union(floor)
assert all(physical.buffer(.001).covers(Point(q)) for q in route)
# Preserve distance to the existing road without touching unrelated perimeter walls.
right_boundary=LineString(p+norm*(hw+1.5+sh)[:,None]);intersections=[]
for i in range(n):
 line=LineString([p[i]+norm[i]*(hw[i]+1.5+sh[i]),p[(i+1)%n]+norm[(i+1)%n]*(hw[(i+1)%n]+1.5+sh[(i+1)%n])])
 if raw_floor.intersection(line).length>.3:intersections.append(i)
separator=set(range(826,n))|set(range(0,31))
assert set(intersections)<=set(doors)|separator,'Pit asphalt crosses an unrelated closed boundary: '+str(set(intersections)-set(doors)-separator)
main_distance=((n-entry+exit)%n)*g['lap_metres']/n
report=dict(edition='1.8.0',entry_path_index=entry,exit_path_index=exit,route=route.tolist(),route_normals=normal.tolist(),route_half_width_metres=half,
            pit_floor_triangles=triangles,pit_wall_segments=wall_lines,right_opening_segments=doors,route_metres=float(cumulative[-1]),main_route_metres=float(main_distance),
            geometric_distance_saved_metres=float(main_distance-cumulative[-1]),bypasses=['Vale','Club'],finish_crossing='Crosses Hamilton finish plane inside the pit lane; native lap-count test required',
            ai_route='Original GP racing path unchanged',physical_floor_area_metres2=float(floor.area),driveable=True)
report['entry_apron']='Continuous broad asphalt junction connecting the main-track opening to the pit approach; marked guide remains 13 metres wide'
report['inner_separator']='Garage asphalt reaches the existing Hamilton barrier; no second parallel wall or unsupported seam beside it'
(R/'source/pit-shortcut.json').write_text(json.dumps(report,indent=2)+'\n')
print('PIT_ROUTE_PREPARED',json.dumps({k:v for k,v in report.items() if k not in ['route','route_normals','pit_floor_triangles','pit_wall_segments','right_opening_segments']}),'triangles',len(triangles),'wall_segments',len(wall_lines))
