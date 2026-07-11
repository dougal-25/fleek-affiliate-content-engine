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

/* inspiration: relevance-gated roster videos, playable in an in-page TikTok embed */
function openPlayer(p) {
  const modal = $("#video-modal");
  const frame = $("#video-frame");
  frame.replaceChildren();
  const iframe = document.createElement("iframe");
  iframe.src = p.embed;
  iframe.allow = "autoplay; encrypted-media; fullscreen";
  iframe.setAttribute("allowfullscreen", "");
  frame.append(iframe);
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

async function loadInspiration() {
  const data = await getData("inspiration");
  $("#insp-grid").replaceChildren(...data.posts.map(p => {
    const card = div("insp-card playable");
    const top = div("insp-top");
    top.append(span("insp-format", p.format));
    if (p.ratio >= 2) top.append(span("insp-ratio", `×${p.ratio} their usual`));
    const views = span("insp-views", fmt(p.views));
    views.append(Object.assign(document.createElement("small"), { textContent: " views" }));
    top.append(views);
    card.append(top);

    const stage = div("insp-play");
    stage.append(span("play-btn", "▶"));
    card.append(stage);

    card.append(div("insp-text", (p.text || "(no caption)")));
    const tags = div("tag-row");
    (p.tags || []).forEach(t => tags.append(span("tag", "#" + t)));
    card.append(tags);
    const foot = div("insp-foot");
    foot.append(span("pauthor", "@" + p.author), span("insp-date", p.date));
    if (p.url) {
      const a = document.createElement("a");
      a.href = p.url; a.target = "_blank"; a.rel = "noopener";
      a.textContent = "TikTok ↗";
      a.addEventListener("click", e => e.stopPropagation());
      foot.append(a);
    }
    card.append(foot);
    if (p.embed) card.addEventListener("click", () => openPlayer(p));
    return card;
  }));
}

$("#video-close").addEventListener("click", closePlayer);
$("#video-modal").addEventListener("click", e => { if (e.target.id === "video-modal") closePlayer(); });
addEventListener("keydown", e => { if (e.key === "Escape") closePlayer(); });

loadFunnel().catch(console.error);
loadTrends().catch(console.error);
loadInspiration().catch(console.error);
