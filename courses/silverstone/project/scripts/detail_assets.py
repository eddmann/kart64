"""Focused original scenery for the native desktop detail edition, in source metres."""
import math
import numpy as np
from assets import Frame


def pit_boom(f):
    f.c.counts['Pit service boom']+=1
    f.box(0,0,0,.30,.30,5.0,'Silver')
    f.box(-3.3,0,4.8,7.0,.26,.26,'Silver')
    f.box(-6.2,0,2.8,.14,.14,2.0,'Rubber')
    f.box(-6.2,0,2.5,.30,.30,.35,'Yellow')
    f.box(.5,0,1.0,1.0,1.4,1.4,'Navy')
    f.box(.5,-.72,1.3,.8,.05,.7,'Red')


def camera_platform(f):
    f.c.counts['Camera platform']+=1
    # Open scaffold, with a narrow stair-flight profile on the back.
    for x in (-1.6,1.6):
        for y in (-1.6,1.6):f.box(x,y,0,.22,.22,8.2,'Silver')
    for z in (2.5,5,7.5):
        for x in (-1.6,1.6):f.box(x,0,z,.15,3.2,.15,'Silver')
        for y in (-1.6,1.6):f.box(0,y,z,3.2,.15,.15,'Silver')
    f.box(0,0,7.5,4,4,.25,'structural_concrete')
    for y in (-1.9,1.9):f.box(0,y,8.6,4,.12,.12,'Silver')
    for x in (-1.9,1.9):f.box(x,0,8.6,.12,4,.12,'Silver')
    for y in (-1.7,0,1.7):f.box(1.9,y,7.7,.12,.12,.95,'Silver')
    f.box(0,0,7.75,.2,.2,1.15,'Silver')
    f.box(-.25,0,8.65,1.25,.8,.7,'Navy')
    f.box(-1.0,0,8.78,.35,.46,.40,'Black')
    f.box(.45,0,9.0,.12,.9,.18,'Silver')
    for j in range(9):
        z=.4+j*.83;y=-2.15+j*.4
        f.quad([(2,y,z),(3,y,z),(3,y+.4,z),(2,y+.4,z)],'Silver')
    f.box(2.95,-.1,4.0,.12,4.1,.12,'Silver')


def armco_module(f,length=14):
    f.c.counts['Armco module']+=1
    for y in (-length*.38,length*.38):f.box(.15,y,0,.18,.18,1.15,'Silver')
    for z in (.35,.66,.97):
        # Folded thin rail profile gives readable edge highlights without solid boxes.
        profile=[(-.20,z-.08),(-.25,z),(-.20,z+.08),(-.10,z+.10)]
        verts=[(x,y,h) for y in (-length/2,length/2) for x,h in profile]
        f.poly(verts,[(j,j+1,j+5,j+4) for j in range(3)],'Silver')


def transporter(f,colour='Ivory'):
    f.c.counts['Paddock transporter']+=1
    f.box(0,0,1,3.7,14.5,3.2,colour)
    f.box(0,6.9,1,3.7,3.5,3.4,'Navy')
    f.quad([(-1.5,8.8,2.1),(1.5,8.8,2.1),(1.5,8.8,3.9),(-1.5,8.8,3.9)],'glass')
    f.box(0,-7.3,1.1,3.45,.20,3.0,'Silver')
    f.box(0,0,2.1,3.82,13.5,.50,'Red')
    for x in (-1.95,1.95):
        for y in (-5.5,-3.0,5.8):f.box(x,y,.4,.40,1.3,1.3,'Rubber')
    f.box(0,8.9,1.5,3.4,.20,.30,'Silver')


def wing_detail(f,length=250):
    # Visible under-edges and thickened folded roof silhouette.
    stride=length/5
    for j in range(5):
        y=-length/2+j*stride;end=y+stride-2;peak=(23,17,25,18,27)[j]
        f.quad([(-17,y,12.7),(17,y,13.5),(17,y,13.2),(-17,y,12.4)],'Silver')
        f.quad([(-17,end,15.2),(17,end,peak),(17,end,peak-.30),(-17,end,14.9)],'Silver')
        # End fins receive thin silver edges which catch the baked light.
        f.quad([(-17,end+.3,15.0),(17,end+.3,peak-.2),(17,end+.3,peak),(-17,end+.3,15.2)],'Silver')
    # Upper viewing gallery mullions and railing posts.
    for j in range(26):
        y=-length/2+j*length/25
        f.box(-16.42,y,8,.18,.18,4,'Silver')
    bays=20;spacing=length/bays
    for j in range(bays):
        y=-length/2+(j+.5)*spacing
        # The dark surround and raised sill reveal depth behind roller-door panels.
        f.box(-12.73,y,.15,.18,spacing*.90,6.45,'Navy')
        f.box(-13.12,y,.12,.80,spacing*.92,.22,'structural_concrete')
        for yy in (-spacing*.46,spacing*.46):
            f.box(-13.06,y+yy,.3,.42,.36,6.0,'Silver')
    f.box(-16.65,0,7.8,.18,length,.18,'Silver')
    for j in range(10):
        pit_boom(Frame(f.c,'Wing service booms',f.point((-14.6,-107+j*23,0)),f.angle))


def add_detail_passes(c,data,frame_at):
    points=np.asarray(data['points']);normals=np.asarray(data['normals'])
    width=np.asarray(data['half_width']);shoulder=np.asarray(data['shoulder'])
    wing_detail(Frame(c,'Wing architectural detail',(64,65,0)))
    for j,colour in enumerate(('Ivory','Blue')):
        transporter(Frame(c,'Paddock transporters',(180,-30+j*110,0),math.pi/2),colour)
    for name in ('Village','Copse','Stowe'):
        i=data['landmarks'][name]['path_index']
        camera_platform(frame_at(name+' broadcast platform',i+5,-1,43,True))
    for first,side in [('Chapel',1),('Stowe',-1)]:
        i=data['landmarks'][first]['path_index']
        for j in range(8):
            k=(i+12+j*3)%len(points)
            f=frame_at(first+' service Armco',k,side,width[k]+shoulder[k]+9,side<0)
            # Guard against the nearby crossing ribbon, not just the current waypoint.
            verts=np.asarray([f.point((x,y,0)) for x in (-.4,.4) for y in (-7,7)])
            d=np.linalg.norm(verts[:,None,:2]-points,axis=2);closest=d.argmin(axis=1)
            if np.any(d[np.arange(4),closest]<width[closest]+4):continue
            armco_module(f)
    # Marshal figures use the original sprite atlas, outside the race wall.
    for name in ('Village','Copse','Stowe','Club'):
        i=data['landmarks'][name]['path_index']
        f=frame_at(name+' marshal figures',i+9,-1,40,True)
        f.quad([(-2,0,0),(2,0,0),(2,0,2.2),(-2,0,2.2)],'spectators')
        c.counts['Marshal spectator group']+=1
    return {'passes':['Trackside visibility and export-safe sign depth','Architecture and HD material coverage','Corner broadcast/service detail'],
            'visible_barrier_height_metres':1.25,'collision_barrier_height_metres':3.0,
            'fence_top_metres':4.05,'collision_footprint_unchanged':True,
            'triangle_budget':72000,'target':'Native desktop Spaghetti Kart; not N64 hardware or browser acceptance'}
