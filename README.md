# Timelines

**History on a map.** Pick a topic, such as a war or a person's life, then drag the time slider
and watch where and when things happened.

The idea: you can't really understand a historical event without understanding its geography.
Timelines puts the *where* and the *when* together, so a complete beginner can follow the shape
of a story before reading the details.

Every event carries its own sources, and where historians disagree the page shows each
account side by side instead of picking one.

## Topics

| Topic | Period | Status |
|-------|--------|--------|
| [The 1948 War](data/topics/1948-war/) | Nov 1947 – Jul 1949 | first draft: researched, not yet human-reviewed |

Planned kinds of topics: wars and campaigns, biographies and journeys (where someone went and
when), empires, and so on. Some topics will have borders, many won't.

## Run it locally

It's a static site with no build step. From this folder:

```
python -m http.server 8000
```

then open <http://localhost:8000>. (Opening `index.html` directly as a file won't work, because
browsers block loading the data files that way.)

## How it's organised

```
index.html, src/            the viewer (MapLibre GL map + time slider, plain JavaScript)
data/topics.json            list of topics
data/topics/<id>/           one folder per topic: topic.json, events.json, places.json …
docs/data-format.md         what goes in each file
docs/sourcing.md            the rules every piece of data follows
scripts/validate.mjs        checks the data: run `node scripts/validate.mjs`
```

## Controls

- Drag the slider, or press ▶ to play through time
- ‹ › (or Shift + ← →) jump to the previous / next event; ← → move one day
- Click a dot or a tick on the timeline to read about an event and see its sources
- The address bar always links to the exact date and event you're looking at

## Credits

Base map: [OpenFreeMap](https://openfreemap.org) / © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors.
Relief: [Terrain Tiles](https://registry.opendata.aws/terrain-tiles/) (Mapzen, on AWS Open Data).
Map rendering: [MapLibre GL JS](https://maplibre.org).
The base map deliberately shows no modern borders, roads or city names. Labels come from each
topic's own period data.
