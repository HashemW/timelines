"""Step 6: work/extract.json -> data/topics/1948-war/borders/partition-plan-1947.geojson

- Line ends that stop at a land frontier (Lebanon, the Jordan, Egypt) are joined to the Mandate boundary
  already on the map when it is within 1.5 km (the gaps are 0.3-0.9 km), so the lines meet it.
- The resolution's text has the boundary turn at 'Ein Geddi "due east to join the Transjordan frontier
  in the Dead Sea". The map stops at the shore, so that stretch is added along the end's latitude."""
import json, numpy as np, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import EXTRACT, MANDATE, OUTPUT

e = json.load(open(EXTRACT))
AREAS_END = "1948-06-10"           # the day before the first truce
KX, KY = 111.32 * np.cos(np.radians(31.5)), 110.57          # km per degree, near enough for distances here

segs = []
for f in json.load(open(MANDATE))["features"]:
    g = f["geometry"]
    for l in (g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]):
        segs += [(np.array(a), np.array(b)) for a, b in zip(l[:-1], l[1:])]


def nearest_on_boundary(pt):
    p = np.array(pt) * [KX, KY]; best = (1e9, None)
    for a, b in segs:
        A, B = a * [KX, KY], b * [KX, KY]; d = B - A
        t = np.clip(np.dot(p - A, d) / (np.dot(d, d) + 1e-12), 0, 1); q = A + t * d
        dist = np.linalg.norm(p - q)
        if dist < best[0]: best = (dist, q / [KX, KY])
    return best


lines = []
for l in e["aj"]:
    l = list(l)
    for end in (0, -1):
        dist, q = nearest_on_boundary(l[end])
        if dist <= 1.5:              # km; coast and Dead Sea ends are much further from the land boundary
            pt = [round(float(q[0]), 4), round(float(q[1]), 4)]
            print(f"joined end {l[end]} to the Mandate boundary at {pt} ({dist * 1000:.0f} m)")
            if end == 0: l.insert(0, pt)
            else: l.append(pt)
    for end in (0, -1):
        lon0, lat0 = l[end]
        if 35.3 < lon0 < 35.6 and 31.0 < lat0 < 31.8:          # the end on the Dead Sea shore
            xs = [float(a[0] + (lat0 - a[1]) * (b[0] - a[0]) / (b[1] - a[1])) for a, b in segs
                  if (a[1] - lat0) * (b[1] - lat0) < 0]
            xs = [x for x in xs if x > lon0]
            if xs:
                pt = [round(min(xs), 4), lat0]
                print(f"Dead Sea: extended {l[end]} due east to the Transjordan frontier at {pt}")
                if end == 0: l.insert(0, pt)
                else: l.append(pt)
    lines.append(l)


def mp(polys):
    return {"type": "MultiPolygon", "coordinates": polys} if len(polys) > 1 else {"type": "Polygon", "coordinates": polys[0]}


fc = {"type": "FeatureCollection", "features": [
    {"type": "Feature", "properties": {"name": "Boundary between the proposed Arab and Jewish states"},
     "geometry": {"type": "MultiLineString", "coordinates": lines}},
    {"type": "Feature", "properties": {"name": "Boundary of the City of Jerusalem (proposed international zone)"},
     "geometry": {"type": "LineString", "coordinates": e["ajl"][0]}},
    # the shading gives way to the 'areas held' layer at the first truce; the boundary lines stay for the whole war
    {"type": "Feature", "properties": {"name": "Arab State (proposed)", "end": AREAS_END, "fill": "#d9822b", "fill-opacity": 0.2}, "geometry": mp(e["pa"])},
    {"type": "Feature", "properties": {"name": "Jewish State (proposed)", "end": AREAS_END, "fill": "#2a9d8f", "fill-opacity": 0.2}, "geometry": mp(e["pj"])},
    {"type": "Feature", "properties": {"name": "City of Jerusalem (proposed international zone)", "end": AREAS_END, "fill": "#fffaf0", "fill-opacity": 0.55}, "geometry": mp(e["pjl"])},
]}
out = sys.argv[1] if len(sys.argv) > 1 else OUTPUT
s = json.dumps(fc, separators=(",", ":"))
open(out, "w", newline="\n").write(s + "\n")
print("wrote", out, f"({len(s) // 1024} KB)")
