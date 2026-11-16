"""Step 3 (module): pixel <-> lon/lat for the scan, from the graticule followed in step 2.

Longitude is linear along each row between the 35E and 36E meridians (the frame's 10-minute marks are
evenly spaced, so this holds) and extrapolated beyond them. Latitude is piecewise linear between the
30-33N parallels and extrapolated beyond 30N and 33N.

Run it directly for a self-check of the graticule intersections and the corners of the frame."""
import json, numpy as np, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import GRATICULE

_d = json.load(open(GRATICULE))
PAR = {k: _d[f"lat{k}"]["quad"] for k in (30, 31, 32, 33)}    # y = f(x) for each parallel
MER = {k: _d[f"lon{k}"]["quad"] for k in (35, 36)}            # x = f(y) for each meridian


def pix2ll(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    x35 = np.polyval(MER[35], y); x36 = np.polyval(MER[36], y)
    lon = 35 + (x - x35) / (x36 - x35)
    shape = np.broadcast(x, y).shape
    ys = np.broadcast_to(np.stack([np.polyval(PAR[k], x) for k in (30, 31, 32, 33)], axis=-1), shape + (4,))
    yb = np.broadcast_to(y, shape)
    # interval: 0 = south of 31N, 1 = 31-32N, 2 = north of 32N (image y grows southwards)
    seg = np.argmax(np.concatenate([yb[..., None] >= ys[..., 1:], np.ones(shape + (1,), bool)], -1), -1)
    seg = np.clip(seg, 0, 2)
    y0 = np.take_along_axis(ys, seg[..., None], -1)[..., 0]
    y1 = np.take_along_axis(ys, seg[..., None] + 1, -1)[..., 0]
    return lon, 30 + seg + (yb - y0) / (y1 - y0)


def ll2pix(lon, lat, iters=8):
    """Inverse of pix2ll by Newton's method."""
    lon = np.asarray(lon, float); lat = np.asarray(lat, float)
    x = 3150 + (lon - 35) * 2690.0
    y = 8150 - (lat - 31) * 3190.0
    for _ in range(iters):
        lo, la = pix2ll(x, y)
        e = 0.5
        lo_x, la_x = pix2ll(x + e, y); lo_y, la_y = pix2ll(x, y + e)
        J11 = (lo_x - lo) / e; J12 = (lo_y - lo) / e; J21 = (la_x - la) / e; J22 = (la_y - la) / e
        det = J11 * J22 - J12 * J21
        dlo = lon - lo; dla = lat - la
        x = x + (J22 * dlo - J12 * dla) / det
        y = y + (-J21 * dlo + J11 * dla) / det
    return x, y


if __name__ == "__main__":
    for lon in (35, 36):
        for lat in (30, 31, 32, 33):
            x, y = ll2pix(lon, lat); lo, la = pix2ll(x, y)
            print(f"{lon}E {lat}N -> px ({x:.1f}, {y:.1f}) -> back ({lo:.5f}, {la:.5f})")
    corners = [(850, 818), (6750, 818), (850, 13088), (6750, 13088)]
    print("frame corners (lon, lat):", [tuple(round(float(v), 4) for v in pix2ll(a, b)) for a, b in corners])
