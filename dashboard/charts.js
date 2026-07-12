/* Hand-rolled SVG charts. Direct labels on every mark (contrast relief), hover tooltips.
   IIFE so these top-level names don't collide with app.js in the shared global scope. */
(() => {
const SVGNS = "http://www.w3.org/2000/svg";
const tooltip = () => document.getElementById("tooltip");

function el(name, attrs = {}, text) {
  const n = document.createElementNS(SVGNS, name);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  if (text != null) n.textContent = text;
  return n;
}

function showTip(evt, html) {
  const t = tooltip();
  t.innerHTML = html;
  t.hidden = false;
  const pad = 14;
  let x = evt.clientX + pad, y = evt.clientY + pad;
  const r = t.getBoundingClientRect();
  if (x + r.width > innerWidth - 8) x = evt.clientX - r.width - pad;
  if (y + r.height > innerHeight - 8) y = evt.clientY - r.height - pad;
  t.style.left = x + "px";
  t.style.top = y + "px";
}
function hideTip() { tooltip().hidden = true; }

function hover(node, htmlFn) {
  node.addEventListener("mousemove", e => showTip(e, htmlFn()));
  node.addEventListener("mouseleave", hideTip);
}

const fmt = n => n >= 1e6 ? (n / 1e6).toFixed(1) + "M"
  : n >= 1e3 ? (n / 1e3).toFixed(n >= 1e4 ? 0 : 1) + "K" : String(n);

/* escape data-derived strings before they enter tooltip/legend innerHTML */
const esc = s => String(s).replace(/[&<>"']/g, c =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/* Horizontal bars: rows = [{label, value, tip}] */
function hBarChart(container, rows, { color = "var(--chart-1)", valueFmt = fmt } = {}) {
  container.innerHTML = "";
  if (!rows.length) { container.innerHTML = '<p class="empty-note">No data yet.</p>'; return; }
  const rowH = 26, gap = 8, lblW = 120, valW = 52;
  const W = 560, H = rows.length * (rowH + gap) - gap;
  const svg = el("svg", { class: "chart-svg", viewBox: `0 0 ${W} ${H}`, role: "img" });
  const max = Math.max(...rows.map(r => r.value), 1);
  const plotW = W - lblW - valW;
  rows.forEach((r, i) => {
    const y = i * (rowH + gap);
    const w = Math.max((r.value / max) * plotW, r.value > 0 ? 3 : 0);
    svg.append(el("text", { x: lblW - 8, y: y + rowH / 2 + 4, "text-anchor": "end", class: "bar-lbl" },
      r.label.length > 16 ? r.label.slice(0, 15) + "…" : r.label));
    const bar = el("rect", { x: lblW, y, width: w, height: rowH, rx: 4, fill: color });
    hover(bar, () => r.tip || `${esc(r.label)}: ${valueFmt(r.value)}`);
    svg.append(bar);
    svg.append(el("text", { x: lblW + w + 6, y: y + rowH / 2 + 4, class: "bar-val" }, valueFmt(r.value)));
  });
  container.append(svg);
}

/* Funnel: ordered stages with stage-to-stage conversion labels */
function funnelChart(container, stages) {
  container.innerHTML = "";
  const rowH = 30, gap = 16, lblW = 130, valW = 60;
  const W = 720, H = stages.length * (rowH + gap) - gap;
  const svg = el("svg", { class: "chart-svg", viewBox: `0 0 ${W} ${H}`, role: "img" });
  const max = Math.max(...stages.map(s => s.value), 1);
  const plotW = W - lblW - valW - 90;
  stages.forEach((s, i) => {
    const y = i * (rowH + gap);
    const w = Math.max((s.value / max) * plotW, s.value > 0 ? 4 : 0);
    svg.append(el("text", { x: lblW - 10, y: y + rowH / 2 + 4, "text-anchor": "end", class: "bar-lbl" }, s.label));
    if (s.value === 0) {
      svg.append(el("rect", { x: lblW, y: y + rowH / 2 - 1, width: plotW, height: 2, rx: 1, fill: "var(--chart-grid)" }));
    }
    const bar = el("rect", { x: lblW, y, width: w || 0.01, height: rowH, rx: 4, fill: "var(--chart-1)" });
    hover(bar, () => `<b>${s.label}</b><br>${s.value} creator${s.value === 1 ? "" : "s"}`);
    svg.append(bar);
    svg.append(el("text", { x: lblW + Math.max(w, 2) + 8, y: y + rowH / 2 + 4, class: "bar-val" }, s.value));
    if (i > 0 && stages[i - 1].value > 0) {
      const pct = Math.round((s.value / stages[i - 1].value) * 100);
      svg.append(el("text", { x: W - 4, y: y + rowH / 2 + 4, "text-anchor": "end", class: "conv-lbl" }, `↳ ${pct}%`));
    }
  });
  container.append(svg);
}

/* Time series: series = [{name, color, dash, points: [{x(label), y}]}], shared x labels */
function lineChart(container, xLabels, series) {
  container.innerHTML = "";
  const W = 860, H = 260, padL = 40, padR = 16, padT = 14, padB = 30;
  const legend = document.createElement("div");
  legend.className = "legend";
  legend.innerHTML = series.map(s =>
    `<span><span class="sw" style="background:${s.color};${s.dash ? "background-image:repeating-linear-gradient(90deg,transparent 0 3px," + s.color + " 3px 6px);background-color:transparent;" : ""}"></span>${esc(s.name)}</span>`).join("");
  container.append(legend);
  const svg = el("svg", { class: "chart-svg", viewBox: `0 0 ${W} ${H}`, role: "img" });
  const maxY = Math.max(...series.flatMap(s => s.points.map(p => p.y ?? 0)), 1);
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const xPos = i => padL + (xLabels.length < 2 ? plotW / 2 : (i / (xLabels.length - 1)) * plotW);
  const yPos = v => padT + plotH - (v / maxY) * plotH;
  for (let g = 0; g <= 4; g++) {
    const v = Math.round((maxY / 4) * g);
    svg.append(el("line", { x1: padL, x2: W - padR, y1: yPos(v), y2: yPos(v), class: "grid-line" }));
    svg.append(el("text", { x: padL - 8, y: yPos(v) + 4, "text-anchor": "end", class: "axis-lbl" }, v));
  }
  const step = Math.ceil(xLabels.length / 10);
  xLabels.forEach((lb, i) => {
    if (i % step) return;
    svg.append(el("text", { x: xPos(i), y: H - 8, "text-anchor": "middle", class: "axis-lbl" }, lb));
  });
  for (const s of series) {
    const pts = s.points.map((p, i) => p.y == null ? null : `${xPos(i)},${yPos(p.y)}`).filter(Boolean);
    if (pts.length > 1) {
      svg.append(el("polyline", {
        points: pts.join(" "), fill: "none", stroke: s.color, "stroke-width": 2,
        "stroke-dasharray": s.dash ? "5 5" : "none", "stroke-linecap": "round",
      }));
    }
    s.points.forEach((p, i) => {
      if (p.y == null) return;
      const dot = el("circle", {
        cx: xPos(i), cy: yPos(p.y), r: 4, fill: s.color,
        stroke: "var(--surface)", "stroke-width": 2,
      });
      hover(dot, () => `<b>${s.name}</b><br>${xLabels[i]}: ${p.y}`);
      svg.append(dot);
    });
  }
  container.append(svg);
}

window.Charts = { hBarChart, funnelChart, lineChart, fmt, esc };
})();
