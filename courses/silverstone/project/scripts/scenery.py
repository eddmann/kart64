"""Extra original paddock, spectator and airfield scenery; dimensions in metres."""
import math
import random
import numpy as np
from assets import Frame,flagpole,light_mast,pit_trolley,concession,picnic_table,windsock,tent


def add_details(c,data,frame_at):
    points=np.array(data['points']);normals=np.array(data['normals'])
    rng=random.Random(641101);centre=points.mean(axis=0)
    for j in range(10):
        pit_trolley(Frame(c,'Wing pit equipment',(50,-45+j*23,0)))
    for j in range(7):
        flagpole(Frame(c,'Wing paddock flags',(112,-70+j*36,0)),('Red','White','Blue')[j%3])
    for j in range(5):
        light_mast(Frame(c,'Hamilton lighting',(-36,-85+j*62,0)),22)
    # Four small hospitality areas, placed well beyond the racing barriers.
    for name in ('Luffield','Copse','Becketts','Stowe'):
        index=data['landmarks'][name]['path_index']
        f=frame_at(name+' spectator amenities',index,-1,112,True)
        concession(f)
        for j in range(3):
            picnic_table(Frame(c,f.group,f.point((12+j*6,8,0)),f.angle))
        for j in range(3):
            f.cylinder(-6+j*3,-6,0,.7,1.4,'Blue' if j%2 else 'Green paint',6)
        flagpole(Frame(c,f.group,f.point((-12,0,0)),f.angle),'Red',12)
        # Rectangular access forecourts and path edging beneath the structures.
        f.quad([(-18,-12,-.16),(34,-12,-.16),(34,18,-.16),(-18,18,-.16)],'concrete',(5,3))
        for x in (-18,34):f.box(x,3,-.1,.4,30,.2,'Silver')
    for name in ('Abbey','Copse','Stowe','Club'):
        i=data['landmarks'][name]['path_index']
        light_mast(frame_at(name+' lighting',i,-1,78),19)
    # Keep the distant hedges small so the circuit retains its airfield character.
    for sector,name in enumerate(('Luffield','Copse','Becketts','Stowe','Club')):
        i=data['landmarks'][name]['path_index']
        for j in range(12):
            k=(i-40+j*7)%len(points);pos=points[k]-normals[k]*(190+sector*9)
            if np.linalg.norm(points-pos,axis=1).min()<90:continue
            angle=math.atan2(normals[k,1],normals[k,0])
            f=Frame(c,name+' hedgerows',(*pos,0),angle)
            length=16+rng.uniform(0,7);h=3+rng.uniform(0,2)
            vertices=[]
            for y,scale in ((-length/2,.58),(0,1),(length/2,.72)):
                vertices.extend([(-2.5,y,0),(-1.8,y,h*scale*.8),(.6,y,h*scale),(2.5,y,0)])
            faces=[(3,2,1,0),(8,9,10,11)]
            faces.extend((4*k+j,4*k+(j+1)%4,4*(k+1)+(j+1)%4,4*(k+1)+j) for k in range(2) for j in range(4))
            f.poly(vertices,faces,'leaves')
            c.counts['Hedgerow module']+=1
    # Village is an open spectator festival, contrasting with Copse woodland.
    i=data['landmarks']['Village']['path_index']
    base=frame_at('Village fan area',i,-1,80,True)
    f=Frame(c,base.group,base.point((0,125,0)),base.angle)
    for j in range(6):
        tent(Frame(c,f.group,f.point((30+(j%2)*20,-45+(j//2)*30,0)),f.angle))
    f.sign('FAN ZONE',0,-48,2.5,15,3)
    for j in range(3):flagpole(Frame(c,f.group,f.point((-12+j*12,-55,0)),f.angle),('Red','Blue','White')[j],12)
    event=centre+np.array([-130,30])
    windsock(Frame(c,'Airfield windsock installation',(*(event+np.array([-115,-100])),0)))
    f=Frame(c,'Event access paths')
    for a,b in [(event+[-45,0],event+[45,0]),(event+[45,-62],event+[45,75])]:
        d=b-a;n=np.array([d[1],-d[0]])/np.linalg.norm(d)*2.5
        f.quad([(*tuple(a-n),-.17),(*tuple(a+n),-.17),(*tuple(b+n),-.17),(*tuple(b-n),-.17)],'concrete',(2,12))
    Frame(c,'Paddock wayfinding',(104,-83,0)).sign('PADDOCK',0,0,3,10,2)
    Frame(c,'Pit exit furniture',(53,225,0)).sign('PIT EXIT',0,0,2,5,1.5)
    Frame(c,'Event wayfinding',(*(event+[-38,-10]),0)).sign('FAN ZONE',0,0,2,10,2)
    # Cloud cards are original exported geometry; no game cloud sprite dependencies.
    for j in range(24):
        angle=j*math.tau/24+rng.uniform(-.08,.08);radius=rng.uniform(2100,2800)
        pos=centre+np.array([math.cos(angle),math.sin(angle)])*radius
        height=rng.uniform(340,620);width=rng.uniform(290,480);h=rng.uniform(110,170)
        f=Frame(c,'Sky clouds sector '+str(j//6),(*pos,height),angle-math.pi/2)
        f.quad([(-width/2,0,0),(width/2,0,0),(width/2,0,h),(-width/2,0,h)],'cloud')
        c.counts['Cloud cluster']+=1


def sky_geometry(centre,radius=3600,sectors=40):
    vertices=[];faces=[]
    elevations=(-100,0,180,430,800,1300,1900,2500,3050,3400)
    for z in elevations:
        r=radius*math.sqrt(max(0,1-(max(z,0)/radius)**2))
        vertices.extend((centre[0]+r*math.cos(j*math.tau/sectors),
                         centre[1]+r*math.sin(j*math.tau/sectors),z) for j in range(sectors))
    for k in range(len(elevations)-1):
        faces.extend((k*sectors+j,k*sectors+(j+1)%sectors,
                      (k+1)*sectors+(j+1)%sectors,(k+1)*sectors+j) for j in range(sectors))
    vertices.append((centre[0],centre[1],radius))
    base=(len(elevations)-1)*sectors
    faces.extend((base+j,base+(j+1)%sectors,len(vertices)-1) for j in range(sectors))
    return vertices,faces
