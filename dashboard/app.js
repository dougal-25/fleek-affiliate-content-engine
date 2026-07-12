/* Creators view: toolbar, cards grouped by funnel stage, detail drawer.
   Shared constants/helpers live in helpers.js; funnel/trends/inspiration in views.js. */

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

let creators = [];
let AVATARS = null;  // handle → src map (data URIs when baked, static paths when hosted)
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
  AVATARS = (await getData("avatars").catch(() => null)) || null;
  creators = data.records.map(r => ({ id: r.id, ...r.fields }));
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
  const wrap = $("#platform-toggles");
  wrap.replaceChildren(...[...new Set(creators.map(c => c.Platform).filter(Boolean))].sort().map(p => {
    const b = document.createElement("button");
    b.className = "ptoggle" + (platformFilter.has(p) ? " on" : "");
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
  const groups = $("#filter-chips");
  groups.replaceChildren();
  for (const key of Object.keys(chipFilters)) {
    const values = [...new Set(creators.map(c => c[key]).filter(Boolean))].sort();
    if (values.length < 2) continue;
    const g = div("chip-group");
    g.append(span("glbl", key === "Segment" ? "Niche" : key));
    for (const v of values) {
      const b = document.createElement("button");
      b.className = "chip" + (chipFilters[key].has(v) ? " on" : "");
      b.textContent = window.Lang.t(v);
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
$("#lang-toggle").addEventListener("click", () => {
  window.Lang.toggle();
  const en = window.Lang.mode === "en";
  const b = $("#lang-toggle");
  b.textContent = en ? "🇬🇧 English" : "🇫🇷 Original";
  b.classList.toggle("en", en);
  renderToolbar();
  renderSections();
  closeDrawer();
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
  const known = AVATARS ? AVATARS[c.Handle] : null;
  if (AVATARS && !known) return initialsNode(c);
  const img = document.createElement("img");
  img.className = "avatar";
  img.loading = "lazy";
  img.alt = "";
  img.src = known ||
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
      <circle cx="22" cy="22" r="${r}" fill="none" stroke="var(--gold-deep)" stroke-width="4"
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

  const aud = div("tag-row");
  (c._audience_tags || []).forEach(t => aud.append(span("tag aud", "👥 " + t)));
  card.append(aud);

  const tags = div("tag-row");
  if (c.Segment) tags.append(span("tag seg", window.Lang.t(c.Segment)));
  (c["Content Keywords"] || "").split(",").map(s => s.trim()).filter(Boolean).slice(0, 4)
    .forEach(k => tags.append(span("tag", window.Lang.t(k))));
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

  d.append(qualifyBlock(c));

  // contact — clearly displayed, actionable
  const contact = div("contact-box sec");
  contact.append(span(null, "📮 Contact: "));
  if (c["Contact Email"]) {
    const mail = document.createElement("a");
    mail.href = "mailto:" + c["Contact Email"];
    mail.textContent = c["Contact Email"];
    contact.append(mail);
    if (c["Contact Route"]) contact.append(span(null, ` · via ${c["Contact Route"]}`));
  } else {
    contact.append(span(null, c["Contact Route"]
      ? `${c["Contact Route"]} (no email on file)` : "no route on file yet"));
  }
  d.append(contact);

  // every known channel — primary + auto-detected from bio + manual "Channels" field in Airtable
  const chans = Object.entries(c._channels || {});
  if (chans.length) {
    const sec = div("sec");
    sec.append(Object.assign(document.createElement("h4"), { textContent: "Channels" }));
    const row = div("channel-links");
    for (const [name, url] of chans) {
      const a = document.createElement("a");
      a.href = url; a.target = "_blank"; a.rel = "noopener";
      if (PLATFORM_ICONS[name]) a.innerHTML = PLATFORM_ICONS[name];
      else a.append(span("ch-letter", name.slice(0, 1).toUpperCase()));
      a.append(span(null, name));
      row.append(a);
    }
    sec.append(row);
    sec.append(Object.assign(document.createElement("p"), {
      className: "footnote",
      textContent: "Auto-detected from profile + bio. Add more in Airtable via a “Channels” field (one per line, “Platform: url”).",
    }));
    d.append(sec);
  }

  const kv = document.createElement("dl");
  kv.className = "kv sec";
  const pairs = [["Type", c._type + " (derived from wholesale + credibility sub-scores)"],
    ["Audience type", (c._audience_tags || []).join(", ")],
    ["Platform", c.Platform], ["Followers", fmt(c.Followers || 0)],
    ["Niche", window.Lang.t(c.Segment || "")], ["Funnel stage", c.Stage],
    ["Predicted CAC", c["Predicted CAC"] ? "£" + c["Predicted CAC"] : "—"],
    ["Confidence", c.Confidence], ["Source", c.Source]];
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
    const body = field === "Content Keywords"
      ? c[field].split(",").map(k => window.Lang.t(k.trim())).join(", ")
      : c[field];
    sec.append(Object.assign(document.createElement("p"), { textContent: body }));
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

/* ---------- manual qualification: the human gate on the discovery engine ----------
   Engine surfaces & scores prospects; a person reviews and qualifies (Prospect->Qualified).
   Reversible. Below the recommend line it's an override, flagged but allowed. */
const RECOMMEND_MIN = 60;
const READONLY = !!window.__DATA__;  // baked single-file export can't write

function toast(msg, kind = "ok") {
  let t = $("#toast");
  if (!t) {
    t = div("toast"); t.id = "toast"; document.body.append(t);
  }
  t.textContent = msg;
  t.className = "toast show " + kind;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { t.className = "toast"; }, 3200);
}

async function postQualify(handle, stage) {
  const headers = { "Content-Type": "application/json" };
  const tok = localStorage.getItem("fleek_qualify_token");
  if (tok) headers["X-Qualify-Token"] = tok;
  let res = await fetch("/api/qualify", {
    method: "POST", headers, body: JSON.stringify({ handle, stage }),
  });
  if (res.status === 401) {  // hosted + token required/wrong — ask once, retry
    const entered = prompt("Enter the qualification token to approve on the live dashboard:");
    if (!entered) throw new Error("cancelled");
    localStorage.setItem("fleek_qualify_token", entered.trim());
    headers["X-Qualify-Token"] = entered.trim();
    res = await fetch("/api/qualify", {
      method: "POST", headers, body: JSON.stringify({ handle, stage }),
    });
  }
  const out = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(out.error || `HTTP ${res.status}`);
  return out;
}

function qualifyBlock(c) {
  const box = div("qualify-box sec");
  const stage = c.Stage || "Prospect";
  const score = c.Score || 0;
  const recommended = score >= RECOMMEND_MIN;

  const status = div("qualify-status");
  status.append(span("q-lbl", "Funnel stage"), span("q-stage stage-" + stage.replace(/\s+/g, "-").toLowerCase(), stage));
  box.append(status);

  if (READONLY) {
    box.append(div("q-note", "Read-only export — qualify on the live dashboard."));
    return box;
  }
  if (stage !== "Prospect" && stage !== "Qualified") {
    box.append(div("q-note", `Past the qualify gate — manage “${stage}” in Airtable.`));
    return box;
  }

  const act = (label, next, cls) => {
    const b = document.createElement("button");
    b.className = "qualify-btn " + cls;
    b.textContent = label;
    b.addEventListener("click", async () => {
      b.disabled = true; b.textContent = "…";
      try {
        const r = await postQualify(c.Handle, next);
        c.Stage = r.to;                 // optimistic: the card moves funnel sections live
        renderSections();
        toast(r.noop ? `@${c.Handle} already ${r.to}`
          : r.override ? `@${c.Handle} qualified (override — fit score ${r.score}, below ${RECOMMEND_MIN})`
          : `@${c.Handle} → ${r.to}`, r.override ? "warn" : "ok");
        openDrawer(c);                  // re-render the drawer in its new state
      } catch (e) {
        b.disabled = false; b.textContent = label;
        toast(`Couldn't update: ${e.message}`, "bad");
      }
    });
    return b;
  };

  if (stage === "Prospect") {
    box.append(act("✓ Qualify partner", "Qualified", "primary"));
    box.append(div("q-note", recommended
      ? `Engine-recommended · fit score ${score}. You’re the approval gate.`
      : `⚠ Fit score ${score} — below the recommend line (${RECOMMEND_MIN}). Qualifying is an override.`));
  } else {  // Qualified
    box.append(act("↩ Move back to Prospect", "Prospect", "reverse"));
    box.append(div("q-note", "Qualified by a human. Reversible."));
  }
  return box;
}

loadCreators().catch(e => { $("#source-badge").textContent = "error"; console.error(e); });
