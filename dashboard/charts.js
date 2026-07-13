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

/* smoothed path through points [{x,y}] (Catmull-Rom → cubic bezier) */
function smooth(pts) {
  if (pts.length < 2) return "";
  let d = `M ${pts[0].x} ${pts[0].y}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2;
    const c1x = p1.x + (p2.x - p0.x) / 6, c1y = p1.y + (p2.y - p0.y) / 6;
    const c2x = p2.x - (p3.x - p1.x) / 6, c2y = p2.y - (p3.y - p1.y) / 6;
    d += ` C ${c1x} ${c1y} ${c2x} ${c2y} ${p2.x} ${p2.y}`;
  }
  return d;
}

/* Streamgraph — centered silhouette; band thickness = weekly mentions. series=[{tag,values[]}] */
function streamgraph(container, weeks, series, colors) {
  container.innerHTML = "";
  if (!series.length) { container.innerHTML = '<p class="empty-note">No data.</p>'; return; }
  const W = 1000, H = 300, padX = 24, padTop = 16, padBot = 28;
  const n = weeks.length, plotW = W - padX * 2, plotH = H - padTop - padBot;
  const totals = weeks.map((_, i) => series.reduce((s, ser) => s + (ser.values[i] || 0), 0));
  const maxTotal = Math.max(...totals, 1);
  const scale = plotH / maxTotal;
  const x = i => padX + (n < 2 ? plotW / 2 : (i / (n - 1)) * plotW);
  const yOf = v => padTop + plotH - v * scale;
  const svg = el("svg", { class: "chart-svg", viewBox: `0 0 ${W} ${H}`, role: "img" });

  const cum = weeks.map((_, i) => (maxTotal - totals[i]) / 2);  // centered baseline (value units)
  series.forEach((ser, s) => {
    const bottom = [], top = [];
    weeks.forEach((_, i) => {
      const lo = cum[i], hi = cum[i] + (ser.values[i] || 0);
      bottom.push({ x: x(i), y: yOf(lo) });
      top.push({ x: x(i), y: yOf(hi) });
      cum[i] = hi;
    });
    const d = smooth(top) + " L " + bottom.slice().reverse().map(p => `${p.x} ${p.y}`).join(" L ") + " Z";
    const band = el("path", { d, fill: colors[s % colors.length], stroke: "var(--surface)", "stroke-width": 2 });
    hover(band, () => `<b>#${esc(ser.tag)}</b><br>${ser.values.reduce((a, b) => a + b, 0)} mentions`);
    svg.append(band);
  });
  weeks.forEach((w, i) => { if (i % 1 === 0) svg.append(el("text", { x: x(i), y: H - 8, "text-anchor": "middle", class: "axis-lbl" }, w)); });
  container.append(svg);
}

/* Force-directed co-occurrence map. nodes=[{tag,count,category}] edges=[{a,b,weight}] */
function networkGraph(container, nodes, edges, catColors) {
  container.innerHTML = "";
  const W = 620, H = 460, cx = W / 2, cy = H / 2;
  const N = nodes.map((d, i) => ({ ...d,
    x: cx + Math.cos(i / nodes.length * 2 * Math.PI) * 150,
    y: cy + Math.sin(i / nodes.length * 2 * Math.PI) * 150, vx: 0, vy: 0 }));
  const idx = Object.fromEntries(N.map((d, i) => [d.tag, i]));
  const E = edges.filter(e => e.a in idx && e.b in idx);
  const maxC = Math.max(...N.map(d => d.count), 1);
  const rOf = c => 8 + Math.sqrt(c / maxC) * 20;
  for (let it = 0; it < 320; it++) {                       // simple spring layout
    for (let i = 0; i < N.length; i++) for (let j = i + 1; j < N.length; j++) {
      const a = N[i], b = N[j]; let dx = a.x - b.x, dy = a.y - b.y;
      let dist = Math.hypot(dx, dy) || 0.1;
      // strong short-range repulsion + a floor so big nodes never overlap
      const rep = 4200 / (dist * dist) + Math.max(0, (rOf(a.count) + rOf(b.count) + 14 - dist)) * 0.6;
      a.vx += dx / dist * rep; a.vy += dy / dist * rep; b.vx -= dx / dist * rep; b.vy -= dy / dist * rep;
    }
    for (const e of E) {
      const a = N[idx[e.a]], b = N[idx[e.b]]; let dx = b.x - a.x, dy = b.y - a.y;
      let dist = Math.hypot(dx, dy) || 0.1; const k = (dist - 95) * 0.018 * Math.min(e.weight / 6, 2);
      a.vx += dx / dist * k; a.vy += dy / dist * k; b.vx -= dx / dist * k; b.vy -= dy / dist * k;
    }
    for (const d of N) {
      d.vx += (cx - d.x) * 0.004; d.vy += (cy - d.y) * 0.004;   // gentle gravity to center
      d.x += Math.max(-10, Math.min(10, d.vx)); d.y += Math.max(-10, Math.min(10, d.vy));
      d.vx *= 0.86; d.vy *= 0.86;
      d.x = Math.max(34, Math.min(W - 34, d.x)); d.y = Math.max(26, Math.min(H - 26, d.y));
    }
  }
  const svg = el("svg", { class: "chart-svg", viewBox: `0 0 ${W} ${H}`, role: "img" });
  const maxW = Math.max(...E.map(e => e.weight), 1);
  for (const e of E) {
    const a = N[idx[e.a]], b = N[idx[e.b]];
    svg.append(el("line", { x1: a.x, y1: a.y, x2: b.x, y2: b.y, stroke: "var(--border)",
      "stroke-width": 1 + (e.weight / maxW) * 3, "stroke-opacity": 0.7 }));
  }
  for (const d of N) {
    const g = el("g", {});
    const c = el("circle", { cx: d.x, cy: d.y, r: rOf(d.count), fill: catColors[d.category] || "var(--chart-muted)",
      stroke: "var(--surface)", "stroke-width": 2 });
    hover(c, () => `<b>#${esc(d.tag)}</b><br>${d.category} · ${d.count} posts`);
    g.append(c, el("text", { x: d.x, y: d.y + rOf(d.count) + 12, "text-anchor": "middle", class: "net-lbl" }, "#" + d.tag));
    svg.append(g);
  }
  container.append(svg);
}

/* tiny sparkline node for the movers list */
function sparkline(values, color) {
  const W = 96, H = 28, max = Math.max(...values, 1);
  const pts = values.map((v, i) => ({ x: (i / (values.length - 1)) * W, y: H - 3 - (v / max) * (H - 6) }));
  const svg = el("svg", { class: "spark", viewBox: `0 0 ${W} ${H}`, width: W, height: H });
  svg.append(el("path", { d: smooth(pts), fill: "none", stroke: color, "stroke-width": 2, "stroke-linecap": "round" }));
  svg.append(el("circle", { cx: pts[pts.length - 1].x, cy: pts[pts.length - 1].y, r: 2.5, fill: color }));
  return svg;
}

window.Charts = { hBarChart, funnelChart, lineChart, streamgraph, networkGraph, sparkline, fmt, esc };
})();
