# Data format

All content lives in plain JSON files under `data/`, so every change is visible in git history.

```
data/
  topics.json                  list of topics (id, title, one-line blurb)
  topics/<topic-id>/
    topic.json                 title, names, summary, date range, map view, phases
    events.json                things that happened at a place on a date
    places.json                (optional) reference labels: towns/regions as named in the period
    journeys.json              (planned) ordered stops for a person or group, e.g. a biography
    areas.geojson              (planned) borders / areas of control, each with a date range
```

Not every topic needs every file. A biography might be mostly `journeys.json`. A war
might have `events.json` and, where good data exists, `areas.geojson`.

## Dates

Dates are strings in ISO order, as precise as the evidence allows:

| Written      | Means                     |
|--------------|---------------------------|
| `1948`       | sometime in 1948          |
| `1948-07`    | sometime in July 1948     |
| `1948-07-12` | 12 July 1948              |

`end` is inclusive and optional. Leave it out for single-day events.

## Event

```json
{
  "id": "lydda-ramle-1948",
  "title": "Capture of Lydda and Ramle",
  "altNames": [{ "name": "Operation Dani (part of)", "usage": "Israeli operation name" }],
  "type": "military-operation",
  "start": "1948-07-10",
  "end": "1948-07-14",
  "importance": 1,
  "place": { "name": "Lydda (Lod)", "lat": 31.951, "lon": 34.888, "precision": "exact" },
  "summary": "Two to four plain sentences a beginner can follow.",
  "parties": ["Israel Defense Forces", "Arab Legion", "local militia"],
  "glance": {
    "by": { "text": "Israel Defense Forces", "sources": ["s1"] },
    "killed": [
      { "who": "Residents", "kind": "unclear", "n": "<range the accounts span>", "sources": ["s1", "s2"], "dispute": "number killed" }
    ]
  },
  "disputes": [
    {
      "about": "number killed",
      "accounts": [
        { "claim": "<figure given by source s1>", "sources": ["s1"] },
        { "claim": "<different figure given by source s2>", "sources": ["s2"] }
      ]
    }
  ],
  "sources": [
    {
      "id": "s1",
      "title": "Lydda and Ramle (article)",
      "author": "",
      "publisher": "Wikipedia",
      "url": "https://en.wikipedia.org/wiki/...",
      "kind": "reference",
      "accessed": "2026-11-15",
      "supports": "dates, sequence of events, the s1 figure",
      "via": "the book or article this page relies on, if any"
    }
  ],
  "status": "draft"
}
```

| Field        | Required | Notes |
|--------------|----------|-------|
| `id`         | yes | kebab-case, unique within the topic |
| `title`      | yes | neutral wording |
| `altNames`   | no  | names used by different sides or languages |
| `type`       | yes | `battle`, `military-operation`, `siege`, `massacre`, `war-crime`, `expulsion`, `displacement`, `attack` (bombings, ambushes), `political`, `diplomatic`, `ceasefire`, `other` (topics like biographies may add their own: `birth`, `death`, `residence`, `journey`, `work`…). The type picks the icon; see [Icons and colours](#icons-and-colours) |
| `start`      | yes | see Dates |
| `end`        | no  | inclusive |
| `importance` | yes | `1` = a beginner must know it, `2` = important, `3` = detail |
| `place`      | yes | `precision` is `exact`, `approximate` or `region` (shown as a soft area, not a pin); add `note` if the place was renamed or destroyed |
| `summary`    | yes | short and plain; no claims that are not backed by `sources` |
| `parties`    | no  | who was involved |
| `glance`     | no  | the short "at a glance" facts shown above the details; see [At a glance](#at-a-glance). Expected for fighting, attacks, massacres and expulsions |
| `disputes`   | no  | where sources disagree, each claim attributed to its sources |
| `sources`    | yes | at least one; see [sourcing.md](sourcing.md) |
| `status`     | yes | `draft` until a human has reviewed it, then `reviewed` |

## At a glance

Most readers want the results first: what kind of event it was, who did it, who won, how
many died. `glance` holds those facts in a fixed shape, and the viewer shows them in a box
above the summary. Every part is optional, and every part needs `sources` (ids from the
event's `sources`).

```json
"glance": {
  "by":        { "text": "Egyptian Army", "sources": ["s1"] },
  "against":   { "text": "Kibbutz members with Palmach fighters", "sources": ["s1"] },
  "winner":    [
    { "text": "Egyptian Army", "level": "tactical", "sources": ["s1"] },
    { "text": "Israeli forces", "level": "strategic", "note": "the five-day stand delayed the Egyptian advance north", "sources": ["s1", "s2"] }
  ],
  "result":    { "text": "The defenders withdrew after five days and the Egyptians took the empty kibbutz", "sources": ["s1", "s2"] },
  "killed":    [
    { "who": "Egyptian soldiers", "kind": "fighters", "n": "<figure from the sources>", "sources": ["s2"], "dispute": "Size of the forces and Egyptian losses" }
  ],
  "displaced": { "text": "<how many left or were forced out>", "sources": ["s1"] }
}
```

| Part        | Shown as | Notes |
|-------------|----------|-------|
| `by`        | Attacker / Carried out by / Agreed by / By | who did it. The label depends on the type |
| `against`   | Defender / Against / Victims / Targeted / Target | who it was aimed at |
| `winner`    | Winner | battles, sieges and operations only. One row per claim. `text` is a side, or `No clear winner`. `level` (optional): `tactical` = won the fight at that place, `strategic` = achieved the wider aim. If perspectives differ, give each its own row and say whose view it is in `note` |
| `result`    | Result | what changed, in one short sentence |
| `killed`    | Killed | one row per group. `kind` is `civilians`, `fighters` or `unclear` (the sources don't separate them). `n` is text: `"72"`, `"about 100–120"`, `"dozens"` |
| `displaced` | Displaced | how many people left or were forced out |

- Keep each `text` under about 110 characters. The summary and disputes carry the nuance.
  Put asides in `note` (shown smaller, underneath), not in brackets inside `text`.
- Only figures the sources give. If none do, leave the `killed` row out; if a source says a
  side's losses are unknown, the row can say so (`"n": "not known"`), so that one side's dead
  aren't shown alone just because the other side's weren't counted.
- When the sources disagree, set `dispute` to the `about` of one of the event's disputes. The
  viewer marks the fact as disputed and links to it. Write the text so it shows the
  disagreement, never just one side's figure: give the range, or the usual estimate and the
  main alternative ("about 100–120 by most estimates; 254 reported at the time").
- Use the same names for the sides as `parties`, with no loaded adjectives.

## Icons and colours

The viewer gives each kind of event an icon and a colour, so readers can tell a battle from a
truce at a glance and filter by kind:

| Icon | Types |
|------|-------|
| crossed swords | `battle`, `siege` |
| arrow | `military-operation` |
| skull and crossbones (red) | `massacre`, `war-crime`, `expulsion`, `displacement` |
| burst | `attack` |
| handshake | `ceasefire` |
| columned building | `political`, `diplomatic`, `other` |

- Icons and colours show **what kind of event it was, never which side did it**. Massacres,
  war crimes and expulsions get the same red skull and crossbones, whoever carried them out.
- The viewer never totals, counts or ranks massacres by side.
- Event colours avoid the colours a topic's map layers use for sides (in the 1948 topic: teal
  for Israeli-held areas and orange for Arab-held ones), so an icon is never read as a side.

## Source `kind`

- `primary`: documents from the time (resolutions, treaties, declarations, letters, diaries)
- `scholarly`: academic books and articles
- `reference`: encyclopedias (Britannica, Wikipedia)
- `organization`: institutions, NGOs, governments, museums (note whose voice it is)
- `journalism`: news reporting

`via` names the work a source itself relies on. Use it when you read a web page that
cites a book you did not open yourself.

## Topic

```json
{
  "id": "1948-war",
  "title": "The 1948 War",
  "names": [{ "name": "1948 Arab–Israeli War", "usage": "common English name" }],
  "summary": "A paragraph orienting a beginner.",
  "start": "1947-11-29",
  "end": "1949-07-20",
  "view": { "center": [35.0, 31.6], "zoom": 7.3 },
  "phases": [
    { "title": "…", "start": "…", "end": "…", "sources": [ … ] }
  ]
}
```

Phases appear as coloured bands on the time slider, so a beginner can see the shape of
the whole story before reading any single event.

## Map layers (borders, lines, areas)

Optional, per topic: some topics have good border data, many don't. Each layer is a GeoJSON
file in the topic folder, listed in `topic.json` under `layers`:

```json
{
  "id": "armistice-1949",
  "title": "1949 armistice lines",
  "file": "borders/armistice-lines-1949.geojson",
  "style": "armistice",
  "start": "1949-02-24",
  "end": "1949-07-20",
  "on": true,
  "note": "What the line is, how it was made, and its limits.",
  "labels": [{ "text": "Held by Egypt (Gaza Strip)", "lat": 31.42, "lon": 34.4, "start": "1949-02-24" }],
  "sources": [ … ],
  "status": "draft"
}
```

- The layer is drawn only while the slider is between `start` and `end`. Readers can switch it off.
- `style`: `reference` (dashed grey frame), `armistice` (solid green), `zone` (dashed green),
  `plan` (dotted, for proposals that were never in force, like a partition plan), `front` (solid
  dark line, for front lines that move). Labels take the style's colour. A label can have its own
  `start` and `end` inside the layer's range.
- A feature can also have its own `start` and `end` (in its `properties`), so one file can hold
  several stages of the same map, e.g. who held what at each point in a war. Features without
  dates are shown for the layer's whole range.
- Lines (`LineString`, `MultiLineString`) are drawn in the layer's style. Areas (`Polygon`,
  `MultiPolygon`) are shaded with the feature's own `fill` colour and `fill-opacity` (default
  0.2), the same property names GitHub's map preview uses. Areas sit under the water, so the
  modern coastline trims them; it is fine for an area to run a little out to sea.
- `legend` (optional) explains the shading in the layer list:
  `[{ "text": "Arab state", "color": "#d9822b" }]`, one entry per fill colour.
- Geometry needs sources like everything else. Say in `note` who traced it, from what, and how
  far it has been checked.
