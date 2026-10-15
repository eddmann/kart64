"""Original painted-edge and apron geometry informed by the 2025 pole onboard.

These are visual proportions, not a survey. Paint is on existing road asphalt;
external runoff remains scenery outside the existing physical barrier.
"""
import numpy as np
from assets import Frame

RED_APEXES=('Village','The Loop','Luffield','Copse','Becketts','Stowe','Vale','Club')

def outside_side(data,name):
    p=np.asarray(data['points']);i=data['landmarks'][name]['path_index'];n=len(p)
    a=p[i]-p[(i-5)%n];b=p[(i+5)%n]-p[i]
    return 1 if a[0]*b[1]-a[1]*b[0]>0 else -1

def kerb_materials(data,side):
    n=len(data['points']);mats=['White' if i%2 else 'Black' for i in range(n)]
    for name in RED_APEXES:
        if side!=-outside_side(data,name):continue
        i=data['landmarks'][name]['path_index']
        for offset in range(-2,3):
            k=(i+offset)%n;mats[k]='Red' if offset%2==0 else 'White'
    return mats

def add_exit_paint(c,data):
    p=np.asarray(data['points']);normal=np.asarray(data['normals']);hw=np.asarray(data['half_width']);n=len(p)
    specs=[('Hamilton',-16,30,1,1.10),('Abbey',2,15,None,1.25),('Aintree',1,28,None,1.35),
           ('Brooklands',4,14,None,1.20),('Luffield',4,19,None,1.25),('Copse',3,24,None,1.70),
           ('Becketts',3,15,None,1.35),('Chapel',2,24,None,1.40),('Stowe',3,22,None,1.65),
           ('Vale',3,12,None,1.20),('Club',4,24,None,1.70)]
    occupied=set();segments=0;areas=[]
    for name,before,after,side,width in specs:
        idx=0 if name=='Hamilton' else data['landmarks'][name]['path_index']
        side=side if side is not None else outside_side(data,name)
        f=Frame(c,'Onboard — '+name+' green exit paint');count=0
        for j in range(before,after):
            i=(idx+j)%n;k=(i+1)%n
            if (i,side) in occupied:continue
            occupied.add((i,side))
            # Taper over four samples. Leave the continuous white road-edge line visible.
            w=max(.20,width*min(1,(j-before)/4,(after-j)/4))
            w2=max(.20,width*min(1,(j+1-before)/4,(after-j-1)/4))
            lo,hi=hw[i]-.48-w,hw[i]-.48;lo2,hi2=hw[k]-.48-w2,hw[k]-.48
            v=[(*tuple(p[i]+normal[i]*side*lo),.26),(*tuple(p[i]+normal[i]*side*hi),.26),
               (*tuple(p[k]+normal[k]*side*hi2),.26),(*tuple(p[k]+normal[k]*side*lo2),.26)]
            xy=np.asarray(v)[:,:2];area=np.sum(xy[:,0]*np.roll(xy[:,1],-1)-xy[:,1]*np.roll(xy[:,0],-1))
            if area<0:v.reverse()
            f.quad(v,'Green paint');count+=1
        areas.append(dict(area=name,side=side,painted_segments=count,maximum_width_metres=width));segments+=count
    return dict(edition='1.7.0',reference='Max Verstappen 2025 British GP pole onboard',
                red_apex_areas=list(RED_APEXES),default_kerb='alternating black and white',green_paint_areas=areas,
                green_paint_segments=segments,collision_changes=False,
                paint_physics='Overlay on existing asphalt; no grass painted as driveable tarmac',
                external_runoff='Visual scenery beyond unchanged barrier footprint',survey_accurate=False)

def runoff_profile(name):
    if name in ('Vale','Club'):return 15,42,[(0,3,'Green paint'),(3,None,'service_asphalt')]
    if name=='Copse':return 16,44,[(0,3,'Green paint'),(3,24,'service_asphalt'),(24,None,'gravel')]
    if name=='Stowe':return 16,44,[(0,3,'Green paint'),(3,21,'service_asphalt'),(21,None,'gravel')]
    if name in ('Brooklands','Luffield'):return 13,38,[(0,3,'runoff_blue'),(3,11,'service_asphalt'),(11,None,'gravel')]
    if name in ('Maggotts','Becketts'):return 12,38,[(0,3,'Green paint'),(3,17,'service_asphalt'),(17,None,'gravel')]
    return 11,34,[(0,3,'Green paint'),(3,15,'service_asphalt'),(15,None,'gravel')]
