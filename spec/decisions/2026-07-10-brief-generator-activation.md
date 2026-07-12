# 2026-07-10 — Section 4 built: the brief generator, on real creators

Section 4 of the deck existed as prose before the engine could do what the prose claimed. This closes
that gap. Four decisions worth recording, and three claims that had to be corrected rather than shipped.

## Decisions

### 1. Codes are found, not minted

`evidence.py` scans a creator's own captions for a live `RFD-` Fleek referral code. If one is present,
the creator is treated as an **inherited partner** — lifecycle `dormant`, re-activation brief, *their real
code reused* — regardless of what the Airtable `Stage` column says.

This is not a hypothetical. Julia Courcelle carries `RFD-JULIA` in **25 of 25** scraped videos while the CRM
has her as `Stage = Prospect / Outreach Status = Not started`. The engine had scored an active affiliate as
a cold lead.

**Rule: evidence beats the CRM.** A brief that invented a fresh `FLEEK-xxxx` code for a creator already
running `RFD-JULIA` would break her existing attribution and look, to her, like nobody at Fleek reads her
videos.

### 2. Two profile paths, because the evidence genuinely differs

Synthetic roster creators have a full attribution funnel. Real French prospects have posts and **no
attribution at all**. Passing the second through `build_profile` would mean synthesising `first_orders=0`
for every post — and a model reads that as *"this creator never converts"*, not *"we have never measured
them."* Hence `build_profile_from_evidence`.

This is the one place we accepted a second code path rather than a flag. The inputs are different in kind,
not degree, and collapsing them would have made the model lie.

### 3. The do-not-mention list is load-bearing, not garnish

Fleek's own hardest problem, in their words: *"Many pro resellers think Fleek is for beginners and not for
them. Changing that perception is one of our hardest problems."*

A brief that permits *"great if you're just starting out"* actively damages the positioning the programme
depends on. So `do_not_mention` is a required field, the prompt names the beginner-positioning trap
explicitly, and any competitor code the creator is currently promoting goes on the list. In the Notion page
each item renders as its own 🚫 callout — impossible to skim past.

The Notion publisher pages blocks in 100-block chunks rather than truncating, specifically so a long brief
can never silently drop this section.

### 4. Notion is the delivery surface, Airtable is the source of truth

The record is Fleek's; the page is the creator's. A creator should never need a seat in the ops tool to read
their own brief. If Notion publishing fails, `run_brief_job.py` still writes the brief to Airtable and
reports the failure — delivery degrades, the work is never lost.

The job talks to the Notion REST API directly rather than through an MCP connector, because it has to run
unattended on a scheduler and interactive OAuth is not available to a cron.

## Corrections forced by the data

The deck's Section 4 promised inputs we do not hold. Rather than quietly generating briefs that imply
otherwise, `deliverables/case-study-approach.md` §8 now states what each input really is.

1. **"Transcript"** → **captions.** TikTok captions and YouTube titles + descriptions. No audio was ever
   scraped. The prompt forbids quoting these as spoken words.
2. **"Best Fleek creatives"** → **partner archetypes.** Fleek's three named top performers are patterns to
   emulate. There is no creative asset library, and claiming one would not survive a follow-up question.
3. **"Educational carousel"** → dropped. The deck's Creator B was an Instagram carousel; the scraped roster
   has TikTok and YouTube only. The real Creator B (Felix Beauregard) is a YouTube long-form educator.

Also corrected, in the code: **`referral_post_count` is computed against untruncated post text.** The first
implementation counted matches in the 400-char prompt-trimmed description and reported Julia at "8 of 25" —
an artifact of our own truncation, and a number that would have contradicted the wiki on stage.

## Prompt caching — the claim was false, now it's measured

`spec/engine-architecture.md` claimed the cached system prompt was "most of the token bill at 300
briefs/cycle." It was caching **nothing**.

Opus 4.8 will not cache a prefix under **4096 tokens**. Below that, `cache_control` is silently ignored — no
error, `cache_creation_input_tokens: 0`. The bare system prompt is ~250 tokens.

Fix: the cycle's shared context (FR trend pack + archetypes, ~22k chars) now sits behind the breakpoint with
the system prompt, and per-creator evidence goes after it. `llm.cache_report()` prints the real outcome
(hit / write / miss-under-minimum) on every run, so the saving is a receipt rather than a promise.

**Do not "optimise" the trend pack smaller.** Trimming it drops the prefix under the minimum, loses every
cache hit, and makes each brief more expensive.

## Not yet verified

- **Claude-generated briefs have never run.** The `ANTHROPIC_API_KEY` in the workspace `.env` returns
  `400 — credit balance is too low`. Everything up to the API call is exercised; the model output is not.
  Mock mode is a template and looks like one, deliberately.
- **Notion publishing has never run against the real workspace.** The token authenticates
  (`Claude Workspace Bot`), but `NOTION_BRIEFS_PAGE_ID` is unset. Block rendering and the >100-block paging
  path are tested against a stubbed client; the live `POST /v1/pages` is not.

Airtable *is* verified live: `ensure_fields` created `Brief Generated At` in the real base, the
`Stage = Onboarded AND Brief = ""` trigger query runs, and `--handle` targeting resolves.
