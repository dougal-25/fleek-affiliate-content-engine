# 2026-07-10 — The `outreach_drafts` job

`spec/autonomy-layer.md` named five engine jobs. Four existed. This built the fifth, and building it
against the live Airtable base surfaced a scoring problem worth more than the job itself.

---

## The calibration finding (the important one)

`mission/mission.md` names three real Fleek top-performing partners and instructs: *"calibrate the
scoring model against them, not against guesses."* Nobody had.

Doing it exposed two things at once.

**One of the three is already in our roster, filed as a stranger.** `@juliacourcelle` (YouTube, live
seller via Whatnot, `Stage = Prospect`, `Outreach Status = Not started`) is near-certainly the
`@juliacrcl` the mission names. Discovery scrapes the open web; it has no way to know who Fleek
already works with. An unguarded outreach run would have drafted a cold *"we've never worked
together"* DM to one of Fleek's three best partners.

**And she scores 62.** The bar this job was originally specced to use was `Score >= 70`. A partner
Fleek independently identifies as top-performing does not clear our own bar. That is not a rounding
error — it is the scoring model failing the one calibration test we were explicitly told to run.

Two further facts from the same inspection:

- `Stage = Qualified` and `Score >= 70` are **disjoint sets**. All 10 Qualified creators are TikTok
  scoring 52–62; all 8 creators scoring ≥70 are un-Qualified Prospects, 5 of them YouTube.
  `--auto --min-score 70 --stage Qualified` returns zero creators.
- The roster is 49 creators across three platforms (28 TikTok / 16 YouTube / 5 Instagram), not the
  12 TikTok creators the repo's history implies.

**Consequences.** The `--min-score` default of 70 stays — but it is labelled in `--help` as
unevidenced, and the deck's "calibrated, then learning" beat
(`deliverables/case-study-approach.md` §7.5) now has a real worked example instead of an assertion:
*we ran the calibration the brief asked for, and it told us our threshold was wrong.* Re-weighting
against all three named partners is the follow-up, and it needs Fleek to confirm the
juliacrcl ↔ juliacourcelle identity.

---

## Decisions

**Selection is two modes, not one.** `--handles` hand-picks creators (the case study); `--auto
--min-score N` drafts for everyone above the bar (the day-30/60/90 scale story: crossing a threshold
triggers the drafting agent). One mode is required — a bare invocation does nothing, so there is no
accidental mass run. Both write `Status = Draft`. Neither sends.

The spec's original wording, "drafts for newly *Qualified* creators", would have drafted for zero
creators above any sensible score. `Stage` is the human's funnel; `Score` is the engine's judgment.
Keeping both as independent selectors is more honest than collapsing them.

**Known partners are excluded before any spend, and flagged rather than silently dropped.** The three
names from `mission/mission.md` are checked before the first Claude call. `@juliacourcelle` matches on
an *inferred* alias, so the engine prints `possible known partner — VERIFY` instead of quietly
skipping. `spec/log.md` (2026-07-10) records a prior failure where an inference — "absence of public
evidence is evidence of absence" — hardened into a false claim. Loud beats tidy.

**Two Claude calls per creator, not one.** Extract personalisation variables → then draft from them.
The split costs one extra call and buys two things: the deck's split-screen shows a *stored artifact*
on the left rather than a retro-rationalisation of the message, and a bad draft becomes debuggable —
you can see whether the extraction or the writing failed. Every variable must carry a verbatim quote
from the creator's own content; unsupported fields are `null`.

**Recency is a gate, not a preference.** Evidence is filtered to a `--days` window (default 45),
client-side on the normalised date, regardless of what each actor's own date parameter does. A
creator with no in-window posts is **skipped, not drafted**. This fired correctly on its first live
run: `@jf_vintagewholesalefr` last posted 2026-04-15 and was skipped rather than sent a "loved your
recent post" opener. A stale personalisation is worse than a generic message — it proves you looked
and didn't care.

**All three platform adapters, built now.** 28 TikTok / 16 YouTube / 5 Instagram creators need them
today. Verified against the live Apify API, the platforms are not symmetric:

| | Posts | Comments | Transcript |
|---|---|---|---|
| TikTok | `clockworks~tiktok-scraper` | `clockworks~tiktok-comments-scraper` — takes `profiles`, so one call | none |
| Instagram | `apify~instagram-scraper` | `apify~instagram-comment-scraper` — **requires post URLs**, two-step | none |
| YouTube | `streamers~youtube-scraper` | `streamers~youtube-comments-scraper` — **requires video URLs**, two-step | **yes** (`downloadSubtitles`) |

**Transcripts: YouTube only.** `deliverables/case-study-approach.md` promised
"transcript → captions → comments" across the board. TikTok and Instagram have no transcript; YouTube
does, and it is where the highest-scoring reseller-educators live. The claim is corrected rather than
quietly carried.

**Evidence is batched per platform, not per creator.** All handles on a platform go into one actor
run. This is the scale answer, and the job now prints it as a measured receipt rather than a claim:
drafting for 1,000 creators costs the same 2 Apify calls per platform as drafting for 2. Only Claude
scales per creator, at 2 calls, and the system prompt is cached (`cache_read` observed at 2,062
tokens on a 2-creator run).

**The engine drafts, never sends.** No `smtplib`, no mail or DM client, no transmit path — every
outbound call in the codebase goes to Apify or Airtable. The gate holds because the capability is
absent, not because a flag is off.

---

## Bugs fixed on the way

- **The Apify token was leaking into stdout.** `apify_run` passed the token as a `?token=` query
  param; `requests` embeds the full URL in `HTTPError`, so any actor failure printed the secret — and
  would have written it into every GitHub Actions log once this runs on cron. The token now goes in
  an `Authorization` header and the error surfaces the actor's own validation message instead.
- **`load_env` was broken under git worktrees.** A hardcoded `../../../.env` resolves correctly from
  the real checkout but lands on `.claude/.env` from a worktree, where it silently loads nothing and
  every job dies later on `KeyError`. It now walks up the parents.
- **YouTube comments were being silently dropped.** Comment items key their parent video on
  `pageUrl`, not `videoUrl`/`url`. Comment parsing now tries every known parent-URL field name across
  actors, skips inline error rows (`{"error": "VIDEO_UNAVAILABLE"}`), and excludes the creator's own
  replies — those are not audience voice.

## What this does not do

Reply tracking and no-reply follow-up scheduling: the three touches are drafted upfront, so touch 2
cannot reference what actually happened. That is the natural next build and needs reply state in
Airtable. Auto-send is permanently excluded.

---

## Addendum — same-day review by Doug, two calls changed

**Known partners: flag, don't exclude.** The build's hard exclusion was overturned. Doug's reasoning:
nothing sends, so the human gate should *see* a known partner in the pipeline — with a loud banner on
the draft — rather than lose them from it. `@juliacourcelle` now gets drafted like anyone else, but
her draft opens with `⚠️ POSSIBLE KNOWN PARTNER … VERIFY … reframe as re-activation`, the terminal
prints the same flag, and the Runs row records it. The exclusion protected against a mistake by
hiding the creator; the flag protects against it by informing the human. The second is the design the
whole engine claims to have.

**The bar is a percentile, not a number.** The guessed absolute 70 is gone. `--auto` now computes its
cutoff from the roster's live score distribution: `--top-pct` (default 50) takes the top N% of scored
creators. The default is not arbitrary — 50 is where the known-good partner sits today (62 = top ~49%
of the 49-creator roster; the computed cutoff lands on exactly 62). Doug's framing, which the deck
should carry: *the bar reflects where proven-good creators sit; it is then our responsibility through
activation to raise the roster's scores so the same percentile becomes a higher absolute bar.*
Tiering should be read the same way — percentile bands, not fixed grades. `--min-score` survives as
an explicit absolute override.

**The deck must show the pushbacks.** Doug's two build-time interventions (recency as a hard gate;
"what about Instagram?" → multi-platform, saving 21 of 49 creators) are now a named slide beat in
`deliverables/case-study-approach.md` §6 — the human-in-the-loop story is design-time + review-time +
send-time, with receipts.

---

## Addendum 2 — the trigger is qualification, and messages use first names

Doug's design for going live, 2026-07-10:

**Qualification is the trigger, and it stays human.** The pipeline is: discovery scores → a human
*qualifies* the creators worth pursuing (`Stage = Qualified`, always a human act, always overridable)
→ qualification releases the drafting agent. The new `--qualified` mode selects
`Stage = Qualified AND Outreach Status = Not started` — this is the exact call a scheduler makes once
"the agent is active." It resolves the disjoint-set problem cleanly: scoring only *surfaces*
candidates; a person decides who to pursue; the score bar (`--auto`) demotes to a candidate-finder
("who should I consider qualifying"), no longer an outreach trigger.

**Still drafts, never sends.** Doug confirmed the gate explicitly when asked: qualification triggers
a *draft* to `Outreach Status = Draft`, a human reviews/edits/sends and flips to `Sent`. Auto-send
was offered and declined — it would break the permanent gate and is exactly what
`spec/autonomy-layer.md` §7 names as the thing that backfires in the room. If a send job is ever
built, it is a separate job behind its own approval flag, not folded into this one.

**First name, never the handle, never invented.** The most personal messages open on a real first
name. The evidence gatherer now captures each creator's profile display name (TikTok `nickName`, IG
`ownerFullName`, YouTube `channelName`); the extract step pulls a real given name from it — but only
if clearly a person's name. A brand/shop name returns `null`, and the draft then opens on content
with no name at all. Verified live: `"Alicia 🌙"` → *Salut Alicia*; `"CODE DES GRANDS ✦ Friperies"`
→ null → opened on their Lacoste content, no fabricated name. A wrong name is worse than no name — a
handle-as-name or a `[name]` placeholder is the tell of a mail-merge.

**What "run through manually" means today.** `--qualified` is run by hand this week (the case study);
the only thing the autonomy layer changes is who presses enter (a GitHub Actions poll on
`Stage = Qualified`, per `spec/autonomy-layer.md`). The code is identical.

---

## Addendum 3 — the message sells the marketplace, on wiki-grounded facts only

Doug's steer: the draft was leaning too hard on the grading-pain wound. The objective is a narrative
that makes the creator want to **buy from and/or promote** Fleek — so the draft now works from a
**value palette** and picks the one or two items that fit the creator's niche and flagged
observations, led by the observation, never by the pitch.

The palette, every figure traced to `Fleek Wiki/research/Fleek Company Profile.md` (which cites its
own sources): direct global supply (**2,000+ verified suppliers, 100+ countries**); de-risked buying
(**Make an Offer**, **~10-piece MOQ**, **30-day BNPL**); grading trust (QC + **Fleek Sort** + Buyer
Protection); the relationship (customs/shipping handled, Fleeky, a human partner contact); and
earn-as-well-as-buy. "Competitive pricing" was deliberately **not** written as a superiority claim —
nothing substantiates it, and a false claim to a real reseller burns trust. The concrete mechanics
(negotiate, low MOQ, pay-after-arrival) are the honest, stronger version.

**Factual discipline is now a hard rule in the prompt.** The only numbers the model may state are the
palette facts; it may not invent rates, discounts or "cheaper than X" claims; and any benefit it
asserts beyond the palette must land in `human_check` for commercial confirmation. This fired on its
first run: drafting for `@sososolyspam` (a **perfume** wholesaler), the model dropped the
clothing-grading vocabulary as inapplicable and flagged the niche mismatch for a human — surfacing a
probable mis-qualification rather than papering over it. The palette lives in the prompt, not the
wiki, but is sourced *from* the wiki — if Fleek's numbers change, update `Fleek Company Profile.md`
and the `DRAFT_SYSTEM` palette together.
