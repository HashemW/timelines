"""Check: which side of the traced lines do known towns fall on?

Fetches each town's coordinates from Wikipedia (cached in work/), finds which area of
partition-plan-1947.geojson contains it, and compares with the side the plan gives it (from the
resolution's text where it names the place, otherwise from the UN map). Places close to a line are
the interesting ones: the source map is about 1:1,000,000 with boundary lines printed 400-600 m wide."""
import json, numpy as np, os, sys, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import OUTPUT, WORK, USER_AGENT

EXPECTED = {
    "Jaffa": "Arab", "Tel Aviv": "Jewish", "Haifa": "Jewish", "Beersheba": "Arab", "Tiberias": "Jewish",
    "Safed": "Jewish", "Beit She'an": "Jewish", "Acre, Israel": "Arab", "Nazareth": "Arab", "Shefa-'Amr": "Arab",
    "Lod": "Arab", "Ramla": "Arab", "Isdud": "Arab", "Al-Majdal, Askalan": "Arab", "Gaza City": "Arab",
    "Hebron": "Arab", "Nablus": "Arab", "Jenin": "Arab", "Tulkarm": "Arab", "Qalqilya": "Arab",
    "Old City (Jerusalem)": "City of Jerusalem", "Bethlehem": "City of Jerusalem", "Ein Karem": "City of Jerusalem",
    "Abu Dis": "City of Jerusalem", "Shu'fat": "City of Jerusalem", "Motza": "City of Jerusalem",
    "Deir Yassin": "City of Jerusalem", "Ramallah": "Arab", "Latrun": "Arab", "Afula": "Jewish",
    "Kfar Etzion": "Arab", "Nitzanim": "Arab", "Yad Mordechai": "Arab", "Eilat": "Jewish", "Rehovot": "Jewish",
    "Beit Jibrin": "Arab", "Al-Faluja": "Arab", "Iraq Suwaydan": "Arab", "Nahariya": "Arab",
    "Majd al-Krum": "Arab", "Kafr Kanna": "Arab", "Rafah": "Arab", "Khan Yunis": "Arab",
    "Mitzpe Ramon": "Jewish", "Gan Yavne": "Jewish", "Batani Sharqi": "Arab", "Barqa, Gaza": "Arab",
    "Saliha": "Arab", "Sarid": "Jewish", "Al-Mujaydil": "Arab", "Tur'an": "Arab", "Qastina": "Arab",
}
OTHERS = ["Kafr Bir'im", "Mount Tabor", "Yasur, Gaza"]          # on or near a line; reported, not scored


def coords():
    cache = os.path.join(WORK, "wp_coords.json")
    if os.path.exists(cache):
        return json.load(open(cache, encoding="utf8"))
    names, out = list(EXPECTED) + OTHERS, {}
    for i in range(0, len(names), 50):                     # the API takes at most 50 titles per request
        q = urllib.parse.urlencode({"action": "query", "prop": "coordinates", "colimit": "max", "coprimary": "primary",
                                    "redirects": 1, "format": "json", "titles": "|".join(names[i:i + 50])})
        req = urllib.request.Request("https://en.wikipedia.org/w/api.php?" + q, headers={"User-Agent": USER_AGENT})
        d = json.load(urllib.request.urlopen(req))["query"]
        alias = {}
        for m in d.get("normalized", []) + d.get("redirects", []):
            alias[m["to"]] = alias.get(m["from"], m["from"])
        for p in d["pages"].values():
            if p.get("coordinates"):
                c = p["coordinates"][0]
                out[alias.get(p["title"], p["title"])] = [c["lon"], c["lat"]]
    json.dump(out, open(cache, "w", encoding="utf8"), ensure_ascii=False)
    return out


g = json.load(open(OUTPUT))
areas = [f for f in g["features"] if "fill" in f["properties"]]
lines = [l for f in g["features"] if "fill" not in f["properties"]
         for l in (f["geometry"]["coordinates"] if f["geometry"]["type"] == "MultiLineString" else [f["geometry"]["coordinates"]])]
KX, KY = 111.32 * np.cos(np.radians(31.5)), 110.57


def inside(pt, ring):
    x, y = pt; c = False
    for (x1, y1), (x2, y2) in zip(ring[:-1], ring[1:]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1): c = not c
    return c


def which(pt):
    for f in areas:
        polys = f["geometry"]["coordinates"] if f["geometry"]["type"] == "MultiPolygon" else [f["geometry"]["coordinates"]]
        for poly in polys:
            if inside(pt, poly[0]) and not any(inside(pt, h) for h in poly[1:]):
                return f["properties"]["name"].split(" (")[0]
    return "outside"


def km_to_line(pt):
    p = np.array(pt) * [KX, KY]; best = 1e9
    for l in lines:
        a = np.array(l) * [KX, KY]
        for A, B in zip(a[:-1], a[1:]):
            d = B - A; t = np.clip(np.dot(p - A, d) / (np.dot(d, d) + 1e-12), 0, 1)
            best = min(best, float(np.linalg.norm(p - (A + t * d))))
    return best


co = coords()
scored = ok = 0
for name in list(EXPECTED) + OTHERS:
    if name not in co:
        print(f"{name:24s} (no coordinates on Wikipedia)")
        continue
    got, exp = which(co[name]), EXPECTED.get(name)
    flag = ""
    if exp:
        scored += 1
        if got.startswith(exp): ok += 1
        else: flag = "  <-- differs"
    print(f"{name:24s} {got:18s} expected {exp or '-':18s} {km_to_line(co[name]):5.1f} km from a line{flag}")
print(f"\n{ok} of {scored} places are on the expected side")
