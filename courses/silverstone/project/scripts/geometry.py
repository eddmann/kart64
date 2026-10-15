"""Build a closed Silverstone centreline from MIT-licensed geographic data."""
import json
import math
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
GAME_UNITS_PER_METRE = 6.0
EXPORT_SCALE = 100.0
ROAD_WIDTH_METRES = 36.0
SPACING_METRES = 7.0


def make_geometry():
    source = json.loads((ROOT / 'source/silverstone-layout.geojson').read_text())
    lonlat = np.array(source['features'][0]['geometry']['coordinates'][:-1], dtype=float)
    # Local equirectangular projection; sufficient for a circuit-sized blockout.
    origin = lonlat.mean(axis=0)
    xy = (lonlat - origin) * [111320 * math.cos(math.radians(origin[1])), 111320]
    source_xy = xy.copy()
    # Hamilton Straight lies on source segment 70->71. Place the grid within it.
    start = xy[70] * .70 + xy[71] * .30
    xy = np.concatenate(([start], xy[71:], xy[:71]))
    # Centripetal Catmull-Rom smooths sampled corners without rounding off the layout.
    dense = []
    count = len(xy)
    for i in range(count):
        p = [xy[(i+j) % count] for j in (-1, 0, 1, 2)]
        t = [0.0]
        for j in range(3):
            t.append(t[-1] + np.linalg.norm(p[j+1]-p[j]) ** .5)
        for u in np.linspace(t[1], t[2], max(12, int(np.linalg.norm(p[2]-p[1])/2)), endpoint=False):
            a = [(t[j+1]-u)/(t[j+1]-t[j])*p[j] + (u-t[j])/(t[j+1]-t[j])*p[j+1] for j in range(3)]
            b = [(t[j+2]-u)/(t[j+2]-t[j])*a[j] + (u-t[j])/(t[j+2]-t[j])*a[j+1] for j in range(2)]
            dense.append((t[2]-u)/(t[2]-t[1])*b[0] + (u-t[1])/(t[2]-t[1])*b[1])
    dense = np.array(dense + [dense[0]])
    lengths = np.linalg.norm(np.diff(dense, axis=0), axis=1)
    cumulative = np.concatenate(([0], np.cumsum(lengths)))
    lap = float(cumulative[-1])
    n = round(lap / SPACING_METRES)
    distances = np.arange(n) * lap/n
    points = np.column_stack([np.interp(distances, cumulative, dense[:,j]) for j in range(2)])
    forward = points[1]-points[0]
    forward /= np.linalg.norm(forward)
    right = np.array([forward[1], -forward[0]])
    points = (points-points[0]) @ np.column_stack((right, forward))
    landmark_indices = {'Abbey':75,'Farm':81,'Village':87,'The Loop':93,'Aintree':101,
                        'Brooklands':111,'Luffield':122,'Woodcote':130,'Copse':4,
                        'Maggotts':18,'Becketts':27,'Chapel':32,'Stowe':42,'Vale':56,'Club':66}
    landmarks = {}
    for name,index in landmark_indices.items():
        pos = (source_xy[index]-start) @ np.column_stack((right,forward))
        nearest = int(np.argmin(np.linalg.norm(points-pos,axis=1)))
        landmarks[name] = {'source_index':index,'path_index':nearest,'position':points[nearest].tolist()}
    tangent = np.roll(points, -1, axis=0)-np.roll(points, 1, axis=0)
    tangent /= np.linalg.norm(tangent, axis=1)[:,None]
    normals = np.column_stack((tangent[:,1], -tangent[:,0]))
    angle = np.arccos(np.clip(np.sum(tangent*np.roll(tangent, 1, axis=0), axis=1), -1, 1))
    radius = (lap/n) / np.maximum(angle, 1e-5)
    # Use a conservative neighbourhood radius so widths do not jump at a corner apex.
    radius = np.minimum.reduce([np.roll(radius, offset) for offset in range(-4,5)])
    half_width = np.minimum(ROAD_WIDTH_METRES/2, radius*.58)
    # Narrow shoulders on tight bends to prevent folded offset geometry.
    shoulder = np.clip(radius*.70-half_width-1.5, .5, 8)
    result = dict(points=points.tolist(), normals=normals.tolist(), half_width=half_width.tolist(),
                  shoulder=shoulder.tolist(), lap_metres=lap, sample_count=n,
                  game_units_per_metre=GAME_UNITS_PER_METRE, export_scale=EXPORT_SCALE,
                  metres_to_blender=GAME_UNITS_PER_METRE/EXPORT_SCALE,
                  nominal_road_width_metres=ROAD_WIDTH_METRES,
                  minimum_road_width_metres=float(half_width.min()*2),
                  start_source_segment=70, start_segment_fraction=.30,
                  source_origin_lonlat=origin.tolist())
    result['landmarks'] = landmarks
    from terrain import HeightField
    result['heights'] = HeightField(result)(points).tolist()
    result['elevation_source'] = 'Synthetic shallow landscape; not surveyed Silverstone elevation'
    (ROOT/'source/geometry.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    data = make_geometry()
    print(json.dumps({k:v for k,v in data.items() if k not in ('points','normals','half_width','shoulder')}, indent=2))
