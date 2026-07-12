# Content Brain — Architecture

## Design principles

1. **LLM for judgment, code for money.** Claude writes profiles, briefs, and insight
   narratives. Deterministic Python computes CAC, activation %, and budget splits. A model
   never allocates spend; a human never writes 300 briefs.
2. **Everything flows through the segment.** The atomic unit of strategy is a segment
   (tier × channel × geo × niche × lifecycle). Insights are learned per segment, budgets are
   allocated per segment, campaigns are launched per segment — briefs are the only
   per-creator artifact.
3. **Closed loop by construction.** A brief is not "sent and forgotten": it records its
   predictions (expected format/hook performance), the post records actuals, and the delta is
   what the feedback agent learns from.

## Data model (`content_brain/models.py`)

| Entity | Key fields | Notes |
|---|---|---|
| `Creator` | id, handle, tier (nano→mega), channel, geo (UK/FR), niche, lifecycle, follower count, join date, gifting cost, incentive rate | Lifecycle is derived: `new`, `active`, `at_risk` (no post 30–60d), `dormant` (60d+), `core` (top decile by buyers) |
| `Post` | creator id, date, format, hook type, views, clicks, signups, first orders, revenue, spend | The funnel: views → clicks → signups → first orders. Spend = gifting amortisation + incentives |
| `PartnerProfile` | strengths, best formats/hooks, audience-ICP fit, recommended ask, risk flags, one-line "how to work with them" | **LLM-generated**, cached, refreshed when new posts land |
| `Brief` | objective, 3 content ideas, hooks (3 options), format, talking points, thumbnail direction, CTA stack, example captions, posting schedule, do's, don'ts, **do-not-mention list**, reference examples, success target | **LLM-generated** from profile + segment insights + campaign spec + real post evidence |
| `BriefEvidence` | the creator's Airtable record, their scraped posts and hashtags, the wiki's trend pack, any live Fleek referral code found in their own captions | Deterministic (`evidence.py`). Carries its own provenance rules into the prompt |
| `SegmentInsight` | segment key, what worked, what didn't, recommended play, confidence | LLM narrative over deterministic aggregates |
| `BudgetPlan` | per-segment allocation, test budgets, caps, kill/scale calls | Deterministic |

## The agents

### 1. Partner Profiler (`profiler.py`)
**Input:** creator record + last 90 days of posts + segment benchmarks.
**Output (structured):** `PartnerProfile`.
**Why an agent:** the judgment call — "this creator's audience skews hobbyist-reseller, her
storytime hooks outperform tutorials 2:1, she goes quiet when briefs feel corporate" — is
pattern recognition over messy evidence, exactly what an LLM is for. The profile is the
persistent memory that makes the *next* brief better than the last.

### 2. Brief Generator (`brief_generator.py`)
**Input:** `PartnerProfile` + current `SegmentInsight`s + campaign spec (objective, offer,
geo/language, deadline) +, for real creators, a `BriefEvidence` bundle (`evidence.py`).
**Output (structured):** `Brief` — the JD's field list (hook, format, full CTA stack, do's
and don'ts, reference examples) plus three content ideas, talking points, thumbnail
direction, example captions, posting schedule, and a **do-not-mention list**.
**Personalisation levers:** the creator's own best past post is cited as reference #1;
hooks are written in the creator's register; the CTA stack carries their unique code; French
creators get French briefs.

**Two input paths, because the evidence genuinely differs.** Synthetic roster creators have
a full attribution funnel; real French prospects have posts and no attribution at all.
Forcing the second through the first would mean synthesising `first_orders=0` for every
post — which a model reads as *"this creator never converts"* rather than *"we have never
measured them."* Hence `build_profile_from_evidence` alongside `build_profile`.

**The evidence bundle states what it does not know.** Captions are not transcripts. Fleek's
named top partners are archetypes, not an asset library. A creator with no Fleek history has
no conversion numbers, and the prompt says so rather than letting the model invent them.
This is the same standard the wiki holds itself to: kept honest, not laundered.

**Codes are found, not minted.** `evidence.py` scans a creator's own captions for a live
`RFD-` Fleek code. If one is there, the creator is an inherited partner regardless of what
the Airtable `Stage` column claims, the brief reuses their real code, and the lifecycle
flips to `dormant` (re-activation). This is how the engine found Julia Courcelle carrying
`RFD-JULIA` in 25 of 25 videos while the CRM had her as *"Prospect / Not started"*.
**Evidence beats the CRM.**

### 2b. Brief job (`scripts/run_brief_job.py`)
Polls Airtable for `Stage = Onboarded AND Brief = ""`, generates, writes the brief back to
the record, and publishes a shareable Notion page (`notion_publish.py`) — the link the
creator actually opens, because the record is Fleek's and the page is theirs.

Idempotent by construction: it only touches records with an empty `Brief`, so recovery is
just re-running. Capped at 25 Claude calls per run — a runaway loop must not be able to bill
the whole roster. If Notion fails, the brief is still written to Airtable and the failure is
reported; delivery degrades, the work is never lost.

### 3. Feedback Loop (`feedback.py`)
**Input:** cycle's posts joined to their briefs, aggregated per segment (deterministic), plus
brief-adherence signal.
**Output:** `SegmentInsight`s — "codify what works into the system." These are stored and
injected into the next cycle's brief-generation context, and the deterministic aggregates
update creator lifecycles (active/at-risk/dormant transitions) and CAC tables.

### 4. Budget engine (`budget.py`) — deterministic
Weekly reallocation: rank segments by blended CAC (with a volume-confidence penalty so a
lucky 2-post segment doesn't eat the budget), apply floor/cap rules, ring-fence a test budget
(default 20%) for under-observed segments, flag kill candidates (CAC > threshold with
sufficient volume). This is the "trading desk" from the JD.

### 5. Activation targeting (`activation.py`) — deterministic
Computes the headline metric (% posting this month) and produces the target list for the next
cycle: due-for-brief actives, at-risk saves, dormant re-activation batch, new-recruit
onboarding.

## Claude API usage (`llm.py`)

- Model: `claude-opus-4-8`, adaptive thinking, structured outputs via `client.messages.parse`
  with Pydantic schemas — briefs come back as validated objects, no JSON parsing.
- **Prompt caching, with the catch stated.** The cached prefix is the system prompt (Fleek
  context, ICP definition, style guide) **plus the cycle's shared context** — the FR trend
  pack and Fleek's partner archetypes. Per-creator evidence goes after the breakpoint, so it
  never invalidates the prefix. At 300 briefs/cycle the prefix is most of the token bill.

  The catch: **Opus 4.8 will not cache a prefix shorter than 4096 tokens.** Below that,
  `cache_control` is silently ignored — no error, `cache_creation_input_tokens: 0`. The bare
  system prompt is ~250 tokens, so marking *it alone* would have cached nothing while looking
  like it did. Passing the trend pack as `cached_context` is what carries the prefix over the
  line. `llm.cache_report()` prints the actual outcome (hit / write / miss-under-minimum), so
  the saving is measured rather than asserted. Trimming the trend pack "to save tokens" would
  lose every cache hit and make each brief *more* expensive.
- **Batch API for scale:** generating briefs for the whole roster is not latency-sensitive —
  the Message Batches API runs it at 50% cost. The prototype runs sequentially for clarity;
  the production path is batching (noted in code).
- **Mock mode:** with no API key, agents return deterministic template outputs so the whole
  loop is runnable and testable offline.

## What I'd build next (talk track)

1. **Adherence scoring** — did the post actually use the briefed hook/format/CTA? (Vision +
   transcript analysis of the post itself.) Separates "brief was wrong" from "brief was ignored".
2. **Outreach agent** — drafts the personalised send (email/DM) that wraps the brief, with
   re-activation variants; human approves, system sends and schedules the follow-up.
3. **Auto-refresh cadence** — profiles refresh on new-post events, not on a cron; briefs
   regenerate when a segment insight materially changes.
4. **French-first market pack** — FR-language briefs, FR reference library, FR Discord tie-ins
   (France is the flagship community market).
5. **Attribution hardening** — code + link + post-purchase survey triangulation, so weekly
   reallocation runs on numbers the finance team trusts.
