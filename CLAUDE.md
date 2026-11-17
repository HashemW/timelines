# Timelines: notes for Claude

A beginner-facing history site: a map plus a time slider. The owner sets direction. Claude does
most of the research, coding and repo upkeep.

## Ground rules
- **Data rules live in `docs/data-format.md` and `docs/sourcing.md`. Follow them exactly.**
  The most important one: cite only pages you actually opened; a book you didn't read goes in `via`.
- Everything Claude researches is `"status": "draft"`. Only the owner marks things `reviewed`.
- Contested facts go in `disputes`, with each claim attributed to its sources. Never quietly pick one.
- Topics vary: wars, biographies/journeys, etc. Borders are optional per topic; never block on them.
- Run `node scripts/validate.mjs` before every commit. It must report 0 errors.
- Event icons and colours show the kind of event, never the side. Massacres, war crimes and expulsions
  share one red skull and crossbones whoever did them; never count or rank them by side (owner's rule).

## Repo
- GitHub: `HashemW/timelines` (`main`, public). Live on GitHub Pages at https://hashemw.github.io/timelines/ (served
  from `main`). Claude owns commits/pushes. Keep commits small and descriptive.
- Remote uses HTTPS (gh is the credential helper). The SSH keys on this machine are rejected by GitHub.
- The older `HashemW/TimeLine` repo is an abandoned earlier attempt. Leave it alone.

## Working locally
- `python -m http.server 8000`, then http://localhost:8000 (`?topic=<id>` picks a topic, `#d=YYYY-MM-DD&e=<event-id>&only=<kinds>` deep-links).
- No build step: `index.html` + `src/app.js` + `src/style.css`; MapLibre GL 4.7.1 from unpkg.
- Base map = OpenFreeMap vector tiles (water/rivers only) + AWS Terrain Tiles hillshade. No modern
  borders/labels on purpose; period labels come from each topic's `places.json`.

## Research workflow
- Wikipedia coordinates: `curl -s -A "timelines-research/0.1" "https://en.wikipedia.org/w/api.php?action=query&prop=coordinates&colimit=max&coprimary=primary&redirects=1&format=json&titles=A|B"`
- Some sites block WebFetch (Britannica, UNRWA, palquest.org, palestine-studies.org, gov.il). Britannica serves curl with an
  honest user agent (`-A "timelines-research/0.1"`). Never disguise requests as a browser or get around a block; use another source.
- paljourneys.org (Institute for Palestine Studies) now redirects to palquest.org, which is behind a Cloudflare challenge.
  For Palestinian perspectives, Zochrot and the UN study "The Origins and Evolution of the Palestine Problem" are readable.
- When running parallel research agents, don't let them use the Chrome tools at the same time.

## Topic notes
- `1948-war`: politically sensitive. Use neutral titles, give Israeli and Palestinian names
  (`altNames`), mix sources from different perspectives, and put casualty figures and
  flight-vs-expulsion questions in `disputes`.
