# Fleek Content Brain — an agentic affiliate content engine

A working prototype of the **Content Brain**: an AI system that profiles every creator partner, generates a
personalised campaign brief for each one, and closes the loop from post performance back into the next brief
— so a single operator can run many segmented campaigns across a 1,000+ creator roster.

Built as case-study prep for the Influencer Marketing Manager role at Fleek.

**The argument in one line:** Fleek's next unit of growth isn't more creators — it's *more posts per existing
creator*, and the way to get them without headcount is an engine that makes every brief feel hand-written,
then learns from every post.

## The weekly cycle

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

The metrics mirror the JD: **# and % of partners posting each month** as the headline activation metric, then
channel CAC, payback and first-order AOV — segmented by tier (mega→nano), channel (TikTok / YouTube /
Instagram), geo (UK / FR), niche and lifecycle.

The division of labour is deliberate and worth stating: **LLMs for judgment at scale** (profiles, briefs,
narrative insight), **deterministic code for money and measurement** (CAC, budgets, attribution). Never let a
model allocate budget; never ask a human to write 300 briefs.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python run_campaign.py generate-data          # 1,000 synthetic creators, 90 days of post history
python run_campaign.py report                 # state of the channel: activation %, CAC by segment
python run_campaign.py plan-budget            # next week's reallocation toward best-CAC segments
python run_campaign.py brief CRE-0042         # profile one creator → their personalised brief
python run_campaign.py weekly-cycle --limit 10  # target → profile → brief → simulate posts → feed back
```

Runs **without an API key** in deterministic mock mode, which is the fastest way to understand the data flow.
With `ANTHROPIC_API_KEY` set, the profiler, brief generator and insight agents run on Claude with structured
outputs, so the briefs are genuinely personalised.

```bash
cp .env.example .env   # add your key
```

## Repo map

| Path | What it is |
|---|---|
| `mission/` | The constants: the verbatim job description and task brief, and what they oblige |
| `Fleek Wiki/` | The knowledge base — 21 cited pages of ground truth on FR/EU reselling. An Obsidian vault |
| `spec/` | Design intent: architecture, operating playbook, autonomy layer, decision records |
| `content_brain/` | The engine: segmentation, profiler, briefs, feedback, budget |
| `scripts/` | Discovery scrape, roster generation, Airtable setup |
| `run_campaign.py` | The CLI that drives it all |
| `deliverables/` | What Fleek receives: the strategy, the approach, the evidence pack |
| `.claude/agents/` | The research agent that builds and refreshes the wiki |

Start with `spec/overview.md` for the design, or `deliverables/strategy.md` for the argument.

## Why a wiki sits underneath it

Before finding a single creator, the engine builds the knowledge base that teaches it what "good" looks like:
the FR platform landscape, reseller archetypes and their economics, community vocabulary that feeds discovery
keywords, the formats working right now, and where resellers congregate. Every claim carries its source;
single-sourced claims are marked unverified.

Discovery keywords, scoring factors, personalisation variables and brief content all reason from it.
**Perplexity teaches the engine; Apify feeds it.**
