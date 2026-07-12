# 2026-07-10 — The evidence pipeline, and the deck that presents it

Fleek's brief tests one thing above all: *"how natively you work with AI… Show the tools, the actual prompts
**including the failures**."* The engine existed. The proof of how it was built did not —
`deliverables/evidence/` had been named in the approach doc and left empty.

## What was decided

**1. The raw transcripts never enter this repo.**
Nine Claude Code sessions (13.7 MB, 59 real prompts, 684 tool calls) held the entire evidentiary record, in
one place, outside git, and — with `cleanupPeriodDays` unset — scheduled for deletion around 2026-08-08.

They are now archived at `~/claude-transcript-archive/fleek-2026-07-10/` (mode 700), and
`cleanupPeriodDays: 365` stops the clock. They are deliberately **outside the working tree**. The first
instinct was `_evidence_raw/` inside the repo with a `.gitignore` entry; that was wrong. This repo is public,
and a gitignore line prevents an accident, not a mistake. Keeping unscrubbed material out of the tree removes
the risk class instead of guarding it. `.githooks/pre-commit` refuses `_evidence_raw/` even under `git add -f`,
as a backstop.

**2. The security gate was built before the extractor, not after.**
`gitleaks` was installed but nothing invoked it. Now: `.gitleaks.toml` (defaults plus Apify, Perplexity,
Airtable and Firecrawl token shapes), pre-commit and pre-push hooks via `core.hooksPath`, and CI on push and
PR. Both hooks were tested against a planted token and a forced `_evidence_raw/` add; both rejected, HEAD
unmoved.

*Amended 2026-07-10:* pre-push originally scanned **full history** on every push. That took ~11 minutes here
(a 20MB dashboard export lives on a sibling branch, and re-walking the whole ancestry is pathological), which
read as a hang. Pre-push now scans only `origin/main..HEAD` — the commits actually being pushed (~0.2s) — and
**full-history scanning is CI's job**, where it has a time budget on GitHub's machines. The range scan was
re-verified to still reject a planted token.

The archive was then audited before a byte was processed. **Zero real secrets.** Every hit was a *command*
reading `.env` (`grep '^APIFY_API_TOKEN' … | cut -d= -f2`), never a value. The one high-entropy token in the
corpus turned out to be a broken wikilink slug.

**3. The receipts are generated, never written.**
`scripts/extract_receipts.py` reads the archive against `deliverables/evidence/manifest.json` — 17 curated
exchanges out of 59 — redacts every credential on the way out, and renders six pages. It is deterministic:
two runs produce byte-identical output. So the evidence is regenerated from source and cannot drift, and
`so_what` is the only prose written after the fact. Every quote is verbatim, with the timestamp it was typed
at. Four were checked byte-for-byte against the raw JSONL.

If the prompts were rewritten afterwards they would read better. They would also be worthless as evidence.

**4. The deck is vanilla HTML in the repo.** This reverses the Canva decision in
[2026-07-09-round-2-notion-review.md](2026-07-09-round-2-notion-review.md), per Doug at 2026-07-09 16:32. The
reversal is logged there rather than backdated. Design intent: [../deck.md](../deck.md).

14 slides, not 25 — twenty minutes is ~90 seconds a slide. Dark to present, light to send. Sections 1–5 map
to the brief's five parts; slide 11 is the hero.

**5. Simulated data is labelled, everywhere.** The 1,000-creator roster, 39.3% activation and £25.53 CAC come
from `run_campaign.py generate-data`. They carry a `simulated` badge on every slide. What is real — 49 scored
FR creators, 588 ingested posts, 12 discovered via Apify, hashtags validated against real post data — is
badged `real`. Presenting simulation as measurement is the same failure mode as the claim below, and it is the
one thing that would actually lose the room.

## What this surfaced

**The retraction had reached the footnote but not the headline.** `Fleek Wiki/index.md` was revised on
2026-07-10 with a `[!CAUTION]` block explaining that *"Fleek has no structured creator program"* is false. But
its **first pillar bullet** — the first line any reader meets — still asserted it, alongside the superseded
`$45M` figure. Fixed. Logged in `Fleek Wiki/log.md`.

The method lesson generalises: **when a claim is retracted, grep for every place it was asserted, not just the
page where it was argued.** Summaries, indexes, deck outlines and strategy docs all repeat headline claims.
Retracting one instance is not retracting the claim.

## The thing worth defending in the room

The deck's thesis is not *"I used AI."* It is *"I knew when to distrust it."*

At `2026-07-09T22:17`, nine hours into the build, Doug stopped and asked whether the model had read the brief.
It answered, in its own words, that it had not. Supplying the real JD immediately falsified two load-bearing
claims — one of which the JD contradicts outright, and which, said aloud in the interview, would have been
unrecoverable.

That exchange is on slide 11, verbatim, with its timestamp.
