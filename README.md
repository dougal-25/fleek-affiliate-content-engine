# Fleek Content Brain — Agentic Affiliate Content Engine

Case-study prep for the **Influencer Marketing Manager** role at Fleek. A working prototype of
the "Content Brain" described in the JD: an AI system that profiles every creator partner,
generates personalised campaign briefs, and closes the loop from post performance back into
the next brief — so one operator can run many segmented campaigns concurrently across a
1,000+ creator roster.

## What it does

```
┌─────────────────────────────────────────────────────────────────────┐
│                        THE WEEKLY CYCLE                             │
│                                                                     │
│  Roster (1,000 creators) ──► Segmentation ──► Activation targeting  │
│        ▲                    (tier × channel     (who to brief:      │
│        │                     × geo × niche       active, at-risk,   │
│        │                     × lifecycle)        dormant)           │
│        │                                             │              │
│  Profile updates                                     ▼              │
│        ▲                                    Partner Profiler agent  │
│        │                                    (what works for THIS    │
│        │                                     creator)               │
│  Feedback loop agent                                 │              │
│  (codify what worked,                                ▼              │
│   kill what didn't)                        Brief Generator agent    │
│        ▲                                   (hook, format, CTA stack,│
│        │                                    do's/don'ts, references)│
│        │                                             │              │
│  Post performance ◄──── creators post ◄─────────────┘              │
│  (views→clicks→signups→first orders→CAC/AOV)                        │
│                                                                     │
│  Budget engine: weekly reallocation toward best-CAC segments        │
└─────────────────────────────────────────────────────────────────────┘
```

The metrics mirror the JD exactly: **# and % of partners posting each month** (the headline
activation metric), **channel CAC, payback, first-order AOV**, segmented by tier (mega→nano),
channel (TikTok/YouTube/Instagram), geo (UK/FR), niche, and lifecycle.

## Quick start

```bash
cd fleek-content-engine
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1. Generate a synthetic 1,000-creator roster with 90 days of post history
python run_campaign.py generate-data

# 2. See the state of the channel (activation %, CAC by segment)
python run_campaign.py report

# 3. Plan next week's budget (reallocation toward best-CAC segments)
python run_campaign.py plan-budget

# 4. Profile a creator and generate their personalised brief
python run_campaign.py brief CRE-0042

# 5. Run a full weekly cycle: target → profile → brief → simulate posts → feed back
python run_campaign.py weekly-cycle --limit 10
```

Works **without an API key** (deterministic mock mode, useful for understanding the data
flow). With `ANTHROPIC_API_KEY` set, the profiler, brief generator, and insight agents run on
Claude (`claude-opus-4-8`) with structured outputs, so briefs are genuinely personalised.

```bash
cp .env.example .env   # add your key, or: export ANTHROPIC_API_KEY=sk-ant-...
```

## Repo map

| Path | What it is |
|---|---|
| `docs/01-case-study-strategy.md` | How to attack the case study — the argument, mapped to the JD |
| `docs/02-content-brain-architecture.md` | System design: agents, data model, feedback loops |
| `docs/03-campaign-playbook.md` | The operating cadence: segments, calendar, budget rules |
| `scripts/generate_roster.py` | Synthetic roster: 1,000 creators, 90 days of posts |
| `content_brain/` | The engine: segmentation, profiler, briefs, feedback, budget |
| `run_campaign.py` | CLI to drive it all |

## Moving this to its own private repo

This folder is fully self-contained. To lift it into a new private repo:

```bash
gh repo create fleek-affiliate-content-engine --private
git clone git@github.com:<you>/fleek-affiliate-content-engine.git
cp -r fleek-content-engine/* fleek-affiliate-content-engine/
cd fleek-affiliate-content-engine && git add -A && git commit -m "Content Brain prototype" && git push
```
