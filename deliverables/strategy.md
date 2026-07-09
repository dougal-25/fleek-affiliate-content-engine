# Case Study Strategy — How to Attack It

## The one-sentence thesis

> Fleek's next unit of growth is not more creators — it's **more posts per existing creator**,
> and the way to get them without headcount is an AI engine that makes every brief feel
> hand-written, then learns from every post.

The JD says this almost verbatim: *"The next chapter is keep scaling recruiting while
**activating better at scale**"* and *"The # and % of partners posting each month is the
headline metric."* Whatever the case study prompt turns out to be, anchor the answer on
**activation of the existing 1,000+ roster**, with recruitment as a supporting motion
(quality over headcount, YouTube as the compounding channel).

## The problem, framed as an operator

A 1,000-creator roster with (assume) ~25% posting monthly is really four different problems:

1. **Core partners (~top 5%)** drive most volume → high-touch, long-term contracts, hero
   campaigns. Human relationship work; the engine handles reporting, not briefs.
2. **Active long tail (~20–30%)** post but inconsistently → the engine's sweet spot:
   personalised monthly briefs that fit what already works for each creator, so posting is
   low-friction and performance compounds.
3. **Dormant partners (~50%+)** haven't posted in 60+ days → dedicated re-activation
   campaigns with a different message ("here's what changed, here's a brief built on your
   best past post, here's the incentive").
4. **New recruits** → onboarding briefs that get to first post fast (activation window is
   short — day-30 posting rate is the KPI here).

Each 5-point gain in monthly activation on a 1,000-creator roster ≈ 50 more posting partners
per month. At even modest per-partner buyer yield that moves the channel number more than any
plausible recruitment win in the same period — and it's cheaper, because the acquisition cost
of these creators is already sunk.

## Why an agentic engine (and not a spreadsheet + templates)

The bottleneck to activating the long tail is **brief quality at scale**. A generic brief gets
ignored; a personalised brief ("your March thrift-haul short converted 3× your average — do
that format again, here's the hook, here's your code") gets acted on. Hand-writing 300
briefs/month doesn't scale; the Content Brain does:

- **Partner Profiler agent** — reads each creator's history and maintains a living profile:
  best formats, best hooks, audience fit vs the reseller ICP, conversion track record, risks.
- **Brief Generator agent** — turns profile + segment insights + campaign spec into a
  partner-specific brief: hook options, format, full CTA stack, do's & don'ts, reference
  examples. (The JD lists exactly these fields.)
- **Feedback Loop agent** — after each cycle, aggregates post performance per segment,
  codifies what worked into insights, and those insights are injected into the next round of
  briefs. *"Post performance feeds back into the system to sharpen the next round."*
- **Budget engine** — deterministic, not an LLM: weekly reallocation toward best-CAC
  segments, per-campaign test budgets and caps, kill-or-scale rules. Portfolio of small bets.

The division of labour matters and is worth saying out loud in the case study: **LLMs for
judgment at scale (profiles, briefs, narrative insights), deterministic code for money and
measurement (CAC, budgets, attribution).** Never let a model allocate budget; never ask a
human to write 300 briefs.

## The metrics tree (what you'd put on the weekly business review slide)

```
New hobbyist & pro buyers via influencer  ← THE number
├── # partners posting this month (headline activation metric)
│   ├── activation % by segment (tier × channel × geo × niche × lifecycle)
│   ├── dormant → reactivated count
│   └── new recruit → first post within 30d %
├── buyers per posting partner
│   ├── post → click → signup → first order funnel
│   └── brief adherence (did they use the hook/format/CTA?)
└── channel economics
    ├── CAC by segment (weekly, drives reallocation)
    ├── payback (months to recover CAC from margin)
    └── first-order AOV (hobbyist vs pro mix)
```

## Community flywheel tie-in

The prompt notes: *"community will grow off the back of their success."* The engine feeds the
flywheel directly — top-performing posts become UGC/reference examples in the next briefs
(social proof inside the system), winners get surfaced in Discord (UK + FR), and creator
success stories become recruitment assets. Success → visibility → community → more creators
wanting in. Mention it, keep it as the closing chapter, don't let it dilute the activation
story.

## Likely case-study prompts and the pivot for each

| If they ask… | Lead with… |
|---|---|
| "Design your first 90 days" | Weeks 1–2 audit (activation baseline, CAC by segment), weeks 3–6 first engine-driven cycle on one segment (UK TikTok micro), weeks 7–12 scale + dormant reactivation campaign |
| "How would you lift activation?" | The 4-cohort framing above + the personalised-brief engine + re-activation campaign design |
| "How would you use the Content Brain?" | The three agents + feedback loop + what you'd build next (adherence scoring, auto-scheduled follow-ups, French-language briefs) |
| "Allocate £X budget" | Portfolio logic: tiered gifting, per-campaign caps, weekly CAC-driven reallocation, 70/20/10 (proven / scaling tests / wild bets) |

## What the prototype in this repo proves

You can walk into the interview and *show* the loop running: 1,000 synthetic creators →
segment report → budget plan → a genuinely personalised brief for a named creator → a
simulated week of posts → insights that visibly change the next brief. That's the difference
between "I'd use AI" and "I run channels on AI systems."
