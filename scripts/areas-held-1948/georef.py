"""(module) Pixel <-> lon/lat for the two CIA maps.

Both maps are printed on the same CIA base map (Map Branch, 11010). The July scan is 2.4 times larger,
so it is fitted from its own graticule ticks (read off the scan: 30-minute marks on the frame), and the
June scan is mapped onto it through the two frames' corners."""
import numpy as np


def _design(x, y, terms):
    x = np.asarray(x, float); y = np.asarray(y, float)
    cols = {"1": np.ones_like(x), "x": x, "y": y, "xy": x * y}
    return np.stack([cols[t] for t in terms], -1)


class Georef:
    """lon = bilinear in x, y (the meridians converge slightly); lat = linear in x, y."""
    def __init__(self, lon_pts, lat_pts, lon_terms=("1", "x", "y", "xy"), lat_terms=("1", "x", "y")):
        self.lt, self.at = lon_terms, lat_terms
        X = np.array(lon_pts, float); Y = np.array(lat_pts, float)
        self.cl = np.linalg.lstsq(_design(X[:, 0], X[:, 1], lon_terms), X[:, 2], rcond=None)[0]
        self.ca = np.linalg.lstsq(_design(Y[:, 0], Y[:, 1], lat_terms), Y[:, 2], rcond=None)[0]

    def pix2ll(self, x, y):
        return _design(x, y, self.lt) @ self.cl, _design(x, y, self.at) @ self.ca

    def ll2pix(self, lon, lat, x0=900.0, y0=1100.0, iters=20):
        lon = np.asarray(lon, float); lat = np.asarray(lat, float)
        x = np.full(lon.shape, x0); y = np.full(lon.shape, y0)
        for _ in range(iters):            # Newton's method
            lo, la = self.pix2ll(x, y); e = 0.5
            lx, ax = self.pix2ll(x + e, y); ly, ay = self.pix2ll(x, y + e)
            J11, J12, J21, J22 = (lx - lo) / e, (ly - lo) / e, (ax - la) / e, (ay - la) / e
            det = J11 * J22 - J12 * J21
            x = x + (J22 * (lon - lo) - J12 * (lat - la)) / det
            y = y + (-J21 * (lon - lo) + J11 * (lat - la)) / det
        return x, y


# July scan: (x, y, value) of the graticule ticks on the frame. The left-hand 33N point comes from the
# June scan, where the parallel is labelled beside the legend box.
JULY = Georef(lon_pts=[(857, 168, 35.0), (1206, 168, 35.5), (490, 2064, 34.5), (851, 2064, 35.0), (1206.5, 2064, 35.5)],
              lat_pts=[(1449, 456.8, 33.0), (1449, 873, 32.5), (1449, 1286, 32.0), (1449, 1698, 31.5), (732, 454, 33.0)])
JULY_PANEL = (228, 170, 1447, 2062)                    # x0, y0, x1, y1 inside the frame

# June scan -> July scan, from the inner frames: June (53..558, 71..860), July (226..1449, 168..2064)
_SX, _SY = (1449 - 226) / (558 - 53), (2064 - 168) / (860 - 71)


def july_to_june(x, y):
    return 53 + (np.asarray(x) - 226) / _SX, 71 + (np.asarray(y) - 168) / _SY
