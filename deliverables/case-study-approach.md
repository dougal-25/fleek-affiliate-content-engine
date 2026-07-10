# Fleek Influencer Growth Task — the approach

**Date:** 2026-07-09 · **Status:** round 2 — Notion review comments folded in
**Answers:** `mission/task-brief.md` · **Judged against:** `mission/mission.md`

The case-study approach, following the same six-section chronology as the task brief. Tool stack locked up
front. Every section shows AI inputs *and* outputs, opens with a stack strip, and closes with a scale answer.

> How this document got here — the open questions from draft 1 and the round-2 review comments — is recorded
> in `spec/decisions/2026-07-09-draft-1-open-questions-resolved.md` and
> `spec/decisions/2026-07-09-round-2-notion-review.md`.

---

## 1. The story

They should not think "Doug found 10 French influencers."
They should think: **"Doug built the operating system we'd use to find 10,000 creators."**

Fleek's own vocabulary for this is the **Brain** and the **content & affiliate growth engine** — use their words. You are not presenting a campaign; you are presenting an engine that runs on a schedule with human gates.

Every section uses the same presentation formula:
1. **Section opener — mini executive summary**: the stack strip (tools used in this section + where that piece is hosted) and the prompt receipts (real input → real output)
2. The problem
3. My AI-assisted workflow
4. The system I built
5. Example output
6. **The scale answer**: how this exact step runs automatically at 10 → 10,000. They WILL ask "how does this scale?" at every section — the answer is pre-baked into the slide.

## 2. Deliverables — trimmed and prioritised

Draft 1 listed five deliverables flat. That's scope creep — name the demon. Priorities:

- **P0 — The deck**: 12–15 slides + appendix, built in Canva. NOT 25–30: twenty minutes is ~90 seconds a slide; 25+ means rushing your best material.
- **P0 — The Airtable creator ecosystem**: the database everything else screenshots from.
- **P0 — The live demo**: the content_brain repo, run in terminal.
- **P1 — In-deck video demos**: short clips embedded in the deck where live isn't practical (Kalodata walkthrough, agent build, terminal run). No standalone Loom backup — Doug presents live.
- **P1 — Appendix** (PDF or Notion): the ARCHIVE, not the showcase. Receipts (prompts, AI conversations, inputs → outputs) live IN the slides throughout — the appendix holds the full transcripts, failed prompts and the scoring rubric.

Deck + database + demo tell the whole story. The appendix is the archive.

## 3. Tool stack — locked from the get-go

| Stage | Tool | Why / fit with current stack |
|---|---|---|
| Research wiki | Claude Code + Perplexity API | Perplexity key already in `.env`; output filed into Fleek Wiki Obsidian vault (exists) |
| Discovery / scraping | Apify (TikTok, IG, YouTube) | Already used in WebLift pipeline; API-driven → schedulable |
| Web enrichment | Firecrawl | Key in `.env`; also scrapes link-in-bio pages for contact routes |
| Contact finding | Apollo | Fallback only — B2B data; finds emails for the subset of creators who run registered businesses. Does NOT scrape TikTok handles. Primary route: DMs + bio emails + link-in-bio via Firecrawl |
| Classification, scoring, drafting | Claude (Anthropic API) | Key in `.env`; structured outputs; already wired in `content_brain/llm.py` |
| Database + ecosystem dashboard | Airtable (free tier) | Gallery = cards, Kanban = funnel, Interface = dashboard; screenshot-ready |
| Automation / glue | Python scripts driven by Claude Code | How you already work; `content_brain` + `run_campaign.py` exist. No Make/Zapier needed for v1 |
| Briefs | `content_brain` brief generator → Notion share pages | Notion key in `.env`; shareable link per creator |
| Deck | Canva — decided | Edit flexibility, screenshots + links, embedded video clips; already in stack and MCP-connected |
| In-deck video demos | Screen recording (QuickTime / Loom) | Short clips where live isn't practical: Kalodata walkthrough, agent build, terminal demo |

> 🧠 **Apify vs Perplexity — different jobs, not rivals.** Perplexity reads the web and synthesises — perfect for building the wiki (landscape, archetypes, vocabulary, trends). It cannot return structured platform data: it can name big creators, but it can't hand you 200 French TikTok profiles with follower counts, captions, comments and posting frequency as JSON. Apify runs maintained scrapers against the platforms themselves and returns exactly that, at scale, through an API — which is also what makes it schedulable. Rule of thumb: **Perplexity teaches the engine; Apify feeds it.** And yes — a Claude Code + Perplexity agent is the simpler tool, and it's the RIGHT tool for the wiki. The shortlist just can't be built from it.

> 🏗️ **Where the engine runs:** everything is Python in one GitHub repo (fleek-affiliate-content-engine — already exists). Today it runs locally via Claude Code; autonomous = the same scripts on a scheduler (GitHub Actions or Railway cron — Railway is already in the stack). Data layer: Airtable (creators, funnel, briefs) + the wiki (markdown in the repo, edited in Obsidian, versioned on GitHub). Nothing lives only on a laptop; every piece is API-driven and schedulable.

One honest line for the interview: "I run this on Claude + Apify + Airtable glued with Python. The same architecture drops onto whatever Fleek runs internally."

## 4. Phase 0 — The Wiki (before anything else)

**Decision:** build it first, timebox to half a day. It is a means, not the deliverable.

A research agent (Claude Code + Perplexity) produces a small wiki on French/EU reselling:
- Platform landscape: Vinted, Vestiaire Collective, Leboncoin, Whatnot France, eBay FR
- Reseller archetypes and their economics (thrift flippers, wholesale buyers, live sellers, educators)
- Community vocabulary and slang (FR) — feeds search keywords and outreach tone, e.g. "friperie"
- Trends and formats currently working (sourcing-trip vlogs, live selling, "come thrift with me")
- Where resellers congregate (Discord, Facebook groups, subreddits, TikTok hashtags)

**It powers everything downstream:** discovery keywords, scoring factors, personalisation variables, brief content.

**Deck moment (1 slide):** "Before finding creators, I built the knowledge base that teaches the system what 'good' looks like." Screenshot: Obsidian graph view + one wiki page.

**AI receipts:** input = research question list → output = wiki pages. Show both.

**Showcase the agent itself (deck beat):** don't just show the wiki — show how the agent is BUILT (its definition file: role, sources, output format, where it files pages) and then a quick performance run: one research question in, a new wiki page out, live or as a short in-deck clip. That's engine-building, not tool-using.

**Where the wiki lives:** markdown files inside the GitHub repo — edited locally in Obsidian, versioned with git, pushed to GitHub. **Refresh cadence:** a weekly scheduled run where the agent re-checks trends and forums and appends a dated trends note. The wiki is a living component of the engine, not a one-off research doc.

## 5. Section 1 — Discovery engine + shortlist

**Pipeline:** wiki keywords → Apify scrapes (TikTok/IG/YouTube search) → raw creator list → Claude enrichment (is this a reseller? niche? audience? content themes?) → scoring → Airtable.

**Apify setup — show it once, then automate it:** choose the actor (TikTok Scraper) → configure the input JSON (hashtags + keywords from the wiki, geo = FR, result limit) → run via API from a Python script → JSON results → enrichment → Airtable. After the first manual run there is no UI clicking: the whole run is one API call, which is exactly what makes it schedulable as a daily/weekly job. (Apify also has an MCP server for interactive use; the engine uses the plain API.) Discovery is not "Doug searching TikTok" — it's a job the engine owns.

**Show real prompts, including the failures** (kept from draft 1 — it demonstrates iteration):
- Prompt 1 → too many fashion creators
- Prompt 2 → too many thrifters
- Prompt 3 → reseller educators found ✅

**Filtering:** score signals, not followers — wholesale mentions, selling tutorials, audience comments, posting frequency, evidence of sourcing, community engagement, business-owner signals, referral friendliness.

**Kalodata validation snippet (in this section):** before a creator makes the shortlist, their commercial reality gets checked in Kalodata — TikTok Shop GMV, revenue trend, product categories. Search → export (API where the plan allows) → validation fields on the Airtable record. One line for the room: "the scrape finds them, the enrichment reads them, Kalodata proves they actually sell." Fuller tool showcase sits in §10/appendix.

**The shortlist = Airtable Gallery view.** Each card: photo, followers, audience, strength, weakness, predicted CAC, confidence score. Screenshot for the deck; scroll it live in the demo.

**AI receipts:** Apify run screenshot (input) → enrichment JSON (output) → scored cards (system).

## 6. Section 2 — Outreach

**Per-creator personalisation pipeline** (built: `scripts/run_outreach.py`):
Creator record → recent posts (last 45d) + audience comments + transcript *(YouTube only — TikTok and IG have none)* → Claude extracts personalisation variables, each carrying a verbatim quote → Claude drafts 3 French touches → human edit → native-speaker QA → sent by a human.

**Recency is a gate.** A creator with no posts inside the window is skipped, not drafted. A stale personalisation is worse than a generic one: it proves you looked and didn't care.

**Deck moment:** split screen. Left = AI inputs (the variables extracted). Right = final French message. Highlight what the human changed. "AI translated → I localised → native speaker QA'd" shows maturity. The localisation choices are written up in `deliverables/outreach-localisation.md`.

**Emergent segments (orange note):** every creator is tagged with content keywords during enrichment. Group by tag in Airtable → segments you didn't know existed appear. Outreach angle differs per segment. Trends from the wiki keep the keyword set current.

**AI receipts:** input variables → prompt → draft → human-edited final, side by side.

**Where the human pushed back (slide beat — show this):** the human gate isn't only at send; it shaped the engine's design. Two pushbacks from Doug during the build, both of which changed the system:
1. *"The personalised touches HAVE to be recent and relevant and trending"* → recency became a **hard gate**, not a preference. A creator with no posts inside the window is skipped, not drafted — and it fired correctly on its first live run (a creator 86 days quiet was skipped rather than sent a fake "loved your recent post").
2. *"What about the Instagram scraper?"* → the evidence gatherer went **multi-platform**. The roster turned out to be 28 TikTok / 16 YouTube / 5 Instagram; a TikTok-only build would have silently skipped 21 of 49 creators. One question saved 43% of the pipeline.

This is the deck's honest answer to "where does the human stay in the loop": at design time, at review, and at send — with receipts for all three (`spec/decisions/2026-07-10-outreach-drafts.md`).

**Where this runs (stack strip for this section):** Python in the repo — Claude Code today, cron later. Drafts write back to each creator's Airtable record with Status = Draft. Nothing is machine-sent: a human reviews in Airtable, edits, sends via DM/email, flips Status = Sent. The human gate doubles as the audit trail.

## 7. Section 3 — Recruitment funnel (inside the ecosystem)

**Decision: the funnel is a VIEW of the same database, not a separate build.**
Airtable Kanban grouped by Stage: Prospect → Qualified → Contacted → Responded → Call booked → Contract → Onboarded → First post → First sale → Repeat posting.

Keep the drop-off slide: 100 prospects → 70 qualified → 40 replies → 20 calls → 15 signed → 10 activated → 7 first sales → 5 repeat posters. This is commercial thinking.

**Scoring framework — how and why (orange note):**
1. **Start from the commercial goal.** The score predicts one thing: "will this creator drive reseller signups at low CAC" — not reach, not aesthetics.
2. **Factors are chosen for signal on that outcome:** Audience relevance 30 · Reseller credibility 25 · Posting consistency 15 · Wholesale content 10 · Engagement quality 10 · Professionalism 10.
3. **Why these weights:** relevance + credibility = 55% because trust inside the reseller community is the conversion mechanism. Follower count is deliberately absent — vanity metric for this goal.
4. **Grounded in the wiki:** what "credible" looks like in FR resale comes from the knowledge base, not gut feel.
5. **Calibrated, then learning:** score the 3 known-good partners first; sanity-check the ranking. Weights are v1 hypotheses — funnel data (who actually converts) re-weights them each cohort. The feedback loop IS the "rich factoring system".

**Scoring roadmap (say this in the room):** v1 is a stated theory — six weighted factors, one
calibration point — and that's the honest pitch, not a weakness. The upgrade path is data, not
opinion: each cohort's funnel outcomes (who converted, at what CAC, by scored band) re-fit the
weights, and at ~100+ outcomes that's a regression, not a debate. Then the weighting itself becomes
an engine job: a **re-weighting agent** that reads the cohort numbers and *proposes* new weights with
a rationale — never silently applies them. And weights are **per-market**: what "credible" looks like
in FR came from the FR wiki, so every new market gets its own wiki pass, its own known-good
calibration partners, and its own weights. That's scoping item #1 for any new geo.

> 🎯 **We ran that calibration, it failed, and the failure set the bar.** `@juliacrcl`, one of the three partners Fleek names as top-performing, is in our scraped roster as `@juliacourcelle` and scores **62** — under the guessed absolute bar of 70. The model that was supposed to find creators like her rejected her. The fix isn't a better guess: **the bar is a percentile, not a number.** It's set today at the top ~50% of the roster's live score distribution — which computes to exactly 62, where the proven-good partner sits. From there, raising the bar is activation's job: better briefs → more posting → higher scores → the *same percentile* selects a stronger cohort. Tiering reads the same way — percentile bands over a distribution activation keeps pushing right, not fixed grades. Known partners found in the roster are flagged loudly on their drafts, never silently dropped, because the engine can't know who Fleek already works with — but the human gate can. (Full record: `spec/decisions/2026-07-10-outreach-drafts.md`.)

**Division of labour line (use it):** LLMs for judgment at scale; deterministic code for money and measurement.

## 8. Section 4 — Activation: the AI Brief Generator

**Where briefs live + how it scales (orange note):**
- Generated by the existing `content_brain` brief generator from the creator's Airtable record
- Written back to the record (brief field + attachment) — the ecosystem stays the source of truth
- Auto-published as a **shareable Notion page** per creator — that's the link they receive
- **Trigger:** stage changes to Onboarded → script runs. Batchable across the whole cohort. One click per creator; scales because the input is the record, not fresh human research.

**Inputs:** creator profile, audience, past videos, transcript, best Fleek creatives, referral performance, trending formats.
**Outputs:** 3 content ideas, hook, CTA, thumbnail direction, talking points, do-not-mention list, example captions, posting schedule.

**Deck moment:** Creator A gets a live-sourcing angle, Creator B an educational carousel, Creator C a day-in-my-life-reseller — same system, completely different briefs. That's AI-native, not mail-merge.

## 9. Section 5 — Budget

Framework, not guesses. Example on £10,000:
- 40% existing partners (they already trust Fleek — lowest CAC)
- 30% new recruitment
- 20% experiments
- 10% performance bonuses

**Monthly reallocation:** lowest CAC → increase spend; highest CAC → pause. Marketplace thinking.
**Say it again here:** the budget engine is deterministic code, not an LLM. Never let a model allocate money.

## 10. Section 6 — AI throughout + the demo

Tool-stack slide (table from §3). Pipeline slide: Discovery → Enrichment → Scoring → Outreach → Brief generation → Reporting — every stage AI-assisted, human gates at outreach send and contract.

### The engine on autopilot — the slide that answers every "how does this scale?"

The framework built by hand this week is the same engine on a scheduler:
- **Every Monday 06:00 — trend scrape:** a scheduled job scrapes the forums, TikTok hashtags and caption patterns the wiki flagged; Claude condenses the pull into a dated trends note appended to the wiki.
- **Trends trigger discovery:** new trend keywords automatically seed the next Apify run → new creators enriched, scored → land in Airtable as Prospects.
- **Briefs ride the trend:** top affiliates get a trend-based brief generated in the same cycle ("live sourcing hauls are spiking in FR — here's your angle this week").
- **Human gates stay:** outreach send, contract, brief approval. The engine proposes; humans approve.

It runs locally today; autonomous is the same scripts on GitHub Actions / Railway cron. That's the difference between a campaign and an engine — and it's one slide.

**The demo (replaces Replit):** terminal, your repo:
`python run_campaign.py brief CRE-0042` — profile → personalised brief in seconds. Better: run it on a real scraped French creator from the shortlist. If live isn't possible on the day, the same run goes into the deck as a short embedded clip.

## 11. Evidence pack — screenshot shot-list

Rule: every AI claim in the deck has a visible input AND output. No "trust me, AI did it."

| # | Screenshot | Captured where | Used in |
|---|---|---|---|
| 1 | Fleek Wiki graph view + a wiki page | Obsidian | Phase 0 slide |
| 2 | Prompt iterations 1→2→3 (incl. failures) | Claude / ChatGPT | Discovery |
| 3 | Apify scrape run with result count | Apify console | Discovery |
| 4 | Enrichment output (structured JSON for one creator) | Terminal / Claude | Discovery |
| 5 | Airtable Gallery — creator cards | Airtable | Shortlist |
| 6 | Airtable Kanban — funnel stages | Airtable | Funnel |
| 7 | Airtable grid — scores + formula | Airtable | Qualification |
| 8 | Split-screen outreach: variables vs final FR message | Deck-built | Outreach |
| 9 | Brief: input record → generated Notion brief page | Notion | Activation |
| 10 | Budget reallocation table | Sheet/deck | Budget |
| 11 | Terminal demo run (also captured as an in-deck clip) | Terminal | Demo |
| 12 | wiki agent build + quick performance run (short clip) | Claude Code | Phase 0 |
| 13 | Kalodata creator/revenue validation (short clip) | Kalodata | Qualification |

## 12. Build timeline

- **Day 1:** Wiki (half day) · Apify discovery scrape · Airtable base up · first enrichment pass
- **Day 2:** Scoring + shortlist locked · outreach drafts (FR) · emergent-segment tags
- **Day 3:** Briefs generated (3 contrasting creators) · budget framework · funnel populated with drop-off numbers
- **Day 4:** Canva deck build · demo rehearsal · record in-deck demo clips (Kalodata, agent run, terminal) · appendix

## 13. Closing slide — "If I had six months"

Keep from draft 1: continuous AI discovery + scoring · automated enrichment · AI outreach with human approval · CRM pipeline with activation tracking · personalised brief generation per creator style · performance dashboard reallocating budget to lowest-CAC creators · a re-weighting agent that re-fits the scoring weights from each cohort's funnel data, per market. You're designing the infrastructure Fleek would actually build.

---

## Open items for Doug

1. ~~Deck tool~~ → **DECIDED: Canva** (edit flexibility, screenshots + links, embedded clips; in stack + MCP-connected).
2. Shortlist creators: real scraped French creators (recommended — receipts are real) vs illustrative profiles?
3. Custom dashboard stretch goal: only if Days 1–3 land early. Airtable Interfaces is the v1 answer.
