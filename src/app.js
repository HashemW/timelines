/* Timelines viewer: plain JavaScript, no build step.
 * Loads one topic from data/topics/<id>/ and lets the reader scrub through time. */

const DAY_MS = 86400000;
const LINGER_DAYS = 10;   // an event stays highlighted this many days after it ends
const THUMB_PX = 16;      // keep in sync with --thumb in style.css
const PLAY_MS = 110;

const MONTHS = ["January", "February", "March", "April", "May", "June", "July",
  "August", "September", "October", "November", "December"];
const MON = MONTHS.map((m) => m.slice(0, 3));

const CATEGORY_OF = {
  battle: "military", "military-operation": "military", siege: "military",
  massacre: "civilian", attack: "civilian", displacement: "civilian",
  political: "political", diplomatic: "political", ceasefire: "political", other: "political",
  birth: "life", death: "life", residence: "life", journey: "life", work: "life",
};
const CATEGORIES = {
  military:  { label: "Military", color: "#b03a2e" },
  civilian:  { label: "Massacres, attacks & displacement", color: "#6a3d9a" },
  political: { label: "Political & diplomatic", color: "#2a6f97" },
  life:      { label: "Life events", color: "#3c7a4a" },
};
const PHASE_COLORS = ["#eadcc2", "#dfe7d5", "#ecd5cf", "#d8e2eb", "#efe3c8", "#e1d9ea", "#d6e6e1"];
// Border / area layers (topic.json "layers"): a style per kind of line.
const LAYER_STYLES = {
  reference: { "line-color": "#6f665a", "line-width": 1.3, "line-opacity": 0.7, "line-dasharray": [3, 2] },
  armistice: { "line-color": "#2e7d32", "line-width": 2.4, "line-opacity": 0.9 },
  zone:      { "line-color": "#2e7d32", "line-width": 1.4, "line-opacity": 0.9, "line-dasharray": [2, 1.5] },
  plan:      { "line-color": "#a0522d", "line-width": 1.8, "line-opacity": 0.85, "line-dasharray": [1, 1.5] },
};

/* ---------- dates ----------
 * Data uses partial ISO strings ("1948", "1948-07", "1948-07-12").
 * Internally a date is a whole number of days since 1970-01-01 (UTC).
 * TODO: BCE years will need their own parser when an ancient topic arrives. */
function toDay(iso, edge = "start") {
  const [y, m, d] = iso.split("-").map(Number);
  let ms;
  if (d) ms = Date.UTC(y, m - 1, d);
  else if (m) ms = edge === "start" ? Date.UTC(y, m - 1, 1) : Date.UTC(y, m, 0);
  else ms = edge === "start" ? Date.UTC(y, 0, 1) : Date.UTC(y, 11, 31);
  return Math.round(ms / DAY_MS);
}
function parts(day) {
  const dt = new Date(day * DAY_MS);
  return { y: dt.getUTCFullYear(), m: dt.getUTCMonth() + 1, d: dt.getUTCDate() };
}
const pad = (n) => String(n).padStart(2, "0");
function dayToIso(day) { const { y, m, d } = parts(day); return `${y}-${pad(m)}-${pad(d)}`; }
function fmtDay(day) { const { y, m, d } = parts(day); return `${d} ${MONTHS[m - 1]} ${y}`; }
function fmtPartial(iso) {
  const [y, m, d] = iso.split("-");
  if (d) return `${+d} ${MONTHS[m - 1]} ${y}`;
  if (m) return `${MONTHS[m - 1]} ${y}`;
  return y;
}
function fmtRange(start, end) {
  if (!end || end === start) return fmtPartial(start);
  const [y1, m1, d1] = start.split("-");
  const [y2, m2, d2] = end.split("-");
  if (d1 && d2 && y1 === y2) {
    if (m1 === m2) return `${+d1}–${+d2} ${MONTHS[m1 - 1]} ${y1}`;
    return `${+d1} ${MON[m1 - 1]} – ${+d2} ${MON[m2 - 1]} ${y1}`;
  }
  return `${fmtPartial(start)} – ${fmtPartial(end)}`;
}

/* ---------- helpers ---------- */
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const posCss = (frac) => `calc(${THUMB_PX / 2}px + (100% - ${THUMB_PX}px) * ${frac})`;
const widthCss = (frac) => `calc((100% - ${THUMB_PX}px) * ${frac})`;
const colorOf = (ev) => CATEGORIES[ev.category].color;
function isSafeUrl(u) { try { return ["http:", "https:"].includes(new URL(u).protocol); } catch { return false; } }

async function getJSON(path, optional = false) {
  const res = await fetch(path);
  if (!res.ok) {
    if (optional) return null;
    throw new Error(`Could not load ${path} (${res.status})`);
  }
  return res.json();
}

/* ---------- state ---------- */
const state = {
  topic: null, events: [], phases: [], places: null, layers: [],
  min: 0, max: 0, day: 0, selected: null, timer: null, speed: 3, earlierOpen: false,
};
let map;
let hoverPopup;

function statusOf(ev, day) {
  if (day < ev.s) return "future";
  if (day <= ev.e) return "now";
  if (day <= ev.e + LINGER_DAYS) return "recent";
  return "past";
}

/* ---------- map ---------- */
function baseStyle() {
  return {
    version: 8,
    glyphs: "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
    sources: {
      omt: { type: "vector", url: "https://tiles.openfreemap.org/planet" },
      dem: {
        type: "raster-dem",
        tiles: ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"],
        encoding: "terrarium", tileSize: 256, maxzoom: 12,
      },
    },
    // Deliberately no modern borders, roads, cities or labels: only land, relief and water.
    // Labels on the map come from the topic's own period data.
    layers: [
      { id: "land", type: "background", paint: { "background-color": "#efe8d8" } },
      {
        id: "relief", type: "hillshade", source: "dem",
        paint: {
          "hillshade-exaggeration": 0.5,
          "hillshade-shadow-color": "#6b5a40",
          "hillshade-highlight-color": "#fffaf0",
          "hillshade-accent-color": "#8a7556",
        },
      },
      { id: "water", type: "fill", source: "omt", "source-layer": "water", paint: { "fill-color": "#a8c3ce" } },
      {
        id: "rivers", type: "line", source: "omt", "source-layer": "waterway",
        filter: ["==", ["get", "class"], "river"],
        paint: { "line-color": "#8fb0be", "line-width": ["interpolate", ["linear"], ["zoom"], 6, 0.6, 11, 2] },
      },
      {
        id: "water-names", type: "symbol", source: "omt", "source-layer": "water_name",
        layout: {
          "text-field": ["coalesce", ["get", "name:en"], ["get", "name_en"], ["get", "name"]],
          "text-font": ["Noto Sans Italic"], "text-size": 12, "text-letter-spacing": 0.08,
        },
        paint: { "text-color": "#4d7080", "text-halo-color": "rgba(255,255,255,.45)", "text-halo-width": 1 },
      },
    ],
  };
}

function initMap() {
  const { center, zoom } = state.topic.view;
  map = new maplibregl.Map({
    container: "map", style: baseStyle(), center, zoom, minZoom: 3, maxZoom: 13,
    attributionControl: false, dragRotate: false, pitchWithRotate: false,
  });
  map.touchZoomRotate.disableRotation();
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-left");
  map.addControl(new maplibregl.AttributionControl({
    compact: true,
    // OpenFreeMap / OpenStreetMap credits come from the tile source itself.
    customAttribution: 'Relief: <a href="https://registry.opendata.aws/terrain-tiles/" target="_blank">Terrain Tiles (Mapzen/AWS)</a>',
  }), "bottom-left");
  applyPadding();
  window.addEventListener("resize", applyPadding);

  map.on("load", () => {
    addBorderLayers();
    addPlaceLayers();
    addEventLayers();
    render();
  });
}

function applyPadding() {
  if (!map) return;
  const panel = $("panel").getBoundingClientRect();
  const narrow = window.innerWidth <= 760;
  map.setPadding(narrow
    ? { top: 60, bottom: panel.height + 16, left: 0, right: 0 }
    : { top: 0, bottom: 0, left: 0, right: panel.width + 24 });
}

function addBorderLayers() {
  for (const l of state.layers) {
    map.addSource(`layer-${l.id}`, { type: "geojson", data: l.url });
    map.addLayer({
      id: `layer-${l.id}`, type: "line", source: `layer-${l.id}`,
      layout: { "line-join": "round", "line-cap": "round", visibility: "none" },
      paint: LAYER_STYLES[l.style] || LAYER_STYLES.reference,
    });
  }
  const labels = state.layers.flatMap((l) => (l.labels || []).map((lb) => ({
    type: "Feature",
    properties: { text: lb.text, layer: l.id, s: toDay(lb.start || l.start, "start"), e: toDay(lb.end || l.end, "end") },
    geometry: { type: "Point", coordinates: [lb.lon, lb.lat] },
  })));
  map.addSource("layer-labels", { type: "geojson", data: { type: "FeatureCollection", features: labels } });
  map.addLayer({
    id: "layer-labels", type: "symbol", source: "layer-labels", filter: ["==", ["get", "layer"], ""],
    layout: {
      "text-field": ["get", "text"], "text-font": ["Noto Sans Italic"], "text-size": 12, "text-max-width": 9,
      "text-allow-overlap": true,
    },
    paint: { "text-color": "#2e6b32", "text-halo-color": "rgba(251,248,241,.85)", "text-halo-width": 1.4 },
  });
}

function updateBorderLayers() {
  if (!map?.getLayer("layer-labels")) return;
  const day = state.day;
  for (const l of state.layers) {
    const visible = l.on && day >= l.s && day <= l.e;
    map.setLayoutProperty(`layer-${l.id}`, "visibility", visible ? "visible" : "none");
  }
  const on = state.layers.filter((l) => l.on).map((l) => l.id);
  map.setFilter("layer-labels", ["all",
    ["in", ["get", "layer"], ["literal", on]], ["<=", ["get", "s"], day], [">=", ["get", "e"], day]]);
}

function layersHTML() {
  if (!state.layers.length) return "";
  return `<div class="layers"><h2>Map layers</h2>${state.layers.map((l) => {
    const inRange = state.day >= l.s && state.day <= l.e;
    return `<label class="layer"><input type="checkbox" data-layer="${esc(l.id)}"${l.on ? " checked" : ""}>
      <span class="swatch ${esc(l.style)}"></span>
      <span><span class="item-title">${esc(l.title)}</span>
      <span class="item-meta">${esc(fmtRange(l.start, l.end))}${inRange ? "" : " · not on the map at this date"}</span></span></label>
      <details class="layer-about"${state.openLayerInfo === l.id ? " open" : ""} data-layer-info="${esc(l.id)}"><summary>About this layer</summary>
      <p>${esc(l.note || "")}</p><ol class="sources">${(l.sources || []).map((s) => sourceHTML(s, `layer-${l.id}`)).join("")}</ol>
      ${l.status !== "reviewed" ? `<p class="draft">Draft: not yet checked by a person.</p>` : ""}</details>`;
  }).join("")}</div>`;
}

function addPlaceLayers() {
  const p = state.places;
  if (!p) return;
  const fc = (rows) => ({
    type: "FeatureCollection",
    features: rows.map((r) => ({
      type: "Feature", properties: { name: r.name, rank: r.rank ?? 3 },
      geometry: { type: "Point", coordinates: [r.lon, r.lat] },
    })),
  });
  map.addSource("towns", { type: "geojson", data: fc(p.towns || []) });
  map.addSource("regions", { type: "geojson", data: fc(p.regions || []) });

  map.addLayer({
    id: "regions", type: "symbol", source: "regions",
    layout: { "text-field": ["get", "name"], "text-font": ["Noto Sans Regular"], "text-size": 12, "text-letter-spacing": 0.3 },
    paint: { "text-color": "rgba(92, 76, 54, .55)", "text-halo-color": "rgba(239,232,216,.6)", "text-halo-width": 1 },
  });
  [[1, 0], [2, 7], [3, 8]].forEach(([rank, minzoom]) => {
    map.addLayer({
      id: `town-dot-${rank}`, type: "circle", source: "towns", minzoom, filter: ["==", ["get", "rank"], rank],
      paint: { "circle-radius": rank === 1 ? 3 : 2.2, "circle-color": "#5c5346", "circle-stroke-color": "#fffaf0", "circle-stroke-width": 1 },
    });
    map.addLayer({
      id: `town-label-${rank}`, type: "symbol", source: "towns", minzoom, filter: ["==", ["get", "rank"], rank],
      layout: {
        "text-field": ["get", "name"], "text-font": ["Noto Sans Regular"],
        "text-size": rank === 1 ? 13 : rank === 2 ? 12 : 11,
        "text-anchor": "left", "text-offset": [0.6, 0], "text-optional": true,
      },
      paint: { "text-color": "#3d3428", "text-halo-color": "rgba(251,248,241,.9)", "text-halo-width": 1.4 },
    });
  });
}

function addEventLayers() {
  map.addSource("events", { type: "geojson", data: eventFeatures() });
  const color = ["match", ["get", "category"],
    ...Object.entries(CATEGORIES).flatMap(([k, v]) => [k, v.color]), "#555"];
  const size = ["match", ["get", "importance"], 1, 8, 2, 6.5, 5];
  const active = ["in", ["get", "status"], ["literal", ["now", "recent"]]];

  // Region-wide events (precision "region") get a soft area instead of looking like a pinpoint.
  map.addLayer({
    id: "ev-zone", type: "circle", source: "events", filter: ["all", active, ["==", ["get", "region"], true]],
    paint: {
      "circle-radius": 48, "circle-color": color, "circle-opacity": 0.07,
      "circle-stroke-color": color, "circle-stroke-width": 1.2, "circle-stroke-opacity": 0.45,
    },
  });
  map.addLayer({
    id: "ev-past", type: "circle", source: "events", filter: ["==", ["get", "status"], "past"],
    paint: { "circle-radius": 3.5, "circle-color": color, "circle-opacity": 0.4, "circle-stroke-color": "#fff", "circle-stroke-width": 0.6, "circle-stroke-opacity": 0.6 },
  });
  map.addLayer({
    id: "ev-halo", type: "circle", source: "events", filter: active,
    paint: { "circle-radius": ["+", size, 8], "circle-color": color, "circle-opacity": ["case", ["==", ["get", "status"], "now"], 0.2, 0.08], "circle-blur": 0.4 },
  });
  map.addLayer({
    id: "ev-active", type: "circle", source: "events", filter: active,
    paint: {
      "circle-radius": size, "circle-color": color,
      "circle-opacity": ["case", ["==", ["get", "status"], "now"], 1, 0.6],
      "circle-stroke-color": "#fff", "circle-stroke-width": 2,
    },
  });
  map.addLayer({
    id: "ev-selected", type: "circle", source: "events", filter: ["==", ["get", "id"], ""],
    paint: { "circle-radius": 14, "circle-color": "rgba(0,0,0,0)", "circle-stroke-color": "#2b2620", "circle-stroke-width": 2 },
  });
  map.addLayer({
    id: "ev-label", type: "symbol", source: "events", filter: active,
    layout: {
      "text-field": ["get", "title"], "text-font": ["Noto Sans Bold"], "text-size": 12,
      "text-anchor": "top", "text-offset": [0, 1.1], "text-max-width": 11, "text-optional": true,
      "symbol-sort-key": ["get", "importance"],
    },
    paint: { "text-color": "#2b2620", "text-halo-color": "rgba(251,248,241,.95)", "text-halo-width": 1.6 },
  });

  hoverPopup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 12 });
  for (const layer of ["ev-active", "ev-past"]) {
    map.on("click", layer, (e) => selectEvent(e.features[0].properties.id, { moveMap: false }));
    map.on("mouseenter", layer, (e) => {
      map.getCanvas().style.cursor = "pointer";
      const ev = byId(e.features[0].properties.id);
      hoverPopup.setLngLat([ev.place.lon, ev.place.lat])
        .setHTML(`<strong>${esc(ev.title)}</strong><span>${esc(fmtRange(ev.start, ev.end))}</span>`)
        .addTo(map);
    });
    map.on("mouseleave", layer, () => { map.getCanvas().style.cursor = ""; hoverPopup.remove(); });
  }
}

function eventFeatures() {
  return {
    type: "FeatureCollection",
    features: state.events
      .map((ev) => ({ ev, status: statusOf(ev, state.day) }))
      .filter(({ status }) => status !== "future")
      .map(({ ev, status }) => ({
        type: "Feature",
        properties: {
          id: ev.id, title: ev.title, category: ev.category, importance: ev.importance, status,
          region: ev.place.precision === "region",
        },
        geometry: { type: "Point", coordinates: [ev.place.lon, ev.place.lat] },
      })),
  };
}

/* ---------- time bar ---------- */
function buildTimebar() {
  const slider = $("slider");
  slider.min = state.min;
  slider.max = state.max;
  const span = state.max - state.min || 1;
  const frac = (day) => (Math.min(Math.max(day, state.min), state.max) - state.min) / span;

  $("phases").innerHTML = state.phases.map((ph, i) =>
    `<div class="phase" title="${esc(ph.title)}: ${esc(fmtRange(ph.start, ph.end))}"
      style="left:${posCss(frac(ph.s))};width:${widthCss(frac(ph.e) - frac(ph.s))};background:${ph.color}">${esc(ph.title)}</div>`
  ).join("");

  $("ticks").innerHTML = state.events.map((ev) =>
    `<button class="tick" data-id="${esc(ev.id)}" title="${esc(ev.title)} (${esc(fmtRange(ev.start, ev.end))})"
      style="left:${posCss(frac(ev.s))};height:${[0, 18, 13, 9][ev.importance]}px;background:${colorOf(ev)}"></button>`
  ).join("");

  // Month labels on the axis, thinned out so there are at most ~10.
  const months = [];
  let { y, m } = parts(state.min);
  for (;;) {
    const d = toDay(`${y}-${pad(m)}-01`);
    if (d > state.max) break;
    if (d >= state.min) months.push({ d, y, m });
    m += 1; if (m > 12) { m = 1; y += 1; }
  }
  const every = Math.max(1, Math.ceil(months.length / 10));
  let lastYear = null;
  $("axis").innerHTML = months.filter((_, i) => i % every === 0).map((mo) => {
    const showYear = mo.y !== lastYear;
    lastYear = mo.y;
    return `<span style="left:${posCss(frac(mo.d))}">${MON[mo.m - 1]}${showYear ? ` ${mo.y}` : ""}</span>`;
  }).join("");

  slider.addEventListener("input", () => { stop(); setDay(+slider.value); });
  $("ticks").addEventListener("click", (e) => {
    const t = e.target.closest(".tick");
    if (t) { stop(); selectEvent(t.dataset.id, { setDay: true }); }
  });
  $("play").addEventListener("click", togglePlay);
  $("speed").addEventListener("change", (e) => { state.speed = +e.target.value; });
  $("prev").addEventListener("click", () => step(-1));
  $("next").addEventListener("click", () => step(1));
}

function setDay(day) {
  state.day = Math.min(Math.max(Math.round(day), state.min), state.max);
  render();
}

function step(dir) {
  stop();
  const target = dir > 0
    ? state.events.find((ev) => ev.s > state.day)
    : [...state.events].reverse().find((ev) => ev.s < state.day);
  if (target) selectEvent(target.id, { setDay: true });
}

function togglePlay() { state.timer ? stop() : play(); }
function play() {
  if (state.day >= state.max) state.day = state.min;
  state.selected = null;
  $("play").textContent = "❚❚";
  $("play").setAttribute("aria-label", "Pause");
  state.timer = setInterval(() => {
    setDay(state.day + state.speed);
    if (state.day >= state.max) stop();
  }, PLAY_MS);
}
function stop() {
  if (!state.timer) return;
  clearInterval(state.timer);
  state.timer = null;
  $("play").textContent = "▶";
  $("play").setAttribute("aria-label", "Play");
}

/* ---------- panel ---------- */
const byId = (id) => state.events.find((ev) => ev.id === id);

function selectEvent(id, { setDay: jump = false, moveMap = true } = {}) {
  const ev = byId(id);
  if (!ev) return;
  state.selected = id;
  if (jump) state.day = ev.s;
  render();
  if (moveMap && map) {
    const far = distanceKm(ev.place, { lon: state.topic.view.center[0], lat: state.topic.view.center[1] }) > 600;
    const pt = map.project([ev.place.lon, ev.place.lat]);
    const box = map.getContainer().getBoundingClientRect();
    const pad = map.getPadding();
    const visible = pt.x > pad.left + 30 && pt.x < box.width - pad.right - 30 && pt.y > pad.top + 30 && pt.y < box.height - pad.bottom - 30;
    if (far) map.flyTo({ center: [ev.place.lon, ev.place.lat], zoom: 4.5 });
    else if (!visible || map.getZoom() < 6) map.flyTo({ center: [ev.place.lon, ev.place.lat], zoom: Math.max(map.getZoom(), state.topic.view.zoom) });
  }
}

function closeDetail() {
  state.selected = null;
  render();
  if (map && distanceKm(lngLatObj(map.getCenter()), { lon: state.topic.view.center[0], lat: state.topic.view.center[1] }) > 600) {
    map.flyTo({ center: state.topic.view.center, zoom: state.topic.view.zoom });
  }
}

function itemHTML(ev, status) {
  return `<button class="item ${status}" data-id="${esc(ev.id)}">
    <span class="dot" style="background:${colorOf(ev)}"></span>
    <span><span class="item-title">${esc(ev.title)}</span>
    <span class="item-meta">${esc(fmtRange(ev.start, ev.end))} · ${esc(ev.place.name)}</span></span></button>`;
}

function renderList() {
  const day = state.day;
  const groups = { now: [], recent: [], past: [] };
  for (const ev of state.events) {
    const st = statusOf(ev, day);
    if (groups[st]) groups[st].push(ev);
  }
  let html = "";
  if (groups.now.length) html += `<h2>Happening now</h2>${groups.now.map((ev) => itemHTML(ev, "now")).join("")}`;
  if (groups.recent.length) html += `<h2>Just before</h2>${groups.recent.map((ev) => itemHTML(ev, "recent")).join("")}`;
  if (!groups.now.length && !groups.recent.length) {
    html += `<p class="empty">Nothing recorded around this date.</p>`;
  }
  const next = state.events.find((ev) => ev.s > day);
  if (next) html += `<h2>Next</h2><button class="jump" data-id="${esc(next.id)}">${esc(next.title)} · ${esc(fmtRange(next.start, next.end))}</button>`;
  if (groups.past.length) {
    html += `<details class="earlier"${state.earlierOpen ? " open" : ""}><summary>Earlier events (${groups.past.length})</summary>
      ${[...groups.past].reverse().map((ev) => itemHTML(ev, "past")).join("")}</details>`;
  }
  html += layersHTML();
  html += `<div class="legend">${Object.entries(CATEGORIES)
    .filter(([k]) => state.events.some((ev) => ev.category === k))
    .map(([, c]) => `<div><span class="dot" style="background:${c.color}"></span>${esc(c.label)}</div>`).join("")}
    <div>Bigger dots are more important. Faded dots happened earlier.</div></div>`;
  $("panel-body").innerHTML = html;
}

function sourceHTML(s, evId) {
  const title = isSafeUrl(s.url)
    ? `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a>`
    : esc(s.title);
  const by = [s.author, s.publisher].filter(Boolean).map(esc).join(", ");
  return `<li id="src-${esc(evId)}-${esc(s.id)}">${title}${by ? `. ${by}` : ""}<span class="badge">${esc(s.kind)}</span>
    ${s.supports ? `<div class="supports">Used for: ${esc(s.supports)}</div>` : ""}
    ${s.via ? `<div class="via">Relies on: ${esc(s.via)}</div>` : ""}</li>`;
}

function renderDetail(ev) {
  const num = new Map(ev.sources.map((s, i) => [s.id, i + 1]));
  const refs = (ids) => (ids || []).map((id) =>
    `<button class="ref" data-src="${esc(id)}">[${num.get(id) ?? "?"}]</button>`).join("");
  const cat = CATEGORIES[ev.category];
  const st = statusOf(ev, state.day);
  const p = ev.place;
  $("panel-body").innerHTML = `
    <button class="back">← All events around ${esc(fmtDay(state.day))}</button>
    <div class="kind" style="color:${cat.color}">${esc(cat.label)} · ${esc(ev.type.replace(/-/g, " "))}</div>
    <h2 class="ev-title">${esc(ev.title)}</h2>
    ${ev.altNames?.length ? `<p class="alt">Also called: ${ev.altNames.map((a) => `${esc(a.name)}${a.usage ? ` <span>(${esc(a.usage)})</span>` : ""}`).join("; ")}</p>` : ""}
    <p class="meta"><strong>${esc(fmtRange(ev.start, ev.end))}</strong>
      ${st === "now" ? "" : `<button class="goto" data-day="${ev.s}">go to date</button>`}<br>
      ${esc(p.name)}${p.precision !== "exact" ? ` (${esc(p.precision)} location)` : ""}${p.note ? `<br>${esc(p.note)}` : ""}</p>
    <p class="summary">${esc(ev.summary)}</p>
    ${ev.parties?.length ? `<p class="meta"><strong>Involved:</strong> ${ev.parties.map(esc).join(", ")}</p>` : ""}
    ${ev.disputes?.length ? `<h3>Where sources disagree</h3>${ev.disputes.map((d) => `
      <div class="dispute"><div class="about">${esc(d.about)}</div>
      <ul>${d.accounts.map((a) => `<li>${esc(a.claim)} ${refs(a.sources)}</li>`).join("")}</ul></div>`).join("")}` : ""}
    <h3>Sources</h3>
    <ol class="sources">${ev.sources.map((s) => sourceHTML(s, ev.id)).join("")}</ol>
    ${ev.status !== "reviewed" ? `<p class="draft">Draft: researched by Claude, not yet checked by a person.</p>` : ""}`;
  $("panel-body").scrollTop = 0;
}

$("panel-body").addEventListener("click", (e) => {
  const item = e.target.closest(".item, .jump");
  if (item) { stop(); selectEvent(item.dataset.id, { setDay: item.classList.contains("jump") }); return; }
  if (e.target.closest(".back")) { closeDetail(); return; }
  const go = e.target.closest(".goto");
  if (go) { stop(); setDay(+go.dataset.day); return; }
  const ref = e.target.closest(".ref");
  if (ref) {
    const li = document.getElementById(`src-${state.selected}-${ref.dataset.src}`);
    if (li) { li.scrollIntoView({ block: "center", behavior: "smooth" }); li.classList.add("flash"); setTimeout(() => li.classList.remove("flash"), 1200); }
  }
});
$("panel-body").addEventListener("toggle", (e) => {
  if (e.target.classList?.contains("earlier")) state.earlierOpen = e.target.open;
  if (e.target.dataset?.layerInfo) state.openLayerInfo = e.target.open ? e.target.dataset.layerInfo : null;
}, true);
$("panel-body").addEventListener("change", (e) => {
  const id = e.target.dataset?.layer;
  const layer = id && state.layers.find((l) => l.id === id);
  if (layer) { layer.on = e.target.checked; render(); }
});

/* ---------- render ---------- */
function render() {
  const day = state.day;
  $("slider").value = day;
  $("now-date").textContent = fmtDay(day);
  // Phases can share a boundary day (a truce starts the day the fighting phase ends): the newer one wins.
  const phase = state.phases.filter((ph) => day >= ph.s && day <= ph.e).at(-1);
  $("now-phase").innerHTML = phase ? `<span class="phase-dot" style="background:${phase.color}"></span>${esc(phase.title)}` : "&nbsp;";
  $("prev").disabled = !state.events.some((ev) => ev.s < day);
  $("next").disabled = !state.events.some((ev) => ev.s > day);

  if (map?.getSource("events")) {
    map.getSource("events").setData(eventFeatures());
    map.setFilter("ev-selected", ["==", ["get", "id"], state.selected ?? ""]);
  }
  updateBorderLayers();
  const sel = state.selected && byId(state.selected);
  if (sel) renderDetail(sel); else renderList();
  writeHash();
}

/* ---------- URL (#d=1948-07-12&e=event-id) so any moment can be linked ---------- */
let hashTimer;
function writeHash() {
  clearTimeout(hashTimer);
  hashTimer = setTimeout(() => {
    const p = new URLSearchParams();
    p.set("d", dayToIso(state.day));
    if (state.selected) p.set("e", state.selected);
    history.replaceState(null, "", `${location.pathname}${location.search}#${p}`);
  }, 150);
}
function readHash() {
  const p = new URLSearchParams(location.hash.slice(1));
  const d = p.get("d");
  if (d && /^\d{4}-\d{2}-\d{2}$/.test(d)) state.day = Math.min(Math.max(toDay(d), state.min), state.max);
  const e = p.get("e");
  if (e && byId(e)) state.selected = e;
}

// Someone edits or pastes a link while the page is open.
window.addEventListener("hashchange", () => {
  if (!state.topic) return;
  stop();
  state.selected = null;
  readHash();
  render();
});

/* ---------- keyboard ---------- */
document.addEventListener("keydown", (e) => {
  if (e.target.closest?.("input, select, textarea")) return;
  if (e.key === "ArrowRight") { e.preventDefault(); e.shiftKey ? step(1) : (stop(), setDay(state.day + 1)); }
  else if (e.key === "ArrowLeft") { e.preventDefault(); e.shiftKey ? step(-1) : (stop(), setDay(state.day - 1)); }
  else if (e.key === " " && !e.target.closest("button")) { e.preventDefault(); togglePlay(); }
  else if (e.key === "Escape" && state.selected) closeDetail();
});

/* ---------- geometry ---------- */
function lngLatObj(ll) { return { lon: ll.lng, lat: ll.lat }; }
function distanceKm(a, b) {
  const R = 6371, r = Math.PI / 180;
  const dLat = (b.lat - a.lat) * r, dLon = (b.lon - a.lon) * r;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

/* ---------- start ---------- */
function renderIntro() {
  const t = state.topic;
  document.title = `${t.title} · Timelines`;
  $("topic-title").textContent = t.title;
  $("topic-names").innerHTML = (t.names || []).map((n) => `<strong>${esc(n.name)}</strong> ${n.usage ? `(${esc(n.usage)})` : ""}`).join("<br>");
  $("topic-summary").textContent = t.summary || "";
  $("topic-sources").innerHTML = (t.sources || []).map((s) => sourceHTML(s, "topic")).join("");
}

async function main() {
  try {
    const params = new URLSearchParams(location.search);
    const topics = await getJSON("data/topics.json");
    const id = params.get("topic") || topics[0].id;
    if (!topics.some((t) => t.id === id)) throw new Error(`Unknown topic "${id}"`);
    const base = `data/topics/${id}/`;
    const [topic, events, places] = await Promise.all([
      getJSON(`${base}topic.json`), getJSON(`${base}events.json`), getJSON(`${base}places.json`, true),
    ]);
    state.topic = topic;
    state.places = places;
    state.min = toDay(topic.start, "start");
    state.max = toDay(topic.end, "end");
    state.events = events
      .map((ev) => ({
        ...ev,
        s: toDay(ev.start, "start"),
        e: toDay(ev.end || ev.start, "end"),
        category: CATEGORY_OF[ev.type] || "political",
      }))
      .sort((a, b) => a.s - b.s || a.importance - b.importance);
    state.layers = (topic.layers || []).map((l) => ({
      ...l, url: `${base}${l.file}`, on: l.on !== false,
      s: toDay(l.start, "start"), e: toDay(l.end, "end"),
    }));
    state.phases = (topic.phases || []).map((ph, i) => ({
      ...ph, s: toDay(ph.start, "start"), e: toDay(ph.end, "end"), color: PHASE_COLORS[i % PHASE_COLORS.length],
    }));
    state.day = state.min;
    readHash();

    renderIntro();
    buildTimebar();
    render();
    initMap();
  } catch (err) {
    console.error(err);
    const box = $("error");
    box.hidden = false;
    box.innerHTML = location.protocol === "file:"
      ? `This page needs to be served, not opened as a file.<br>In this folder run <code>python -m http.server 8000</code>, then open <code>http://localhost:8000</code>.`
      : `Something went wrong loading the data.<br><code>${esc(err.message)}</code>`;
  }
}

// Handy for debugging from the browser console.
window.timelines = { state, get map() { return map; } };

main();
