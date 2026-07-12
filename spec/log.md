# Spec — Log

Dated record of design intent changing. Newest first. Decisions with reasoning get their own page in
`spec/decisions/`; this is the running thread.

---


## 2026-07-10 (later still) — Outreach goes live-shaped: qualification is the trigger, messages use first names

Doug's spec for taking the outreach job operational (addendum 2 on
`spec/decisions/2026-07-10-outreach-drafts.md`):

- **Trigger = human qualification.** New `--qualified` mode drafts for every
  `Stage = Qualified AND Outreach Status = Not started` creator — the exact call a scheduler makes
  once the agent is active. Scoring surfaces candidates; a human qualifies; qualification releases
  the draft. The percentile `--auto` mode is demoted to a candidate-finder.
- **Still drafts, never sends** — confirmed explicitly. Auto-send offered and declined; the permanent
  gate holds.
- **First name, never the handle, never invented.** The evidence gatherer captures the profile
  display name; the extract step derives a real given name or `null` (a shop name is not a name).
  Verified live: `Alicia 🌙 → Salut Alicia`; `CODE DES GRANDS ✦ Friperies → null`, opened on content.

Run manually this week; the autonomy layer only changes who presses enter.

**Message content refined (same day):** the draft was over-indexing on the grading-pain wound. It now
works from a **value palette** — direct global supply (2,000+ suppliers/100+ countries), de-risked
buying (Make an Offer / ~10-piece MOQ / 30-day BNPL), grading trust (Fleek Sort + Buyer Protection),
the human relationship, and buy-and-earn — picking what fits each creator's niche, led by the
observation. Every figure is wiki-sourced (`Fleek Company Profile.md`); "competitive pricing" was
deliberately not written as a superiority claim. Factual discipline is a hard prompt rule: palette
facts only, everything else → `human_check`. It immediately caught a perfume-wholesaler qualified for
a clothing marketplace and flagged the mismatch. (Addendum 3 on the decision record.)

## 2026-07-10 (later) — Doug's review: the bar becomes a percentile; known partners flagged, not excluded

Doug reviewed the outreach build and overturned two calls (addendum on
`spec/decisions/2026-07-10-outreach-drafts.md`):

- **Known partners stay in the pipeline, flagged.** The hard exclusion hid `@juliacourcelle` from the
  run; the flag shows her to the human with a `⚠️ VERIFY / reframe as re-activation` banner on the
  draft itself. Nothing sends, so visibility beats removal.
- **The score bar is a percentile of the roster's live distribution, not an absolute number.**
  `--auto` now defaults to the top 50% — which computes to a cutoff of exactly 62, where the
  known-good partner sits. Raising the bar is activation's job: better briefs raise scores, and the
  same percentile then selects a stronger cohort. Tiering is to be read the same way.

Also per Doug: the deck's §6 must name the two build-time pushbacks (recency as a hard gate;
multi-platform evidence) as a slide beat — human-in-the-loop at design time, not just at send.

And the scoring roadmap is now explicit intent: v1 is a stated theory, upgraded by data not opinion —
funnel outcomes re-fit the weights per cohort (a regression once volume allows, ~100+ outcomes), then
a **re-weighting agent** owns the proposal step (never silently applies), and weights become
**per-market config** — a scoping item for every new geo. Captured in the deck (§7 roadmap, §13
closing slide) and `spec/engine-architecture.md` (next-build item 6).

## 2026-07-10 — `outreach_drafts` is built, and the scoring model failed its calibration test

The fifth engine job exists: `scripts/run_outreach.py` turns an Airtable creator into a 3-touch French
outreach sequence, grounded in their own recent posts and audience comments, and writes it back as
`Outreach Status = Draft`. Nothing is sent — there is no send code path anywhere in the repo. Full
reasoning in `spec/decisions/2026-07-10-outreach-drafts.md`.

**The thing worth reading.** `mission/mission.md` said to calibrate the scoring model against Fleek's
three named top-performing partners. Doing that before writing the selector found one of them —
`@juliacrcl` — already sitting in our own roster as `@juliacourcelle`, `Stage = Prospect`,
`Outreach = Not started`, **scoring 62**. The bar this job was specced to use is 70. So: the engine
would have cold-pitched one of Fleek's best partners, *and* our own threshold rejects a creator Fleek
independently rates as top-performing. The `--min-score` default stays at 70 but is now labelled
unevidenced in `--help`; re-weighting is the follow-up, and it needs Doug to confirm the
juliacrcl ↔ juliacourcelle identity.

Related: `Stage = Qualified` and `Score >= 70` turn out to be **disjoint sets** across the 49-creator
roster (all 10 Qualified are TikTok, 52–62; all 8 at ≥70 are un-Qualified Prospects). The spec's
"drafts for newly Qualified creators" would have drafted for nobody worth drafting for. Selection is
now two explicit modes — `--handles` for hand-picked case-study creators, `--auto --min-score N` for
the score-triggered scale story.

**Also corrected:** the roster is 49 creators across three platforms (28 TikTok / 16 YouTube /
5 Instagram), not the 12 TikTok creators the commit history implies — so the evidence gatherer
(`content_brain/evidence.py`) has an adapter per platform. `deliverables/case-study-approach.md`
promised transcripts as a personalisation input on every platform; only YouTube has them, and the
claim is now accurate.

**Three bugs fixed on the way**, one of them security-relevant: `apify_run` was passing the API token
as a query param, and `requests` puts the full URL into `HTTPError` — so any actor failure printed the
token to stdout, and would have written it into GitHub Actions logs under the autonomy layer. It now
uses an `Authorization` header. `load_env` was silently finding no `.env` under git worktrees. And
YouTube comments were being dropped wholesale because they key their parent on `pageUrl`, not `url`.

**Open:** confirm `@juliacourcelle` is `@juliacrcl`, then re-weight the scoring model against all
three named partners.

## 2026-07-11 — Manual qualification is now a command (`scripts/qualify.py`)

The human approval gate becomes a first-class engine action instead of an Airtable click. `qualify.py
--list` prints the review queue; `qualify.py @handle …` approves (Prospect → Qualified) by handle,
with `--platform` to disambiguate a cross-platform handle, `--key` for an exact record, `--unqualify`
to reverse, `--dry-run` to preview. It refuses to guess an ambiguous handle, skips misses, and flags
approvals of creators the engine did *not* recommend (human override — the point of a human gate).
Scriptable, batch-capable, auditable — and the same Qualified state the outreach job consumes.
Documented in `spec/discovery-engine.md` §4.

## 2026-07-11 — Auto-qualification off: the engine recommends, a human approves

Doug's call: qualifying a creator stays a **manual approval** until the system is consistent and
predictable — *"we want to work with them,"* so approval is deliberate, not automatic. The engine now
sets a **`Recommended`** flag when a creator passes the bar; `Stage` stays `Prospect` until a human
moves it to `Qualified`, and that approval is what triggers the outreach-draft job (which still never
auto-sends — the permanent gate). Same discipline as the `CLAUDE.md` standing rule, made literal.

Changed: both `run_discovery.py` mappers write `Recommended` not `Stage=Qualified`; `Recommended`
checkbox added to the Creators schema; the 39 auto-qualified from the first run were migrated back to
`Prospect` + `Recommended` (pending approval). Airtable review surfaces are views, documented in
`spec/discovery-engine.md` §4: Review Queue (Recommended + Prospect), Qualified Roster (Stage=Qualified),
Shortlist Gallery. The engine is now explicitly a targeted Kalodata for the reseller space — it
suggests with reasons; the human curates.

## 2026-07-11 — The discovery engine went live: market-driven, both channels, into Airtable

The engine is no longer a pile of scripts — it is one market-driven machine. `run_discovery.py` reads a
**market profile** (`content_brain/markets/france.py`) for everything France-specific and runs both
channels through one enrichment path: TikTok hashtag scrape + Instagram relatedProfiles graph-walk →
free gates (lexicon · fashion-vertical · supplier · fleek-code) + a TikTok LLM read → the shortlist bar
→ Airtable upsert on Creator Key. Adding a market is now writing `markets/germany.py`, not editing the
engine. Documented in `spec/discovery-engine.md`.

**Doug's channel decisions, encoded:** Instagram and TikTok co-primary, **no fixed weight** (a guess
would bias the roster; the feedback loop learns the real split per market via `budget.py`). YouTube
**dropped from active search** — the long-form / pro-credibility channel, roadmap for the pro segment;
its 16 existing rows stay in the roster. Vinted/Depop/Whatnot are context signals, not search sources.

**The shortlist bar is deliberately comment-free:** genuine reseller AND clothing vertical AND not a
supplier. Comments enrich a profile where rich, are ignored where thin (Instagram lead-magnet comment
sections carry no audience signal) — they never decide who reaches the shortlist. This corrects the
prior session's drift, where comment-classification had become the de-facto gate.

**First live run:** 120 creators upserted, **39 Qualified** across the roster (24 TikTok, 15 Instagram),
nano→mid tier. Roster now 169. Apify ~$0.30, well within the $29 Starter cap. `@juliacrcl` correctly
holds two records (TikTok + Instagram) under the platform:handle key.

**Provenance note:** the engine code was authored by a background task that failed on network in its
sandbox (wrote nothing to Airtable). Reviewed before trusting it, smoke-tested, then run live here.

**Known gap:** the fashion-vertical gate passes on IG-only signal a cross-platform check would catch
(`@alex_yeddertcg`, a Pokémon-TCG seller, qualified at a low score — well outside the top 10). Tighten
with second-platform resolution before the final shortlist.

**Open:** strata-pick the final 10 (deliberate pro/hobbyist mix across both channels) from the 39
Qualified — the last step before the next case-study sections.

## 2026-07-10 — Instagram graph walk, second generation: 165 creators, 10 survive

Apify moved to Starter ($29/mo), the leaked token was rotated. The graph was re-walked from 20 seeds — the
three known-good plus the pro creators the first walk surfaced from `@juliacrcl` — resolving **all 147**
candidates rather than truncating. Total spend $0.38. Then three gates cut 165 to 10.

**The find: `@saw2hands`.** Bio: *"Vêtements de seconde-main et sneakers sur @whatnot — +111.000 produits
vendus."* 2,414 Instagram followers, **175** on TikTok, and 111,000 items sold on Whatnot. He is the pro
segment Fleek says it cannot reach, he is invisible to any follower floor, and no hashtag found him — Julia's
graph did, two hops out. Alongside him: `@felix_brgd` (23k, sells access to private suppliers — a competitor
for Fleek's own value proposition) and `@zozrsl` (paid Discord).

**Three gates, each added because the data demanded it:**

1. *Vertical.* The pro lexicon is vertical-agnostic — `revente`, `stock`, `marge` describe reselling anything.
   Seeding from `@cashandrepair` and `@50.grass` dragged the walk into refurbished laptops and BNPL fintech.
   `@50.grass` sells **synthetic lawn**. Fleek sells clothes.
2. *Substring matching.* `hits()` matched `"chine"` inside *ma-chine* and `"mode"` inside *mode d'emploi*, and
   had been inflating every score in the project since the first commit. Word boundaries **improved**
   calibration separation: the two known-good partners go from 4.5/6.0 to 7.0/8.0 against `@giu.cst`'s 0.5.
   Handles and URLs still match as substrings — `@felix_brgd`'s link is `resellvinted.com`.
3. *Suppliers.* Category alone missed `@laprovidencewholesale` (*"Grossiste vêtements premium"*, no category
   set), which ranked second. Bio text alone flagged `@juliacrcl`, who merely talks about her suppliers.
   Category **or** bio.

**A creator's second platform is a cheap lie detector.** `@alex_yeddertcg` passed every Instagram gate; his
TikTok bio reads *"TCG / Pokémon / En Live Lundi 20h sur eBay"*. Only 3 of 7 candidates exist on TikTok at all,
so this cohort is Instagram-native and must be classified on Instagram comments despite them costing $2.60/1k
against TikTok's $1.25/1k and carrying more spam.

**452 comments staged** across 7 creators. The audience classification cannot run: Anthropic credit is
exhausted. Apify stands at $6.20 of $29.

**Open:** top up Anthropic, re-run `classify_audience.py` with the `signal_quality` schema, then strata
selection. Four of the ten candidates have fewer than 40 comments — `@resellelitee_` has none — which is a real
limit of the method on nano creators, not a bug. They will need TikTok presence or human review.

## 2026-07-10 — The scorer was calibrated against real partners, and most of its signals were wrong

The task brief names three top-performing partners. The scorer had never seen them — it ran on guessed
archetypes while the ground truth sat two directories away in `mission/`. We scraped them, plus five French
creators from the wiki, for **$1.35 total**. Raw evidence in `data/calibration/2026-07-10T10-24-45/`.

**What the data overturned:**

- **`@juliacrcl` is French**, tags `#fleek`, and is a top-performing Fleek partner. The single most valuable
  calibration point in the project, and we had been treating all three named partners as English anchors.
- **Engagement rate does not predict fit — it inverts.** `@giu.cst`, the clearest wrong-fit in the set
  (253k followers, decor content), has the *highest* engagement at 8.1%. Followers, views-per-follower and
  posting cadence separate nothing either. Only vocabulary and audience do.
- **Posting cadence belongs to activation, not fit.** `@juliacrcl` posts once every five weeks and is a top
  partner. The old scorer's "posting consistency: 15 points" would have penalised her.
- **`creator_type` ≠ `audience_mix`.** `@nathanviall3` is a pro creator with a 55%-hobbyist audience. Fleek's
  hardest problem ("pro resellers think Fleek is for beginners") is an *audience* problem. One field hides it.
- **CAC cannot select the shortlist.** Under pure revenue share it ranks the two worst creators best (it
  reduces to `commission × AOV`). With a flat fee it ranks `@behindthesale` fourth, because CAC is
  reach-weighted and his reach is 2,644 median views. Both results in `spec/cac-model.md` §4.

**Four hypotheses tested and rejected**, all recorded in `spec/discovery-scoring.md` §7: a keyword pro:consumer
ratio (scored `@giu.cst` 9.5× pro; the blind model said 0%); supply-side hashtags (`#grossiste` returns
wholesalers, not creators); `#achatrevente` (generic French business jargon — returned real estate); and
same-handle-means-same-person (`@behindthesale` on Instagram is a real-estate coach with 110 followers).

**The blind test.** The audience classifier never saw which creators Fleek rates. It ranked both named partners
first and second on pro-reseller audience, and independently flagged both as Fleek-aware from comments alone —
spotting a viewer asking Julia *"vous avez des fournisseurs fiables sur Fleek ? ça me fait peur de commander."*
Fleek's trust problem, unprompted, in the wild.

**Written:** `spec/discovery-scoring.md`, `spec/cac-model.md`. **Code:** `content_brain/signals.py` (shared
lexicon), `apify_run()` (reads real cost back), Instagram actors, `scripts/calibrate.py`,
`scripts/scrape_comments.py`, `scripts/classify_audience.py`, `scripts/discover_instagram.py`. Fixed: `.env`
resolution broke inside a git worktree; every stage now persists artifacts before anything consumes them.

**Open, and blocking:** the Airtable key is still `Handle`, so no Instagram creator can be written without
overwriting a TikTok namesake. Both spec pages await Doug's sign-off before they drive the base.

### Same day, after sign-off — key migrated, Instagram wired, both budgets exhausted

**Done.** `Creator Key` (`platform:handle`) added and backfilled across all 49 existing rows; 17 new fields
created from `spec/cac-model.md` §8; `run_discovery.py` upserts on the key and no longer asks the model for
`predicted_cac_gbp`. Instagram discovery by graph walk works: seeded from `@juliacrcl`, it surfaced
`@zozrsl`, `@tikvinted_`, `@resellelitee_`, `@matthias_achatrevente`, `@whatnot_fr`, and correctly quarantined
`@united.vintage`/`@pawpickvintage`/`@vinqa.grossiste` as suppliers via Instagram's own business category.

**The Instagram finding that reshapes the plan: `audience_mix` is a property of `platform:handle`, not of a
person.** `@juliacrcl` classifies **pro_reseller on TikTok** and **general_consumer on Instagram**, same week.
Her business discourse lives on TikTok; her Instagram comments are compliments, Vinted complaints, and a
coordinated bot campaign shilling a tool called *Lbcx* (which the classifier named and excluded). Instagram is
excellent for **discovery, identity and reach** — it found the best nano pro creator we have — but TikTok
comments are the better **audience evidence**, at half the price ($1.25/1k measured vs $2.60/1k measured).
Where a creator exists on both, classify on TikTok.

**A classifier flaw, found and fixed in the schema, not yet re-run.** `@zozrsl` — bio: *"Revendeur Vinted à
plein temps (+100K€ générés)"* — came back 0% pro / general_consumer / **High** confidence. The model had read
the channel correctly (*"single-word keyword replies… engagement-farming"* — a comment-to-DM lead magnet) but
the schema forced a mix summing to 100 with no way to abstain. It now returns
`signal_quality: usable | insufficient | polluted` and `dominant: "unknown"`. **An absent audience is not a
consumer audience.** The pre-fix output is quarantined as `audience_SUPERSEDED_no_signal_quality.json`.

**Three self-inflicted bugs, all fixed:** a `--max-candidates` cap that silently dropped all 30 of
`@juliacrcl`'s graph recommendations (the only ones that mattered) because it filled on insertion order; a
supplier heuristic reading captions rather than business category, which flagged Fleek's own partner as a
wholesaler; and a comments scraper that saved only at the end, discarding four creators' paid data on a crash.
Comments now persist after every paid call, and the lost runs were recovered from Apify's datasets at no cost.

**Security.** The Apify token was passed as a `?token=` query parameter, so a 403 printed it verbatim in a
`requests` traceback. Rotated. All Apify calls now use `Authorization: Bearer` headers, which exceptions do not
echo. `content_brain/engine_io.py::_apify_headers` carries the reason.

**Both budgets are now exhausted.** Apify free tier: `Monthly usage hard limit exceeded`, $5.27 against a $5.00
cap. Anthropic: out of credit. **Correction to the entry above: the "$1.35 total" was read from each run's
`usageTotalUsd`, which under-reports** — it excludes compute units and lags at read time. Real consumption was
~4× that. Cost estimates in this repo should be treated as lower bounds until measured against
`/v2/users/me/limits`.

**Open:** re-run the audience classifier with `signal_quality` (Anthropic credit); classify the Instagram
cohort; then strata selection. Also — `data/` is gitignored, so the calibration artifacts that
`spec/discovery-scoring.md` and `spec/cac-model.md` cite as evidence are **not in the repo**. The derived
files (`features.json`, `audience.json`, `comments_normalised.json`) are small and are exactly the "AI receipts"
the brief asks for. Decision needed: commit the derived artifacts, keep the raw scrapes ignored.

## 2026-07-10 — The deck now wears Fleek's own branding

Doug reviewed the first draft ("good first draft") and called the aesthetic: follow joinfleek.com. Brand
values **measured off the live site with Playwright**, not guessed — yellow `#F8C642` (their Sign Up button),
button black `#0E0E0E`, surface grey `#F2F4F7`, Montserrat 700, 4px radii, halftone-dot motif. Details in
[`deck.md`](deck.md).

Because every colour lived in `tokens.css`, the rebrand was a token swap plus four accent edits — the
no-hardcoded-hex rule paying for itself. Montserrat is self-hosted (35KB variable woff2, OFL) so the deck
still opens from `file://` with no CDN. Yellow is graphics-only where contrast demands (text uses a dark-gold
derivative on light ground). The dot motif is title + hero only.

**Bug found by rendering the PDF, again:** in print, `.slide` was `position: static`, so the dot
pseudo-elements re-anchored to `.stage` — whose print height is the full 14-slide stack — and `height: 45%`
became a six-page dot band that blanked page 1 and tripled the file size. Fixed with `position: relative`;
the reviewer PDF re-verified page by page.

Content untouched — Doug is still building out sections; slide 6's Airtable link and the ~18-min timing cut
remain open.

---

## 2026-07-10 — The proof of how it was built is now part of the deliverable

The brief tests AI-nativeness and asks for *"the actual prompts including the failures."* The engine existed;
the evidence did not — `deliverables/evidence/` was named in the approach doc and empty. Three things landed,
in this order, because the order matters. Full reasoning:
[`decisions/2026-07-10-evidence-and-deck.md`](decisions/2026-07-10-evidence-and-deck.md).

**Preserve.** Nine sessions, 13.7 MB, 59 real prompts, in one place, outside git, and 30 days from automatic
deletion. Archived outside the working tree at `~/claude-transcript-archive/`; `cleanupPeriodDays: 365`.
Deliberately *not* `_evidence_raw/` in the repo behind a `.gitignore` line — this repo is public, and an ignore
rule prevents an accident, not a mistake.

**Secure.** `gitleaks` wired as pre-commit, pre-push and CI *before* the extractor was written. Both hooks
proved to block by planting a token. The archive audited: **zero real secrets** — every hit was a command
reading `.env`, never a value.

**Extract.** `scripts/extract_receipts.py` renders 17 curated exchanges verbatim from the raw transcripts,
redacting on the way out. Deterministic, so the pages regenerate rather than drift.

**Then the deck.** Vanilla HTML, 14 slides, dark to present and light to send —
[`deck.md`](deck.md). This **reverses the Canva decision** of 2026-07-09, per Doug the same day. The reversal
is logged on the original record, not backdated.

**Two bugs found by driving the deck rather than reading it:** `1.3cqw` sat on its own container-query
container and silently resolved against the viewport (26px type in a 1067px stage on a short, wide projector);
and the speaker notes were printing into the PDF that goes to Fleek — page 11 was instructing *them* to pause
for two seconds before speaking.

**And a stale claim, still live.** `Fleek Wiki/index.md`'s first pillar bullet still asserted *"no structured
creator program yet"* while the retraction sat fifty lines below in a `[!CAUTION]` block. Fixed.
**A correction that lives only in the footnotes is not a correction.**

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

## 2026-07-11 — Inspiration v2: thumbnail wall, hover captions, filters, per-video analysis

Doug's review round on the video wall, all landed and live:
- **Real thumbnails** — fetched via TikTok oEmbed at build time and cached as files (`dashboard/thumbs/`,
  CDN URLs expire so files are the durable form). 23/24 resolved; the gap falls back to the play tile.
  Cards are now thumbnail-first (4:5 crop) with format + ×ratio pills and views overlaid; caption is
  hidden and slides up over the image on hover. Baked file inlines thumbs as data URIs.
- **Filter toolbar** on the page, same style as the Creators toolbar: format chips (Live selling / Bale
  unboxing / Haul / Tutorial / Post), sort (best technique / overperformance / views / newest), live count.
- **Per-video analysis panel** — clicking a card opens player + breakdown side by side: views, ×ratio vs
  the creator's own median (median shown), likes, comments, shares, engagement rate, hook/caption,
  hashtags cross-referenced with roster-wide usage from the trends data, and a plain-words "why it's on
  the wall". This panel is the brief generator's citation surface.
- **Honesty notes, stated on-screen and to Doug:** average watch time is not public data — it exists only
  in the creator's own analytics (TikTok shares it via the Creator/Business API only for accounts that
  authorize us; once creators onboard as partners, that unlocks). Comment *text* is scrapeable — add
  comments to the next Apify ingest and the analysis panel can carry comment themes.
- **YouTube on the wall:** blocked only by missing video IDs — the current ingest kept description links,
  not the post's own URL. Two unlocks: re-run ingest keeping the url field, or add a free
  YOUTUBE_API_KEY to .env and a build step recovers IDs by title match. Renderer is platform-agnostic
  and ready either way.

## 2026-07-11 — Inspiration v3: Fleek's own videos + Instagram, source filter

One-time ingest (scripted, reproducible: `scripts/ingest_instagram_fleek.py`): Apify Instagram scrape of
the 5 roster IG creators + 2 bio-detected IG handles + @joinfleek, and a TikTok scrape of @joinfleek —
106 IG videos (thumbnails cached at ingest; IG CDN URLs expire in days) and 60 Fleek TikTok posts into
`Fleek Wiki/_raw/` (immutable, dated 2026-07-11). `load_posts` now globs all apify_* post files, so
future ingests join the pool automatically, and handles both TikTok scraper output generations.

The wall is now 36 videos: **24 community + 12 of Fleek's own** (their accounts skip the vocabulary gate —
their content is Fleek by definition — but keep recency + overperformance ranking). A segmented
**All / 🌟 Fleek / Community** filter heads the toolbar; Fleek cards wear a gold badge. Fleek's own top
performers turn out to be partner success stories and sourcing guides (×95–×99 their median) — exactly
the affiliate-education formats briefs should reference. Instagram reels play in the same in-page modal
(`/p/<shortcode>/embed/`) with the full analysis panel. Verified locally and live: 36/36 thumbnails,
filter counts correct, IG embed loads. Baked file now 20.5 MB (thumbs inline) — heavy but functional.

## 2026-07-12 — Manual qualification: the human gate on the discovery engine

The discovery engine surfaces & scores creators, upserting them as **Prospect** keyed on **Handle**
(`scripts/run_discovery.py:84,155`). This adds the missing half — a **human qualifies** Prospect→Qualified
from the dashboard, matching the mission's permanent rule *"the engine proposes, humans approve."*

- **Where:** the creator drawer. A qualify block under the handle shows the funnel stage, a green
  **✓ Qualify partner** button for prospects (**↩ Move back to Prospect** once qualified — fully reversible),
  and the engine's judgment inline: *"Engine-recommended · fit score N"* at/above the recommend line (60),
  or an amber *"⚠ below the recommend line — qualifying is an override"* below it. Overrides are allowed but
  flagged, in the UI and the API response, so going against the score is a visible decision.
- **Backend:** `set_stage(handle, stage)` in `serve.py` — keyed on Handle (the engine's own identity),
  restricted to Prospect↔Qualified only (no arbitrary stage jumps from the UI), writes one Airtable PATCH.
  Local dev (`/api/qualify` in `serve.py`) is ungated — it's Doug's machine. The public deployment
  (`dashboard/api/qualify.py`) is **disabled by default** and only writes when `QUALIFY_TOKEN` is set in the
  Vercel env and sent as an `X-Qualify-Token` header (browser stores it in localStorage, prompts once).
- **Card motion:** optimistic — on success the card moves funnel sections live and a toast confirms; the
  write is already persisted (verified: qualified @juliacrcl → Airtable showed Qualified → reversed → back
  to Prospect, data restored).
- **Read-only export:** the baked single-file dashboard shows the stage + "qualify on the live dashboard"
  note instead of a button (no server to write to).

**Deploy note:** enabling qualification on the production URL is a deliberate act — it needs `QUALIFY_TOKEN`
set in Vercel (outward-facing write to real Airtable from a public page), so that's Doug's call, not baked in.

## 2026-07-12 — Refactor: serve.py split into pipeline.py + serve.py

The qualify feature pushed `serve.py` to 557 lines, over the 500-line limit. Split along the natural seam:
`pipeline.py` (474) holds all data + compute — Airtable IO, enrichment, trends/funnel/inspiration,
avatars/thumbnails, `set_stage`. `serve.py` (100) is now just the HTTP `Handler` + `main`, importing what it
serves from pipeline. No cycle (pipeline never imports serve). The four importers (`api/data.py`,
`api/qualify.py`, `build_html.py`, `make_static.py`) now import from `pipeline`. Verified: all six files
compile, all GET endpoints 200 (169 creators, 36 inspiration), qualify drawer renders end-to-end.

## 2026-07-12 — Qualification: removed the token gate (it's a prototype)

Reversed the earlier QUALIFY_TOKEN protection. Qualifying only flips a creator's Stage label
Prospect↔Qualified — it never contacts anyone (outreach is a separate, draft-only step). For a
case-study prototype on a demo base, a reversible status change doesn't warrant an auth wall, and the
token prompt was friction in the live demo. `dashboard/api/qualify.py` now writes on any POST; the browser
prompt is gone from `app.js`. QUALIFY_TOKEN removed from Vercel env and `.env`. If this ever becomes a real
internal tool, a proper login goes back in — not a shared token.
