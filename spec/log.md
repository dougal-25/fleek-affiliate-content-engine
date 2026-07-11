# Spec — Log

Dated record of design intent changing. Newest first. Decisions with reasoning get their own page in
`spec/decisions/`; this is the running thread.

---

## 2026-07-10 — The mission is real; two load-bearing claims were wrong

Doug supplied the JD and the case-study brief. Both are now captured verbatim in `mission/`, and
`mission/mission.md` is rewritten against them — the *awaiting sign-off* banner is gone.

Reading the sources against the repo surfaced two claims that had been built on inference:

1. **"Fleek has no structured creator program — greenfield, not a fix-up."** False. The JD describes a 1,000+
   creator roster built over two years, recruitment largely automated, running on an internal Content Brain.
   The wiki had inferred "no programme" from Fleek's *public surface* — the `RFD-` referral codes visible on
   joinfleek.com and TikTok. The programme exists; it isn't public. Corrected on
   `Fleek Wiki/research/Fleek Company Profile.md`, and the strategic thesis on `Fleek Wiki/index.md` revised
   and flagged for Doug's sign-off. **Method lesson recorded on the page:** absence of public evidence was
   treated as evidence of absence.

2. **"Anchor on activation; recruitment is a supporting motion."** Written into `deliverables/strategy.md`
   before the brief existed. The brief asks for both — Part 1 (discovery) is explicitly *"the core
   AI-nativeness test"*, and Part 5 splits budget across recruitment and re-activation. Corrected in place.

**What the sources add that the repo didn't have:** ~20,000 total addressable resellers (bounds every scale
claim); three named real top-performing partners (`@behindthesale`, `@theliveneedham`, `@juliacrcl`) that
should calibrate the scoring model instead of guessed archetypes; the exact attribution mechanic; and Fleek's
self-declared hardest problem — *pro resellers think Fleek is for beginners.* Nothing in the vault addresses
that yet, and it is the most interesting thing in the brief.

**Open:** the revised strategic thesis needs Doug's call before it drives the deck.

## 2026-07-09 — Repo restructured around mission / wiki / spec / code

**Why:** the repo had grown by accretion. Things got built, then a home was found for them. Three concrete
failures: the JD and task brief — the two documents this project is judged against — existed nowhere as
files, only as paraphrase inside two strategy docs. A half-finished vault rename had left git reporting 24
phantom deletions and the research agent pointing at a directory that no longer existed. And `docs/` was
sorting four different genres of document under one numbered sequence.

**What changed:**

- **`mission/` created.** `job-description.md` and `task-brief.md` land as placeholders awaiting the verbatim
  text. `mission.md` states what we build and how we're judged — stamped *awaiting sign-off* until the two
  sources are captured, because right now it's an inference drawn from `deliverables/strategy.md`.
- **The vault is one vault.** `FLEEK BRAIN/` → `Fleek Wiki/`, preserving git history (renames, not
  delete+add). An empty nested Obsidian vault created the night before — which is what breaks the parent's
  graph view — was retired to `_attic/`. `FLEEK BRAIN Index.md`/`Log.md` → `index.md`/`log.md`, and all 21
  notes' wikilinks repointed.
- **Naming settled.** Fleek uses *the Brain* for the whole affiliate content engine, so this repo *is* the
  Brain and no subfolder claims the word. The research vault is *the wiki*. Documented in `CLAUDE.md`.
  The `brain_refresh` job is now `wiki_refresh`.
- **`docs/` dissolved by genre.** Architecture, playbook and autonomy design → `spec/`. Strategy and the
  case-study approach → `deliverables/`. The two "what changed since draft 1" tables → `spec/decisions/`,
  where a decision record belongs.
- **The research agent is invocable.** `agents/brain_research_agent.md` → `.claude/agents/wiki-researcher.md`
  with frontmatter. It had been pointing at `FLEEK BRAIN/` and at `scripts/run_brain_research.py`, a script
  that does not exist — that claim is gone; the agent runs as a subagent.
- **`CLAUDE.md` and `spec/overview.md` written.** Neither existed.

**What deliberately did not change:** `content_brain/`, `scripts/` and `run_campaign.py` stay exactly where
they are. Wrapping working code in an `engine/` folder would look tidier and cost a round of Python import
breakage for zero functional gain. The code was never the mess.

**Open:** `mission/job-description.md` and `mission/task-brief.md` are empty. Until Doug pastes the verbatim
text, everything citing the mission is citing an inference.

## 2026-07-10 — Creator affiliate dashboard shipped (`dashboard/`)

**What:** a standalone live dashboard to present alongside the deck — the Airtable base made visible.
Three views: **Creators** (the hero — 49 real scored FR creators as rich cards: avatar, segment, keyword
tags, score ring, predicted CAC, confidence, funnel stage; filter chips + search; click → full-profile
drawer), **Recruitment funnel** (10-stage pipeline with stage-to-stage conversion, plus a pipeline-over-time
chart), **Trends & keywords** (computed live from the 588 ingested posts: top hashtags by volume and by
views, 90-day risers, top-performing posts — the feed for outreach personalisation and brief ideas).

- **Live, not a mock.** A stdlib Python proxy (`dashboard/serve.py`) fetches the Creators table from
  Airtable on load — the key stays in the workspace `.env`, never reaching the browser. Offline it falls
  back to the committed snapshot, and the header badge says LIVE or SNAPSHOT so the room is never lied to.
  First live pull already diverged from the snapshot (39 Prospect / 10 Qualified vs 49 Prospect) — proof
  the live wire works.
- **Funnel history compounds.** Each launch snapshots stage counts to `dashboard/data/funnel_history.json`
  (gitignored). Real weekly cadence accrues from 2026-07-10; the modelled projection is dashed, grey, and
  labelled with its assumptions on-screen.
- **Fleek's own brand.** Tokens extracted from joinfleek.com live CSS (Montserrat, coral/gold/plum/cream)
  into `dashboard/tokens.css`. Chart colors are darkened brand steps that pass the dataviz six-checks
  validator on the cream surface.
- **Avatars** proxied through unavatar.io with a disk cache (unavatar 403s python-urllib — needed a real
  User-Agent); fallback is branded initials, never a broken image.
- Spec + sign-off: `spec/creator-dashboard.md` (Doug answered the four framing questions 2026-07-10).
- Run: `python3 dashboard/serve.py` → http://localhost:8787 (respects `PORT`).

**Follow-ups:** funnel-over-time gets interesting only as stages move in Airtable — the display is ready
for it. Consider a fourth "Brief" view later (show a generated brief in situ) if the deck needs it.

## 2026-07-10 — Dashboard repackaged as one self-contained HTML file

Doug's call: scrap the run-a-server presentation flow; the deliverable is a single HTML file.
`dashboard/build_html.py` pulls the roster fresh from Airtable, computes funnel + trends, embeds the
avatars as data URIs, inlines all CSS/JS, and writes `dashboard/fleek-affiliate-dashboard.html` (~3.3 MB) —
double-click, works offline, zero server calls (verified: 0 network requests to /api or /avatar). Badge now
reads "airtable data · <date>" so the data's freshness is stated, not implied. `serve.py` stays as the
build's data layer and the live dev mode; `app.js` prefers injected `window.__DATA__` and falls back to
fetch. Rebuild = one command; note the built file embeds the full creator records (incl. bio-scraped
emails) — fine to hand to Fleek, worth remembering if it ever goes anywhere public.

## 2026-07-10 — Dashboard v2: real brand assets, pro/hobbyist split, funnel-grouped cards

Doug's six-point review implemented:
1. **Real Fleek branding** — the actual logo (gold starburst + hand-drawn FLEEK wordmark) pulled from
   joinfleek.com and embedded; Montserrat and the extracted palette stay.
2. **Pro reseller vs hobbyist** on every card — clear-but-subtle: plum/gold top border + small type label.
   Derived from the engine's own sub-scores (wholesale content ≥ 6/10, or credibility ≥ 18/25 with
   wholesale keywords) → 14 pro / 35 hobbyist. First keyword-only attempt gave a useless 47/2; the
   scoring model is the honest signal. Niche/style = segment chip + keyword tags (open-ended, from data).
3. **Channel links** — the platform logo (TikTok/YouTube/Instagram mark) sits as a badge on each avatar
   and IS the link to the creator's channel; repeated in the drawer.
4. **Filter toolbar** — search, All/Pro/Hobbyists segmented control, platform icon toggles, sort
   (score/CAC/followers), live result count, Clear. Niche + confidence chips below.
5. **Funnel-dynamic layout** — the card grid is grouped into funnel-stage sections (furthest along first),
   each header showing count + "funnel stage N of 10". Filters recount sections live.
6. **Audience detail** — each card quotes the creator's bio/audience line (emails/URLs stripped); the
   drawer leads with a full "Audience & bio" section.
Rebuilt single file: 6.7 MB (more avatars resolved on rebuild — 17 embedded photos).

## 2026-07-10 — Dashboard v3: marketplace theme, audience tags, channels, translation, Inspiration page

Doug's second review round, all six landed:
1. **Audience-type tags** — derived deterministically in `serve.py` (regex rules over keywords + bio +
   strength): wholesale buyers, aspiring resellers, bargain hunters, vintage lovers, live-shopping
   viewers, sneakerheads, luxury-resale shoppers, eco-conscious shoppers, fashion-inspo seekers. Max 3
   per creator, shown as gold-tinted 👥 pills on cards and in the drawer.
2. **Channel links** — every creator's drawer now has a Channels row: primary profile + auto-detected
   channels from bio text (found 2 multi-channel creators: intemporal_paris, gdefou) across TikTok /
   Instagram / YouTube / Vinted / Depop / Whatnot patterns. Manual additions: an Airtable "Channels"
   field ("Platform: url" per line) is picked up automatically and wins over auto-detection.
3. **Marketplace theme** — inspected joinfleek.com/collections/womens live (Playwright): white bg, black
   ink, gold CTAs, black active states, light-gray pills. Retheme swaps cream→white, coral actives→black,
   gold accents throughout (stat underlines, niche chips, score rings, platform toggles). Coral demoted
   to hover/status. Real logo already in from v2.
4. **Translation toggle** — 🇫🇷 Original / 🇬🇧 English button in the header; ~80-entry curated FR→EN
   dictionary (`translations.js`) built against the actual 198-keyword vocabulary. Applies to keyword
   tags, niche chips and drawer keywords; unknown terms pass through untranslated, never guessed.
5. **Contact clearly displayed** — gold contact box at the top of every drawer: mailto link when an email
   is on file, otherwise the route ("DM") stated plainly.
6. **Inspiration page** (4th tab) — top 24 roster videos by views, each with a derived format label
   (Live selling / Bale unboxing / Haul / Tutorial / Sourcing vlog), caption, hashtags, author, date and
   a Watch link to the actual TikTok. Framed on-page as the input feed for the next stage: the brief &
   activation generator.

Ship-check note: `app.js` hit 565 lines → split into `helpers.js` (shared consts/DOM utils),
`views.js` (funnel/trends/inspiration) and `app.js` (cards/toolbar/drawer, 399). All files < 500.
Rebuilt file: 6.7 MB, 38/49 real photos, zero network calls verified.

## 2026-07-10 — Dashboard live on Vercel: https://fleek-affiliate-dashboard.vercel.app

The dashboard is now a public site, truly live from Airtable — the stage-motion demo works end-to-end:
edit a creator's Stage in Airtable, reload the page, the card moves funnel sections and the counts update
(proven: moved @felixbeauregard Prospect→Qualified, live site went 39/10 → 38/11 within seconds, then
reverted — data left untouched).

**Architecture (grug-minimal):** static files + ONE Python serverless function (`dashboard/api/data.py`)
that fetches Airtable live (key in Vercel env, added with Doug's explicit approval — never in the page or
repo), enriches via the same `serve.py` code the local server uses, and returns creators + funnel + the
precomputed trends/inspiration/avatar-manifest in one call, edge-cached 60s. `make_static.py` precomputes
what's static (trends and inspiration from the committed post jsonl, avatars as real files, funnel history
baseline, snapshot fallback).

**Public redaction:** Contact Email and Outreach Draft are stripped server-side before any response, and
the snapshot inside the deployment bundle is pre-redacted at build time (belt + braces — verified the
bundle path also 404s). Full contact data remains in the local and baked versions only.

`helpers.js` getData now serves three modes with one accessor: baked `__DATA__` file / hosted `/api/data`
/ local dev `/api/<kind>`. Avatars unified behind an `AVATARS` manifest (data URIs when baked, static
`/avatars/*.jpg` when hosted, proxy in local dev). Deploys via `cd dashboard && npx vercel deploy --prod`;
re-run `make_static.py` after a new ingest.

## 2026-07-10 — Inspiration becomes a playable, relevance-gated video wall

Doug watched the first videos and caught the flaw: raw view-count ranking let off-topic virals (protein
posts, sponsored phone content) onto the wall. Rebuilt `compute_inspiration` around three rules:
1. **Relevance gate (hard):** caption+hashtags must match the reselling/secondhand-fashion vocabulary or
   the video does not enter, regardless of views.
2. **Recency:** nothing older than 18 months; ≤90-day-old videos get a ranking boost.
3. **Ranked by overperformance:** score = √(views ÷ creator's own median views) × log(views) × recency —
   surfaces repeatable techniques, not big accounts. Max 3 videos per creator for diversity. The ×N
   multiple is shown on each card ("×286 their usual").

**Playable in-platform:** TikTok-only wall (natively embeddable; the YouTube "links" field holds
description links, not the post's own video — unusable). Click a card → in-page modal with the TikTok
embed playing; Esc/scrim/✕ closes and stops playback. Verified locally (video played in the modal) and on
production: 24/24 embeddable, 0 irrelevant, dates 2025-04 → 2026-07. Deployed.
