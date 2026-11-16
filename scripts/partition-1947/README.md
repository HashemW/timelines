# Tracing the 1947 UN partition plan

These scripts made `data/topics/1948-war/borders/partition-plan-1947.geojson`. No ready-made dataset
of the plan exists, so it was traced from the UN's own map of it:

> *Palestine: plan of partition with Economic Union proposed by the Ad Hoc Committee on the Palestinian
> Question*, UN Map No. 103, November 1947, marked "A/516 Annex A". Scan: UN Digital Library
> [record 409073](https://digitallibrary.un.org/record/409073), file `103_1.tif` (7578 × 14043 px).

The traced lines were then checked against the boundary description in the text of Resolution 181
(Part II, and Part III B for the City of Jerusalem).

## Running it

```
pip install -r scripts/partition-1947/requirements.txt
python scripts/partition-1947/trace.py          # all steps; rewrites the GeoJSON
python scripts/partition-1947/check_towns.py    # optional: which side known places fall on
node scripts/validate.mjs
```

The scan (about 43 MB) and the intermediate images go in `scripts/partition-1947/work/`, which git
ignores. With the library versions in `requirements.txt`, a run reproduces the committed file exactly.

## Steps

1. `fetch.py`: download the scan and convert it to PNG.
2. `graticule.py`: follow the printed meridians (35°E, 36°E) and parallels (30–33°N) across the scan
   to sub-pixel accuracy. They are slightly bowed (up to ~18 px), so a single affine fit won't do.
3. `georef.py`: pixel ↔ longitude/latitude from those lines. Longitude is linear between the two
   meridians along each row; latitude is piecewise linear between the parallels. Town symbols on the
   map land within about 0.3–1 km of modern coordinates, in no particular direction.
4. `segment.py`: sort pixels by colour into the Arab State (peach), the Jewish State (turquoise), the
   City of Jerusalem (the white hole in the Arab State) and outside. Printed lines and text take the
   nearest colour, which puts each boundary in the middle of its printed line.
5. `build.py`: cut the Arab State's outline into lines by neighbour. In places the colour was printed
   out of register with the black linework by up to ~40 px (~1.4 km), so the lines are snapped onto
   the printed boundary. For Jerusalem the colour edge is the inside of a thick printed ring, so the
   zone is grown by the ring's median half-width (7 px) instead. The areas are rebuilt from the
   snapped lines and grown ~400 m out over the coast and frontier, because the site draws them under
   the water layer.
6. `export.py`: join three line ends to the Mandate boundary already on the map (gaps of 0.3–0.9 km),
   add the stretch across the Dead Sea that only the text describes ("due east to join the Transjordan
   frontier in the Dead Sea"), and write the GeoJSON.

## Limits

- The source is about 1:1,000,000 and its boundary lines are printed 400–600 m wide. Expect errors of
  a few hundred metres, up to about 1 km. `check_towns.py` scores 48 places, and 46 fall on the
  expected side. The two that don't are both within a kilometre of a line: Motza, which the text puts
  inside the Jerusalem zone, falls about 700 m outside, and Qalqilya, which the text leaves in the Arab
  State, falls about 400 m on the Jewish side.
- The seed points, search windows and colour thresholds at the top of each script fit this scan only.
- The text says Jerusalem's boundary is shown in more detail on a separate sketch map (Annex B). That
  map was not used.
