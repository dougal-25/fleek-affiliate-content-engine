# FLEEK BRAIN — Log

Dated record of what entered the vault and how. Newest first. Hub: [[FLEEK BRAIN Index]].

---

## 2026-07-09 (evening) — ENGINE MILESTONE: discovery live, real creators in Airtable

**What**: The discovery stage of the engine ran end-to-end for real. Not a mock — 12 actual French reseller creators scraped, scored by Claude, and written to the Airtable ecosystem, with an observability Run row.

**Pipeline proven** (`scripts/run_discovery.py` + `content_brain/engine_io.py`):
Brain hashtags → Apify TikTok scrape (90 videos, 6 FR hashtags) → dedupe to 79 unique creators → FR-language + follower-band pre-filter (27) → Claude enrich+score against the Brain's rubric → **12 confirmed resellers upserted to Airtable** (15 non-resellers auto-rejected: news, music, UGC accounts).

**Proof points for the deck**:
- Score breakdowns follow the Brain's exact rubric (audience relevance 30 / reseller credibility 25 / …) — visible per creator in Airtable.
- The AI catches nuance a filter can't: flagged a high-follower friperie owner as Benin-not-France and docked audience relevance.
- Bio emails auto-extracted (2/12) → Contact Route = "Bio email"; rest → DM. Directly answers the "how do we contact them / is Apollo needed" comment.
- Idempotent upsert on Handle — re-runs refresh, never duplicate. This is what makes it schedulable.

**Infra built**: `scripts/build_airtable_base.py` (schema-as-code — Creators 25 fields + Runs 8 fields), reusable `content_brain/engine_io.py` (Apify + Airtable + Claude helpers), project `.venv` + `requirements.txt` (requests added).

**Honest gaps**: FR-language ≠ France (some Québec creators surfaced; scoring flags them). Broad hashtags surface mid-fit creators (scores 32–68); tighter tags + more volume find the 80+ gems. First-run population is deliberately small to prove the loop.

**Next**: outreach_drafts + brief_generator jobs (reuse engine_io), then wrap discovery in a GitHub Actions cron for the autonomy proof.

---

## 2026-07-09 (later) — FR ops enrichment: Perplexity sweep for the live engine

**What**: 5 new pages closing the founding sweep's FR-operational gaps, ahead of the case-study engine build (live deadline 2026-07-10 13:00).

**Method**: `brain-builder` skill — 8 questions, hard cap 16, `sonar`, 8/16 calls used. Mock run first (0 cost), then live. Raw JSONL kept at `_raw/perplexity_fr_sweep_2026-07-09.jsonl`.

**Pages created**: [[FR Reseller Vocabulary and Hashtags]] (⚠️ weak lane, hypothesis-status), [[FR Resale Platform Landscape]], [[FR Creator Content Formats]], [[TikTok Shop France]], [[Wholesale Sourcing and Buying Triggers FR-EU]].

**Headline findings**: France's TikTok Shop market is structurally affiliate-first (81.7% dependency, €31.98 avg unit price — exec-summary stat); the grossiste complaint list (opaque sorting, fake Grade A grades, rigid MOQs) is ready-made outreach ammunition; bale-unboxing content doubles as Fleek's product demo.

**Honest misses**: hashtag lane garbled (marked unverified — the discovery scrape validates it empirically); no verified FR creator handles from search (the Apify run builds the seed list instead); FR communities are private Facebook groups, unreachable by search.

---

## 2026-07-09 — Founding ingest: first research scrape

**What**: Seeded the empty vault with four research pillars via the new `research-scout` agent.

**Method**: 4 parallel Sonnet scouts, one topic lane each, token-capped (≤6 WebSearch, ≤8 WebFetch, ≤1,200-word return, saturation early-stop). Ran in the background from a single Claude Code session.

**Spend**: ~255k tokens total (61k + 62k + 62k + 70k across the four scouts). Well inside the "don't burn 8M tokens" constraint that prompted the build.

**Pages created**:
- [[Fleek Company Profile]]
- [[Vintage Reseller Creator Ecosystem]]
- [[Affiliate Program Playbooks]]
- [[Competitor Creator Programs]]
- [[FLEEK BRAIN Index]] (hub + strategic thesis)

**Headline finding**: the Fleek wedge — no competitor pays a creator to earn commission *and* build inventory at wholesale in one relationship; only a wholesale-sourcing marketplace can. Fleek runs no structured creator program today, and its creators are already buyers whose #1 time-sink is sourcing.

**Known gaps (carried to Index backlog)**: no Reddit/Discord sentiment (fetches blocked across all lanes), TikTok Shop never swept, no named creator shortlist yet, wholesale-supplier referral programs unexplored.

**Provenance rule applied**: every claim carries its source link; single-sourced / blocked-fetch claims marked *(unverified)*. Nothing laundered into false confidence.

**Agent**: `~/.claude/agents/research-scout.md` — reusable across projects, not Fleek-specific. This run is its first use.
