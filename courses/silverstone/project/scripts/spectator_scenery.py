"""Reference-led spectator landmarks, in source metres; no racing surfaces."""
import math
import numpy as np
from assets import Frame


def compact_stand(f, length=90, roof=True):
    """A long, economical stand module for grouped spectator rooflines."""
    f.c.counts['Grouped grandstand module'] += 1
    profile = [(-12, 0), (10.4, 0)]
    for row in reversed(range(7)):
        x=-12+row*3.2; z=1.1+row*1.55
        profile.extend([(x+3.2,z),(x,z)])
    n=len(profile)
    f.poly([(x,y,z) for y in (-length/2,length/2) for x,z in profile],
           [tuple(reversed(range(n))),tuple(range(n,n*2))] +
           [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)], 'structural_concrete')
    for row in range(7):
        x = -10.5 + row*3.2
        z = 1.32 + row*1.55
        f.quad([(x-1.5,-length/2,z),(x+1.5,-length/2,z),
                (x+1.5,length/2,z),(x-1.5,length/2,z)], 'crowd', (1,length/7))
        f.quad([(x-1.1,-length/2+2,z+.18),(x-1.1,length/2-2,z+.18),
                (x-1.1,length/2-2,z+1.95),(x-1.1,-length/2+2,z+1.95)],
               'spectators', ((length-4)/8,1))
    if roof:
        for y in np.linspace(-length/2, length/2, 5):
            f.box(13,y,0,.65,.65,18,'Silver')
        f.quad([(-15,-length/2-3,15),(16,-length/2-3,18),
                (16,length/2+3,18),(-15,length/2+3,15)], 'Roof')
        f.box(-15,0,14.6,.55,length+6,.65,'Ivory')
    for y in (-length/2, length/2):
        f.box(1,y,0,25,.4,12,'Navy')
        for row in range(6):
            f.quad([(13.4,y+row*1.6,2+row*1.8),(16.4,y+row*1.6,2+row*1.8),
                    (16.4,y+(row+1)*1.6,2+row*1.8),(13.4,y+(row+1)*1.6,2+row*1.8)], 'structural_concrete')


def spectator_bank(f, length=120):
    """Low grassy banking with dense original crowd cards, not a tall building."""
    f.c.counts['Spectator bank'] += 1
    profile = [(-14,-.08),(30,-.08),(30,1),(20,5.8),(-14,.25)]
    n = len(profile)
    f.poly([(x,y,z) for y in (-length/2,length/2) for x,z in profile],
           [tuple(reversed(range(n))),tuple(range(n,n*2))] +
           [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)], 'grass')
    for row in range(6):
        x = -9 + row*5
        z = .25 + (x+14)/34*5.55 + .24
        f.quad([(x-1,-length/2+3,z),(x+1,-length/2+3,z+.33),
                (x+1,length/2-3,z+.33),(x-1,length/2-3,z)], 'crowd', (1,(length-6)/7))
        f.quad([(x,-length/2+3,z),(x,length/2-3,z),
                (x,length/2-3,z+1.75),(x,-length/2+3,z+1.75)], 'spectators', ((length-6)/8,1))
    f.quad([(-15,-length/2,-.15),(-15,length/2,-.15),
            (-20,length/2,-.15),(-20,-length/2,-.15)], 'dirt', (1,length/8))
    f.quad([(-21,-length/2,1),(-21,length/2,1),
            (-21,length/2,4),(-21,-length/2,4)], 'fence', (length/4,1))


def overhead_gantry(f, span=74):
    """Bridge-like advertising truss seen before Copse; pedestrian use unclaimed."""
    f.c.counts['National Straight overhead gantry'] += 1
    for side in (-1,1):
        for y in (-1.8,1.8):
            f.box(side*span/2,y,0,1.1,1.1,17,'Silver')
        f.box(side*span/2,0,-.1,4.5,7,.5,'structural_concrete')
    f.box(0,0,13.5,span+3,4.8,3.8,'Navy')
    for y in (-2.8,2.8):
        f.box(0,y,17.5,span+3,.24,.24,'Silver')
        for x in np.linspace(-span/2,span/2,9):
            f.box(x,y,16.8,.22,.22,1.1,'Silver')
    f.sign('SILVERSTONE',0,-2.3,13.7,span-4,3)
    f.sign('KART64',0,2.3,13.7,span-4,3,face='back')


def event_display(f):
    f.c.counts['Event display board'] += 1
    for x in (-4,4):
        f.box(x,0,0,1.1,1.5,9,'Silver')
    f.box(0,0,6,19,2,12,'Navy')
    f.quad([(-8.6,-1.3,6.7),(8.6,-1.3,6.7),(8.6,-1.3,16.7),(-8.6,-1.3,16.7)], 'event_screen')


def add_spectator_pass(c, data, frame_at):
    landmarks = data['landmarks']
    placements = []
    # These wrap the outside of the bends, rather than repeating one isolated stand.
    for name, delta, side, offset, length in (
        ('Luffield',-21,-1,77,105), ('Luffield',20,-1,76,108),
        ('Woodcote',18,-1,70,108),
        ('Becketts',-22,-1,78,115), ('Chapel',8,-1,83,90),
        ('Vale',-20,-1,76,110), ('Club',-18,-1,77,108),
    ):
        index = (landmarks[name]['path_index']+delta) % len(data['points'])
        group = 'Spectators — '+name+' stand '+str(delta)
        compact_stand(frame_at(group,index,side,offset,True),length)
        placements.append({'mesh':group,'path_index':index,'side':side,'offset_metres':offset,'length_metres':length})
    for delta, length, offset in ((-26,110,76),(4,145,76)):
        index = landmarks['Stowe']['path_index']+delta
        group = 'Spectators — Stowe bank '+str(delta)
        f = frame_at(group,index,-1,offset,True)
        spectator_bank(f,length)
        # Small peaked canopies form the white roof rhythm seen in the 2025 lap.
        for y in np.linspace(-length/2+10,length/2-10,5):
            roof = Frame(c,group,f.point((34,y,0)),f.angle)
            roof.poly([(-5,-5,4),(5,-5,4),(5,5,4),(-5,5,4),(0,0,8)],
                      [(0,1,4),(1,2,4),(2,3,4),(3,0,4)],'Ivory')
            for x in (-4.5,4.5):roof.box(x,0,0,.25,.25,4,'Silver')
    gantry_index = landmarks['Woodcote']['path_index']+46
    overhead_gantry(frame_at('Spectators — National Straight gantry',gantry_index))
    for name, delta, side, offset in (
        ('Luffield',-6,1,67), ('Copse',-18,1,61),
        ('Becketts',-10,1,63), ('Stowe',0,1,66), ('Club',-12,1,65),
    ):
        event_display(frame_at('Spectators — '+name+' display',landmarks[name]['path_index']+delta,side,offset,True))
    return {'reference_lap':'Official 2025 British GP pole onboard',
            'stand_modules':placements,'gantry_path_index':gantry_index,
            'banks':2,'display_boards':5,'pedestrian_crossing_claimed':False,
            'collision_added':False,'placement':'Approximate map/onboard-informed kart interpretation'}
