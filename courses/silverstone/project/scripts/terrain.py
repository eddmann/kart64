"""Synthetic, shallow terrain for the stylised course; not survey elevation."""
import numpy as np


class HeightField:
    def __init__(self, data):
        points = np.asarray(data['points'])
        normals = np.asarray(data['normals'])
        self.bumps = []
        for name, height, width in [('Copse', 5.0, 390), ('Becketts', 4.5, 420),
                                    ('Stowe', 3.5, 360), ('Village', 1.8, 330)]:
            i = data['landmarks'][name]['path_index']
            self.bumps.append((points[i], height, width))
        # Broad spectator banks sit beyond the barriers, with soft rounded edges.
        for name in ('Copse', 'Luffield', 'Stowe'):
            i = data['landmarks'][name]['path_index']
            self.bumps.append((points[i] - normals[i] * 145, 3.0, 110))

    def __call__(self, xy):
        xy = np.asarray(xy, dtype=float)
        height = np.zeros(xy.shape[:-1])
        for centre, amplitude, width in self.bumps:
            height += amplitude * np.exp(-np.sum((xy-centre)**2, axis=-1)/(2*width**2))
        # Flat grid and Wing apron, joined with zero-slope smooth transitions.
        t = np.clip((np.linalg.norm(xy, axis=-1)-220)/220, 0, 1)
        return height * t*t*(3-2*t)


def grass_tint(xy):
    """Olive and straw patches, informed by summer circuit reference photographs."""
    x, y = np.asarray(xy).T
    t=np.clip(.48+.23*np.sin(x/140+y/260)+.17*np.cos(y/185-x/350)+.12*np.sin((x+y)/85),0,1)
    t=t*t*(3-2*t)
    green=np.array([.66,.80,.58]);dry=np.array([.99,.92,.84])
    return green[None,:]*(1-t[:,None])+dry[None,:]*t[:,None]


def foliage_tint(xy):
    x,y=np.asarray(xy).T
    t=.5+.25*np.sin(x/115+y/240)+.25*np.cos(y/160-x/310)
    return np.column_stack((.83+.17*t,.90+.10*t,.76+.24*(1-t)))
