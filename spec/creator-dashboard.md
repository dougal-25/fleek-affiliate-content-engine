# Creator Affiliate Dashboard — UI spec

A standalone live dashboard presented **alongside the deck**. It is the visual proof that the roster is an
engine, not a spreadsheet: the Airtable base rendered as something Fleek can *see and touch*. Signed off by
Doug 2026-07-10 (four framing answers via question flow).

**References:** joinfleek.com itself — the dashboard must feel like Fleek's own brand and touch. Extracted
from their live CSS: Montserrat; coral `#f86868` (primary CTA), gold `#f8c642` (secondary accent), dark plum
`#270626`, cream `#fffcf4`, ink `#111827`, slate `#667085`/`#6b6e8b`, border `#eaecf0`. Light, warm, product-y.

**Mood/feel:** "Fleek built this for themselves." A page that could sit inside joinfleek.com — same type, same
warmth — but doing ops work: dense with real data, calm layout, zero dashboard-kitsch. Impressive on a
projector at arm's length.

**Hero moment:** the **creator card grid** — the wall of 49 real, scored French creators. Photo, handle,
platform, followers, segment, keyword tags, score, predicted CAC, confidence, funnel stage. Filterable live in
front of the room. Everything else supports this.

**Anti-examples:** generic admin-template dashboards (AdminLTE / dark "crypto dashboard" look), Airtable's own
grid view (if it looks like the spreadsheet, we've failed), chart-junk (gauges, 3-D, gradients-for-no-reason).

**Constraints:** desktop-only, presented locally. Doug's call 2026-07-10 (superseding the server-first
packaging): the deliverable is **one self-contained HTML file** — `dashboard/fleek-affiliate-dashboard.html`,
double-click to open, works offline, zero moving parts in the room. Data is pulled **fresh from Airtable at
build time** by `python3 dashboard/build_html.py` (key stays in the workspace `.env`; the file carries data,
never the key) and the header badge states the data date. `serve.py` remains as the dev/live mode and the
build's data layer. Vanilla HTML/CSS/JS, no frameworks, hand-rolled SVG charts.

## Pages

1. **Creators** (hero) — stat strip (roster size, avg score, median predicted CAC, segments), filter chips
   (segment / platform / stage / confidence) + text search, card grid. Click a card → detail drawer:
   strength, weakness, score breakdown, audience bio, contact route, keywords.
2. **Funnel** — the 10-stage recruitment pipeline (Prospect → Repeat posting) as horizontal bars with
   stage-to-stage conversion. Over-time view: the server snapshots stage counts to
   `dashboard/data/funnel_history.json` on every launch, so the weekly-cadence chart **compounds real data**
   from today forward. A dashed "modelled projection" overlay (rates stated on-screen) shows where the 49
   prospects are expected to flow — clearly labelled modelled, never presented as fact.
3. **Trends** — computed live from the 588 ingested TikTok/YouTube posts: top hashtags by volume and by
   engagement, rising terms week-over-week, top-performing posts. The narrative: this is what feeds outreach
   personalisation and brief ideas.

## Data honesty rules

- Funnel history is real from 2026-07-10 onward; anything modelled is labelled modelled.
- Avatars proxied (and disk-cached) from public profile-image sources; fallback is branded initials — no
  scraping games, no broken-image icons.
- LIVE/SNAPSHOT badge always visible.

## Build notes

- `dashboard/` folder: `serve.py` (stdlib only), `index.html`, `tokens.css`, `style.css`, `charts.js`
  (SVG chart renderers), `app.js`, `data/` (gitignored cache: avatars, funnel history).
- All colors/spacing via `tokens.css` custom properties; no hardcoded hex in feature CSS.
- Files stay under the 500-line limit (largest: `app.js` at 345).
- Chart marks use `#d63c3c` / `#a97c08` — darkened brand steps that pass all six dataviz checks on the
  cream surface (raw brand coral/gold fail contrast/lightness). Brand coral stays for UI chrome.
- unavatar.io 403s Python's default urllib User-Agent — the proxy sends a browser-ish UA.
- charts.js is wrapped in an IIFE: classic scripts share one global lexical scope, so two files both
  declaring `const fmt` kill the second script with "already declared" before it runs.
- Server respects `PORT` env var (default 8787) — the preview harness and any port clash both need it.
