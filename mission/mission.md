# Mission

> [!CAUTION] **AWAITING SIGN-OFF.** Every claim below is *inferred* from `deliverables/strategy.md` and
> `deliverables/case-study-approach.md`, which paraphrase the JD and task brief. Neither source document has
> been captured yet. Once `job-description.md` and `task-brief.md` are populated, this page gets rewritten
> against them, contradictions get resolved in the source's favour, and this banner comes off.

**Role:** Influencer Marketing Manager, Fleek
**Artefact:** a case study, presented live (~20 min), backed by a working engine
**Date:** presentation TBC · this file last checked 2026-07-09

## What we are building

Not a campaign. An **engine** — the system Fleek would use to find, qualify, recruit, activate and learn from
creator partners at a scale one operator could never reach by hand.

The line the room should leave with:

> They should not think *"Doug found 10 French influencers."*
> They should think: *"Doug built the operating system we'd use to find 10,000 creators."*

## How we are judged

Everything here is downstream of one number that the JD names as the headline metric:

**# and % of partners posting each month.**

Not reach. Not follower count. Not creators signed. Activation. Every design decision in this repo — the
scoring weights, the personalised briefs, the feedback loop, the budget reallocation — exists to move that
number, and should be defensible in those terms.

The supporting economics: **channel CAC, payback period, first-order AOV**, segmented by tier (mega→nano),
channel (TikTok / YouTube / Instagram), geo (UK / FR), niche and lifecycle.

## The three commitments

**1 — Activation over recruitment.** Fleek has a 1,000+ creator roster and (assume) ~25% posting monthly.
Each 5-point gain in activation is ~50 more posting partners a month, on creators whose acquisition cost is
already sunk. That beats any plausible recruitment win in the same window, and it's cheaper. Recruitment is a
supporting motion — quality over headcount.

**2 — LLMs for judgment, deterministic code for money.** Models write profiles, briefs and narrative
insight, at a scale no human can. Code computes CAC, allocates budget, and measures attribution. Never let a
model allocate spend; never ask a human to write 300 briefs. This division is worth saying out loud in the
room — it's the line that separates an operator from someone who has heard of AI.

**3 — The engine proposes, humans approve.** Outreach drafts, never auto-sends. Contracts are signed by
people. Briefs are approved before they ship. The human gates are permanent, and they double as the audit
trail.

## What "done" looks like

| Deliverable | Priority | Where |
|---|---|---|
| The deck (12–15 slides + appendix), built in Canva | P0 | external |
| The Airtable creator ecosystem — one base, three views | P0 | external |
| The live demo — this repo, run in a terminal | P0 | `run_campaign.py` |
| In-deck video clips where live isn't practical | P1 | `deliverables/evidence/` |
| Appendix: full transcripts, failed prompts, scoring rubric | P1 | `deliverables/` |

Every AI claim in the deck carries a visible **input and output**. No "trust me, AI did it." The shot-list
lives in `deliverables/case-study-approach.md` §11.

## Standing rule

`mission/` is **read-only to agents.** The two source documents are transcripts of what Fleek asked for. If
the work drifts from them, the work is wrong — not the brief.
