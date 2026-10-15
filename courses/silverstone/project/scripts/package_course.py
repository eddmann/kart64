"""Create metadata, a minimap, and a ZIP_STORED SpaghettiKart mod archive."""
import json
import shutil
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image, ImageDraw
from terrain import HeightField
from stabilize_materials import stabilize_export

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'export'
TRACK=OUT/'tracks/silverstone'
print('STABILIZED_MATERIALS', stabilize_export(TRACK))
data=json.loads((ROOT/'source/geometry.json').read_text())
points=data['points']; factor=data['game_units_per_metre']
height=HeightField(data)
world=[(x*factor,-y*factor) for x,y in points]
minimum=[min(p[j] for p in world) for j in range(2)]
maximum=[max(p[j] for p in world) for j in range(2)]
size=96; padding=6
scale=(size-padding*2)/max(maximum[j]-minimum[j] for j in range(2))
offset=[(size-(maximum[j]-minimum[j])*scale)/2-minimum[j]*scale for j in range(2)]
pixels=[(x*scale+offset[0],y*scale+offset[1]) for x,y in world]
im=Image.new('RGBA',(size,size),(0,0,0,0))
ImageDraw.Draw(im).line(pixels+[pixels[0]],fill=(255,255,255,255),width=3)
im.save(TRACK/'minimap.png')
scene=json.loads((ROOT/'source/scene-defaults.json').read_text())
sky=list(ET.parse(TRACK/'mk64_Sky_dome_mesh_vtx').getroot())
horizon=[int(next(v for v in sky if int(v.get('Y'))<=0).get(a)) for a in ('R','G','B')]
zenith=[int(max(sky,key=lambda v:int(v.get('Y'))).get(a)) for a in ('R','G','B')]
scene['Props'].update(ResourceName='eddmann:silverstone',DebugName='silver',Name='Silverstone',
                      TrackLength='5.89 km',WaterLevel=-60.0,
                      FarPersp=30000.0,
                      Skybox=zenith+horizon+horizon+zenith+horizon+[112,115,78]*2+horizon,
                      MinimapPlayerScaleFactor=scale,
                      MinimapPlayerX=round(offset[0]),MinimapPlayerY=round(offset[1]),
                      MinimapFinishlineX=0,MinimapFinishlineY=0,
                      MinimapColour=[255,255,255],MinimapPosition=[260,166])
actors=[]
rows=[90,215,390,635,750,825]
for index in rows:
    px,py=points[index];nx,ny=data['normals'][index]
    half=min(12,data['half_width'][index]*.65)
    for multiplier in (-1,-.5,0,.5,1):
        offset=half*multiplier
        x,y=px+nx*offset,py+ny*offset
        actors.append({'Name':'mk:item_box','Location':{'x':x*factor,'y':float(height([x,y]))*factor,'z':-y*factor}})
scene.update(Actors=actors,StaticMeshActors=[],Tour={'Enabled':False,'Shots':[]},Fog={'Enabled':False})
(TRACK/'scene.json').write_text(json.dumps(scene,indent=2)+'\n')
(OUT/'mods.toml').write_text('[mod]\nname = "kart64-silverstone"\nversion = "1.9.0"\n'
                          '\n[dependencies]\nmk64-assets = "=1.0.0-alpha1"\n')
(OUT/'credits').mkdir(exist_ok=True)
shutil.copyfile(ROOT/'source/circuit-data-LICENSE.txt',OUT/'credits/circuit-data-LICENSE.txt')
(OUT/'credits/SOURCES.txt').write_text('Silverstone layout derived from bacinger/f1-circuits (MIT):\n'
    'https://github.com/bacinger/f1-circuits/blob/master/circuits/gb-1948.geojson\n'
    'Original course geometry/scenery generated for the Kart64 course prototype.\n'
    'Exported using HarbourMasters Fast64. See courses/silverstone/docs/VALIDATION.md for native test scope.\n')
provenance={
    'layout_source':'https://github.com/bacinger/f1-circuits/blob/master/circuits/gb-1948.geojson',
    'layout_license':'MIT; see source/circuit-data-LICENSE.txt',
    'fast64_repository':'https://github.com/HarbourMasters/fast64',
    'fast64_commit':'0f7a80a6b40c73a8d65dd2dab37310c163f54c68',
    'target_spaghettikart_commit':'aedcf9ada627f4f8e861f12d8b48f587de521e6b',
    'target_kart64_repository':'https://github.com/eddmann/kart64',
    'scene_defaults_source':'HarbourMasters/SpaghettiKart assets/tracks/harbour/scene.json at target commit',
    'created':'2026-10-03','edition':'1.9.0',
    'runtime_tested':False,
    'runtime_test_report':'courses/silverstone/docs/VALIDATION.md',
    'original_textures':str(len(json.loads((ROOT/'textures/manifest.json').read_text())))+' original procedural and pixel-art PNGs, no reference photographs used as textures',
    'original_models':str(len(json.loads((ROOT/'source/asset-library-manifest.json').read_text())['models']))+' reusable models in the Asset Library Blender scene',
    'sky':'Vertex-colour dome, 24 original cloud cards and matching engine skybox palette; all exported as non-collidable scenery',
    'ground_surfaces':'Photo-informed dry-weather grass, paved compounds, service routes and mixed runoff; original generated textures',
    'ground_reference_review':'courses/silverstone/references/ground-reference-review.json',
    'assumptions':['Summer/dry-weather colour interpretation', 'Approximate external surface placements', 'Synthetic shallow elevation; not a surveyed profile','Synthetic road widths','Stylised original scenery',
                   'Grid placed approximately within Hamilton Straight','Minimap calibration needs runtime confirmation'],
}
(ROOT/'source/provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
archive=ROOT/'silverstone.o2r'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_STORED) as z:
    for path in sorted(OUT.rglob('*')):
        if path.is_file():z.write(path,path.relative_to(OUT).as_posix())
print('PACKAGED',archive,archive.stat().st_size)
