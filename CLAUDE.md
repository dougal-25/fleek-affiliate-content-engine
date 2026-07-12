# CLAUDE.md — Fleek Affiliate Content Engine

Case-study prep for the **Influencer Marketing Manager** role at Fleek. This repo is the deliverable's
engine: a working prototype of the AI system that profiles creator partners, generates personalised briefs,
and closes the loop from post performance back into the next brief.

## Read this first

Before doing anything substantive, read `mission/mission.md`. It states what we're building and the one
number we're judged on. If a change doesn't serve that number, say so before making it.

## Naming — one word, one meaning

Fleek calls their whole affiliate content system **the Brain**. So do we. Nothing *inside* this repo takes
that name.

| Word | Means | Lives at |
|---|---|---|
| **the Brain** / the engine | this whole project — Fleek's own word for it | the repo itself |
| **the wiki** | the Obsidian research knowledge base | `Fleek Wiki/` |
| **the spec** | design intent — why, for whom, how it works | `spec/` |
| **the mission** | the two immutable source documents + what they oblige | `mission/` |

`content_brain/` (the Python package) keeps its name: it is the engine's code, and "brain" there is Fleek's
word for the system.

## The layers

```
mission/         THE CONSTANTS. The verbatim JD and task brief, plus what they oblige.
Fleek Wiki/      THE KNOWLEDGE. Researched ground truth about FR/EU reselling. An Obsidian vault.
spec/            THE INTENT. Architecture, playbook, autonomy design, dated decision records.
content_brain/   THE CODE. Segmentation, profiler, brief generator, feedback loop, budget engine.
scripts/         Discovery, roster generation, Airtable setup.
run_campaign.py  The CLI that drives it all.
deliverables/    What Fleek actually receives: strategy, approach, evidence.
_attic/          Orphaned files. Kept, not deleted. Nothing here is live.
```

## Standing rules

- **`mission/` is read-only to agents.** The JD and task brief are transcripts of what Fleek asked for. If
  the work drifts from them, the work is wrong — not the brief. Never edit, summarise or "improve" them.
- **The wiki cites its sources.** Every claim a downstream job acts on (a hashtag, a platform, an archetype)
  carries its source. Single-sourced claims are marked *(unverified)*. Kept honest, not laundered.
- **A wiki run isn't done until `Fleek Wiki/index.md` and `Fleek Wiki/log.md` are current.**
- **Wikilinks inside `Fleek Wiki/` only.** `[[Page Title]]`, filenames unique across the vault. Everywhere
  else in the repo, use markdown links with real paths.
- **LLMs for judgment, deterministic code for money.** Models write profiles, briefs and insight. Code
  computes CAC, allocates budget, measures attribution. Never let a model allocate spend.
- **The engine proposes, humans approve.** Outreach drafts, never auto-sends. This gate is permanent.

## dwcw deviation, on purpose

The dwcw workspace standard puts project intent in `wiki/`. Here "wiki" already means the research vault, so
intent lives in **`spec/`** instead. The `wiki-update` skill should write to `spec/log.md` and
`spec/decisions/`, not to `Fleek Wiki/`.

## Running it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python run_campaign.py generate-data      # synthetic 1,000-creator roster + 90d of posts
python run_campaign.py report             # activation %, CAC by segment
python run_campaign.py plan-budget        # reallocation toward best-CAC segments
python run_campaign.py brief CRE-0042     # profile a creator, generate their brief
python run_campaign.py weekly-cycle --limit 10
```

Runs without an API key in deterministic mock mode. With `ANTHROPIC_API_KEY` set, the profiler, brief
generator and insight agents run on Claude with structured outputs.

The jobs that touch the **real** Airtable base (not the synthetic roster) are scripts, not `run_campaign`
subcommands. They need `APIFY_API_TOKEN` and `AIRTABLE_API_KEY`:

```bash
python scripts/run_discovery.py --dry-run                        # scrape → score → Prospects
python scripts/run_outreach.py --handles gdefou --dry-run        # hand-picked FR outreach drafts
python scripts/run_outreach.py --auto --dry-run                  # score-triggered, at scale
                                                                 # (percentile bar: --top-pct, default top 50%)
```

`run_outreach.py` **drafts, never sends** — it writes `Outreach Status = Draft` to Airtable and a human
reviews, edits, sends and flips the status. That gate is permanent. Always `--dry-run` first.

## Code style

- Python, minimal dependencies, full runnable code — no `# TODO: implement` placeholders.
- snake_case files and folders (the two title-case exceptions, `Fleek Wiki/` and its pages, are Obsidian
  convention and deliberate).
- API keys come from the workspace root `.env`. Never in code, never in chat.
