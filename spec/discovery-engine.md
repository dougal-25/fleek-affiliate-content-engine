# Spec — The Discovery Engine

How the engine finds French creators and builds the Roster the weekly cycle consumes. The scoring
*rubric* lives in [discovery-scoring.md](discovery-scoring.md); this page is the *machine* — its
shape, its market-tailoring seam, and what one run does.

**Judged against:** `mission/mission.md`. Discovery is Part 1, *"the core AI-nativeness test."*

**Status:** live 2026-07-11. First market-driven both-channel run: 120 creators upserted, 30 Qualified.

---

## 1. Where it sits

The discovery engine is **upstream of the whole weekly cycle** (`spec/overview.md`). It *builds the
Roster*; Segmentation then slices that roster by `tier × channel × geo × niche × lifecycle`. `geo` is
the market — so market-tailoring is not bolted on, it is a dimension the cycle already names.

The engine's job: fill the Roster with French creators positioned to post a Fleek **wholesale
bundle / bale** video, tagged richly enough for Segmentation to work.

## 2. The market-profile seam

The engine is **market-agnostic machinery**. Everything France-specific lives in one profile,
`content_brain/markets/france.py`, consumed via `content_brain/markets/get("france")`:

| Profile field | What it carries |
|---|---|
| `channels` | Active search channels this pass — `["tiktok", "instagram"]`, co-primary |
| `context_platforms` | Vinted / Depop / Whatnot / Vestiaire / Leboncoin — a *signal* in a bio, never a search source |
| `follower_min/max` | The band (1k–500k) — nano floor because trust density is highest there |
| `tiktok_hashtags` | Demand-side seed tags (what resellers *do*), cited to the wiki |
| `ig_seeds` + `ig_seed_weight` | Graph-walk seeds; verified pros weighted 3× (the graph inherits the seed's audience) |
| `archetypes` | Bale-unboxer, sourcing-vlogger, live-seller, reseller-educator, thrift-flipper — labels, not gates |

**Adding a market = writing `markets/germany.py` and reusing the engine unchanged.** No engine edits.
Each market also gets its own wiki index (France's is `Fleek Wiki/index.md`); a second market gets a
parallel one so its ground truth (hashtags, vocabulary, platforms, archetypes) is separately sourced.

## 3. The pipeline — one run of `--market france`

```
load profile
  → SOURCE per channel
        tiktok    : hashtag scrape (clockworks/tiktok-scraper)
        instagram : relatedProfiles graph-walk from verified seeds (apify/instagram-profile-scraper)
  → ENRICH (one path, whatever the source)
        free gates : lexicon · fashion-vertical · supplier · fleek-referral-code   (content_brain/signals.py)
        tiktok also: an LLM read of captions → is_reseller, segment, strength/weakness, coarse fit score
  → SHORTLIST BAR
        genuine reseller  AND  clothing vertical  AND  not a supplier   → Stage = Qualified
        everyone else discovered stays in the roster                    → Stage = Prospect
  → SINK
        Airtable upsert on Creator Key (platform:handle) + one Run row
```

`--channels tiktok` runs one channel; `--dry-run` skips the Airtable write; `--smoke` runs tiny.

## 4. The shortlist bar

`signals.passes_shortlist_bar(is_reseller, fashion_vertical, likely_supplier)` — deterministic, and
**comment-free by design**. A genuine reseller, in the clothing vertical, who is not themselves a
wholesaler. Nothing else gates entry to the shortlist.

**Comments are not part of discovery.** They enrich a creator's profile where they are rich and are
ignored where thin (an Instagram lead-magnet comment section carries no audience signal — see
`spec/discovery-scoring.md` §4). Discovery decides who is *in the roster* and who is *Qualified*;
comments are a later synthesis into creator profiles and the wiki, never a filter.

## 5. Channel weighting — prior now, measured later

The channels are **co-primary with no fixed weight**. At discovery time there is no performance data,
so forcing a ratio would bias the roster on a guess. Two deliberate positions:

- **Channel never enters the fit score.** A strong reseller-educator on one platform beats a weak
  hauler on another; weighting the score by platform would repeat the follower-count mistake
  (`discovery-scoring.md` §6).
- **Sourcing allocation becomes measured, not guessed.** Once creators post and the feedback loop
  measures CAC *by channel*, `content_brain/budget.py` reallocates toward the best-CAC channel —
  per market, because channel is a segmentation axis. Same discipline as the CAC model: a stated
  prior now, Fleek's real data later.

## 6. Deliberately out of scope this pass

- **YouTube search.** Dropped from active discovery — it is the long-form / pro-credibility channel
  (highest LTV per post, lowest volume) and belongs on the roadmap for the *pro* segment, but the 16
  existing YouTube rows stay in the roster. Adding it = a YouTube source + `channels` entry in the
  profile; the enrichment path and bar are unchanged.
- **A YouTube source script.** Not built. The existing rows arrived via an earlier pass.

## 7. Known gaps

- The fashion-vertical gate passes on IG-only signal that a cross-platform check would catch
  (`@alex_yeddertcg`, a Pokémon-TCG seller, qualified at a low score). Tighten with a second-platform
  resolution step before promoting to the final shortlist.
- The graph walk caps candidates (`--max-candidates`); the run logs what it drops, never silently.
- No test suite — same debt as the rest of `content_brain/`.

## 8. Sources

- `content_brain/markets/france.py`, `content_brain/markets/__init__.py` — the profile + registry
- `scripts/run_discovery.py` — the engine
- `content_brain/signals.py` — the gates and the shortlist bar
- `spec/discovery-scoring.md` — the rubric · `spec/cac-model.md` — where weighting becomes measured
- `Fleek Wiki/index.md` — the France market's research context
