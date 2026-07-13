/* Brief Studio view — localised, channel-aware briefs, rendered into #view-briefs.
   Reuses shared helpers ($, div, span, fmt, window.Charts) from helpers.js/charts.js and the
   #drawer from app.js. Data: getData("briefs") → { creators: [...] } (api/_static/briefs.json).

   The hero is localisation: every creator-facing message is shown in French AND English, always,
   because that IS the point of this view. Delivery is channel-aware — email (subject + body) or
   DM — per the creator's real contact route. Emails are redacted server-side for the public page. */
(() => {
  let BRIEFS = [];
  let cur = 0;

  const CH_COLOR = { youtube: "#d63c3c", tiktok: "#111827", instagram: "#a97c08" };
  const PLAT = { youtube: "YouTube", tiktok: "TikTok", instagram: "Instagram" };
  const LIFE = { dormant: "Re-activation", new: "Onboarding · brief #1", active: "Always-on" };
  const TYPECLS = { dormant: "type-hobby", new: "type-pro", active: "type-hobby" };

  const esc = s => String(s == null ? "" : s)
    .replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const initial = h => (h || "?").replace(/[^a-z]/i, "").charAt(0).toUpperCase() || "?";
  const html = (cls, s) => { const n = document.createElement("div"); if (cls) n.className = cls; n.innerHTML = s; return n; };

  async function initBriefs() {
    const root = $("#bf-root");
    if (!root) return;
    const data = await getData("briefs").catch(() => null);
    BRIEFS = (data && data.creators) || [];
    if (!BRIEFS.length) { root.replaceChildren(div("empty-note", "No briefs generated yet.")); return; }
    render();
  }

  function render() {
    const d = BRIEFS[cur];
    const root = $("#bf-root");
    root.replaceChildren(
      intro(),
      switcher(),
      stats(d),
      grid(d),
    );
  }

  function intro() {
    return html("bf-intro panel-head",
      `<h2>Brief Studio</h2><p>One personalised, localised brief per creator — generated from their own posts,
       delivered on their channel. French as written · English translation shown throughout.</p>`);
  }

  function switcher() {
    const wrap = div("bf-switcher");
    BRIEFS.forEach((d, i) => {
      const card = document.createElement("button");
      card.className = "bf-switch " + (TYPECLS[d.lifecycle] || "");
      card.setAttribute("aria-current", String(i === cur));
      card.innerHTML =
        `<div class="bf-switch-top">
           <span class="avatar-fallback" style="background:${CH_COLOR[d.platform] || "#475467"}">${esc(initial(d.handle))}</span>
           <div class="bf-switch-id">
             <div class="bf-switch-handle">@${esc(d.handle)}</div>
             <div class="bf-switch-meta">${esc(PLAT[d.platform] || d.platform)} · ${fmt(d.followers || 0)} · score ${esc(d.score)}</div>
           </div>
           <span class="bf-switch-life"><span class="bf-life ${esc(d.lifecycle)}">${esc(LIFE[d.lifecycle] || d.lifecycle)}</span></span>
         </div>
         <div class="bf-switch-line">${esc(d.oneLiner)}</div>`;
      card.addEventListener("click", () => { cur = i; render(); });
      wrap.append(card);
    });
    return wrap;
  }

  function statTile(num, lbl, sub, mono) {
    const s = div("stat");
    const n = div("num");
    if (mono) n.style.fontFamily = "ui-monospace, Menlo, monospace";
    if (String(num).length > 10) n.style.fontSize = "15px";
    n.append(Object.assign(document.createElement("em"), { textContent: num }));
    s.append(n, div("lbl", lbl));
    if (sub) { const p = div("bf-ev-caption", sub); p.style.marginTop = "2px"; s.append(p); }
    return s;
  }

  function stats(d) {
    const strip = div("stat-strip");
    strip.append(
      statTile(LIFE[d.lifecycle] || d.lifecycle, "Brief type", d.code ? "reuses " + d.code : "new code issued"),
      statTile("€" + d.cac, "Target CAC", "from discovery scoring", true),
      statTile(d.channelLabel, "Contact channel", esc(d.contactValue)),
      statTile(d.format, "Format", "their proven winner"),
    );
    return strip;
  }

  function grid(d) {
    const g = div("bf-grid");
    const left = div("bf-col"), right = div("bf-col");
    left.append(messagesPanel(d), deliveryPanel(d));
    right.append(evidencePanel(d), guardrailsPanel(d), fullBtn(d));
    g.append(left, right);
    return g;
  }

  function msgCard(kind, i, m) {
    return `<div class="bf-msg">
      <div class="bf-msg-kind">${i != null ? `<span class="n">${i}</span>` : ""}${esc(kind)}</div>
      <div class="bf-msg-fr">${esc(m.fr)}</div>
      <div class="bf-msg-en">${esc(m.en)}</div>
    </div>`;
  }

  function messagesPanel(d) {
    const p = div("panel");
    p.append(html("bf-panel-head",
      `<span class="bf-eyebrow">What the creator says</span><h3>Localised messages</h3>
       <span class="bf-why">French in her register, English translation beneath. The engine localises per creator, not just translates.</span>`));
    const list = d.hooks.map((m, i) => msgCard("Hook option", i + 1, m)).join("")
      + d.captions.map((m, i) => msgCard("Caption", i + 1, m)).join("");
    p.append(html("bf-msg-list", list));
    return p;
  }

  function deliveryPanel(d) {
    const o = d.outreach, isEmail = o.channel === "email";
    const p = div("panel");
    p.append(html("bf-panel-head",
      `<span class="bf-eyebrow">How we reach her</span><h3>Outreach — ${isEmail ? "email" : "direct message"}</h3>`));
    const subj = isEmail && o.subjectFr
      ? `<div class="bf-del-subj"><span class="k">Subject</span>${esc(o.subjectFr)}</div>` : "";
    const enSubj = isEmail && o.subjectEn ? "<b>" + esc(o.subjectEn) + "</b>\n\n" : "";
    p.append(html("bf-delivery",
      `<div class="bf-del-head">
         <span class="bf-ch"><span class="ic">${isEmail ? "@" : "✉"}</span>${isEmail ? "Email" : "Direct message"}</span>
         <span class="bf-del-route">${isEmail ? "bio email on file" : "no public email — DM"} · <b>@${esc(d.handle)}</b></span>
       </div>
       <div class="bf-del-body">
         ${subj}
         <div class="bf-del-fr">${esc(o.bodyFr)}</div>
         <div class="bf-del-en">${enSubj}${esc(o.bodyEn)}</div>
         <div class="bf-human">✎ <span><b>Draft only.</b> ${esc(o.humanNote)}</span></div>
       </div>`));
    return p;
  }

  function evidencePanel(d) {
    const p = div("panel");
    p.append(html("bf-panel-head", `<span class="bf-eyebrow">Why this creator</span><h3>Their top posts</h3>`));
    const chartHost = div("");
    p.append(chartHost);
    const rows = (d.topPosts || []).map(t => ({
      label: t.label, value: t.v,
      tip: `<b>${esc(t.label)}</b><br>${fmt(t.v)} views · ${fmt(t.l)} likes`,
    }));
    window.Charts.hBarChart(chartHost, rows, { color: CH_COLOR[d.platform] || "var(--chart-1)" });
    p.append(html("bf-ev-caption", d.evCaption || ""));  // evCaption carries intentional <b> emphasis
    if (d.code) {
      p.append(html("bf-code-found",
        `<div><span class="cf-code">${esc(d.code)}</span><span class="cf-hit">found in ${esc(d.codeCount)}/${esc(d.postsTotal)} videos</span></div>
         <div class="cf-note">Airtable had her as <b>Prospect · not started</b>. Her own videos say she's an active partner. The engine believes the videos.</div>`));
    }
    return p;
  }

  function guardrailsPanel(d) {
    const p = div("panel");
    p.append(html("bf-panel-head", `<span class="bf-eyebrow">Positioning guardrails</span><h3>Do not mention</h3>`));
    const items = (d.doNotMention || []).map((x, i) =>
      `<div class="bf-dnm ${i === 0 ? "key" : ""}"><span class="x">✕</span><span>${esc(x)}</span></div>`).join("");
    p.append(html("bf-dnm-list", items));
    return p;
  }

  function fullBtn(d) {
    const b = document.createElement("button");
    b.className = "bf-fullbtn";
    b.textContent = "View the full brief →";
    b.addEventListener("click", () => openBriefDrawer(d));
    return b;
  }

  /* full brief in the shared right-hand drawer (reuses #drawer + closeDrawer from app.js) */
  function openBriefDrawer(d) {
    const b = d.full || {};
    const drawer = $("#drawer");
    const sec = (title, inner) => `<div class="bf-dsec"><h4>${esc(title)}</h4>${inner}</div>`;
    const ul = arr => "<ul>" + (arr || []).map(x => `<li>${esc(x)}</li>`).join("") + "</ul>";
    drawer.innerHTML =
      `<button class="close" id="bf-dclose">✕</button>
       <h3>Full brief · @${esc(d.handle)}</h3>
       <p class="bf-ev-caption" style="margin-top:4px">${esc(b.brief_id || "")} · ${esc(d.oneLiner)}</p>
       ${sec("Objective", `<p>${esc(b.objective)}</p>`)}
       ${sec("Three content ideas", ul((b.content_ideas || []).map(i => i.title + " — " + i.premise)))}
       ${sec("Talking points", ul(b.talking_points))}
       ${sec("Thumbnail", `<p>${esc(b.thumbnail_direction)}</p>`)}
       ${sec("CTA stack", ul(b.cta_stack))}
       ${sec("Posting schedule", `<p>${esc(b.posting_schedule)}</p>`)}
       ${sec("Do", ul(b.dos))}
       ${sec("Don't", ul(b.donts))}
       ${sec("Reference", ul(b.reference_examples))}
       ${sec("Success target", `<p class="mono">${esc(b.success_target)}</p>`)}`;
    $("#bf-dclose").addEventListener("click", closeDrawer);
    drawer.classList.add("open");
    $("#drawer-scrim").classList.add("open");
  }

  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", initBriefs);
  else initBriefs();
})();
