"""Combine validated core resources with HD overlays for a single-file installation."""
import json,zipfile,hashlib
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'silverstone.o2r';addon=ROOT/'silverstone-hd.o2r';out=ROOT/'silverstone-hd-complete.o2r'
manifest=json.loads((ROOT/'textures/hd/manifest.json').read_text());used=[];unused=[]
# Assemble the addon from source PNGs even when artwork is not regenerated.
with zipfile.ZipFile(addon,'w',zipfile.ZIP_STORED) as target:
 target.writestr('mods.toml','[mod]\nname = "kart64-silverstone-hd"\nversion = "1.1.0"\n\n[dependencies]\nkart64-silverstone = ">=1.9.0"\n')
 target.writestr('credits/Silverstone-HD.txt','Original Silverstone HD textures. Quality and replacement-format reference: MK64 Reloaded by GhostlyDark and contributors, v2026.04.03. No textures copied from that pack.\n')
 for name,info in manifest.items():
  target.write(ROOT/'textures/hd'/info['file'],'tracks/silverstone/'+info['file'])
with zipfile.ZipFile(base) as core,zipfile.ZipFile(addon) as hd,zipfile.ZipFile(out,'w',zipfile.ZIP_STORED) as target:
 assert core.testzip() is None and hd.testzip() is None
 for name in core.namelist():
  if name!='mods.toml':target.writestr(name,core.read(name))
 target.writestr('mods.toml','[mod]\nname = "kart64-silverstone"\nversion = "1.9.0"\n\n[dependencies]\nmk64-assets = "=1.0.0-alpha1"\n')
 for name in hd.namelist():
  if name!='mods.toml':target.writestr(name,hd.read(name))
 for name,info in manifest.items():
  data=(ROOT/'textures/hd'/info['file']).read_bytes()
  assert hashlib.sha256(data).hexdigest()==info['sha256']
  image=Image.open(ROOT/'textures/hd'/info['file']);assert image.mode=='RGBA' and list(image.size)==info['size']
  assert info['size']==[s*16 for s in info['logical_size']]
  path='tracks/silverstone/'+name
  (used if path in core.namelist() else unused).append(name)
with zipfile.ZipFile(base) as core,zipfile.ZipFile(out) as complete:
 assert complete.testzip() is None
 for name in core.namelist():
  if name!='mods.toml':assert core.read(name)==complete.read(name),name
report={'status':'passed','edition':'1.9.0-HD','texture_count':len(manifest),'used_in_course':len(used),'unused_library_textures':unused,'scale_per_axis':16,'core_game_resources_unchanged':True,'checks':['Archive integrity','All HD RGBA PNG dimensions, aspect ratios and hashes','Exact equality of core geometry, collision, AI, scene and binary textures'],'addon_sha256':hashlib.sha256(addon.read_bytes()).hexdigest(),'complete_mod_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'reference_pack_bundled':False}
(ROOT/'source/hd-validation-report.json').write_text(json.dumps(report,indent=2)+'\n')
print('HD_COMPLETE',out.stat().st_size,report)
