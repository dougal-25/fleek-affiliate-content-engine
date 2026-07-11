# Spec — Log

Dated record of design intent changing. Newest first. Decisions with reasoning get their own page in
`spec/decisions/`; this is the running thread.

---

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
