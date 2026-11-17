#!/usr/bin/env node
// Checks every topic's data against docs/data-format.md and docs/sourcing.md.
// Usage: node scripts/validate.mjs        (exit code 1 if there are errors)

import { readFileSync, existsSync } from "node:fs";

const root = new URL("../", import.meta.url);
const read = (p) => JSON.parse(readFileSync(new URL(p, root), "utf8"));
const exists = (p) => existsSync(new URL(p, root));

let errors = 0;
let warnings = 0;
const err = (where, msg) => { errors++; console.log(`ERROR  ${where}: ${msg}`); };
const warn = (where, msg) => { warnings++; console.log(`warn   ${where}: ${msg}`); };

const DATE = /^\d{4}(-(0[1-9]|1[0-2])(-(0[1-9]|[12]\d|3[01]))?)?$/;
const ID = /^[a-z0-9]+(-[a-z0-9]+)*$/;
const TYPES = new Set(["battle", "military-operation", "siege", "massacre", "war-crime", "expulsion", "displacement",
  "attack", "political", "diplomatic", "ceasefire", "other", "birth", "death", "residence", "journey", "work"]);
const KINDS = new Set(["primary", "scholarly", "reference", "organization", "journalism"]);
const PRECISION = new Set(["exact", "approximate", "region"]);
const COLOR = /^#[0-9a-f]{6}$/i;
// "At a glance" (docs/data-format.md#at-a-glance)
const GLANCE_PARTS = new Set(["by", "against", "winner", "result", "killed", "displaced"]);
const KILLED_KINDS = new Set(["civilians", "fighters", "unclear"]);
const WIN_LEVELS = new Set(["tactical", "strategic"]);
const EXPECTS_GLANCE = new Set(["battle", "siege", "military-operation", "massacre", "war-crime", "expulsion", "displacement", "attack"]);
const GLANCE_MAX = 140;

function dayOf(iso, edge) {
  const [y, m, d] = iso.split("-").map(Number);
  if (d) return Date.UTC(y, m - 1, d);
  if (m) return edge === "start" ? Date.UTC(y, m - 1, 1) : Date.UTC(y, m, 0);
  return edge === "start" ? Date.UTC(y, 0, 1) : Date.UTC(y, 11, 31);
}
function realDate(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  if (!d) return true;
  const dt = new Date(Date.UTC(y, m - 1, d));
  return dt.getUTCMonth() === m - 1 && dt.getUTCDate() === d;
}
function checkDate(where, label, iso, required) {
  if (iso === undefined) { if (required) err(where, `missing ${label}`); return false; }
  if (typeof iso !== "string" || !DATE.test(iso) || !realDate(iso)) { err(where, `${label} "${iso}" is not YYYY, YYYY-MM or YYYY-MM-DD`); return false; }
  return true;
}
function host(url) { try { return new URL(url).host.replace(/^www\./, ""); } catch { return null; } }

function checkSources(where, sources) {
  if (!Array.isArray(sources) || sources.length === 0) { err(where, "needs at least one source"); return new Set(); }
  const ids = new Set();
  for (const s of sources) {
    const w = `${where} source ${s.id ?? "?"}`;
    if (!s.id) err(w, "source missing id");
    else if (ids.has(s.id)) err(w, "duplicate source id");
    ids.add(s.id);
    if (!s.title) err(w, "missing title");
    if (!KINDS.has(s.kind)) err(w, `kind "${s.kind}" must be one of ${[...KINDS].join(", ")}`);
    if (!s.url && !s.author && !s.publisher) err(w, "needs a url, author or publisher so it can be found");
    if (s.url && !host(s.url)) err(w, `bad url "${s.url}"`);
    if (s.accessed && !DATE.test(s.accessed)) err(w, `bad accessed date "${s.accessed}"`);
    if (s.url && !s.accessed) warn(w, "web source without an accessed date");
  }
  return ids;
}
// One fact in an event's `glance`: short text, its sources, and optionally the dispute it belongs to.
function checkFact(w, label, f, ids, abouts, textKey = "text") {
  if (!f || typeof f !== "object" || Array.isArray(f)) { err(w, `glance ${label} must be an object`); return; }
  const text = f[textKey];
  if (typeof text !== "string" || !text.trim()) err(w, `glance ${label} needs "${textKey}"`);
  else if (text.length > GLANCE_MAX) warn(w, `glance ${label} is ${text.length} characters; keep it under ${GLANCE_MAX}`);
  if (f.note !== undefined && (typeof f.note !== "string" || f.note.length > GLANCE_MAX)) warn(w, `glance ${label} note should be short text`);
  if (!Array.isArray(f.sources) || !f.sources.length) err(w, `glance ${label} needs sources`);
  for (const id of f.sources || []) if (!ids.has(id)) err(w, `glance ${label} cites unknown source "${id}"`);
  if (f.dispute !== undefined && !abouts.has(f.dispute)) err(w, `glance ${label} links to unknown dispute "${f.dispute}"`);
}
function checkGlance(w, g, ids, abouts) {
  if (typeof g !== "object" || Array.isArray(g)) { err(w, "glance must be an object"); return; }
  for (const k of Object.keys(g)) if (!GLANCE_PARTS.has(k)) err(w, `glance has unknown part "${k}"`);
  for (const k of ["by", "against", "result", "displaced"]) if (g[k] !== undefined) checkFact(w, k, g[k], ids, abouts);
  for (const k of ["winner", "killed"]) {
    if (g[k] !== undefined && (!Array.isArray(g[k]) || !g[k].length)) err(w, `glance ${k} must be a list with at least one row`);
  }
  for (const [i, r] of (Array.isArray(g.winner) ? g.winner : []).entries()) {
    checkFact(w, `winner #${i + 1}`, r, ids, abouts);
    if (r.level !== undefined && !WIN_LEVELS.has(r.level)) err(w, `glance winner #${i + 1} level must be ${[...WIN_LEVELS].join(" or ")}`);
  }
  for (const [i, r] of (Array.isArray(g.killed) ? g.killed : []).entries()) {
    checkFact(w, `killed #${i + 1}`, r, ids, abouts, "n");
    if (typeof r.who !== "string" || !r.who.trim()) err(w, `glance killed #${i + 1} needs "who"`);
    if (!KILLED_KINDS.has(r.kind)) err(w, `glance killed #${i + 1} kind must be ${[...KILLED_KINDS].join(", ")}`);
  }
}

// Independent = different website/publisher.
const independentCount = (sources) =>
  new Set((sources || []).map((s) => host(s.url) || (s.publisher || s.author || s.title).toLowerCase())).size;

const topics = read("data/topics.json");
for (const t of topics) {
  const dir = `data/topics/${t.id}/`;
  if (!exists(`${dir}topic.json`)) { err(t.id, "missing topic.json"); continue; }
  const topic = read(`${dir}topic.json`);
  if (topic.id !== t.id) err(t.id, `topic.json id "${topic.id}" does not match folder`);
  const okRange = checkDate(t.id, "start", topic.start, true) & checkDate(t.id, "end", topic.end, true);
  const tStart = okRange ? dayOf(topic.start, "start") : -Infinity;
  const tEnd = okRange ? dayOf(topic.end, "end") : Infinity;
  if (!topic.view?.center || typeof topic.view.zoom !== "number") err(t.id, "topic needs view.center and view.zoom");
  if (topic.summary) checkSources(`${t.id} (topic summary)`, topic.sources);
  for (const ph of topic.phases || []) {
    const w = `${t.id} phase "${ph.title}"`;
    checkDate(w, "start", ph.start, true);
    checkDate(w, "end", ph.end, true);
    checkSources(w, ph.sources);
  }

  const STYLES = new Set(["reference", "armistice", "zone", "plan", "front"]);
  for (const l of topic.layers || []) {
    const w = `${t.id} layer "${l.id}"`;
    if (!l.id || !ID.test(l.id)) err(w, "layer needs a kebab-case id");
    if (!l.title) err(w, "missing title");
    if (!l.file || !exists(`${dir}${l.file}`)) err(w, `file "${l.file}" not found`);
    else {
      try {
        const g = read(`${dir}${l.file}`);
        if (g.type !== "FeatureCollection") err(w, "file must be a GeoJSON FeatureCollection");
        for (const f of g.features || []) {
          const p = f.properties || {}, name = `feature "${p.name ?? "?"}"`;
          if (/Polygon$/.test(f.geometry?.type || "") && !COLOR.test(p.fill || "")) err(w, `area ${name} needs a "fill" colour like "#d9822b"`);
          const okS = p.start === undefined || checkDate(w, `${name} start`, p.start, true);
          const okE = p.end === undefined || checkDate(w, `${name} end`, p.end, true);
          const s = p.start || l.start, e = p.end || l.end;
          if (okS && okE && typeof s === "string" && typeof e === "string" && dayOf(s, "start") > dayOf(e, "end")) err(w, `${name} ends before it starts`);
        }
      } catch { err(w, "file is not valid JSON"); }
    }
    if (!STYLES.has(l.style)) err(w, `style must be one of ${[...STYLES].join(", ")}`);
    checkDate(w, "start", l.start, true);
    checkDate(w, "end", l.end, true);
    if (!l.note) warn(w, "explain the layer and its limits in `note`");
    checkSources(w, l.sources);
    for (const lb of l.labels || []) {
      if (!lb.text || typeof lb.lat !== "number" || typeof lb.lon !== "number") err(w, "each label needs text, lat and lon");
      if (lb.start) checkDate(w, "label start", lb.start, true);
      if (lb.end) checkDate(w, "label end", lb.end, true);
    }
    for (const k of l.legend || []) {
      if (!k.text || !COLOR.test(k.color || "")) err(w, "each legend entry needs text and a colour like \"#d9822b\"");
    }
    if (!["draft", "reviewed"].includes(l.status)) err(w, `status must be "draft" or "reviewed"`);
  }

  const events = exists(`${dir}events.json`) ? read(`${dir}events.json`) : [];
  const seen = new Set();
  for (const ev of events) {
    const w = `${t.id}/${ev.id ?? "(no id)"}`;
    for (const f of ["id", "title", "type", "start", "importance", "place", "summary", "sources", "status"]) {
      if (ev[f] === undefined) err(w, `missing ${f}`);
    }
    if (ev.id !== undefined) {
      if (!ID.test(ev.id)) err(w, "id must be kebab-case");
      if (seen.has(ev.id)) err(w, "duplicate id");
      seen.add(ev.id);
    }
    if (ev.type && !TYPES.has(ev.type)) warn(w, `unusual type "${ev.type}"`);
    const okS = checkDate(w, "start", ev.start, true);
    const okE = checkDate(w, "end", ev.end, false);
    if (okS && okE && dayOf(ev.end, "end") < dayOf(ev.start, "start")) err(w, "end is before start");
    if (okS && (dayOf(ev.start, "start") > tEnd || dayOf(ev.end || ev.start, "end") < tStart)) warn(w, "falls outside the topic's date range");
    if (![1, 2, 3].includes(ev.importance)) err(w, "importance must be 1, 2 or 3");
    const p = ev.place;
    if (p) {
      if (!p.name) err(w, "place needs a name");
      if (typeof p.lat !== "number" || p.lat < -90 || p.lat > 90) err(w, "place.lat must be a number between -90 and 90");
      if (typeof p.lon !== "number" || p.lon < -180 || p.lon > 180) err(w, "place.lon must be a number between -180 and 180");
      if (!PRECISION.has(p.precision)) err(w, `place.precision must be ${[...PRECISION].join(", ")}`);
    }
    if (ev.summary && ev.summary.length > 900) warn(w, "summary is long for a beginner; aim for 2–4 sentences");
    const ids = checkSources(w, ev.sources);
    for (const d of ev.disputes || []) {
      if (!d.about || !Array.isArray(d.accounts) || d.accounts.length < 2) err(w, "each dispute needs `about` and at least two accounts");
      for (const a of d.accounts || []) {
        if (!a.claim) err(w, "dispute account missing claim");
        if (!a.sources?.length) err(w, `dispute claim "${a.claim}" has no sources`);
        for (const id of a.sources || []) if (!ids.has(id)) err(w, `dispute cites unknown source "${id}"`);
      }
    }
    if (ev.glance !== undefined) checkGlance(w, ev.glance, ids, new Set((ev.disputes || []).map((d) => d.about)));
    else if (EXPECTS_GLANCE.has(ev.type)) warn(w, "no `glance` (the short facts shown above the details)");
    if ((ev.importance === 1 || ev.disputes?.length) && independentCount(ev.sources) < 2) {
      warn(w, "key or contested event with fewer than two independent sources");
    }
    if (!["draft", "reviewed"].includes(ev.status)) err(w, `status must be "draft" or "reviewed"`);
  }
  const drafts = events.filter((e) => e.status === "draft").length;
  console.log(`${t.id}: ${events.length} events (${drafts} draft, ${events.length - drafts} reviewed), ${(topic.phases || []).length} phases`);
}

console.log(`\n${errors} error(s), ${warnings} warning(s)`);
process.exit(errors ? 1 : 0);
