"""Photo-informed, stylised paddock paving, access routes and worn spectator ground."""
import math,json
from pathlib import Path
import numpy as np
from assets import Frame


def add_ground_surfaces(c,data,frame_at):
    points=np.asarray(data['points']);normals=np.asarray(data['normals'])
    widths=np.asarray(data['half_width'])+np.asarray(data['shoulder'])+3.5
    counts={};occupied=[]
    pit_points=np.asarray(json.loads((Path(__file__).resolve().parents[1]/'source/pit-shortcut.json').read_text())['route'])

    def safe(poly):
        # Protect the entire racing corridor, including shoulders and barriers.
        xy=np.asarray(poly)[:,:2]
        samples=np.concatenate((xy,[(xy[i]+xy[(i+1)%len(xy)])/2 for i in range(len(xy))],xy.mean(axis=0)[None,:]))
        dist=np.linalg.norm(samples[:,None,:]-points,axis=2)
        closest=dist.argmin(axis=1)
        pit_distance=np.linalg.norm(samples[:,None,:]-pit_points,axis=2).min(axis=1)
        return np.all(dist[np.arange(len(samples)),closest]>widths[closest]+1) and np.all(pit_distance>8)

    def tile(f,local,mat,z=.10):
        world=[f.point((x,y,z)) for x,y in local]
        if not safe(world):return
        xy=np.asarray(world)[:,:2]/5;phase=np.floor(xy.min(axis=0))
        c.add(f.group,world,[(0,1,2,3)],mat,[tuple(q-phase) for q in xy])
        raw=np.asarray(world)[:,:2];occupied.append((raw.min(axis=0),raw.max(axis=0)))
        counts[mat]=counts.get(mat,0)+1

    def panel(f,bounds,mat):
        x0,y0,x1,y1=bounds
        for x in np.arange(x0,x1,20):
            for y in np.arange(y0,y1,20):
                xx=min(x+20,x1);yy=min(y+20,y1)
                tile(f,[(x,y),(xx,y),(xx,yy),(x,yy)],mat)

    def paint(f,local,mat='White'):
        world=[f.point((x,y,.40)) for x,y in local]
        if safe(world):c.add(f.group,world,[(0,1,2,3)],mat)

    # The Wing and National garages sit in extensive paved paddock compounds.
    f=Frame(c,'Ground — Wing paddock paving')
    panel(f,(47,-126,165,224),'service_asphalt')
    panel(f,(165,-96,207,184),'dirt')
    for row in range(2):
        for j in range(12):
            x=132+row*18;y=-102+j*23
            paint(f,[(x,y),(x+.28,y),(x+.28,y+10),(x,y+10)])
    for y in range(-102,175,23):
        paint(f,[(131,y),(154,y),(154,y+.28),(131,y+.28)])
    i=data['landmarks']['Woodcote']['path_index']+22
    panel(frame_at('Ground — National paddock paving',i,1,54,True),(-23,-111,56,111),'service_asphalt')

    # Paved circulation beneath/behind stands, transitioning into compacted earth.
    lengths={'Hamilton':140,'Abbey':100,'Village':76,'Luffield':108,'Woodcote':110,
             'Copse':104,'Becketts':86,'Stowe':100,'Club':112}
    for name,length in lengths.items():
        f=Frame(c,'Ground — Hamilton spectator paving',(-64,60,0),math.pi) if name=='Hamilton' else frame_at('Ground — '+name+' spectator paving',data['landmarks'][name]['path_index'],-1,62,True)
        panel(f,(-14,-length/2-12,29,length/2+12),'service_asphalt')
        panel(f,(29,-length/2-12,49,length/2+12),'dirt')

    # Short, separated service-road sections avoid suggesting a second race loop.
    for name,before,after in [('Abbey',-27,27),('Woodcote',-32,23),('Copse',-12,32),
                              ('Becketts',-20,28),('Stowe',-30,28),('Club',-22,16)]:
        idx=data['landmarks'][name]['path_index']
        f=Frame(c,'Ground — '+name+' service road')
        for j in range(idx+before,idx+after):
            i=j%len(points);k=(j+1)%len(points)
            lo,hi=88,95
            world=[(*tuple(points[i]-normals[i]*lo),.10),(*tuple(points[i]-normals[i]*hi),.10),
                   (*tuple(points[k]-normals[k]*hi),.10),(*tuple(points[k]-normals[k]*lo),.10)]
            if not safe(world):continue
            xy_raw=np.asarray(world)[:,:2]
            low,high=xy_raw.min(axis=0),xy_raw.max(axis=0)
            if any(np.all(low<b-1e-6) and np.all(high>a+1e-6) for a,b in occupied):continue
            edges=np.roll(xy_raw,-1,axis=0)-xy_raw
            cross=edges[:,0]*np.roll(edges[:,1],-1)-edges[:,1]*np.roll(edges[:,0],-1)
            if not (np.all(cross>1e-5) or np.all(cross<-1e-5)):continue
            if cross[0]<0:world.reverse()
            xy=np.asarray(world)[:,:2]/5;phase=np.floor(xy.min(axis=0))
            c.add(f.group,world,[(0,1,2,3)],'service_asphalt',[tuple(q-phase) for q in xy])
            counts['service-road segments']=counts.get('service-road segments',0)+1

    village=data['landmarks']['Village']['path_index']
    base=frame_at('Ground — Village fan area',village,-1,80,True)
    f=Frame(c,base.group,base.point((0,125,0)),base.angle)
    panel(f,(9,-62,65,35),'dirt')
    panel(f,(-16,-62,9,35),'service_asphalt')
    event=points.mean(axis=0)+np.array([-130,30])
    panel(Frame(c,'Ground — infield event apron',(*event,0)),(-70,-72,66,76),'dirt')

    # A handful of small parked cars, instead of filling fields with arbitrary props.
    f=Frame(c,'Paddock parked cars')
    for j,colour in enumerate(('Silver','White','Blue','Red')):
        g=Frame(c,f.group,(139,-70+j*46,0))
        g.box(0,0,.5,2.3,4.6,1.05,colour);g.box(0,.2,1.55,2,2.3,.8,colour)
        g.quad([(-.85,-.97,1.65),(.85,-.97,1.65),(.85,-.97,2.2),(-.85,-.97,2.2)],'glass')
        for x in (-1.15,1.15):
            for y in (-1.4,1.4):g.box(x,y,.15,.35,.85,.85,'Rubber')
    c.counts['Parked car']+=4
    return counts
