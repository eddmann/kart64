"""Build the prepared physical shortcut and its original trackside markings."""
import math,numpy as np
from assets import Frame


def build_pit_collision(pit,make_mesh):
    verts=[];faces=[];uv=[]
    for t in pit['pit_floor_triangles']:
        tri=np.asarray(t);area=np.cross(tri[1]-tri[0],tri[2]-tri[0])
        if area<0:tri=tri[::-1]
        first=len(verts);verts.extend([(float(x),float(y),0) for x,y in tri]);faces.append(tuple(range(first,first+3)))
        q=tri/5;q-=np.floor(q.min(axis=0));uv.append([tuple(v) for v in q])
    make_mesh('Pit shortcut asphalt',verts,faces,['asphalt']*len(faces),uv,clip='CLIP_SURFACE')
    vertices=[];polys=[];walluv=[]
    for a,b in pit['pit_wall_segments']:
        i=len(vertices);vertices.extend([(*a,0),(*b,0),(*b,3),(*a,3)]);polys.append((i,i+1,i+2,i+3));walluv.append([(0,0),(1,0),(1,1),(0,1)])
    # Native ParseMeshForCollision keeps its surface-filter state between meshes.
    # Fast64 sorts sections by name, so every wall must precede the floor meshes.
    make_mesh('Barrier pit collision',vertices,polys,['structural_concrete']*len(polys),walluv,surface='STONE',clip='CLIP_DOUBLE_SIDED_WALL',draw='DRAW_INVISIBLE')
    make_mesh('Pit barrier visible',[(x,y,min(z,1.25)) for x,y,z in vertices],polys,['structural_concrete']*len(polys),walluv,surface='STONE')
    fence=[]
    for a,b in pit['pit_wall_segments']:fence.extend([(*a,1.25),(*b,1.25),(*b,4.05),(*a,4.05)])
    make_mesh('Pit perimeter fence',fence,polys,['fence']*len(polys),walluv)


def add_pit_details(c,pit):
    route=np.asarray(pit['route']);norm=np.asarray(pit['route_normals'])
    # Lane arrows make the turning entry and merging exit readable from the kart.
    for idx in [9,19,31,43,len(route)-19,len(route)-9]:
        p=route[idx];normal=norm[idx];f=Frame(c,'Pit shortcut direction arrows',(*p,0),math.atan2(normal[1],normal[0]))
        f.poly([(-.4,-4,.26),(.4,-4,.26),(.4,1,.26),(1.3,1,.26),(0,4,.26),(-1.3,1,.26),(-.4,1,.26)],[(0,1,2,3,4,5,6)],'White')
    for idx in [12,len(route)-16]:
        p=route[idx]+norm[idx]*16;f=Frame(c,'Pit shortcut signs',(*p,0),math.atan2(norm[idx,1],norm[idx,0]))
        f.sign('PIT LANE',0,0,1.7,10,2.5);f.box(-4,0,0,.25,.25,1.7,'Silver');f.box(4,0,0,.25,.25,1.7,'Silver')
    # Extend the finish stripe across the alternate lane. Lap counting uses the
    # engine's normal Hamilton finish plane; there is no checkpoint or state hack.
    f=Frame(c,'Pit lane finish stripe')
    for row in range(2):
        for j in range(10):
            x=28.5+j*1.8;y=-1.2+row*1.2
            f.quad([(x,y,.26),(x+1.8,y,.26),(x+1.8,y+1.2,.26),(x,y+1.2,.26)],'White' if (j+row)%2 else 'Black')
    f=Frame(c,'Pit perimeter posts')
    for j,(a,b) in enumerate(pit['pit_wall_segments']):
        if j%6==0:
            pos=np.asarray(a);i=int(np.argmin(np.linalg.norm(route-pos,axis=1)));out=pos-route[i];out/=np.linalg.norm(out);pos+=out*.30
            f.box(pos[0],pos[1],0,.22,.22,4.15,'Silver')
