/* Read-only views: funnel, trends, inspiration. Uses helpers.js globals. */

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
    model.push({ y: Math.round(total * contactRate * Math.min(w / 3, 1)) });
  }
  lineChart($("#history-chart"), labels, [
    { name: "Contacted+ (real snapshots)", color: "var(--chart-1)", points: real },
    { name: "Contacted+ (modelled projection)", color: "var(--chart-muted)", dash: true, points: model },
  ]);
  $("#model-note").textContent =
    "Modelled assumptions: 60% of prospects qualify → all contacted over 3 weeks → 25% respond → 50% book a call → 60% sign → 90% onboard. Stated so they can be challenged; replaced by real snapshots as weeks accrue.";
}

/* Fleek-light categorical palette — warm hue sweep, distinguishable on white with a 2px gap + legend */
const STREAM_COLORS = ["#e23c56", "#f2789f", "#c9468f", "#8b3fb0", "#5b6ee0", "#1a9fb0", "#d99418"];
const CAT_COLORS = { Sourcing: "#e23c56", Platform: "#8b3fb0", Format: "#1a9fb0", Style: "#d99418" };

function legend(container, items) {
  container.replaceChildren(...items.map(([label, color]) => {
    const chip = span("leg");
    const sw = span("leg-sw"); sw.style.background = color;
    chip.append(sw, span("leg-txt", label));
    return chip;
  }));
}

async function loadTrends() {
  const t = await getData("trends");
  const weeks = t.weekly_posts.reduce((a, w) => a + w.count, 0);
  const topMover = (t.movers || []).find(m => m.direction === "up");
  const stats = [
    [t.post_count, "posts analysed"],
    [t.top_by_volume.length ? "#" + t.top_by_volume[0].tag : "—", "top hashtag"],
    [topMover ? "#" + topMover.tag : "—", "fastest riser"],
    [(t.cooccurrence?.edges || []).length, "tag links mapped"],
  ];
  $("#trend-stats").replaceChildren(...stats.map(([num, lbl]) => {
    const s = div("stat");
    const n = div("num"); n.append(Object.assign(document.createElement("em"), { textContent: num }));
    s.append(n, div("lbl", lbl));
    return s;
  }));

  // streamgraph
  const stream = t.stream || { weeks: [], series: [] };
  window.Charts.streamgraph($("#stream-chart"), stream.weeks, stream.series, STREAM_COLORS);
  legend($("#stream-legend"), stream.series.map((s, i) => ["#" + s.tag, STREAM_COLORS[i % STREAM_COLORS.length]]));

  // co-occurrence network
  const cooc = t.cooccurrence || { nodes: [], edges: [] };
  window.Charts.networkGraph($("#cooc-chart"), cooc.nodes, cooc.edges, CAT_COLORS);
  legend($("#cooc-legend"), Object.entries(CAT_COLORS));

  // movers
  const movers = $("#movers-list");
  movers.replaceChildren(...(t.movers || []).map(m => {
    const row = div("mover");
    row.append(span("mv-tag", "#" + m.tag));
    const pct = span("mv-pct " + m.direction, (m.direction === "up" ? "▲ " : "▼ ") + Math.abs(m.pct) + "%");
    row.append(pct);
    row.append(window.Charts.sparkline(m.spark, CAT_COLORS[m.category] || "var(--chart-muted)"));
    return row;
  }));
  if (!(t.movers || []).length) movers.append(div("empty-note", "No movers in the current window."));

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

/* inspiration: relevance-gated roster videos — thumbnail wall, in-page player + analysis */
let inspPosts = [], trendVolume = {};
let inspFormat = "", inspSort = "score", inspSource = "";

function statTile(num, lbl) {
  const s = div("va-stat");
  s.append(div("num", num), div("lbl", lbl));
  return s;
}

function openPlayer(p) {
  const modal = $("#video-modal");
  const frame = $("#video-frame");
  frame.replaceChildren();
  const iframe = document.createElement("iframe");
  iframe.src = p.embed;
  iframe.allow = "autoplay; encrypted-media; fullscreen";
  iframe.setAttribute("allowfullscreen", "");
  frame.append(iframe);

  /* per-video analysis: everything the brief generator would cite */
  const a = $("#video-analysis");
  a.replaceChildren();
  const head = div("va-head");
  head.append(span("insp-format", p.format), span("pauthor", "@" + p.author),
    span("insp-date", `${p.date}${p.weekday ? " · " + p.weekday : ""}`));
  a.append(head);

  const grid = div("va-grid");
  grid.append(
    statTile(fmt(p.views), "views"),
    statTile("×" + p.ratio, "vs their median (" + fmt(p.author_median_views) + ")"),
    statTile(fmt(p.likes), "likes"),
    statTile(fmt(p.comments), "comments"),
    statTile(fmt(p.shares), "shares"),
    statTile(p.engagement + "%", "engagement rate"),
  );
  a.append(grid);

  const hook = div("va-sec");
  hook.append(Object.assign(document.createElement("h4"), { textContent: "Hook / caption" }));
  hook.append(Object.assign(document.createElement("p"), { textContent: p.text || "(no caption)" }));
  a.append(hook);

  const tagSec = div("va-sec");
  tagSec.append(Object.assign(document.createElement("h4"), { textContent: "Hashtags · roster-wide usage" }));
  const row = div("tag-row");
  (p.tags || []).forEach(t =>
    row.append(span("tag", `#${t}` + (trendVolume[t] ? ` · ${trendVolume[t]} posts` : ""))));
  tagSec.append(row);
  a.append(tagSec);

  const why = div("va-sec");
  why.append(Object.assign(document.createElement("h4"), { textContent: "Why it's on the wall" }));
  why.append(Object.assign(document.createElement("p"), {
    textContent: `${p.format} format doing ×${p.ratio} this creator's median views — a repeatable technique, not account size. Relevance-gated to reseller content, posted ${p.date}.`,
  }));
  a.append(why);

  const note = div("footnote");
  note.textContent = "Watch time & comment text aren't public — watch time needs the creator's own analytics; comment text lands with the next ingest.";
  a.append(note);

  const out = document.createElement("a");
  out.href = p.url; out.target = "_blank"; out.rel = "noopener";
  out.className = "va-link"; out.textContent = "Open on TikTok ↗";
  a.append(out);

  modal.hidden = false;
  document.body.style.overflow = "hidden";
}
function closePlayer() {
  const modal = $("#video-modal");
  if (modal.hidden) return;
  modal.hidden = true;
  $("#video-frame").replaceChildren();  // removing the iframe stops playback
  document.body.style.overflow = "";
}

const INSP_SORTS = {
  score: () => 0,                                  // server order = blended technique score
  ratio: (a, b) => b.ratio - a.ratio,
  views: (a, b) => b.views - a.views,
  date: (a, b) => (b.date || "").localeCompare(a.date || ""),
};

function renderInspiration() {
  let rows = inspPosts.filter(p =>
    (!inspFormat || p.format === inspFormat) && (!inspSource || p.source === inspSource));
  if (inspSort !== "score") rows = [...rows].sort(INSP_SORTS[inspSort]);
  $("#insp-count").textContent = `${rows.length} of ${inspPosts.length} videos`;
  $("#insp-grid").replaceChildren(...rows.map(p => {
    const card = div("insp-card playable");
    const stage = div("insp-thumb");
    if (p.thumb) {
      const img = document.createElement("img");
      img.src = p.thumb; img.alt = ""; img.loading = "lazy";
      img.addEventListener("error", () => img.remove());
      stage.append(img);
    }
    const overlayTop = div("thumb-top");
    overlayTop.append(span("insp-format", p.format));
    if (p.source === "fleek") overlayTop.append(span("insp-fleek", "🌟 Fleek"));
    if (p.ratio >= 2) overlayTop.append(span("insp-ratio", `×${p.ratio}`));
    const overlayBottom = div("thumb-bottom");
    overlayBottom.append(span("thumb-views", fmt(p.views) + " views"));
    const caption = div("thumb-caption", p.text || "(no caption)");
    stage.append(overlayTop, overlayBottom, caption, span("play-btn", "▶"));
    card.append(stage);

    const tags = div("tag-row");
    (p.tags || []).slice(0, 4).forEach(t => tags.append(span("tag", "#" + t)));
    card.append(tags);
    const foot = div("insp-foot");
    foot.append(span("pauthor", "@" + p.author), span("insp-date", p.date));
    const a = document.createElement("a");
    a.href = p.url; a.target = "_blank"; a.rel = "noopener";
    a.textContent = "TikTok ↗";
    a.addEventListener("click", e => e.stopPropagation());
    foot.append(a);
    card.append(foot);
    card.addEventListener("click", () => openPlayer(p));
    return card;
  }));
}

async function loadInspiration() {
  const [data, trends] = await Promise.all([getData("inspiration"), getData("trends")]);
  inspPosts = data.posts;
  (trends.top_by_volume || []).forEach(r => { trendVolume[r.tag] = r.count; });

  const chips = $("#insp-format-chips");
  chips.replaceChildren(span("glbl", "Format"));
  [...new Set(inspPosts.map(p => p.format))].sort().forEach(f => {
    const b = document.createElement("button");
    b.className = "chip"; b.textContent = f;
    b.addEventListener("click", () => {
      inspFormat = inspFormat === f ? "" : f;
      chips.querySelectorAll(".chip").forEach(x => x.classList.toggle("on", x.textContent === inspFormat));
      renderInspiration();
    });
    chips.append(b);
  });
  $("#insp-sort").addEventListener("change", e => { inspSort = e.target.value; renderInspiration(); });
  document.querySelectorAll("#insp-source .seg").forEach(b => b.addEventListener("click", () => {
    inspSource = b.dataset.source;
    document.querySelectorAll("#insp-source .seg").forEach(x => x.classList.toggle("on", x === b));
    renderInspiration();
  }));
  renderInspiration();
}

$("#video-close").addEventListener("click", closePlayer);
$("#video-modal").addEventListener("click", e => { if (e.target.id === "video-modal") closePlayer(); });
addEventListener("keydown", e => { if (e.key === "Escape") closePlayer(); });

loadFunnel().catch(console.error);
loadTrends().catch(console.error);
loadInspiration().catch(console.error);
