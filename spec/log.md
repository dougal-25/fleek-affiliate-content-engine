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
