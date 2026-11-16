"""Step 3: on a lon/lat grid, work out the date each piece of ground came under Israeli control.

- Palestine: the partition plan's three areas together (partition-plan-1947.geojson).
- End state: the Israeli side of the 1949 armistice lines (armistice-lines-1949.geojson); the West Bank
  and the Gaza Strip are the two pieces that contain Nablus/Hebron/Jericho and Gaza/Khan Yunis.
- 11 June 1948 (first truce): the CIA June map's 'Jewish held' area plus its 'Jewish controlled' areas,
  except western Galilee, which the CIA July map puts on the Arab side of the first-truce line (apart
  from the coast north of Acre, which it puts on the Israeli side).
- July 1948: the CIA July map's 'Jewish gains between 1st and 2nd truces', dated by place: Lydda and
  Ramle 12 July, Nazareth and Lower Galilee 16 July, the southern block 18 July.
- After July: what remains of the end state is split into pieces dated by the operation that took them
  (REGIONS below). These shapes are our estimate, not traced from a map.
- Leftovers (thin strips where the CIA lines and the armistice lines don't quite meet) take the date of
  the nearest dated ground.
Output: work/didx.npy (0 = never Israeli-held; k = held from DATES[k-1]) and work/dates.json."""
import cv2, numpy as np, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import WORK, PARTITION, ARMISTICE, GW, GH, ll2g, g2ll
from georef import JULY, JULY_PANEL, july_to_june


def fill_geo(mask, geom):
    for poly in (geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]):
        rings = [np.stack(ll2g(np.array(r)[:, 0], np.array(r)[:, 1]), 1).round().astype(np.int32) for r in poly]
        cv2.fillPoly(mask, [rings[0]], 1)
        for h in rings[1:]: cv2.fillPoly(mask, [h], 0)


def poly(pts):
    m = np.zeros((GH, GW), np.uint8); a = np.array(pts, float)
    c, r = ll2g(a[:, 0], a[:, 1]); cv2.fillPoly(m, [np.stack([c, r], 1).round().astype(np.int32)], 1)
    return m


def sample(mask, xs, ys):
    xi, yi = np.round(xs).astype(int), np.round(ys).astype(int)
    ok = (xi >= 0) & (yi >= 0) & (xi < mask.shape[1]) & (yi < mask.shape[0])
    out = np.zeros(xs.shape, np.uint8); out[ok] = mask[yi[ok], xi[ok]]
    return out


cols, rows = np.meshgrid(np.arange(GW), np.arange(GH))
GLON, GLAT = g2ll(cols, rows)

# ---- Palestine and the end state
PAL = np.zeros((GH, GW), np.uint8)
for f in json.load(open(PARTITION))["features"]:
    if f["geometry"]["type"] in ("Polygon", "MultiPolygon"): fill_geo(PAL, f["geometry"])
bar = np.zeros((GH, GW), np.uint8)
for f in json.load(open(ARMISTICE))["features"]:
    gm = f["geometry"]
    for l in (gm["coordinates"] if gm["type"] == "MultiLineString" else [gm["coordinates"]]):
        p = np.stack(ll2g(np.array(l)[:, 0], np.array(l)[:, 1]), 1).round().astype(np.int32)
        cv2.polylines(bar, [p], False, 1, 2)
n, cc = cv2.connectedComponents((PAL & (1 - bar)).astype(np.uint8), connectivity=4)


def comp_at(lon, lat):
    c, r = ll2g(lon, lat); return cc[int(round(float(r))), int(round(float(c)))]


arab = {comp_at(35.2608, 32.2211), comp_at(35.0969, 31.5286), comp_at(35.46, 31.8561), comp_at(34.4597, 31.5075), comp_at(34.3031, 31.3444)}
A = cv2.dilate(np.isin(cc, list(arab)).astype(np.uint8), np.ones((5, 5), np.uint8)) & PAL
FINAL_I = (PAL & (1 - A)).astype(np.uint8)
del cc

# ---- the CIA maps on the grid
inP = PAL > 0
JX = np.full((GH, GW), -1.0); JY = np.full((GH, GW), -1.0)
JX[inP], JY[inP] = JULY.ll2pix(GLON[inP], GLAT[inP])
x0, y0, x1, y1 = JULY_PANEL
COVER = (inP & (JX >= x0) & (JX <= x1) & (JY >= y0) & (JY <= y1)).astype(np.uint8)

held = np.load(os.path.join(WORK, "june_held.npy")); ctrl = np.load(os.path.join(WORK, "june_ctrl.npy"))
n, cc, st, ce = cv2.connectedComponentsWithStats(ctrl, connectivity=8)
keep = np.zeros(n, bool)
for i in range(1, n):
    x, y = ce[i]
    western_galilee = 340 < x < 440 and 150 < y < 300
    keep[i] = st[i, cv2.CC_STAT_AREA] >= 150 and not western_galilee
june_px = held | keep[cc].astype(np.uint8)
gx, gy = july_to_june(JX, JY)
JUNE = np.zeros((GH, GW), np.uint8); JUNE[inP] = sample(june_px, gx[inP], gy[inP]); JUNE &= COVER

gains_px = np.load(os.path.join(WORK, "july_gains.npy"))
n, cc, st, ce = cv2.connectedComponentsWithStats(gains_px, connectivity=8)
GAINS = {}
for i in range(1, n):
    lo, la = JULY.pix2ll(np.array([ce[i][0]]), np.array([ce[i][1]]))
    name = "galilee" if la[0] > 32.6 else "lydda" if 31.85 < la[0] < 32.1 and lo[0] > 34.8 else \
           "south" if 31.6 < la[0] < 31.85 and lo[0] > 34.65 else None        # others: inset border, not hatching
    if name:
        G = np.zeros((GH, GW), np.uint8); G[inP] = sample((cc == i).astype(np.uint8), JX[inP], JY[inP])
        GAINS[name] = G & COVER
JUNE &= 1 - np.max(np.stack(list(GAINS.values())), 0)

# western Galilee coast north of Acre: Israeli side of the CIA July map's first-truce line
JUNE = (JUNE | (poly([(35.00, 33.12), (35.165, 33.12), (35.165, 32.86), (35.00, 32.86)]) & FINAL_I)) & FINAL_I
for k in GAINS: GAINS[k] &= FINAL_I
JULY_I = JUNE.copy()
for gm in GAINS.values(): JULY_I |= gm
DELTA = (FINAL_I & (1 - JULY_I)).astype(np.uint8)

# ---- after July: dated pieces (first match wins). Our estimate, from the dates of the main operations.
REGIONS = [
    ("Hiram: central Galilee", "1948-10-31", [(35.12, 33.40), (35.90, 33.40), (35.90, 32.75), (35.12, 32.75)]),
    ("Shoter: south of Haifa", "1948-07-26", [(34.90, 32.70), (35.04, 32.70), (35.04, 32.58), (34.90, 32.58)]),
    ("Faluja pocket", "1949-02-26", [(34.715, 31.655), (34.81, 31.655), (34.81, 31.595), (34.715, 31.595)]),
    ("Isdud and Majdal coast", "1948-11-05", [(34.40, 31.84), (34.715, 31.84), (34.69, 31.70), (34.63, 31.58), (34.40, 31.52)]),
    ("Triangle villages (armistice)", "1949-04-03", [(34.86, 32.12), (35.08, 32.12), (35.16, 32.42), (35.26, 32.56), (35.10, 32.62), (34.93, 32.50), (34.86, 32.40)]),
    ("Ha-Har: south of the corridor", "1948-10-24", [(34.90, 31.82), (35.16, 31.82), (35.16, 31.68), (34.90, 31.68)]),
    ("Yoav: Beit Jibrin", "1948-10-23", [(34.83, 31.68), (35.05, 31.68), (35.05, 31.57), (34.83, 31.57)]),
    ("Yoav: al-Dawayima", "1948-10-29", [(34.83, 31.57), (35.05, 31.57), (35.05, 31.46), (34.83, 31.46)]),
    ("Yoav: northern Negev and Beersheba", "1948-10-21", [(34.40, 31.84), (34.83, 31.84), (34.83, 31.46), (35.10, 31.46), (35.10, 31.30),
                                                         (34.95, 31.18), (34.80, 31.15), (34.60, 31.20), (34.40, 31.30)]),
    ("Horev: western Negev", "1948-12-27", [(34.20, 31.33), (34.40, 31.30), (34.60, 31.20), (34.80, 31.15), (34.86, 30.95), (34.55, 30.80),
                                           (34.45, 30.68), (34.30, 30.68), (34.20, 31.00)]),
    ("Uvda: southern Negev", "1949-03-10", [(34.20, 31.52), (35.95, 31.52), (35.95, 29.40), (34.20, 29.40)]),
]
assigned = np.zeros((GH, GW), np.uint8); PIECES = []
for name, date, pts in REGIONS:
    m = DELTA & poly(pts) & (1 - assigned); PIECES.append((name, date, m)); assigned |= m
    print(f"{name:36s} {date}  {int(m.sum())} cells")
DATES = sorted({"1948-06-11", "1948-07-12", "1948-07-16", "1948-07-18"} | {d for _, d, _ in PIECES})
GAIN_DATES = {"lydda": "1948-07-12", "galilee": "1948-07-16", "south": "1948-07-18"}
didx = np.zeros((GH, GW), np.int32)
didx[JUNE > 0] = DATES.index("1948-06-11") + 1
for k, gm in GAINS.items(): didx[(gm > 0) & (didx == 0)] = DATES.index(GAIN_DATES[k]) + 1
for _, date, m in PIECES: didx[m > 0] = DATES.index(date) + 1
left = DELTA & (1 - assigned)
_, near = cv2.distanceTransformWithLabels((didx == 0).astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
didx = np.where(left > 0, np.concatenate([[0], didx[didx != 0]]).astype(np.int32)[near], didx)
didx[FINAL_I == 0] = 0
print("leftover cells dated by their neighbours:", int(left.sum()))
np.save(os.path.join(WORK, "pal.npy"), PAL); np.save(os.path.join(WORK, "didx.npy"), didx)
json.dump(DATES, open(os.path.join(WORK, "dates.json"), "w"))
print("dates:", DATES)
