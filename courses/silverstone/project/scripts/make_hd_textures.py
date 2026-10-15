"""Generate original HD replacements while retaining the logical N64 texture sizes."""
from pathlib import Path
import json,math,zipfile,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'textures/hd';OUT.mkdir(parents=True,exist_ok=True)
base=json.loads((ROOT/'textures/manifest.json').read_text());manifest={}
rng=np.random.default_rng(64202604)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def noise(n,blur):
 a=rng.normal(size=(n,n));freq=np.fft.fftfreq(n);fy,fx=np.meshgrid(freq,freq)
 a=np.fft.ifft2(np.fft.fft2(a)*np.exp(-2*math.pi**2*blur**2*(fx*fx+fy*fy))).real
 return np.clip(a/(a.std()+1e-9),-2.5,2.5)
def save(name,im,purpose):
 im=im.convert('RGBA');path=OUT/(name+'.png');im.save(path,optimize=True)
 w,h=base[name]['size'];assert im.size==(w*16,h*16)
 manifest[name]={'file':name+'.png','size':list(im.size),'logical_size':[w,h],'scale':16,'original':True,'purpose':purpose,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
def surface(name,col,rough,broad):
 n=512;a=noise(n,.45)*rough+noise(n,7)*rough*.55+noise(n,42)*broad
 arr=np.clip(np.array(col)[None,None,:]+a[:,:,None],0,255).astype('uint8');im=Image.fromarray(arr);d=ImageDraw.Draw(im)
 if name in ('grass','leaves'):
  for _ in range(18000 if name=='grass' else 10000):
   x,y=rng.integers(0,n,2);v=int(rng.integers(-20,24));c=tuple(int(np.clip(q+v,0,255)) for q in col)
   length=int(rng.integers(2,10));end=(int(x+rng.integers(-3,4)),int(y-length))
   d.line((int(x),int(y),*end),fill=c,width=int(rng.integers(1,3)))
 elif name=='gravel':
  for _ in range(4500):
   x,y=rng.integers(0,n,2);r=int(rng.integers(2,7));v=int(rng.integers(-36,30));c=tuple(int(np.clip(q+v,0,255)) for q in col)
   d.ellipse((int(x-r),int(y-r),int(x+r),int(y+r*.7)),fill=c)
   d.arc((int(x-r),int(y-r),int(x+r),int(y+r*.7)),190,310,fill=tuple(min(255,q+13) for q in c),width=1)
  im=im.filter(ImageFilter.GaussianBlur(.35))
 save(name,im,'Original detailed seamless surface; reference pack quality/scale study')
for args in [('asphalt',(76,79,82),5,3),('grass',(148,145,103),7,9),('gravel',(173,164,143),8,4),('concrete',(160,166,166),4,7),('leaves',(59,101,52),9,8),('service_asphalt',(110,114,113),5,4),('dirt',(149,130,97),8,10),('runoff_blue',(74,107,107),3,5),('structural_concrete',(168,171,168),3,4),('Roof',(141,150,154),2,3),('Silver',(137,152,160),2,2),('Rubber',(22,26,28),1,1),('Bark',(82,64,43),4,3)]:surface(*args)
# Material details read at close range without introducing large noisy patterns.
for name in ('structural_concrete','Roof','Silver','Rubber','Bark'):
 im=Image.open(OUT/(name+'.png'));d=ImageDraw.Draw(im)
 if name=='structural_concrete':
  d.line((0,0,0,511),fill=(130,137,135,255),width=3)
  d.line((4,0,4,511),fill=(184,187,182,255),width=2)
  for x,y in ((18,36),(493,36),(18,475),(493,475)):d.ellipse((x-2,y-2,x+2,y+2),fill=(139,147,142,255))
 elif name=='Roof':
  for x in range(0,512,64):
   d.line((x,0,x,511),fill=(107,119,126,255),width=3)
   d.line((x+4,0,x+4,511),fill=(178,189,194,255),width=2)
 elif name=='Silver':
  for y in range(0,512,16):d.line((0,y,511,y),fill=(145,159,166,255),width=1)
 elif name=='Rubber':
  for y in range(0,512,128):d.line((0,y,511,y),fill=(13,18,20,255),width=5)
 elif name=='Bark':
  for x in range(0,512,17):
   points=[(x+int(6*math.sin(y/45+x)),y) for y in range(0,513,8)]
   d.line(points,fill=(60,45,30,255),width=3)
 save(name,im,'Original architectural or natural material detail')
# Architectural panels are redrawn at native HD resolution.
im=Image.new('RGB',(512,512),(30,64,78));d=ImageDraw.Draw(im)
for x in range(512):
 c=int(8*math.sin(x/70));d.line((x,0,x,511),fill=(30+c,65+c,80+c))
for y in (0,248,504):d.rectangle((0,y,511,y+7),fill=(154,170,175));d.line((0,y+8,511,y+8),fill=(19,35,42),width=3)
for x in (0,248,504):d.rectangle((x,0,x+7,511),fill=(154,170,175));d.line((x+8,0,x+8,511),fill=(19,35,42),width=3)
for x,y in [(10,10),(258,258)]:d.polygon([(x,y),(x+214,y),(x,y+214)],fill=(63,101,118));d.line((x+13,y+192,x+192,y+13),fill=(88,119,133),width=3)
save('glass',im,'Reflective window panels, recessed mullions and restrained diagonal highlights')
im=Image.new('RGB',(512,512),(43,51,62));d=ImageDraw.Draw(im)
d.rectangle((24,52,479,493),fill=(104,111,118))
for y in range(58,490,20):
 d.rectangle((30,y,473,y+3),fill=(142,148,152));d.rectangle((30,y+15,473,y+19),fill=(65,75,85))
d.rectangle((0,0,511,51),fill=(169,31,42));d.line((0,52,511,52),fill=(76,17,28),width=4)
d.rounded_rectangle((421,263,440,289),radius=4,fill=(203,212,218));d.rectangle((427,267,434,279),fill=(30,41,49))
save('garage',im,'Steel roller-door ribs, header fascia, frame and inset handle')
# Draw small spectators with individual heads, hair and clothes rather than upscale blocks.
im=Image.new('RGB',(512,512),(34,48,64));d=ImageDraw.Draw(im)
for row in range(5):
 y=20+row*100;d.rectangle((0,y+85,511,y+99),fill=(67,74,77))
 for j in range(10):
  x=8+j*51+int(rng.integers(-4,5));skin=[(230,182,139),(151,105,77),(207,157,110),(235,197,165)][j%4]
  shirt=[(183,39,48),(213,193,106),(57,109,163),(222,224,215),(46,63,76)][(j+row)%5]
  d.rounded_rectangle((x+7,y+26,x+39,y+67),radius=8,fill=shirt);d.ellipse((x+14,y+6,x+32,y+27),fill=skin)
  d.arc((x+13,y+4,x+33,y+25),175,355,fill=(55,38,29),width=5)
  d.line((x+11,y+65,x+11,y+81),fill=(29,39,49),width=7);d.line((x+33,y+65,x+33,y+81),fill=(29,39,49),width=7)
  d.line((x+11,y+36,x+4,y+56),fill=shirt,width=7);d.line((x+34,y+36,x+42,y+55),fill=shirt,width=7)
save('crowd',im,'Original crowd rows with distinct clothing, heads and seating')
im=Image.new('RGBA',(512,512),(0,0,0,0));d=ImageDraw.Draw(im)
for offset in range(-512,1025,128):
 d.line((offset,0,offset+512,512),fill=(121,133,140,255),width=3)
 d.line((offset,0,offset-512,512),fill=(121,133,140,255),width=3)
save('fence',im,'Thin low-contrast catch-fence wires with a transparent background')
im=Image.new('RGBA',(1024,512),(0,0,0,0));d=ImageDraw.Draw(im)
for cx,cy,rx,ry in [(256,320,224,112),(464,224,224,192),(688,304,240,128),(848,352,144,80)]:
 d.ellipse((cx-rx,cy-ry,cx+rx,cy+ry),fill=(236,243,246,255))
 d.ellipse((cx-rx+12,cy-ry+8,cx+rx-35,cy+ry-27),fill=(250,251,248,255))
d.rounded_rectangle((145,365,893,425),radius=28,fill=(220,234,242,255));im=im.filter(ImageFilter.GaussianBlur(3))
save('cloud',im,'Smooth original cumulus silhouettes with soft edges and blue shaded undersides')
im=Image.new('RGBA',(512,512),(0,0,0,0));d=ImageDraw.Draw(im)
for j in range(4):
 x=16+j*128;skin=[(230,182,139),(151,105,77),(207,157,110),(235,197,165)][j]
 shirt=[(184,39,48),(214,194,106),(57,109,164),(225,228,218)][j]
 d.ellipse((x+30,98,x+80,173),fill=skin+(255,));d.arc((x+27,93,x+83,161),175,355,fill=(57,38,26,255),width=13)
 d.rounded_rectangle((x+12,175,x+99,342),radius=22,fill=shirt+(255,))
 d.line((x+18,191,x+5,330),fill=shirt+(255,),width=17);d.line((x+93,191,x+106,330),fill=shirt+(255,),width=17)
 d.rounded_rectangle((x+21,336,x+50,477),radius=5,fill=(38,49,65,255));d.rounded_rectangle((x+62,336,x+91,477),radius=5,fill=(38,49,65,255))
 d.rounded_rectangle((x+13,476,x+54,511),radius=5,fill=(22,29,36,255));d.rounded_rectangle((x+60,476,x+101,511),radius=5,fill=(22,29,36,255))
save('spectators',im,'Original standing people, hair, clothes and shoes in the existing silhouette atlas')
im=Image.new('RGB',(1024,512),(18,36,54));d=ImageDraw.Draw(im);font=ImageFont.truetype(FONT,104)
for j in range(20):
 x=(j%5)*192;y=(j//5)*128;d.rectangle((x+5,y+4,x+182,y+119),outline=(151,167,171),width=3)
 text=str(j+1).zfill(2);box=d.textbbox((0,0),text,font=font);d.text((x+(192-box[2])/2,y-9),text,font=font,fill=(242,243,226))
save('garage_numbers',im,'High-resolution pit-bay number atlas, preserving the original UV regions')
for name,info in base.items():
 if not name.startswith('sign_'):continue
 text=info['purpose'].split(': ',1)[1];im=Image.new('RGB',(1024,256),(16,35,54));d=ImageDraw.Draw(im)
 d.rectangle((0,0,1023,31),fill=(192,33,46));d.rectangle((0,224,1023,255),fill=(211,223,223))
 size=168
 while True:
  font=ImageFont.truetype(FONT,size);box=d.textbbox((0,0),text,font=font)
  if box[2]-box[0]<=960:break
  size-=1
 d.text(((1024-(box[2]-box[0]))/2,(256-(box[3]-box[1]))/2-box[1]),text,font=font,fill=(248,247,235))
 save(name,im,'Original vector-redrawn HD lettering: '+text)
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# The event display is shared with the logical-texture generator. Generate it
# after saving the main manifest so both standalone and wrapper runs retain it.
import runpy
runpy.run_path(str(ROOT/'scripts/make_spectator_texture.py'))
manifest=json.loads((OUT/'manifest.json').read_text())
base=json.loads((ROOT/'textures/manifest.json').read_text())
assert set(manifest)==set(base)
archive=ROOT/'silverstone-hd.o2r'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_STORED) as z:
 z.writestr('mods.toml','[mod]\nname = "kart64-silverstone-hd"\nversion = "1.1.0"\n\n[dependencies]\nkart64-silverstone = ">=1.9.0"\n')
 z.writestr('credits/Silverstone-HD.txt','Original Silverstone HD textures. Quality and replacement-format reference: MK64 Reloaded by GhostlyDark and contributors, v2026.04.03. No textures copied from that pack.\n')
 for name,info in manifest.items():z.write(OUT/info['file'],'tracks/silverstone/'+info['file'])
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
# Show native detail without modifying the saved textures.
selected=['asphalt','grass','gravel','concrete','glass','garage','fence','leaves','crowd','cloud','spectators','sign_silverstone']
board=Image.new('RGB',(1200,940),(20,28,35));d=ImageDraw.Draw(board);font=ImageFont.truetype(FONT,17)
for i,name in enumerate(selected):
 x=(i%4)*300;y=(i//4)*310;im=Image.open(OUT/(name+'.png')).convert('RGBA');im.thumbnail((278,267),Image.Resampling.LANCZOS)
 bg=Image.new('RGBA',im.size,(120,155,165,255));bg.alpha_composite(im);board.paste(bg.convert('RGB'),(x+11,y+9));d.text((x+11,y+278),name,font=font,fill='white')
preview=ROOT/'previews/hd';preview.mkdir(parents=True,exist_ok=True);board.save(preview/'texture-sheet.jpg',quality=95)
print('HD_TEXTURES_READY',len(manifest),'textures',archive.stat().st_size,'bytes')
