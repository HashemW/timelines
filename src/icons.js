/* Event icons: one glyph and one colour per kind of event, shared by the map, the lists,
 * the filters and the event card. Glyphs are drawn here (no icon font), on a 24×24 grid,
 * in white on a coloured disc.
 *
 * Icons and colours say what kind of event it was, never which side did it. Massacres,
 * war crimes and expulsions all get the same red skull and crossbones, whoever carried
 * them out. Colours also avoid teal and orange, which the map layers use for sides. */

// "{c}" marks shapes painted in the disc colour, i.e. holes in the white glyph.
const SWORD = `<path d="M12 .4 13.15 2.8V15h-2.3V2.8z"/><rect x="8.6" y="15" width="6.8" height="1.9" rx=".95"/>` +
  `<rect x="11.05" y="16.9" width="1.9" height="2.9"/><circle cx="12" cy="20.9" r="1.5"/>`;

function burst() {
  const pts = [];
  const n = 10;
  for (let i = 0; i < n * 2; i++) {
    const a = (Math.PI * i) / n - Math.PI / 2;
    const r = i % 2 ? 4.9 : i % 4 ? 8.4 : 11;
    pts.push(`${(12 + r * Math.cos(a)).toFixed(2)},${(12.4 + r * Math.sin(a)).toFixed(2)}`);
  }
  return `<polygon points="${pts.join(" ")}"/>`;
}

// Crossbones: two bones crossing under the skull, each with a pair of knobs at both ends.
function bones() {
  const ends = [[[5.4, 16.2], [18.6, 21.8]], [[18.6, 16.2], [5.4, 21.8]]];
  let out = `<path d="${ends.map(([a, b]) => `M${a}L${b}`).join("")}" stroke="#fff" stroke-width="2.2" stroke-linecap="round" fill="none"/>`;
  for (const [a, b] of ends) {
    const dx = b[0] - a[0], dy = b[1] - a[1], len = Math.hypot(dx, dy);
    const px = (-dy / len) * 1.05, py = (dx / len) * 1.05;
    for (const [x, y] of [a, b]) {
      out += `<circle cx="${(x + px).toFixed(2)}" cy="${(y + py).toFixed(2)}" r="1.3"/><circle cx="${(x - px).toFixed(2)}" cy="${(y - py).toFixed(2)}" r="1.3"/>`;
    }
  }
  return out;
}

const GLYPHS = {
  swords: `<g transform="translate(0 1.4) rotate(45 12 8.6)">${SWORD}</g><g transform="translate(0 1.4) rotate(-45 12 8.6)">${SWORD}</g>`,
  arrow: `<path d="M2.4 9.4h11.2V4.6l8 7.4-8 7.4v-4.8H2.4z"/>`,
  skull: `<g transform="translate(0 -.9)">${bones()}` +
    `<ellipse cx="12" cy="8.1" rx="6.3" ry="5.9"/><rect x="8.6" y="10.6" width="6.8" height="4.6" rx="1.6"/>` +
    `<ellipse cx="9.55" cy="8.4" rx="1.8" ry="1.95" fill="{c}"/><ellipse cx="14.45" cy="8.4" rx="1.8" ry="1.95" fill="{c}"/>` +
    `<path d="M12 10.5 10.95 12.3h2.1z" fill="{c}"/>` +
    `<rect x="10.65" y="13.5" width=".75" height="1.7" fill="{c}"/><rect x="12.6" y="13.5" width=".75" height="1.7" fill="{c}"/></g>`,
  burst: burst(),
  handshake:
    // two cuffs, and the clasped hands between them: a palm on top, fingers wrapped below
    `<rect x=".6" y="6.6" width="3.6" height="9" rx=".8" transform="rotate(-12 2.4 11.1)"/>` +
    `<rect x="19.8" y="6.6" width="3.6" height="9" rx=".8" transform="rotate(12 21.6 11.1)"/>` +
    `<path d="M4.6 8.2c2.2-.9 4.1-1.6 6-1.7l3.3.2c1.1.1 1.9.6 2.8 1.3l2.7 2.2-.3 3.9-2 2.4c-.5.6-1.4.7-2 .2l-.4.4c-.6.6-1.5.6-2.1.1l-.4.3c-.6.5-1.5.4-2-.2-.6.4-1.4.3-1.9-.3L4.8 13.6z"/>` +
    `<path d="M9.4 9.6c1-.5 2.1-.7 3.1-.4l4.7 4.1M11.6 15.4l-2.2-2M13.6 15.1l-2.1-2M15.5 14.4l-2-1.9" stroke="{c}" stroke-width=".9" stroke-linecap="round" fill="none"/>`,
  columns: `<path d="M12 2.4 2.6 7.9h18.8z"/><rect x="3" y="8.6" width="18" height="1.7"/>` +
    [4.6, 8.8, 13.2, 17.4].map((x) => `<rect x="${x}" y="11" width="2" height="7.2"/>`).join("") +
    `<rect x="3" y="18.8" width="18" height="1.6"/><rect x="2" y="21" width="20" height="1.6"/>`,
  person: `<circle cx="12" cy="7.2" r="3.9"/><path d="M4.4 21.2c.4-4.6 3.6-7.6 7.6-7.6s7.2 3 7.6 7.6z"/>`,
};

/* Kinds of event, in the order the filters list them. `types` are the data's event types. */
export const GROUPS = [
  { key: "battle", label: "Battles & sieges", color: "#3d4452", glyph: "swords", types: ["battle", "siege"] },
  { key: "operation", label: "Military operations", color: "#5e6f28", glyph: "arrow", types: ["military-operation"] },
  { key: "massacre", label: "Massacres, war crimes & expulsions", color: "#c62828", glyph: "skull", types: ["massacre", "war-crime", "expulsion", "displacement"] },
  { key: "attack", label: "Attacks & bombings", short: "Attacks", color: "#a2307d", glyph: "burst", types: ["attack"] },
  { key: "ceasefire", label: "Ceasefires & armistices", short: "Ceasefires", color: "#2f6db0", glyph: "handshake", types: ["ceasefire"] },
  { key: "political", label: "Political & diplomatic", short: "Politics", color: "#6447a3", glyph: "columns", types: ["political", "diplomatic", "other"] },
  { key: "life", label: "Life events", color: "#7a5c2e", glyph: "person", types: ["birth", "death", "residence", "journey", "work"] },
];
const GROUP_OF_TYPE = new Map(GROUPS.flatMap((g) => g.types.map((t) => [t, g])));
export const groupOf = (type) => GROUP_OF_TYPE.get(type) || GROUPS.find((g) => g.key === "political");

export const TYPE_LABELS = {
  battle: "Battle", siege: "Siege", "military-operation": "Military operation",
  massacre: "Massacre", "war-crime": "War crime", expulsion: "Expulsion", displacement: "Displacement",
  attack: "Attack", ceasefire: "Ceasefire", political: "Political", diplomatic: "Diplomatic", other: "Event",
  birth: "Birth", death: "Death", residence: "Residence", journey: "Journey", work: "Work",
};
export const typeLabel = (type) => TYPE_LABELS[type] || type.replace(/-/g, " ");

function badgeSvg(group, size, { ring = false, shadow = false } = {}) {
  const glyph = GLYPHS[group.glyph].replaceAll("{c}", group.color);
  // The disc fills most of a 32-unit box; the 24-unit glyph is scaled down into it.
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 32 32" aria-hidden="true">` +
    (shadow ? `<circle cx="16" cy="17" r="14" fill="rgba(40,30,15,.28)"/>` : "") +
    `<circle cx="16" cy="16" r="${ring ? 13.6 : 16}" fill="${group.color}"${ring ? ` stroke="#fff" stroke-width="1.8"` : ""}/>` +
    `<g fill="#fff" transform="translate(16 16) scale(${ring ? 0.7 : 0.8}) translate(-12 -12)">${glyph}</g></svg>`;
}

/** Inline badge for HTML (lists, filters, the event card). */
export const iconHTML = (group, size = 18) => badgeSvg(group, size).replace("<svg ", `<svg class="ev-icon" `);

/** Adds one map image per group ("ev-<key>"), drawn at the screen's pixel density. */
export function addMapIcons(map) {
  const pr = Math.min(3, Math.max(2, Math.ceil(window.devicePixelRatio || 1)));
  const px = 32 * pr;
  return Promise.all(GROUPS.map((g) => new Promise((resolve, reject) => {
    const img = new Image(px, px);
    img.onload = () => {
      if (!map.hasImage(`ev-${g.key}`)) map.addImage(`ev-${g.key}`, img, { pixelRatio: pr });
      resolve();
    };
    img.onerror = reject;
    img.src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(badgeSvg(g, px, { ring: true, shadow: true }))}`;
  })));
}
