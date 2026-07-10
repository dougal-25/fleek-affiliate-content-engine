/* Fleek Affiliate Dashboard — data fetch + rendering. DOM built with createElement/textContent. */
const { hBarChart, funnelChart, lineChart, fmt } = window.Charts;

const STAGES = ["Prospect", "Qualified", "Contacted", "Responded", "Call booked",
  "Contract", "Onboarded", "First post", "First sale", "Repeat posting"];
/* Modelled stage-to-stage rates — playbook assumptions, shown on-screen, never presented as data */
const MODEL_RATES = [1, 0.6, 1, 0.25, 0.5, 0.6, 0.9, 0.7, 0.5, 0.6];
const AVATAR_COLORS = ["#f86868", "#270626", "#a97c08", "#475467", "#d63c3c"];

/* Pro reseller vs hobbyist — derived from the engine's own scoring sub-scores, so the
   distinction is deterministic and explainable: heavy wholesale content, or strong reseller
   credibility plus wholesale sourcing keywords. */
const PRO_KEYWORDS = /grossiste|wholesale|en gros|fournisseur|balle|bulk|b2b|destockage/i;
function subScore(c, name) {
  const m = (c["Score Breakdown"] || "").match(new RegExp(name + String.raw`:\s*(\d+)\s*/`, "i"));
  return m ? +m[1] : 0;
}
function creatorType(c) {
  const pro = subScore(c, "wholesale content") >= 6 ||
    (subScore(c, "reseller credibility") >= 18 && PRO_KEYWORDS.test(c["Content Keywords"] || ""));
  return pro ? "Pro reseller" : "Hobbyist";
}

/* Platform marks (16px), monochrome — each rendered as a link to the creator's channel */
const PLATFORM_ICONS = {
  TikTok: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M16.6 5.82A4.28 4.28 0 0 1 15.54 3h-3.09v12.4a2.59 2.59 0 1 1-2.59-2.59c.27 0 .53.04.77.12V9.77a5.76 5.76 0 0 0-.77-.05 5.66 5.66 0 1 0 5.66 5.66V9.01a7.36 7.36 0 0 0 4.3 1.38V7.3a4.34 4.34 0 0 1-3.22-1.48z"/></svg>',
  YouTube: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M23 7.2s-.22-1.55-.9-2.23c-.85-.9-1.8-.9-2.24-.95C16.74 3.8 12 3.8 12 3.8h-.01s-4.73 0-7.86.22c-.44.05-1.39.05-2.24.95-.67.68-.89 2.23-.89 2.23S.78 9.02.78 10.84v1.7c0 1.83.22 3.65.22 3.65s.22 1.55.9 2.23c.84.9 1.96.87 2.46.96 1.79.17 7.64.22 7.64.22s4.74-.01 7.86-.23c.44-.05 1.4-.05 2.24-.95.68-.68.9-2.23.9-2.23s.22-1.82.22-3.65v-1.7C23.22 9.02 23 7.2 23 7.2zM9.68 14.62V8.27l6.08 3.19-6.08 3.16z"/></svg>',
  Instagram: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.16c3.2 0 3.58.01 4.85.07 3.25.15 4.77 1.69 4.92 4.92.06 1.27.07 1.65.07 4.85s-.01 3.58-.07 4.85c-.15 3.23-1.66 4.77-4.92 4.92-1.27.06-1.64.07-4.85.07s-3.58-.01-4.85-.07c-3.26-.15-4.77-1.7-4.92-4.92C2.17 15.58 2.16 15.2 2.16 12s.01-3.58.07-4.85C2.38 3.92 3.9 2.38 7.15 2.23 8.42 2.17 8.8 2.16 12 2.16zm0 3.68A6.16 6.16 0 1 0 18.16 12 6.16 6.16 0 0 0 12 5.84zm0 10.15A4 4 0 1 1 16 12a4 4 0 0 1-4 4zm6.4-11.85a1.44 1.44 0 1 0 1.44 1.44 1.44 1.44 0 0 0-1.44-1.44z"/></svg>',
};

const $ = s => document.querySelector(s);
const div = (cls, text) => {
  const n = document.createElement("div");
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
};
const span = (cls, text) => {
  const n = document.createElement("span");
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
};

/* Single-file build: build_html.py injects window.__DATA__ (creators/funnel/trends/avatars)
   and the page runs from disk with no server. Without it, we fetch from serve.py. */
async function getData(kind) {
  if (window.__DATA__) return window.__DATA__[kind];
  return (await fetch("/api/" + kind)).json();
}

let creators = [];
const chipFilters = { Segment: new Set(), Confidence: new Set() };
const platformFilter = new Set();
let typeFilter = "";
let query = "";
let sortKey = "score";

/* ---------- tabs ---------- */
document.querySelectorAll(".tab").forEach(t => t.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach(x => x.classList.toggle("active", x === t));
  document.querySelectorAll(".view").forEach(v =>
    v.classList.toggle("active", v.id === "view-" + t.dataset.view));
}));

/* ---------- creators ---------- */
async function loadCreators() {
  const data = await getData("creators");
  creators = data.records.map(r => ({ id: r.id, ...r.fields, _type: null }));
  creators.forEach(c => { c._type = creatorType(c); });
  const badge = $("#source-badge");
  if (window.__DATA__) {
    badge.textContent = "airtable data · " + (data.fetched || "").slice(0, 10);
    badge.className = "badge badge-live";
  } else {
    badge.textContent = data.source === "live" ? "● live · Airtable" : "snapshot · 09 Jul";
    badge.className = "badge " + (data.source === "live" ? "badge-live" : "badge-snapshot");
  }
  renderStats();
  renderToolbar();
  renderSections();
}

function renderStats() {
  const scores = creators.map(c => c.Score || 0);
  const cacs = creators.map(c => c["Predicted CAC"]).filter(Boolean).sort((a, b) => a - b);
  const medCac = cacs.length ? cacs[Math.floor(cacs.length / 2)] : 0;
  const reach = creators.reduce((s, c) => s + (c.Followers || 0), 0);
  const pro = creators.filter(c => c._type === "Pro reseller").length;
  const stats = [
    [creators.length, "scored FR creators"],
    [`${pro} / ${creators.length - pro}`, "pro resellers / hobbyists"],
    [fmt(reach), "combined reach"],
    [Math.round(scores.reduce((a, b) => a + b, 0) / (scores.length || 1)) + "/100", "avg fit score"],
    ["£" + medCac, "median predicted CAC"],
  ];
  $("#creator-stats").replaceChildren(...stats.map(([num, lbl]) => {
    const s = div("stat");
    const n = div("num"); n.append(Object.assign(document.createElement("em"), { textContent: num }));
    s.append(n, div("lbl", lbl));
    return s;
  }));
}

/* ---------- toolbar ---------- */
function renderToolbar() {
  // platform icon toggles
  const wrap = $("#platform-toggles");
  wrap.replaceChildren(...[...new Set(creators.map(c => c.Platform).filter(Boolean))].sort().map(p => {
    const b = document.createElement("button");
    b.className = "ptoggle";
    b.title = p;
    b.setAttribute("aria-label", "Filter: " + p);
    b.innerHTML = PLATFORM_ICONS[p] || "";
    b.addEventListener("click", () => {
      platformFilter.has(p) ? platformFilter.delete(p) : platformFilter.add(p);
      b.classList.toggle("on");
      renderSections();
    });
    return b;
  }));
  // segment + confidence chips
  const groups = $("#filter-chips");
  groups.replaceChildren();
  for (const key of Object.keys(chipFilters)) {
    const values = [...new Set(creators.map(c => c[key]).filter(Boolean))].sort();
    if (values.length < 2) continue;
    const g = div("chip-group");
    g.append(span("glbl", key === "Segment" ? "Niche" : key));
    for (const v of values) {
      const b = document.createElement("button");
      b.className = "chip"; b.textContent = v;
      b.addEventListener("click", () => {
        chipFilters[key].has(v) ? chipFilters[key].delete(v) : chipFilters[key].add(v);
        b.classList.toggle("on");
        renderSections();
      });
      g.append(b);
    }
    groups.append(g);
  }
}

document.querySelectorAll("#type-control .seg").forEach(b => b.addEventListener("click", () => {
  typeFilter = b.dataset.type;
  document.querySelectorAll("#type-control .seg").forEach(x => x.classList.toggle("on", x === b));
  renderSections();
}));
$("#search").addEventListener("input", e => { query = e.target.value.toLowerCase(); renderSections(); });
$("#sort").addEventListener("change", e => { sortKey = e.target.value; renderSections(); });
$("#clear-filters").addEventListener("click", () => {
  Object.values(chipFilters).forEach(s => s.clear());
  platformFilter.clear();
  typeFilter = ""; query = "";
  $("#search").value = "";
  document.querySelectorAll(".chip.on, .ptoggle.on").forEach(x => x.classList.remove("on"));
  document.querySelectorAll("#type-control .seg").forEach(x =>
    x.classList.toggle("on", x.dataset.type === ""));
  renderSections();
});

function anyFilterActive() {
  return typeFilter || query || platformFilter.size ||
    Object.values(chipFilters).some(s => s.size);
}

function visible(c) {
  if (typeFilter && c._type !== typeFilter) return false;
  if (platformFilter.size && !platformFilter.has(c.Platform)) return false;
  for (const [k, set] of Object.entries(chipFilters))
    if (set.size && !set.has(c[k])) return false;
  if (!query) return true;
  return ["Handle", "Content Keywords", "Audience", "Segment", "Strength"]
    .some(f => (c[f] || "").toLowerCase().includes(query));
}

const SORTS = {
  score: (a, b) => (b.Score || 0) - (a.Score || 0),
  cac: (a, b) => (a["Predicted CAC"] || 9e9) - (b["Predicted CAC"] || 9e9),
  followers: (a, b) => (b.Followers || 0) - (a.Followers || 0),
};

/* ---------- cards, grouped by funnel stage (furthest along first) ---------- */
function renderSections() {
  const rows = creators.filter(visible).sort(SORTS[sortKey]);
  $("#result-count").textContent = `${rows.length} of ${creators.length}`;
  $("#clear-filters").hidden = !anyFilterActive();

  const byStage = new Map();
  for (const c of rows) {
    const s = c.Stage || "Prospect";
    if (!byStage.has(s)) byStage.set(s, []);
    byStage.get(s).push(c);
  }
  const ordered = [...byStage.entries()]
    .sort((a, b) => STAGES.indexOf(b[0]) - STAGES.indexOf(a[0]));

  const root = $("#card-sections");
  root.replaceChildren(...ordered.map(([stage, list]) => {
    const sec = div("stage-section");
    const head = div("stage-head");
    head.append(span("stage-name", stage),
      span("stage-count", `${list.length} creator${list.length === 1 ? "" : "s"}`),
      span("stage-pos", `funnel stage ${STAGES.indexOf(stage) + 1} of ${STAGES.length}`));
    const grid = div("card-grid");
    grid.append(...list.map(cardNode));
    sec.append(head, grid);
    return sec;
  }));
  if (!rows.length) root.append(div("empty-note", "No creators match those filters."));
}

function avatarNode(c) {
  const baked = window.__DATA__?.avatars?.[c.Handle];
  if (window.__DATA__ && !baked) return initialsNode(c);
  const img = document.createElement("img");
  img.className = "avatar";
  img.loading = "lazy";
  img.alt = "";
  img.src = baked ||
    `/avatar/${encodeURIComponent(c.Handle)}?platform=${encodeURIComponent(c.Platform || "TikTok")}`;
  img.addEventListener("error", () => img.replaceWith(initialsNode(c)));
  return img;
}
function initialsNode(c) {
  const fb = div("avatar-fallback", (c.Handle || "?").slice(0, 2).toUpperCase());
  fb.style.background = AVATAR_COLORS[(c.Handle || "").length % AVATAR_COLORS.length];
  return fb;
}

/* avatar + platform-logo link badge (the logo IS the channel link) */
function avatarWithLink(c) {
  const wrap = div("avatar-wrap");
  wrap.append(avatarNode(c));
  if (c["Profile URL"]) {
    const a = document.createElement("a");
    a.className = "platform-link";
    a.href = c["Profile URL"];
    a.target = "_blank"; a.rel = "noopener";
    a.title = `Open @${c.Handle} on ${c.Platform}`;
    a.innerHTML = PLATFORM_ICONS[c.Platform] || "";
    a.addEventListener("click", e => e.stopPropagation());
    wrap.append(a);
  }
  return wrap;
}

function audienceSnippet(c) {
  const raw = (c.Audience || "").replace(/\S+@\S+/g, "").replace(/https?:\/\/\S+/g, "")
    .replace(/\s+/g, " ").trim();
  return raw.length > 110 ? raw.slice(0, 108) + "…" : raw;
}

function scoreRing(score) {
  const wrap = div("score-ring");
  const r = 18, circ = 2 * Math.PI * r;
  wrap.innerHTML =
    `<svg width="44" height="44" viewBox="0 0 44 44">
      <circle cx="22" cy="22" r="${r}" fill="none" stroke="var(--chart-grid)" stroke-width="4"/>
      <circle cx="22" cy="22" r="${r}" fill="none" stroke="var(--chart-1)" stroke-width="4"
        stroke-linecap="round" stroke-dasharray="${(score / 100) * circ} ${circ}"/>
    </svg><span class="val">${Number(score) || 0}</span>`;
  return wrap;
}

const CONF_COLOR = { High: "var(--ok)", Medium: "var(--warn)", Low: "var(--bad)" };

function cardNode(c) {
  const card = div("card " + (c._type === "Pro reseller" ? "type-pro" : "type-hobby"));
  const top = div("card-top");
  top.append(avatarWithLink(c));
  const id = div("card-id");
  id.append(div("handle", "@" + (c.Handle || "?")));
  const meta = div("meta-line");
  meta.append(span("type-lbl " + (c._type === "Pro reseller" ? "pro" : "hobby"), c._type),
    span(null, "·"), span(null, fmt(c.Followers || 0) + " followers"));
  id.append(meta);
  top.append(id, scoreRing(c.Score || 0));
  card.append(top);

  const snippet = audienceSnippet(c);
  if (snippet) card.append(div("audience-line", "“" + snippet + "”"));

  const tags = div("tag-row");
  if (c.Segment) tags.append(span("tag seg", c.Segment));
  (c["Content Keywords"] || "").split(",").map(s => s.trim()).filter(Boolean).slice(0, 4)
    .forEach(k => tags.append(span("tag", k)));
  card.append(tags);

  const foot = div("card-foot");
  const cac = span(null, "");
  cac.append("CAC ", Object.assign(document.createElement("b"),
    { textContent: c["Predicted CAC"] ? "£" + c["Predicted CAC"] : "—" }));
  const conf = span(null, "");
  const dot = span("conf-dot");
  dot.style.background = CONF_COLOR[c.Confidence] || "var(--chart-muted)";
  conf.append(dot, c.Confidence || "—");
  foot.append(cac, conf);
  if (c["Contact Route"]) foot.append(span(null, c["Contact Route"]));
  card.append(foot);

  card.addEventListener("click", () => openDrawer(c));
  return card;
}

/* ---------- drawer ---------- */
function openDrawer(c) {
  const d = $("#drawer");
  d.replaceChildren();
  const close = document.createElement("button");
  close.className = "close"; close.textContent = "✕";
  close.addEventListener("click", closeDrawer);
  d.append(close);

  const head = div("card-top");
  head.append(avatarWithLink(c));
  const h = document.createElement("h3");
  h.textContent = "@" + (c.Handle || "?");
  head.append(h);
  d.append(head);

  const kv = document.createElement("dl");
  kv.className = "kv sec";
  const pairs = [["Type", c._type + " (derived from wholesale + credibility sub-scores)"],
    ["Platform", c.Platform], ["Followers", fmt(c.Followers || 0)],
    ["Niche", c.Segment], ["Funnel stage", c.Stage],
    ["Predicted CAC", c["Predicted CAC"] ? "£" + c["Predicted CAC"] : "—"],
    ["Confidence", c.Confidence], ["Contact route", c["Contact Route"]],
    ["Source", c.Source]];
  for (const [k, v] of pairs) {
    if (!v) continue;
    kv.append(Object.assign(document.createElement("dt"), { textContent: k }),
      Object.assign(document.createElement("dd"), { textContent: v }));
  }
  d.append(kv);

  const breakdown = parseBreakdown(c["Score Breakdown"]);
  if (breakdown.length) {
    const sec = div("sec");
    sec.append(Object.assign(document.createElement("h4"), { textContent: "Score breakdown" }));
    for (const b of breakdown) {
      const row = div("breakdown-bar");
      row.append(div("blbl", b.label));
      const track = div("btrack");
      const fill = div("bfill");
      fill.style.width = Math.round((b.got / b.max) * 100) + "%";
      track.append(fill);
      row.append(track, div("bval", `${b.got}/${b.max}`));
      sec.append(row);
    }
    d.append(sec);
  }

  for (const [title, field] of [["Audience & bio", "Audience"], ["Why they fit", "Strength"],
    ["Watch out", "Weakness"], ["Keywords", "Content Keywords"], ["Notes", "Notes"]]) {
    if (!c[field]) continue;
    const sec = div("sec");
    sec.append(Object.assign(document.createElement("h4"), { textContent: title }));
    sec.append(Object.assign(document.createElement("p"), { textContent: c[field] }));
    d.append(sec);
  }
  if (c["Profile URL"]) {
    const sec = div("sec");
    const a = document.createElement("a");
    a.href = c["Profile URL"]; a.target = "_blank"; a.rel = "noopener";
    a.textContent = `Open @${c.Handle} on ${c.Platform} ↗`;
    sec.append(a);
    d.append(sec);
  }
  d.classList.add("open");
  $("#drawer-scrim").classList.add("open");
}
function closeDrawer() {
  $("#drawer").classList.remove("open");
  $("#drawer-scrim").classList.remove("open");
}
$("#drawer-scrim").addEventListener("click", closeDrawer);
addEventListener("keydown", e => { if (e.key === "Escape") closeDrawer(); });

function parseBreakdown(s) {
  if (!s) return [];
  return s.split(",").map(part => {
    const m = part.match(/([^:]+):\s*(\d+)\s*\/\s*(\d+)/);
    return m ? { label: m[1].trim(), got: +m[2], max: +m[3] } : null;
  }).filter(Boolean);
}

/* ---------- funnel ---------- */
async function loadFunnel() {
  const data = await getData("funnel");
  const stages = STAGES.map(s => ({ label: s, value: data.stages[s] || 0 }));
  const total = stages.reduce((a, s) => a + s.value, 0);
  $("#funnel-sub").textContent = `${total} creators in pipeline · ` +
    (window.__DATA__ ? "Airtable data at last build"
      : data.source === "live" ? "live from Airtable" : "snapshot data");
  funnelChart($("#funnel-chart"), stages);

  /* history (real) + modelled projection over 8 weeks */
  const hist = data.history;
  const start = total;
  const projWeeks = 8;
  const labels = [], real = [], model = [];
  hist.forEach(h => {
    labels.push(h.date.slice(5));
    real.push({ y: Object.entries(h.stages)
      .filter(([s]) => STAGES.indexOf(s) >= STAGES.indexOf("Contacted"))
      .reduce((a, [, v]) => a + v, 0) });
    model.push({ y: null });
  });
  const contactRate = MODEL_RATES[1] * MODEL_RATES[2];
  for (let w = 1; w <= projWeeks; w++) {
    labels.push("wk +" + w);
    real.push({ y: null });
    model.push({ y: Math.round(start * contactRate * Math.min(w / 3, 1)) });
  }
  lineChart($("#history-chart"), labels, [
    { name: "Contacted+ (real snapshots)", color: "var(--chart-1)", points: real },
    { name: "Contacted+ (modelled projection)", color: "var(--chart-muted)", dash: true, points: model },
  ]);
  $("#model-note").textContent =
    "Modelled assumptions: 60% of prospects qualify → all contacted over 3 weeks → 25% respond → 50% book a call → 60% sign → 90% onboard. Stated so they can be challenged; replaced by real snapshots as weeks accrue.";
}

/* ---------- trends ---------- */
async function loadTrends() {
  const t = await getData("trends");
  const weeks = t.weekly_posts.reduce((a, w) => a + w.count, 0);
  const stats = [
    [t.post_count, "posts analysed"],
    [t.top_by_volume.length ? "#" + t.top_by_volume[0].tag : "—", "top hashtag"],
    [t.rising.length ? "#" + t.rising[0].tag : "—", "fastest riser"],
    [weeks, "posts in last 12 weeks"],
  ];
  $("#trend-stats").replaceChildren(...stats.map(([num, lbl]) => {
    const s = div("stat");
    const n = div("num"); n.append(Object.assign(document.createElement("em"), { textContent: num }));
    s.append(n, div("lbl", lbl));
    return s;
  }));

  hBarChart($("#volume-chart"),
    t.top_by_volume.map(r => ({ label: "#" + r.tag, value: r.count })),
    { color: "var(--chart-1)" });
  hBarChart($("#engagement-chart"),
    t.top_by_engagement.map(r => ({ label: "#" + r.tag, value: r.views })),
    { color: "var(--chart-2)" });

  const ul = $("#rising-list");
  ul.replaceChildren(...t.rising.map(r => {
    const li = document.createElement("li");
    li.append(span("rtag", "#" + r.tag),
      span("rcounts", `${r.prior} → ${r.recent} posts`),
      span("rdelta", "+" + r.delta));
    return li;
  }));
  if (!t.rising.length) ul.append(div("empty-note", "No risers in the current window."));

  const table = $("#posts-table");
  table.replaceChildren(...t.top_posts.map(p => {
    const tr = document.createElement("tr");
    const author = document.createElement("td");
    author.className = "pauthor"; author.textContent = "@" + p.author;
    const text = document.createElement("td");
    text.className = "ptext"; text.textContent = (p.text || "").slice(0, 90) + (p.text?.length > 90 ? "…" : "");
    const views = document.createElement("td");
    views.className = "pviews"; views.textContent = fmt(p.views) + " views";
    tr.append(author, text, views);
    return tr;
  }));
}

loadCreators().catch(e => { $("#source-badge").textContent = "error"; console.error(e); });
loadFunnel().catch(console.error);
loadTrends().catch(console.error);
