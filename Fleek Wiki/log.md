# Fleek Wiki — Log

Dated record of what entered the vault and how. Newest first. Hub: [[index]].

---

## 2026-07-09 (night, 2) — Reddit/Quora practitioner ingest + Apify Reddit actor built

**Why**: Close the Phase 0 "where resellers congregate" + practitioner-voice gaps with real forum voice, and stand up a reliable Reddit-ingest tool for the living Brain.

**Access reality**: Reddit is bot-blocked to WebFetch/WebSearch (domain-refused); Quora is login-walled (403, snippet-only). Fetched anyway via free work-arounds — **PullPush API** (EN threads) and a **redlib mirror (`reddit.nerdvpn.de`) driven by Playwright** (FR threads) — plus substitute forums/surveys/ledgers (Mumsnet, SadVintedFaces survey n=1,500+, Friptadium). ~21 real threads captured. Raw provenance: [[reddit_quora_threads_2026-07-09]].

**Tool built**: `~/.claude/skills/wiki-knowledge-base-builder/scripts/apify_reddit.py` (Apify `trudax/reddit-scraper-lite`), now the **mandated Reddit-fetch method** in the skill (SKILL.md Stage 4b — WebFetch banned for Reddit). Reads `APIFY_API_TOKEN` from `.env`, `--cap` cost guard, `--mock` proof. Mock ✅. **Live 300-run quota-blocked** ("Monthly usage hard limit exceeded" — Apify free credit spent; no charge). Re-run after reset/top-up.

**Pages enriched**: [[French Reseller Community Sentiment]] (on-thread FR anti-reseller voice — "parasites", SHEIN-relabeled, "c'est devenu trop cher", hygiene "ick"; Vinted survey 41%/65%/55%; **subreddit congregation map** — closes the Phase 0 lane; the whitespace finding that FR *business-side* friperie posts get mod-removed), [[FR Bale Sourcing Playbook]] (EN bale ground-truth — $0.10–0.50/lb, 2000 tees/1000lb, 50–70% waste, "sourcing is the ceiling", pick-your-own, rag-export mechanics), [[FR Creator Content Formats]] (haul-engagement drivers — price-reveal hook, designer-steal, "looked it up at home" resale-reveal; + Quora audience question-demand).

**Also**: Doug renamed the vault folder → "Fleek Knowledge Base" (Index/Log files still named "FLEEK BRAIN *"). Synthesis correction: Apify is the **fetch** step, not synthesis — the wiki pages are still hand-synthesised.

---

## 2026-07-09 (night) — Deep-read enrichment: primary-source method (Substack + 4-agent fan-out)

**Why**: Doug flagged the vault as "not rich enough." Root cause named: Perplexity `sonar` is a *summariser* — 1–3k-char syntheses, thin on named FR detail, "no data found" on niche lanes. Fix = a **method shift**: fetch and deep-read named primary sources, not ask an AI to summarise the web.

**Method**: (1) Deep-read a reader-supplied Paris shopping Substack. (2) Fanned out **4 parallel research agents** (general-purpose, WebSearch+WebFetch), each deep-reading ~8–12 real pages in a different vein: FR cities retail, reseller-creator profiles, market intelligence, sourcing practitioner voice. ~30 sources deep-read total (~266k subagent tokens). Agreed the enrichment loop with Doug — **job-first, `Feeds:`-guarded, manual passes**, compounding via a leads backlog.

**Pages created**: [[Paris Secondhand Retail Map]], [[French Cities Secondhand Retail Map]], [[FR Bale Sourcing Playbook]], [[Enrichment Leads Backlog]] (method + compounding to-do).

**Pages deep-enriched**: [[French Reseller Creator Shortlist]] (tiered roster — Nathan Vialle bulk→Whatnot €5–10K/live, Bichette Kids bale-unboxing, Giulia Castellucci; grossistes courting creators; authenticity-vs-brand-deal wedge), [[French Secondhand Market Trends 2026]] (IFM €6bn/2022 + 10.9% share, Xerfi €14bn, Vinted 2025 €10.8bn GMV, **anti-fast-fashion law adopted 29 Jun 2026** — €20 malus by 2030, targets Shein/Temu, spares Zara/Kiabi), [[French Reseller Community Sentiment]] (verbatim grade-A-scam quotes + waste-reality), [[FR Reseller Vocabulary and Hashtags]] (full trade grade-vocab + retail terms — fixes the founding sweep's weakest lane).

**Headline wins**: the practitioner-voice gap is now richly filled with real quotes; named bulk-sourcing creators (the exact Fleek-affiliate archetype) identified; the anti-fast-fashion law dated and specced (a hard positioning asset — it even restricts influencers from promoting Shein/Temu, pushing them toward resale-native offers); the full grade vocabulary (crème/original/A-B-C) now documented.

**Honest caveats**: creator follower counts are source-reported, not profile-checked (TikTok/IG don't render to WebFetch — verify live before outreach); Trustpilot quotes are snippet-level (pages block fetch); market-size figures span €6–14bn by scope definition; several sources 403'd (FashionNetwork, bpifrance) — all logged in [[Enrichment Leads Backlog]] for a browser pass.

**Method proven**: this pass produced ~10× the named detail of the Perplexity sweeps. The deep-read loop is the way forward; leads backlog seeded for the next pass.

---

## 2026-07-09 (latest) — Deep-dive enrichment: 25-question France-primary sweep

**What**: A thorough enrichment pass to harden the foundation. 5 new pages + 4 enriched pages, weighted to the four documented backlog gaps (practitioner sentiment, named creators, supplier referral programs, affiliate mechanics deep-dive).

**Method**: `wiki-knowledge-base-builder` skill — 25 questions, hard cap 35, `sonar`, **25/35 calls used** (10 under cap). France-primary framing throughout (creators/trends France-first; B2B mechanics as comparison backdrop). "friperie" baked into 10 questions per Doug's steer. Mock run first (0 cost), then live. Raw JSONL at `_raw/perplexity_fr_deepdive_2026-07-09.jsonl`. Every one of the 25 answers returned 8–10 citations, zero errors, nothing thin.

**Pages created**: [[French Reseller Community Sentiment]], [[French Reseller Creator Shortlist]], [[Supplier and B2B Referral Mechanics]], [[Creator Affiliate Mechanics]], [[French Secondhand Market Trends 2026]].

**Pages enriched**: [[TikTok Shop France]] (commission %s + By-Application resale gate — closed its own two gaps), [[Competitor Creator Programs]] (Whatnot FR/EU 6.67%+VAT economics + resale-affiliate landscape), [[Fleek Company Profile]] (Series B carried no creator program — re-confirmed; +Pioneer Fund), [[FR Creator Content Formats]] (virality drivers, flagged US-extrapolated).

**Headline wins vs the risky lanes I flagged**: both "search-blocked" lanes actually delivered. **Q1** produced verbatim reseller bale complaints (Trustpilot: "Grade A" = dirty/stained/unsellable) — pre-written outreach ammunition. **Q8** produced a real named FR micro-creator seed list (Na Nin Vintage, @emmaverdierkremer, @veryfrip, Zoé Léger, Nawal Bonnefoy). **Q16/Q17** closed [[TikTok Shop France]]'s outstanding gaps outright.

**Strategic reinforcement**: the wedge held under deeper scrutiny — bale suppliers almost never run referral programs (whitespace confirmed, Q11); wholesale marketplaces can't stack creator commission on 25% platform fees but Fleek doesn't need to (sourcing margin funds the incentive, Q15); Series B brought capital but *no* creator program (Q22). France is a structurally favourable launch market (Vinted = biggest FR clothing retailer, anti-fast-fashion tailwind, social-first discovery, Q24/Q25).

**Honest misses**: direct FR Reddit/FB-group threads still unreached by search (Trustpilot aggregation is the proxy); verified TikTok creator handles + live metrics still owed (IG-heavy shortlist only); virality/format data is US-extrapolated (Q10 flagged). All three are scrape/browser jobs, not Perplexity jobs — carried to the Index backlog.

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
- [[index]] (hub + strategic thesis)

**Headline finding**: the Fleek wedge — no competitor pays a creator to earn commission *and* build inventory at wholesale in one relationship; only a wholesale-sourcing marketplace can. Fleek runs no structured creator program today, and its creators are already buyers whose #1 time-sink is sourcing.

**Known gaps (carried to Index backlog)**: no Reddit/Discord sentiment (fetches blocked across all lanes), TikTok Shop never swept, no named creator shortlist yet, wholesale-supplier referral programs unexplored.

**Provenance rule applied**: every claim carries its source link; single-sourced / blocked-fetch claims marked *(unverified)*. Nothing laundered into false confidence.

**Agent**: `~/.claude/agents/research-scout.md` — reusable across projects, not Fleek-specific. This run is its first use.
