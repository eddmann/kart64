"""Reusable original low-poly models in source metres; independent of Blender."""
import math
from collections import defaultdict


class Collector:
    def __init__(self):
        self.groups={}
        self.counts=defaultdict(int)

    def add(self,group,vertices,faces,material,uv=None):
        out=self.groups.setdefault(group,{'vertices':[],'faces':[],'materials':[],'uv':[]})
        offset=len(out['vertices']);out['vertices'].extend(vertices)
        for face in faces:
            out['faces'].append(tuple(i+offset for i in face));out['materials'].append(material)
            default_uv = ([(0,0),(1,0),(1,1),(0,1)][:len(face)] if len(face)<=4 else
                          [(.5+.5*math.cos(i*math.tau/len(face)),.5+.5*math.sin(i*math.tau/len(face))) for i in range(len(face))])
            out['uv'].append(uv or default_uv)


class Frame:
    def __init__(self,collector,group,origin=(0,0,0),angle=0):
        self.c=collector;self.group=group;self.origin=origin;self.angle=angle

    def point(self,p):
        x,y,z=p;ox,oy,oz=self.origin
        return (ox+x*math.cos(self.angle)-y*math.sin(self.angle),
                oy+x*math.sin(self.angle)+y*math.cos(self.angle),oz+z)

    def quad(self,points,mat,repeat=(1,1)):
        self.c.add(self.group,[self.point(p) for p in points],[(0,1,2,3)],mat,
                   [(0,0),(repeat[0],0),(repeat[0],repeat[1]),(0,repeat[1])])

    def poly(self,points,faces,mat):
        self.c.add(self.group,[self.point(p) for p in points],faces,mat)

    def box(self,x,y,z,sx,sy,sz,mat):
        points=[(x+xx,y+yy,zz) for zz in (z,z+sz) for xx,yy in
                ((-sx/2,-sy/2),(sx/2,-sy/2),(sx/2,sy/2),(-sx/2,sy/2))]
        self.poly(points,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)

    def cylinder(self,x,y,z,r,h,mat,sides=8,caps=True):
        points=[(x+r*math.cos(i*math.tau/sides),y+r*math.sin(i*math.tau/sides),zz)
                for zz in (z,z+h) for i in range(sides)]
        faces=[tuple(reversed(range(sides))),tuple(range(sides,sides*2))] if caps else []
        faces.extend((i,(i+1)%sides,(i+1)%sides+sides,i+sides) for i in range(sides))
        self.poly(points,faces,mat)

    def sign(self,text,x,y,z,width=14,height=3,face='front'):
        self.box(x,y,z-.4,width+.5,.45,height+.8,'Navy')
        # Sign fronts face local -Y; geometry is double-sided in game.
        # Separate both faces by more than a game-unit after integer export.
        # The old 0.015 m gap from the backing collapsed to coplanar coordinates.
        offset=-.55 if face=='front' else .55
        points=[(x-width/2,y+offset,z),(x+width/2,y+offset,z),
                (x+width/2,y+offset,z+height),(x-width/2,y+offset,z+height)]
        if face!='front':points.reverse()
        self.quad(points,'sign_'+text.lower().replace(' ','_'))


def wing(f,length=250):
    f.c.counts['Wing complex']+=1
    f.box(0,0,-.3,35,length+14,.3,'structural_concrete')
    f.box(0,0,0,25,length,7.5,'Ivory')
    f.box(-1.5,0,7.5,29,length,5,'Navy')
    # Glass gallery and parapet, facing the track to local -X.
    f.quad([(-16.1,-length/2,8),(-16.1,length/2,8),(-16.1,length/2,12),(-16.1,-length/2,12)],'glass',(length/10,1))
    f.box(-16.3,0,7.6,.5,length,.4,'Silver')
    f.box(-16.3,0,12,.5,length,.45,'Ivory')
    bays=20;spacing=length/bays
    for i in range(bays):
        y=-length/2+(i+.5)*spacing
        f.quad([(-12.98,y-spacing*.42,.40),(-12.98,y+spacing*.42,.40),
                (-12.98,y+spacing*.42,6.4),(-12.98,y-spacing*.42,6.4)],'garage')
        f.box(-12.7,y-spacing/2,0,.7,.65,7.4,'Silver')
        f.box(-12.7,y,6.8,.4,spacing*.8,.45,'Red')
        # Number plaques share one RGBA16 atlas; no separate texture per bay.
        u=(i%5)*12/64;v=1-(i//5+1)*8/32
        points=[(-13.30,y+1,6.5),(-13.30,y-1,6.5),(-13.30,y-1,7.4),(-13.30,y+1,7.4)]
        f.c.add(f.group,[f.point(p) for p in points],[(0,1,2,3)],'garage_numbers',
                [(u,v),(u+12/64,v),(u+12/64,v+.25),(u,v+.25)])
    # Broad angular roof plates rise into asymmetric fins, inspired by the Wing silhouette.
    modules=5;stride=length/modules
    for i in range(modules):
        y=-length/2+i*stride;end=y+stride-2
        peak=(23,17,25,18,27)[i]
        f.quad([(-17,y,12.7),(17,y,13.5),(17,end,peak),(-17,end,15.2)],'Roof')
        f.quad([(-17,y,12.2),(-17,y,12.7),(-17,end,15.2),(-17,end,14.7)],'Red')
        f.quad([(17,y,13.5),(17,y,13),(17,end,peak-.5),(17,end,peak)],'Silver')
        f.poly([(17,end,12.5),(17,end,peak),(-17,end,15.2),(-17,end,12.5)],[(0,1,2,3)],'Glass dark')
        f.box(15,end,0,1.8,1.8,peak-.6,'Silver')
    # End tower has an angled top and contrasting checker cladding.
    y=length/2+5
    f.poly([(-9,y-4,0),(12,y-4,0),(12,y+4,0),(-9,y+4,0),
            (-9,y-4,14),(12,y-4,29),(12,y+4,29),(-9,y+4,14)],
           [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'Roof')
    f.sign('THE WING',0,-length/2-4,8,20,4)


def grandstand(f,length=90,roof=True,style='wing'):
    f.c.counts['Grandstand']+=1
    # Local -X is the viewing direction; tiers rise towards +X.
    # One stepped shell avoids hidden faces between adjacent tier boxes.
    profile=[(-11.6,0),(10.8,0)]
    for i in reversed(range(7)):
        x=-11.6+i*3.2;z=i*1.65+1.1
        profile.extend([(x+3.2,z),(x,z)])
    profile=list(dict.fromkeys(profile))
    points=[(x,y,z) for y in (-length/2,length/2) for x,z in profile]
    n=len(profile)
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    f.poly(points,faces,'structural_concrete')
    trim={'wing':'Red','woodland':'Green paint','stowe':'Blue','open':'Yellow'}[style]
    for i in range(7):
        x=-10+i*3.2;z=i*1.65
        f.quad([(x-1.5,-length/2,z+1.12),(x+1.5,-length/2,z+1.12),
                (x+1.5,length/2,z+1.12),(x-1.5,length/2,z+1.12)],'crowd',(1,length/7))
        f.box(x-1.5,0,z+1.2,.35,length,.45,trim if i%2 else 'White')
        if i%2==0:
            f.quad([(x-1.2,-length/2+2,z+1.13),(x-1.2,length/2-2,z+1.13),
                    (x-1.2,length/2-2,z+3.13),(x-1.2,-length/2+2,z+3.13)],'spectators',((length-4)/8,1))
    for y in (-length/2,length/2):
        f.box(1,y,0,25,.5,12,'Navy')
        # Side handrails, access staircase and diagonal frame braces.
        f.box(1,y,12,24,.18,.18,'Silver')
        # Open-backed stair surfaces give the same silhouette with fewer triangles.
        for i in range(8):
            yy=y+(i-.5)*1.1;z=(i+1)*1.5
            f.quad([(13.5,yy,z),(16.5,yy,z),(16.5,yy+1.1,z),(13.5,yy+1.1,z)],'structural_concrete')
            f.quad([(13.5,yy,z-1.5),(16.5,yy,z-1.5),(16.5,yy,z),(13.5,yy,z)],'structural_concrete')
        f.box(15,y+3.5,12,.2,9,.2,'Silver')
    if roof:
        for y in range(-int(length/2),int(length/2)+1,18):
            f.box(13,y,0,.8,.8,17,'Silver')
            f.box(-9,y,12.5,.5,.5,3,'Silver')
        if style=='stowe':
            # Three folded canopy spans give Stowe a distinct skyline.
            for j in range(3):
                a=-length/2-3+j*(length+6)/3;b=a+(length+6)/3
                f.poly([(-15,a,15),(16,a,17),(-15,(a+b)/2,18),(16,(a+b)/2,20),
                        (-15,b,15),(16,b,17)],[(0,1,3,2),(2,3,5,4)],'Ivory')
        else:
            f.quad([(-15,-length/2-3,15), (16,-length/2-3,18),
                    (16,length/2+3,18),(-15,length/2+3,15)],'Roof' if style=='woodland' else 'Ivory')
        f.box(-15,0,14.5,.6,length+6,.6,trim)
        f.box(16,0,12,1,length+2,4,'Navy')


def old_pits(f,length=190):
    f.c.counts['National pit building']+=1
    f.box(0,0,0,18,length,7,'Ivory')
    for i in range(16):
        y=-length/2+(i+.5)*length/16
        f.quad([(-9.45,y-5,.2),(-9.45,y+5,.2),(-9.45,y+5,5.4),(-9.45,y-5,5.4)],'garage')
    f.quad([(-11,-length/2,7), (11,-length/2,9),(11,length/2,9),(-11,length/2,7)],'Red')
    f.box(0,length*.22,7,17,28,10,'structural_concrete')
    f.quad([(-8.6,length*.22-13,9),(-8.6,length*.22+13,9),
            (-8.6,length*.22+13,15),(-8.6,length*.22-13,15)],'glass',(3,1))
    f.sign('NATIONAL PITS',0,-length/2-1,7.2,18,3)


def control_tower(f):
    f.c.counts['Control tower']+=1
    f.box(0,0,0,11,11,16,'Ivory')
    for angle in range(4):
        ff=Frame(f.c,f.group,f.point((0,0,0)),f.angle+angle*math.pi/2)
        ff.quad([(-6,-6,15),(6,-6,15),(6,-6,20),(-6,-6,20)],'glass',(2,1))
    f.box(0,0,14.5,13,13,.6,'Silver');f.box(0,0,20,15,15,.8,'Navy')
    f.cylinder(0,0,20,.2,7,'Silver',6)


def marshal_post(f):
    f.c.counts['Marshal hut']+=1
    f.box(0,0,0,4,5,3,'Ivory')
    f.quad([(-2.1,-2.5,3),(2.1,-2.5,3.6),(2.1,2.5,3.6),(-2.1,2.5,3)],'Orange')
    f.quad([(-1.5,-2.55,1.3),(1.5,-2.55,1.3),(1.5,-2.55,2.5),(-1.5,-2.55,2.5)],'glass')
    f.box(3,0,0,.18,.18,6,'Silver')
    f.quad([(3,0,5),(5.7,0,4.5),(5.7,0,5.9),(3,0,6.2)],'Yellow')


def tree(f,height=13,slender=False):
    f.c.counts['Broadleaf tree']+=1
    f.cylinder(0,0,0,.65,height*.58,'Bark',6,caps=False)
    sides=6;r=height*(.23 if slender else .33)
    points=[]
    for radius,z in ((r*.72,height*.45),(r,height*.68),(r*.55,height*.93)):
        points.extend((radius*math.cos(i*math.tau/sides),radius*math.sin(i*math.tau/sides),z) for i in range(sides))
    points.append((0,0,height))
    faces=[]
    for layer in range(2):
        faces.extend((layer*sides+i,layer*sides+(i+1)%sides,(layer+1)*sides+(i+1)%sides,(layer+1)*sides+i) for i in range(sides))
    faces.extend((2*sides+i,2*sides+(i+1)%sides,len(points)-1) for i in range(sides))
    f.poly(points,faces,'leaves')


def tyre_stack(f):
    f.c.counts['Tyre barrier module']+=1
    for x in (-1.7,0,1.7):
        # Top caps preserve the visible gaps between tyres; undersides are omitted.
        for z in (0,.7,1.4):
            f.cylinder(x,0,z,.8,.6,'Rubber',8,caps=False)
            f.poly([(x+.8*math.cos(i*math.tau/8),.8*math.sin(i*math.tau/8),z+.6) for i in range(8)],
                   [tuple(range(8))],'Rubber')


def service_vehicle(f):
    f.c.counts['Service vehicle']+=1
    f.box(0,0,1,3.2,6,2,'Orange')
    f.box(0,-1.5,3,3.1,2.6,1.8,'Ivory')
    f.quad([(-1.3,-2.85,3.3),(1.3,-2.85,3.3),(1.3,-2.85,4.5),(-1.3,-2.85,4.5)],'glass')
    for x in (-1.7,1.7):
        for y in (-1.8,1.8):f.box(x,y,.25,.6,1.4,1.4,'Rubber')
    f.box(0,-1.4,4.8,1,.5,.3,'Blue')


def tent(f):
    f.c.counts['Paddock tent']+=1
    for x in (-5,5):
        for y in (-6,6):f.box(x,y,0,.3,.3,4,'Silver')
    f.poly([(-6,-7,4),(6,-7,4),(6,7,4),(-6,7,4),(0,0,7)],
           [(0,1,4),(1,2,4),(2,3,4),(3,0,4)],'Ivory')


def gantry(f,text='SILVERSTONE'):
    f.c.counts['Gantry']+=1
    for side in (-1,1):
        f.box(side*22,0,0,1.2,2,13,'Silver')
        f.box(side*22,0,0,2.7,3.2,.5,'structural_concrete')
    f.box(0,0,10.5,46,2,3.6,'Navy');f.sign(text,0,-1.15,10.6,44,3.3)
    f.sign(text,0,1.15,10.6,44,3.3,face='back')
    for x in (-3,-1.5,0,1.5,3):
        f.box(x,-1.4,9.5,1,1,.8,'Black')
        f.box(x,-1.95,9.65,.45,.1,.4,'Red')


def flagpole(f,color='Red',height=14):
    f.c.counts['Flagpole']+=1
    f.box(0,0,0,.23,.23,height,'Silver');f.box(0,0,0,1.2,1.2,.25,'structural_concrete')
    f.poly([(0,0,height-3),(2.4,.25,height-3.3),(4.7,-.15,height-2.8),
            (0,0,height),(2.4,.25,height-.3),(4.7,-.15,height+.2)],[(0,1,4,3),(1,2,5,4)],color)


def light_mast(f,height=20):
    f.c.counts['Lighting mast']+=1
    f.box(0,0,0,.55,.55,height,'Silver');f.box(0,0,0,2,2,.5,'structural_concrete')
    f.box(0,0,height,6,.45,.35,'Navy')
    for x in (-2.5,0,2.5):
        f.box(x,-.25,height-.25,1.5,.8,.8,'structural_concrete');f.box(x,-.7,height-.2,1.2,.15,.5,'Ivory')


def pit_trolley(f):
    f.c.counts['Pit trolley']+=1
    f.box(0,0,.35,1.7,2.8,1.6,'Red');f.box(0,0,1.95,1.9,3,.12,'Silver')
    for z in (.7,1.1,1.5):f.box(0,-1.42,z,1.3,.08,.05,'Black')
    for x in (-.7,.7):
        for y in (-1,1):f.box(x,y,.08,.3,.5,.5,'Rubber')
    f.box(.3,0,2.07,.7,.8,.45,'Navy')


def concession(f):
    f.c.counts['Concession kiosk']+=1
    f.box(0,0,0,7,5,3.6,'Ivory');f.box(0,-2.6,1.3,6,.4,.2,'Silver')
    f.box(0,-2.52,1.5,5,.12,1.2,'Navy')
    f.quad([(-4,-3.7,3),(4,-3.7,3),(4,-2,4),(-4,-2,4)],'Red')
    f.box(0,0,3.6,7.5,5.5,.25,'Navy');f.sign('CAFE',0,-2.7,3.05,5,1)


def picnic_table(f):
    f.c.counts['Picnic table']+=1
    f.box(0,0,1.3,2,3,.18,'Bark')
    for x in (-1.5,1.5):
        f.box(x,0,.7,.6,3,.18,'Bark')
        for y in (-1,1):f.box(x,y,0,.2,.2,.7,'Navy')
    for y in (-1,1):f.box(0,y,0,.3,.3,1.3,'Navy')


def windsock(f):
    f.c.counts['Airfield windsock']+=1
    f.box(0,0,0,.3,.3,13,'Silver')
    sides=8
    for segment in range(5):
        points=[]
        for end in (segment,segment+1):
            radius=1.5-end*.2
            points.extend((end*1.4,radius*math.cos(i*math.tau/sides),13-end*.25+radius*math.sin(i*math.tau/sides)) for i in range(sides))
        f.poly(points,[(i,(i+1)%sides,(i+1)%sides+sides,i+sides) for i in range(sides)],'Orange' if segment%2==0 else 'White')
