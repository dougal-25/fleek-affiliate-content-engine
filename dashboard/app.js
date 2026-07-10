/* Fleek Affiliate Dashboard — data fetch + rendering. DOM built with createElement/textContent. */
const { hBarChart, funnelChart, lineChart, fmt } = window.Charts;

const STAGES = ["Prospect", "Qualified", "Contacted", "Responded", "Call booked",
  "Contract", "Onboarded", "First post", "First sale", "Repeat posting"];
/* Modelled stage-to-stage rates — playbook assumptions, shown on-screen, never presented as data */
const MODEL_RATES = [1, 0.6, 1, 0.25, 0.5, 0.6, 0.9, 0.7, 0.5, 0.6];
const AVATAR_COLORS = ["#f86868", "#270626", "#a97c08", "#475467", "#d63c3c"];

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
const filters = { Segment: new Set(), Platform: new Set(), Stage: new Set(), Confidence: new Set() };
let query = "";

/* ---------- tabs ---------- */
document.querySelectorAll(".tab").forEach(t => t.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach(x => x.classList.toggle("active", x === t));
  document.querySelectorAll(".view").forEach(v =>
    v.classList.toggle("active", v.id === "view-" + t.dataset.view));
}));

/* ---------- creators ---------- */
async function loadCreators() {
  const data = await getData("creators");
  creators = data.records.map(r => ({ id: r.id, ...r.fields }));
  const badge = $("#source-badge");
  if (window.__DATA__) {
    badge.textContent = "airtable data · " + (data.fetched || "").slice(0, 10);
    badge.className = "badge badge-live";
  } else {
    badge.textContent = data.source === "live" ? "● live · Airtable" : "snapshot · 09 Jul";
    badge.className = "badge " + (data.source === "live" ? "badge-live" : "badge-snapshot");
  }
  renderStats();
  renderChips();
  renderCards();
}

function renderStats() {
  const scores = creators.map(c => c.Score || 0);
  const cacs = creators.map(c => c["Predicted CAC"]).filter(Boolean).sort((a, b) => a - b);
  const medCac = cacs.length ? cacs[Math.floor(cacs.length / 2)] : 0;
  const reach = creators.reduce((s, c) => s + (c.Followers || 0), 0);
  const segs = new Set(creators.map(c => c.Segment).filter(Boolean));
  const stats = [
    [creators.length, "scored FR creators"],
    [fmt(reach), "combined reach"],
    [Math.round(scores.reduce((a, b) => a + b, 0) / (scores.length || 1)) + "/100", "avg fit score"],
    ["£" + medCac, "median predicted CAC"],
    [segs.size, "segments"],
  ];
  const strip = $("#creator-stats");
  strip.replaceChildren(...stats.map(([num, lbl]) => {
    const s = div("stat");
    const n = div("num"); n.append(Object.assign(document.createElement("em"), { textContent: num }));
    s.append(n, div("lbl", lbl));
    return s;
  }));
}

function renderChips() {
  const groups = $("#filter-chips");
  groups.replaceChildren();
  for (const key of Object.keys(filters)) {
    const values = [...new Set(creators.map(c => c[key]).filter(Boolean))];
    if (key === "Stage") values.sort((a, b) => STAGES.indexOf(a) - STAGES.indexOf(b));
    else values.sort();
    if (values.length < 2) continue;
    const g = div("chip-group");
    g.append(span("glbl", key));
    for (const v of values) {
      const b = document.createElement("button");
      b.className = "chip"; b.textContent = v;
      b.addEventListener("click", () => {
        filters[key].has(v) ? filters[key].delete(v) : filters[key].add(v);
        b.classList.toggle("on");
        renderCards();
      });
      g.append(b);
    }
    groups.append(g);
  }
}

$("#search").addEventListener("input", e => { query = e.target.value.toLowerCase(); renderCards(); });

function visible(c) {
  for (const [k, set] of Object.entries(filters))
    if (set.size && !set.has(c[k])) return false;
  if (!query) return true;
  return ["Handle", "Content Keywords", "Audience", "Segment", "Strength"]
    .some(f => (c[f] || "").toLowerCase().includes(query));
}

function avatarNode(c) {
  const baked = window.__DATA__?.avatars?.[c.Handle];
  if (window.__DATA__ && !baked) {
    const fb = div("avatar-fallback", (c.Handle || "?").slice(0, 2).toUpperCase());
    fb.style.background = AVATAR_COLORS[(c.Handle || "").length % AVATAR_COLORS.length];
    return fb;
  }
  const img = document.createElement("img");
  img.className = "avatar";
  img.loading = "lazy";
  img.alt = "";
  img.src = baked ||
    `/avatar/${encodeURIComponent(c.Handle)}?platform=${encodeURIComponent(c.Platform || "TikTok")}`;
  img.addEventListener("error", () => {
    const fb = div("avatar-fallback", (c.Handle || "?").slice(0, 2).toUpperCase());
    fb.style.background = AVATAR_COLORS[(c.Handle || "").length % AVATAR_COLORS.length];
    img.replaceWith(fb);
  });
  return img;
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

function renderCards() {
  const grid = $("#card-grid");
  const rows = creators.filter(visible).sort((a, b) => (b.Score || 0) - (a.Score || 0));
  grid.replaceChildren(...rows.map(c => {
    const card = div("card");
    const top = div("card-top");
    top.append(avatarNode(c));
    const id = div("card-id");
    id.append(div("handle", "@" + (c.Handle || "?")));
    const meta = div("meta-line");
    meta.append(span(null, c.Platform || ""), span(null, "·"),
      span(null, fmt(c.Followers || 0) + " followers"));
    id.append(meta);
    top.append(id, scoreRing(c.Score || 0));
    card.append(top);

    const tags = div("tag-row");
    if (c.Segment) tags.append(span("tag seg", c.Segment));
    if (c.Stage) tags.append(span("tag stage", c.Stage));
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
  }));
  if (!rows.length) grid.append(div("empty-note", "No creators match those filters."));
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
  head.append(avatarNode(c));
  const h = document.createElement("h3");
  h.textContent = "@" + (c.Handle || "?");
  head.append(h);
  d.append(head);

  const kv = document.createElement("dl");
  kv.className = "kv sec";
  const pairs = [["Platform", c.Platform], ["Followers", fmt(c.Followers || 0)],
    ["Segment", c.Segment], ["Stage", c.Stage],
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

  for (const [title, field] of [["Why they fit", "Strength"], ["Watch out", "Weakness"],
    ["Bio / audience", "Audience"], ["Keywords", "Content Keywords"], ["Notes", "Notes"]]) {
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
    a.textContent = "Open profile ↗";
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
  let inPlay = start;
  const contactRate = MODEL_RATES[1] * MODEL_RATES[2];
  for (let w = 1; w <= projWeeks; w++) {
    labels.push("wk +" + w);
    real.push({ y: null });
    const contacted = Math.round(start * contactRate * Math.min(w / 3, 1));
    model.push({ y: contacted });
    inPlay = contacted;
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
  const strip = $("#trend-stats");
  const weeks = t.weekly_posts.reduce((a, w) => a + w.count, 0);
  const stats = [
    [t.post_count, "posts analysed"],
    [t.top_by_volume.length ? "#" + t.top_by_volume[0].tag : "—", "top hashtag"],
    [t.rising.length ? "#" + t.rising[0].tag : "—", "fastest riser"],
    [weeks, "posts in last 12 weeks"],
  ];
  strip.replaceChildren(...stats.map(([num, lbl]) => {
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
