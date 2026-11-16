"""Step 4: one snapshot per date -> data/topics/1948-war/borders/areas-held-1948-1949.geojson

Each snapshot has the ground held by Israeli forces, the ground held by Arab forces, and the front line
between them, with "start" and "end" dates. Until Operation Uvda (10 March 1949) the southern Negev
below 31.05 N is left unshaded: it was largely empty desert that neither side held."""
import cv2, numpy as np, json, os, sys, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import WORK, OUTPUT, GH, GW, g2ll
from outline import runs_facing
from scipy.ndimage import gaussian_filter1d

PAL = np.load(os.path.join(WORK, "pal.npy")); DIDX = np.load(os.path.join(WORK, "didx.npy"))
DATES = json.load(open(os.path.join(WORK, "dates.json")))
LAT = g2ll(0, np.arange(GH))[1][:, None] * np.ones((1, GW))
UVDA = DATES.index("1949-03-10") + 1
LAST = "1949-07-20"


def to_ll(p):
    lon, lat = g2ll(p[:, 0], p[:, 1])
    return [[round(float(a), 4), round(float(b), 4)] for a, b in zip(lon, lat)]


def smooth(p, sigma, closed):
    mode = "wrap" if closed else "nearest"
    o = np.stack([gaussian_filter1d(p[:, i].astype(float), sigma, mode=mode) for i in (0, 1)], 1)
    if not closed: o[0], o[-1] = p[0], p[-1]
    return o


def simplify(p, eps, closed):
    return cv2.approxPolyDP(p.astype(np.float32).reshape(-1, 1, 2), eps, closed).reshape(-1, 2)


def signed_area(r):
    a = np.array(r); return 0.5 * float(np.sum(a[:-1, 0] * a[1:, 1] - a[1:, 0] * a[:-1, 1]))


def polygons(m, eps=2.0, min_area=40):
    cnts, hier = cv2.findContours(m.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    if hier is None: return []
    hier = hier[0]; out = []
    for i, c in enumerate(cnts):
        if hier[i][3] != -1 or cv2.contourArea(c) < min_area: continue
        rings = [c]; j = hier[i][2]
        while j != -1:
            if cv2.contourArea(cnts[j]) >= min_area: rings.append(cnts[j])
            j = hier[j][0]
        poly = []
        for k, r in enumerate(rings):
            ll = to_ll(simplify(smooth(r.reshape(-1, 2), 1.0, True), eps, True)); ll.append(ll[0])
            a = signed_area(ll)
            if (k == 0 and a < 0) or (k > 0 and a > 0): ll = ll[::-1]
            poly.append(ll)
        out.append(poly)
    return out


def geom(polys):
    return {"type": "MultiPolygon", "coordinates": polys} if len(polys) != 1 else {"type": "Polygon", "coordinates": polys[0]}


features = []
for k, start in enumerate(DATES):
    end = (datetime.date.fromisoformat(DATES[k + 1]) - datetime.timedelta(days=1)).isoformat() if k + 1 < len(DATES) else LAST
    isr = ((DIDX >= 1) & (DIDX <= k + 1)).astype(np.uint8)
    unheld = ((DIDX == UVDA) & (LAT < 31.05) & (k + 1 < UVDA)).astype(np.uint8)
    arab = (PAL & (1 - isr) & (1 - unheld)).astype(np.uint8)
    lab = np.full((GH, GW), 4, np.uint8); lab[arab > 0] = 1; lab[isr > 0] = 2
    front = []
    for r in runs_facing(lab, 1, 2, (2, 4)):           # Arab outline where it faces Israeli-held ground
        if len(r["pts"]) < 12: continue
        ll = to_ll(simplify(smooth(r["pts"], 1.5, r["closed"]), 1.5, r["closed"]))
        if r["closed"]: ll.append(ll[0])
        front.append(ll)
    pi, pa = polygons(isr), polygons(arab)
    features.append({"type": "Feature", "properties": {"name": "Held by Israeli forces", "start": start, "end": end,
                     "fill": "#2a9d8f", "fill-opacity": 0.3}, "geometry": geom(pi)})
    features.append({"type": "Feature", "properties": {"name": "Held by Arab forces", "start": start, "end": end,
                     "fill": "#d9822b", "fill-opacity": 0.26}, "geometry": geom(pa)})
    if front:
        features.append({"type": "Feature", "properties": {"name": "Front line", "start": start, "end": end},
                         "geometry": {"type": "MultiLineString", "coordinates": front}})
    print(f"{start}..{end}: {sum(len(r) for p in pi for r in p)} + {sum(len(r) for p in pa for r in p)} area vertices, "
          f"{sum(map(len, front))} front vertices")
s = json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":"))
open(OUTPUT, "w", newline="\n").write(s + "\n")
print("wrote", OUTPUT, f"({len(s) // 1024} KB)")
