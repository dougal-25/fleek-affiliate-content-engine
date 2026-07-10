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
