# Mission

Written against the two source documents in this folder, both captured verbatim on 2026-07-10.
**Sources:** `job-description.md` · `task-brief.md`

**Role:** the JD says *Influencer Marketing Manager*; the case study says *AI-native Influencer Specialist*.
Same role, two titles. Use theirs, whichever is on the calendar invite.
**Artefact:** a take-home submission, sent **24 hours before** the session. Present ~20 min, then ~40 min of
questions. Assume the 40 minutes is where it's really decided.

## What they are actually testing

> "The one thing we are testing above all else: how natively you work with AI. We want to see your real
> workflow. Do not hide the AI. Show it to us!"

That is the brief's own emphasis, stated twice more as *"Show us, do not just tell us!"* and *"If you built
any small tool, automation or reusable prompt system, show it. Something that would still work if France was
500 creators instead of 10 is more interesting than a one off answer."*

This repo **is** that answer. Not an illustration of one.

Four things a strong submission shows, in their words:

| | |
|---|---|
| **AI-nativeness** | AI woven through as a genuine multiplier, not bolted on. Real prompts, real tools, real leverage. |
| **Creativity** | Angles they wouldn't have thought of — *especially on activation and getting partners to post.* |
| **Relationship & community instinct** | Partners are people. France has its own culture. Community scales trust in a way 1:1 outreach cannot. |
| **Commercial judgement** | CAC, conversion, budget reallocation. The goal is new customers, not follower counts. |

## The scenario

First month. First project: **owning France** for the influencer programme. A modest test budget, a long tail
of **inherited dormant French partners**, and a mandate to drive new customer acquisition through referral
codes shared in creator videos.

Five parts, one coherent submission:

1. **The French shortlist** — 10 creators, mixed across pro and hobbyist reseller audiences. *"We do not want
   10 names you already knew."* Show the tools, the actual prompts **including the failures**, how you
   filtered signal from noise, how you enriched. Then: how does this go from 10 to 10,000 leads?
2. **Outreach** — first touch + follow-ups for at least 2, written as if really sending. French if that's the
   instinct, with a note on localisation choices. How it personalises at scale, and where the human stays in
   the loop. *"Tell us what a new French partner needs to hear that a UK one does not."*
3. **Cold outreach → signed contract** — the funnel, the drop-off, who's worth chasing, and what you'd build
   so the pipeline *"does not live in your head."*
4. **Activation via personalised briefings** — for both the new recruits and the inherited French community.
   Understand each creator, study what has already converted, then build the system that generates briefs at
   a scale one person could never hand-write.
5. **Phased GTM, budget, CAC** — 30/60/90. How budget splits across **new recruitment and re-activation**,
   what a creator is worth, how money moves toward what works. And: *"How do you get partners to post more…
   without simply paying more per post."*

## How we are judged

The JD names the headline metric outright:

**# and % of partners posting each month.**

Supporting economics: **channel CAC, payback, first-order AOV**, segmented by tier (mega→nano), channel
(TikTok / YouTube / Instagram), geo (UK / France), niche and lifecycle.

The case study restates it: *"a signed partner who never posts is worth nothing. We measure the programme on
how many partners actually post, and how often, not on how many contracts exist."*

## Facts from the source documents that the engine must respect

- **The Content Brain already exists.** The JD describes it as *"our internal AI system that profiles every
  partner and generates personalised campaign briefs."* This repo is a working prototype of *their* system,
  not a thing we invented. Frame it that way in the room.
- **The roster already exists.** *"Over the past two years we've built a 1,000+ creator roster across TikTok,
  YouTube, and Instagram, with recruitment already largely automated."* Influencer is *"currently one of our
  biggest channels for new customer acquisition."*
- **Total addressable community: ~20,000 hobbyist and pro resellers.** Not millions. This bounds every scale
  claim.
- **Three named top-performing partners:** `@behindthesale`, `@theliveneedham`, `@juliacrcl`. These are the
  real known-good archetypes — calibrate the scoring model against them, not against guesses.
- **The attribution mechanic:** creator posts a video with their referral code in video/caption as the CTA →
  a new reseller signs up and places a first order with that code → the customer is attributed to the creator.
- **The hardest problem, in their own words:** *"Many [pro resellers] think Fleek is for beginners and not for
  them. Changing that perception is one of our hardest problems."* This is a positioning problem, and it is
  the most interesting thing in the brief.
- **French resellers already pay for private Discord communities to access coaching advice.** They will pay
  for access to expertise. That is a lever.
- **Trust > reach.** *"Creators who genuinely resell and show their real sourcing, process and tips convert
  far better than big accounts."* Follower count is not a scoring factor.

## The three commitments

**1 — Both motions, not one.** The brief asks for recruitment (Parts 1–3) *and* activation of the inherited
dormant partners (Part 4), with budget split across both (Part 5). Recruitment is where the AI-nativeness is
tested; activation is *"the whole game."* Do not lead with one and treat the other as a footnote.

**2 — LLMs for judgment, deterministic code for money.** Models write profiles, briefs and narrative insight.
Code computes CAC, allocates budget, measures attribution. Never let a model allocate spend; never ask a human
to write 300 briefs.

**3 — The engine proposes, humans approve.** Outreach drafts, never auto-sends — especially not into Fleek's
real market. The brief asks twice where the human stays in the loop. The gates are the answer.

## Standing rule

`mission/` is **read-only to agents.** The two source documents are transcripts of what Fleek asked for. If
the work drifts from them, the work is wrong — not the brief.

---

## ⚠️ Corrections the source documents force

Captured 2026-07-10, when the JD and task brief were first read against the repo. Two of the repo's
load-bearing claims were built on inference and are now contradicted by the source.

1. **"Fleek has no structured creator program — greenfield, not a fix-up."** *(`Fleek Wiki/index.md` strategic
   thesis, `Fleek Wiki/research/Fleek Company Profile.md`)* — **False.** The JD states a 1,000+ creator roster
   built over two years with recruitment largely automated, and the case study calls influencer one of their
   biggest acquisition channels. The wiki inferred "no program" from the *outside* — public `RFD-` codes on
   joinfleek.com. The programme exists; it simply isn't public. Saying "you have no creator program" in the
   room would be a credibility loss in the first two minutes. The *offer* wedge (commission **and** wholesale
   sourcing margin in one relationship) may well survive — but it is a wedge against competitors, not against
   a void at Fleek.

2. **"Anchor the answer on activation of the existing 1,000+ roster, with recruitment as a supporting
   motion."** *(`deliverables/strategy.md`)* — Written before the brief was read, and wrong about it. Part 1
   (discovery) is explicitly *"the core AI-nativeness test"*, and Part 5 splits budget across recruitment and
   re-activation. Both motions carry weight.

3. **Funding figure.** The wiki says ~$45M with a sourced breakdown; the JD says ~$50M raised, Series B
   closed. When speaking to Fleek, use Fleek's number.
