"""Original static event-screen artwork; geographic outline, no reference pixels."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
image=Image.new('RGBA',(1024,512),(12,23,35,255))
draw=ImageDraw.Draw(image)
font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
draw.rectangle((0,0,1023,65),fill=(168,28,45))
draw.text((25,10),'KART64  /  SILVERSTONE',font=ImageFont.truetype(font,35),fill=(250,247,226))
draw.rectangle((20,83,730,453),fill=(39,62,42))
data=json.loads((ROOT/'source/geometry.json').read_text())
points=data['points'];lo=[min(p[i] for p in points) for i in (0,1)];hi=[max(p[i] for p in points) for i in (0,1)]
scale=min(640/(hi[0]-lo[0]),320/(hi[1]-lo[1]))
path=[(55+(p[0]-lo[0])*scale,420-(p[1]-lo[1])*scale) for p in points]
draw.line(path+[path[0]],fill=(190,193,179),width=19)
draw.line(path+[path[0]],fill=(33,39,43),width=11)
draw.ellipse((path[0][0]-9,path[0][1]-9,path[0][0]+9,path[0][1]+9),fill=(238,64,73))
for row in range(5):
    y=100+row*67
    draw.rectangle((760,y,1002,y+48),fill=(31,49,66))
    draw.text((773,y+5),str(row+1).zfill(2),font=ImageFont.truetype(font,28),fill=(255,223,103))
    draw.line((842,y+17,980,y+17),fill=(176,199,209),width=5)
    draw.line((842,y+32,937,y+32),fill=(94,135,149),width=4)
draw.text((25,469),'GP CIRCUIT  /  18 TURNS',font=ImageFont.truetype(font,24),fill=(190,218,231))
for hd in (False,True):
    directory=ROOT/'textures'/('hd' if hd else '')
    directory.mkdir(parents=True,exist_ok=True)
    output=directory/'event_screen.png'
    target=image if hd else image.resize((64,32),Image.Resampling.LANCZOS)
    target.save(output)
    manifest_path=directory/'manifest.json'
    manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    entry={'file':output.name,'size':list(target.size),'original':True,'purpose':'Original static event display: GP outline and timing-board motif'}
    if hd:entry.update(sha256=hashlib.sha256(output.read_bytes()).hexdigest(),logical_size=[64,32],scale=16)
    else:entry.update(format='RGBA16',tmem_bytes=4096)
    manifest['event_screen']=entry
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
