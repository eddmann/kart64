"""Create original, deterministic N64-sized tile textures and readable sign artwork."""
import json
import random
import numpy as np
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'textures';OUT.mkdir(parents=True,exist_ok=True)
rng=random.Random(6402026)
manifest={}


def save(name,im,purpose):
    im=im.convert('RGBA');im.save(OUT/(name+'.png'))
    manifest[name]={'file':name+'.png','size':list(im.size),'format':'RGBA16',
                    'tmem_bytes':im.width*im.height*2,'purpose':purpose,'original':True}


for name,base,amount in [('asphalt',(66,72,78),4),('grass',(158,151,108),6),
                         ('gravel',(175,164,140),18),('concrete',(161,166,166),8),
                         ('leaves',(57,103,53),17),('service_asphalt',(112,115,112),6),
                         ('dirt',(151,131,99),8),('runoff_blue',(72,104,104),3),
                         ('structural_concrete',(168,171,168),5),('Roof',(141,150,154),3),
                         ('Silver',(137,152,160),3),('Rubber',(22,26,28),2),('Bark',(82,64,43),5)]:
    # Low contrast grain with a periodic broad component: seams wrap cleanly.
    im=Image.new('RGB',(32,32))
    for y in range(32):
        for x in range(32):
            d=rng.randint(-amount,amount)
            im.putpixel((x,y),tuple(max(0,min(255,c+d)) for c in base))
    save(name,im,'Seamless surface tile')

im=Image.new('RGB',(32,32),(27,66,81));d=ImageDraw.Draw(im)
for x in (0,15,31):d.line((x,0,x,31),fill=(165,185,187),width=1)
for y in (0,15,31):d.line((0,y,31,y),fill=(165,185,187),width=1)
d.polygon([(2,2),(12,2),(2,12)],fill=(70,116,132))
d.polygon([(17,17),(29,17),(17,29)],fill=(57,103,120))
save('glass',im,'Wing and control tower window bays')

im=Image.new('RGB',(32,32),(49,55,66));d=ImageDraw.Draw(im)
d.rectangle((2,2,29,30),fill=(94,99,106))
for y in range(3,31,3):d.line((3,y,28,y),fill=(56,63,72))
d.rectangle((0,0,31,3),fill=(184,32,40));d.rectangle((26,17,27,19),fill=(223,224,226))
save('garage',im,'Pit garage roller door')

im=Image.new('RGB',(32,32),(33,63,106));d=ImageDraw.Draw(im)
for y in range(3,32,8):
    for x in range(2,32,6):
        d.rectangle((x,y,x+2,y+2),fill=(rng.randint(180,236),rng.randint(150,204),120))
        d.rectangle((x-1,y+3,x+3,y+6),fill=rng.choice([(199,37,44),(230,204,89),(60,120,203),(239,239,229)]))
save('crowd',im,'Abstract spectators on grandstand tiers')

im=Image.new('RGBA',(32,32),(0,0,0,0));d=ImageDraw.Draw(im)
for offset in range(-32,65,8):
    d.line((offset,0,offset+32,32),fill=(171,182,189,255),width=1)
    d.line((offset,0,offset-32,32),fill=(171,182,189,255),width=1)
save('fence',im,'Alpha-cutout chain-link catch fence')

im=Image.new('RGBA',(64,32),(0,0,0,0));d=ImageDraw.Draw(im)
# Two distinct cumulus silhouettes, with a pale blue underside; binary alpha is RGBA16-safe.
for cx,cy,rx,ry in [(16,20,14,7),(29,14,14,12),(43,19,15,8),(53,22,9,5)]:
    d.ellipse((cx-rx,cy-ry,cx+rx,cy+ry),fill=(245,249,247,255))
d.rectangle((9,24,55,26),fill=(210,229,241,255))
save('cloud',im,'Original alpha-cutout cumulus sky sprite')

im=Image.new('RGBA',(32,32),(0,0,0,0));d=ImageDraw.Draw(im)
for j in range(4):
    x=2+j*8;skin=[(234,192,150),(155,104,76),(215,166,120),(240,202,162)][j]
    shirt=[(208,39,53),(235,216,86),(51,116,192),(230,235,229)][j]
    d.rectangle((x+1,7,x+4,11),fill=skin+(255,))
    d.rectangle((x,12,x+5,21),fill=shirt+(255,))
    d.rectangle((x,15,x,22),fill=skin+(255,));d.rectangle((x+5,15,x+5,22),fill=skin+(255,))
    d.rectangle((x+1,22,x+2,29),fill=(37,49,71,255));d.rectangle((x+3,22,x+4,29),fill=(37,49,71,255))
    d.rectangle((x,30,x+2,31),fill=(23,28,33,255));d.rectangle((x+3,30,x+5,31),fill=(23,28,33,255))
save('spectators',im,'Standing spectator silhouettes for stepped grandstands')

im=Image.new('RGB',(64,32),(18,36,54));d=ImageDraw.Draw(im)
atlasfont=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',7)
for j in range(20):
    x=(j%5)*12;y=(j//5)*8;text=str(j+1).zfill(2)
    d.text((x+1,y),text,font=atlasfont,fill=(245,242,220))
save('garage_numbers',im,'Twenty numbered pit-bay plaques in one texture atlas')

font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
labels=['SILVERSTONE','THE WING','PIT LANE','NATIONAL PITS','WELCOME','KART64',
        'ABBEY','FARM','VILLAGE','THE LOOP','AINTREE','BROOKLANDS','LUFFIELD',
        'WOODCOTE','COPSE','MAGGOTTS','BECKETTS','CHAPEL','STOWE','VALE','CLUB',
        '150','100','50','PADDOCK','PIT EXIT','CAFE','RACE CONTROL','FAN ZONE']
for text in labels:
    im=Image.new('RGB',(64,16),(16,35,54));d=ImageDraw.Draw(im)
    d.rectangle((0,0,63,1),fill=(219,33,46));d.rectangle((0,14,63,15),fill=(225,228,225))
    size=11
    while True:
        font=ImageFont.truetype(font_path,size)
        box=d.textbbox((0,0),text,font=font)
        if box[2]-box[0]<=60 or size<=6:break
        size-=1
    d.text(((64-(box[2]-box[0]))/2,(16-(box[3]-box[1]))/2-box[1]),text,font=font,fill=(249,246,224))
    save('sign_'+text.lower().replace(' ','_'),im,'Original trackside sign: '+text)
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# A contact sheet makes the actual game textures easy to inspect.
sheet=Image.new('RGB',(640,((len(manifest)+3)//4)*92),(24,30,39));d=ImageDraw.Draw(sheet)
font=ImageFont.truetype(font_path,10)
for i,(name,info) in enumerate(manifest.items()):
    x=(i%4)*160;y=(i//4)*92
    tex=Image.open(OUT/info['file']).convert('RGB');tex.thumbnail((128,64),Image.Resampling.NEAREST)
    # Enlarge with nearest sampling to expose every pixel.
    factor=min(128/tex.width,64/tex.height)
    tex=tex.resize((round(tex.width*factor),round(tex.height*factor)),Image.Resampling.NEAREST)
    sheet.paste(tex,(x+(160-tex.width)//2,y+3));d.text((x+8,y+70),name,font=font,fill=(232,236,242))
(ROOT/'previews').mkdir(parents=True,exist_ok=True)
sheet.save(ROOT/'previews/texture-sheet.png')
print('Generated',len(manifest),'original textures')
