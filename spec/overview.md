# Spec — Overview

The entry point to design intent. What the engine is, who it's for, and where the detail lives.

**Judged against:** `mission/mission.md` — the headline metric is **# and % of partners posting each month.**

## Who it's for

One operator running many segmented campaigns across a 1,000+ creator roster, concurrently, without
headcount. Every design choice here should be defensible as "this lets one person do the work of ten."

## What it is

A weekly cycle, not a campaign:

```
Roster ──► Segmentation ──► Activation targeting ──► Partner Profiler ──► Brief Generator
  ▲          (tier × channel   (who to brief:          (what works for      (hook, format,
  │           × geo × niche     active, at-risk,        THIS creator)        CTA stack, do's,
  │           × lifecycle)      dormant)                                     references)
  │                                                                                │
Profile updates ◄── Feedback loop ◄── Post performance ◄── creators post ◄────────┘
                    (codify what      (views → clicks → signups
                     worked, kill      → first orders → CAC/AOV)
                     what didn't)

Budget engine (deterministic): weekly reallocation toward best-CAC segments.
```

## The four problems, not one

A 1,000-creator roster at ~25% monthly posting is four different problems, and each gets a different motion:

1. **Core partners (~top 5%)** — drive most volume. High-touch, human relationship work. The engine handles
   their reporting, not their briefs.
2. **Active long tail (~20–30%)** — post inconsistently. *This is the engine's sweet spot:* personalised
   monthly briefs built on what already works for them, so posting is low-friction.
3. **Dormant (~50%+)** — 60+ days silent. Re-activation campaigns with a different message and an incentive.
4. **New recruits** — onboarding briefs that reach first post fast. Day-30 posting rate is the KPI.

## The division of labour

**LLMs for judgment at scale** — profiles, briefs, narrative insight.
**Deterministic code for money and measurement** — CAC, budgets, attribution.

Never let a model allocate budget. Never ask a human to write 300 briefs. Say this out loud in the room.

## Where the detail lives

| Question | Page |
|---|---|
| How is the system built? Agents, data model, feedback loops. | `spec/engine-architecture.md` |
| How does discovery work? The market-profile seam, the pipeline, the shortlist bar. | `spec/discovery-engine.md` |
| How are creators scored? What signals were rejected? | `spec/discovery-scoring.md` |
| Where does a predicted CAC number come from, and what may it be used for? | `spec/cac-model.md` |
| How is it operated? Segments, calendar, budget rules. | `spec/campaign-playbook.md` |
| How does it run unattended? Hosting, triggers, breakers, recovery. | `spec/autonomy-layer.md` |
| Why is it built this way? | `spec/decisions/` |
| What do we actually know about FR reselling? | `Fleek Wiki/index.md` |
| What are we presenting? | `deliverables/` |

## Status

The engine runs. The autonomy layer is designed and partially live — see `spec/autonomy-layer.md` §7. The
wiki is seeded (21 pages, cited) with open gaps tracked in `Fleek Wiki/Enrichment Leads Backlog.md`.

`content_brain/` has no tests. That's a known debt, not an oversight.
