# Score dashboard — one framework, every creator — UI + scoring spec

**Status:** ✅ built and verified 2026-07-18. Signed off, merged to main.
**Problem:** the dashboard shows three different scoring schemes, and the detail panel is inconsistent
creator-to-creator and too wordy. **Goal:** one universal score framework, computed identically for every
creator, shown identically on every panel.

## The framing (UI-change protocol)

- **References:** the deck slide "The score predicts one thing: will their audience buy stock" (the 4-pillar
  FIT rubric) + the existing dark dashboard.
- **Mood/feel:** unchanged — matches the existing dashboard (dark, `tokens.css`, Montserrat, coral/gold/plum).
- **Hero moment:** the **4-pillar score breakdown** — one glance tells you *why* a creator scores what they
  score, and it's the same four bars for everyone.
- **Anti-examples:** the current panel — wordy paragraphs, sections that appear for some creators and vanish
  for others.
- **Constraints:** desktop dashboard; reuse `dashboard/tokens.css` (no new hardcoded colours); the score must
  be deterministic (code, not model).

## Why the panels disagree today (root cause, confirmed)

- **Three scoring schemes in play:** the live 4-factor `compute_fit` (credibility 40 / audience 30 /
  wholesale 20 / prof 10), a legacy **6-factor** breakdown baked into the snapshot data (30/25/15/10/10/10),
  and the **FIT rubric** (spec §5, 50/20/20/10) which is *designed but never wired*.
- The dashboard renders the **legacy 6-factor** string, and its "Score breakdown" section only appears when
  that string carries `/max` denominators — **36 of 49 creators have them, 13 don't**, so the section
  silently vanishes for those 13. That is the inconsistency, and it is a data-format accident, not two kinds
  of creator.

## The universal framework — the 4 pillars (the deck's FIT rubric, finally wired)

The score predicts **one** thing: *will this creator's audience buy stock at low CAC.* The customer is the
**viewer**, not the creator — so audience is half the score.

| Pillar | Weight | Measures | Computed from |
|---|---|---|---|
| **Audience quality** | 50 | Will the *viewers* buy stock? | `_audience_tags` → bucket weights (below) |
| **Sourcing intent** | 20 | Do they talk sourcing, kilos, margins? | `signals.lexicon_profile` over their text |
| **Creator credibility** | 20 | Do they *demonstrably* resell? (Whatnot/Discord/coaching) | `signals` credibility flags + pro-ratio |
| **Fleek warmth** | 10 | Already mention Fleek / carry an RFD- code? | `signals.fleek_signals` |

Follower count scores **nothing** — reach is not the signal (mission: *trust > reach*). Confidence is a
**gate, not points**. Weights are v1 and re-fit from funnel outcomes per cohort (see
`discovery-scoring.md §9.5`).

### Audience quality — the tag → bucket map (v1, tunable)

We have audience *tags*, not percentages, so v1 weights the tags a creator carries (a documented proxy for
the deck's `50 × (pro% + 0.8·hobbyist%)`). Score = `50 × mean(weight of each tag)`.

| Bucket | Weight | Tags |
|---|---|---|
| **Pro reseller** | 1.0 | wholesale buyers |
| **Hobbyist reseller** | 0.8 | aspiring resellers · bargain hunters · live-shopping viewers · sneakerheads |
| **General consumer** | 0.0 | vintage lovers · eco-conscious shoppers · luxury-resale shoppers · fashion-inspo seekers · general fashion audience |

This table is the one judgment call in the score; it lives here so it can be argued with and tuned, not
buried in code.

## Where it's computed — `dashboard/pipeline.py enrich()`

`enrich()` is the **single path** both the live Airtable pull and the static snapshot flow through. Adding
`compute_fit(fields)` there means every creator — live or snapshot — gets the same four pillars, computed the
same way, with no dependence on the stale Airtable `Score`/`Score Breakdown`. Consistency becomes structural,
not something the front-end has to defend against.

Output attached to each creator as `_fit`:
```
_fit = {
  "total": int 0-100,
  "pillars": [ {"key","label","got","max"} x4 ],   # always all four, in weight order
  "audience_mix": {"pro": n, "hobbyist": n, "consumer": n},  # for the Type badge + pills
}
```

The legacy `Score` / `Score Breakdown` fields are no longer read by the dashboard. `app.js`'s `subScore`
regex (which scraped creator-type out of the old string) is replaced by `_fit.audience_mix`.

## The panel redesign (Doug's decisions, 2026-07-18)

Every panel, same sections, same order — no conditional disappearing:

1. Header (avatar + @handle)
2. Qualify gate (unchanged)
3. Contact line (unchanged)
4. **Score** — the ring total **= `_fit.total`** (retire the old number), with the **4-pillar breakdown**
   bars beneath it. Shown for **every** creator.
5. Facts `<dl>` — Platform · Followers · Niche · Funnel stage · Predicted CAC · Confidence · Source
6. **Audience** — coloured **pills** by bucket: Pro = green (`--ok`), Hobbyist = gold (`--fleek-gold`),
   Consumer = grey (`--ink-3`). (Replaces the "Audience type" text row + the "Audience & bio" paragraph.)
7. **Keywords** — pills (from `Content Keywords`).
8. **Risk** — *one* coral pill, only when `Weakness` flags a real risk (e.g. competitor promotion). No row
   when clean.

**Cut:** the prose **"Why they fit"** (the 4 pillars *are* the quantified why) and **"Watch out"** paragraph
(compressed to the single risk pill). **Bio** paragraph folds away — the pills carry the audience signal.

## Decisions taken (Doug, 2026-07-18)

1. Cut "Why they fit" + "Watch out" prose; keep one risk pill.
2. Audience quality from existing tags now (deterministic, zero-cost, labelled v1); upgrade to comment-based
   `classify_audience` percentages later.
3. Ring total **and** breakdown both become the FIT — one number, one scheme, they always agree.

## Build order

1. `dashboard/pipeline.py` — `compute_fit()` + attach `_fit` in `enrich()` (reuses `content_brain/signals.py`).
2. Regenerate the committed snapshot (`make_static.py`) so it carries `_fit`.
3. `dashboard/app.js` — render `_fit` (ring + 4 bars), audience/keyword/risk pills; delete the
   `parseBreakdown`/`subScore` legacy paths and the two prose sections.
4. `dashboard/style.css` — pill colour classes from tokens; keep the existing bar styling.
5. Screenshot-verify two contrasting creators (a pro-audience one and a consumer-audience one) look identical
   in structure. Then update `discovery-scoring.md` (FIT is now wired) + `spec/log.md`.

## Build notes (2026-07-18)

- Scoring lives in `dashboard/pipeline.py` (`compute_fit` + `risk_flag`), computed in `enrich()` — the one
  path both live Airtable and the static snapshot flow through, so every creator gets `_fit` identically.
  Kept **stdlib-only** (didn't import `content_brain/signals.py`) so the Vercel serverless bundle is
  unaffected; the lexicons are inlined, mirroring the existing `AUDIENCE_RULES`.
- Text pillars score the creator's **own** signals (Content Keywords / Audience / Notes / Segment), never our
  `Strength`/`Weakness` prose — scoring our own justification would be circular, and "Fleek" appears in nearly
  every Strength line (it falsely maxed warmth on the first pass; fixed).
- Warmth is 0 across the current 49 snapshot creators — they're discovered *prospects*, not existing Fleek
  affiliates, so none carry a code in their own text. Correct, not a bug; the mechanism fires when a code is
  present.
- `app.js`: `Score` is overwritten with `_fit.total` at load so ring/sort/avg-stat all agree; the legacy
  `subScore`/`parseBreakdown` paths are deleted; drawer renders `_fit.pillars` + audience/keyword/risk pills.
- Bars recoloured gold (`--fleek-gold`) — they're the hero element and red read as an alarm.
- Verified in-browser: high-fit (@felixbeauregard 73) and low-fit (@lesbonnesappes 30) render an **identical**
  five-section panel. No console errors. Live Airtable path (169 creators) computes `_fit` on read.

## Verification

- Every one of the 49 creators renders all four pillar bars (no missing "Score breakdown").
- `@behindthesale`/`@juliacrcl` (if present) land high; a vintage-lover-audience creator scores low on
  Audience quality — the ring and bars agree.
- Backend: `python -c "from dashboard.pipeline import compute_fit"` sums correctly; snapshot regenerates.
- **Doug eyeballs a screenshot before this is called done** (backend smoke tests don't catch CSS/DOM).
