# Who held what, 1948–1949 (approximate)

These scripts made `data/topics/1948-war/borders/areas-held-1948-1949.geojson`: one snapshot of the
ground held by each side for every stage of the war, plus the front line between them, each with
`start` and `end` dates so the map changes as the slider moves.

## Sources

- **11 June 1948 (first truce):** CIA Map Branch, *Military Situation – 11 June 1948*, declassified,
  Truman Library ([scan on Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Palestine_Military_Situation,_June_11,_1948,_Truman_Papers.jpg)).
  Its "Jewish held" and "Jewish controlled" areas are read off by colour.
- **July 1948 (second truce):** CIA Map Branch, *Military Situation – 18 July 1948*, declassified
  ([scan hosted by the Jewish Virtual Library](https://www.jewishvirtuallibrary.org/1948-war-military-situation-at-beginning-of-second-truce)).
  Its hatched "Jewish gains between 1st and 2nd truces" are found with a filter tuned to the hatching.
  Western Galilee follows this map, which puts its hills on the Arab side during the first truce,
  although the June map calls them "Jewish controlled".
- **End state:** the Israeli side of the 1949 armistice lines (the armistice layer, from OpenHistoricalMap).
- **In between (our estimate):** the ground that changed hands after July is cut into pieces by hand-drawn
  regions in `build.py`, each dated by the operation that took it: Shoter (26 July), Yoav (21–29 October),
  Ha-Har (24 October), Hiram (31 October), Majdal (5 November), Horev (27 December), the Faluja pocket
  (26 February 1949), Uvda (10 March) and the Triangle villages (armistice with Transjordan, 3 April).
  The West Point maps of October 1948 and December 1948 – January 1949 were used as a guide. Thin strips
  where the CIA lines and the armistice lines don't quite meet take the date of the nearest dated ground.

## Running it

```
pip install -r scripts/areas-held-1948/requirements.txt
python scripts/areas-held-1948/trace.py     # rewrites the GeoJSON
node scripts/validate.mjs
```

It reads the partition plan and armistice layers already in the repo. Downloads and intermediate
arrays go in `scripts/areas-held-1948/work/` (ignored by git).

## Steps

1. `fetch.py`: download the two CIA maps.
2. `segment.py`: read their shading.
3. `build.py`: on a 0.0015° grid (~150 m), work out from which date each piece of ground was Israeli-held.
   `georef.py` fits the CIA maps to coordinates from their printed graticule ticks; both maps use the
   same CIA base map.
4. `export.py`: one snapshot per date: areas held by each side and the front line, simplified to ~300 m.

## Limits

- Expect errors of a kilometre or more: the CIA maps are small (the June scan is 685 px wide) and the
  steps after July are estimates.
- The map changes in steps on the dates above, not day by day.
- The southern Negev below 31.05° N is left unshaded until Operation Uvda (March 1949): neither side held
  that largely empty desert. Ground held outside the former Mandate (Israeli forces in Lebanon and Sinai)
  is not shown.
