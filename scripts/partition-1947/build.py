"""Step 5: labels.png -> partition lines and state areas in lon/lat (work/extract.json).

1. Runs: the Arab State's outline, cut by neighbour (runs.py).
2. Snap: the colour was sometimes printed out of register with the black linework, by up to ~40 px
   (~1.4 km). Each Arab|Jewish run is moved onto the printed boundary line: a dark run 6-55 px wide
   found along the normal, with outlier rejection and smoothing. Runs under 300 px (the Jaffa enclave)
   are left as traced.
3. City of Jerusalem: the Arab colour is printed under the thick boundary ring, so the colour edge is
   the ring's inner edge. Probing for the ring snags on the roads that leave the city, so instead the
   zone is grown evenly by the ring's typical half-width: 7 px (~250 m), the median distance from the
   colour edge to the middle of the ring measured along the outline.
4. Lines are smoothed, simplified and converted to lon/lat.
5. Areas: the lines are burnt into the country as barriers, each cell takes its majority colour, and
   the result is grown ~12 px (~400 m) out over the coast and frontier symbols, so the shading meets the
   modern coastline (the site draws areas under the water) and the Mandate boundary line."""
import cv2, numpy as np, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import SCAN_PNG, LABELS, EXTRACT, A_, J_, JLM, OUT
from runs import raw_runs
from georef import pix2ll
from scipy.ndimage import map_coordinates, gaussian_filter1d, median_filter

lab = cv2.imread(LABELS, 0)
H, W = lab.shape
gray = cv2.cvtColor(cv2.imread(SCAN_PNG), cv2.COLOR_BGR2GRAY).astype(np.float32)
T = np.arange(-50, 51, 1.0)


def normals(p, closed, sigma=6):
    mode = "wrap" if closed else "nearest"
    ps = np.stack([gaussian_filter1d(p[:, i], sigma, mode=mode) for i in (0, 1)], 1)
    t = np.gradient(ps, axis=0); t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-9
    return np.stack([-t[:, 1], t[:, 0]], 1)


def snap(pts, closed):
    p = pts.astype(float)
    if len(p) < 300:
        return p
    n = normals(p, closed)
    idx = np.arange(0, len(p), 3)
    off = np.full(len(idx), np.nan)
    for k, i in enumerate(idx):
        g = map_coordinates(gray, [p[i, 1] + T * n[i, 1], p[i, 0] + T * n[i, 0]], order=1, mode="nearest")
        dark = g < min(150, np.percentile(g, 85) - 55)
        best = None; j = 0
        while j < len(T):                 # nearest dark run of plausible width
            if dark[j]:
                e = j
                while e + 1 < len(T) and dark[e + 1]: e += 1
                w = e - j + 1; c = (T[j] + T[e]) / 2
                if 6 <= w <= 55 and abs(c) <= 45 and (best is None or abs(c) < abs(best)): best = c
                j = e + 1
            else:
                j += 1
        if best is not None:
            off[k] = best
    found = np.isfinite(off)
    # fill gaps, then robust smoothing: rolling median, clamp outliers to it, Gaussian
    x = np.arange(len(off))
    filled = np.interp(x, x[found], off[found], period=len(off) if closed else None)
    mode = "wrap" if closed else "nearest"
    med = median_filter(filled, size=15, mode=mode)
    clean = gaussian_filter1d(np.where(np.abs(filled - med) > 8, med, filled), 3, mode=mode)
    full = np.interp(np.arange(len(p)), idx, clean, period=len(p) if closed else None)
    print("snapped run: %d px, printed line found at %.0f%% of probes, shift median %.1f px, p95 %.1f px"
          % (len(p), found.mean() * 100, np.median(np.abs(clean)), np.percentile(np.abs(clean), 95)))
    return p + full[:, None] * n


def smooth(pts, sigma, closed):
    mode = "wrap" if closed else "nearest"
    out = np.stack([gaussian_filter1d(pts[:, i].astype(float), sigma, mode=mode) for i in (0, 1)], 1)
    if not closed:
        out[0], out[-1] = pts[0], pts[-1]
    return out


def simplify(pts, eps, closed):
    return cv2.approxPolyDP(pts.astype(np.float32).reshape(-1, 1, 2), eps, closed).reshape(-1, 2).astype(float)


def to_ll(pts):
    lon, lat = pix2ll(pts[:, 0], pts[:, 1])
    return [[round(float(a), 4), round(float(b), 4)] for a, b in zip(lon, lat)]


runs = raw_runs(lab)
snapped = {J_: [{"closed": r["closed"], "pts": snap(r["pts"], r["closed"])} for r in runs[J_]]}
zone = cv2.dilate((lab == JLM).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
zc, _ = cv2.findContours(zone, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
snapped[JLM] = [{"closed": True, "pts": max(zc, key=cv2.contourArea).reshape(-1, 2).astype(float)}]


def lines_ll(rs, sigma=2.0, eps=1.0):
    out = []
    for r in rs:
        ll = to_ll(simplify(smooth(r["pts"], sigma, r["closed"]), eps, r["closed"]))
        if r["closed"]:
            ll.append(ll[0])
        out.append(ll)
    return out


aj, ajl = lines_ll(snapped[J_]), lines_ll(snapped[JLM])

# areas: burn the lines into the country as barriers, re-assign each cell by majority colour
inside = (lab != OUT).astype(np.uint8)
barrier = np.zeros((H, W), np.uint8)
for cls in (J_, JLM):
    for r in snapped[cls]:
        p = r["pts"]
        if not r["closed"]:               # extend the ends a little so every cut reaches the outside
            for a in (0, -1):
                d = p[a] - p[a + (5 if a == 0 else -5)]; d /= np.linalg.norm(d) + 1e-9
                p = np.vstack([p[a] + 25 * d, p]) if a == 0 else np.vstack([p, p[a] + 25 * d])
        cv2.polylines(barrier, [p.round().astype(np.int32)], r["closed"], 1, 3)
cells = (inside & (1 - barrier)).astype(np.uint8)
n, cc = cv2.connectedComponents(cells, connectivity=4)
counts = np.zeros((n, 5), np.int64)
np.add.at(counts, (cc.ravel(), lab.ravel()), 1)
counts[:, OUT] = 0
major = counts.argmax(1); major[0] = OUT
new = major[cc].astype(np.uint8)
new[inside == 0] = OUT
bar = (barrier > 0) & (inside > 0)        # barrier pixels take the nearest cell's class
_, near = cv2.distanceTransformWithLabels(bar.astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
new = np.where(bar, np.concatenate([[0], new[~bar]]).astype(np.uint8)[near], new).astype(np.uint8)
new[inside == 0] = OUT
print("pixels whose class changed after snapping:", int(((new != lab) & (inside > 0)).sum()))


def signed_area(r):
    a = np.array(r); x, y = a[:, 0], a[:, 1]
    return 0.5 * float(np.sum(x[:-1] * y[1:] - x[1:] * y[:-1]))


def polygons(m, sigma=1.5, eps=1.5, min_area=500):
    """Polygons with holes, outer rings counter-clockwise and holes clockwise (RFC 7946)."""
    cnts, hier = cv2.findContours(m.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    if hier is None:
        return []
    hier = hier[0]; polys = []
    for i, c in enumerate(cnts):
        if hier[i][3] != -1 or cv2.contourArea(c) < min_area:
            continue
        rings = [c]; j = hier[i][2]
        while j != -1:
            if cv2.contourArea(cnts[j]) >= min_area: rings.append(cnts[j])
            j = hier[j][0]
        out = []
        for k, r in enumerate(rings):
            ll = to_ll(simplify(smooth(r.reshape(-1, 2), sigma, True), eps, True)); ll.append(ll[0])
            a = signed_area(ll)
            if (k == 0 and a < 0) or (k > 0 and a > 0): ll = ll[::-1]
            out.append(ll)
        polys.append(out)
    return polys


d_out, near = cv2.distanceTransformWithLabels((new == OUT).astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
lut = np.concatenate([[0], new[new != OUT]]).astype(np.uint8)
grown = np.where((new == OUT) & (d_out <= 12), lut[near], new).astype(np.uint8)
pa, pj, pjl = polygons(grown == A_), polygons(grown == J_), polygons(grown == JLM)
for nm, p in (("Arab State", pa), ("Jewish State", pj), ("City of Jerusalem", pjl)):
    print(f"{nm}: {len(p)} polygon(s), {sum(len(r) for poly in p for r in poly)} vertices")
print(f"lines: Arab|Jewish {len(aj)} runs, {sum(map(len, aj))} vertices; Arab|Jerusalem {sum(map(len, ajl))} vertices")
json.dump({"aj": aj, "ajl": ajl, "pa": pa, "pj": pj, "pjl": pjl}, open(EXTRACT, "w"))
