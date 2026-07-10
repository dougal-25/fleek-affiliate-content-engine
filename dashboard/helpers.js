/* Shared constants + DOM helpers. Classic scripts share one global lexical scope, so these
   top-level consts are visible to views.js and app.js — declared once, here only. */
const { hBarChart, funnelChart, lineChart, fmt } = window.Charts;

const STAGES = ["Prospect", "Qualified", "Contacted", "Responded", "Call booked",
  "Contract", "Onboarded", "First post", "First sale", "Repeat posting"];
/* Modelled stage-to-stage rates — playbook assumptions, shown on-screen, never presented as data */
const MODEL_RATES = [1, 0.6, 1, 0.25, 0.5, 0.6, 0.9, 0.7, 0.5, 0.6];
const AVATAR_COLORS = ["#f86868", "#270626", "#a97c08", "#475467", "#d63c3c"];

/* Platform marks (16px), monochrome — rendered as links to the creator's channel */
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

/* Single-file build: build_html.py injects window.__DATA__ (creators/funnel/trends/
   inspiration/avatars) and the page runs from disk with no server. Else fetch serve.py. */
async function getData(kind) {
  if (window.__DATA__) return window.__DATA__[kind];
  return (await fetch("/api/" + kind)).json();
}
