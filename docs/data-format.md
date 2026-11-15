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
| `type`       | yes | `battle`, `military-operation`, `siege`, `massacre`, `displacement`, `political`, `diplomatic`, `ceasefire`, `other` (topics like biographies may add their own: `birth`, `death`, `residence`, `journey`, `work`…) |
| `start`      | yes | see Dates |
| `end`        | no  | inclusive |
| `importance` | yes | `1` = a beginner must know it, `2` = important, `3` = detail |
| `place`      | yes | `precision` is `exact`, `approximate` or `region`; add `note` if the place was renamed or destroyed |
| `summary`    | yes | short and plain; no claims that are not backed by `sources` |
| `parties`    | no  | who was involved |
| `disputes`   | no  | where sources disagree, each claim attributed to its sources |
| `sources`    | yes | at least one; see [sourcing.md](sourcing.md) |
| `status`     | yes | `draft` until a human has reviewed it, then `reviewed` |

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
