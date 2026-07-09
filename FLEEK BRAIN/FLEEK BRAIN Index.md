# 🧠 FLEEK BRAIN — Index

The knowledge base behind the **Fleek affiliate content engine** — case-study prep for the **Influencer Marketing Manager** role at Fleek. This vault holds *intent and evidence*; the code in `content_brain/` holds *what/how*. Seeded 2026-07-09 by the `research-scout` agent (4 parallel web scouts, ~255k tokens). See [[FLEEK BRAIN Log]].

## The four research pillars

1. [[Fleek Company Profile]] — who Fleek is: $45M raised (incl. fresh $25M Series B, 8 Jul 2026), a16z/YC/eBay-backed, wholesale secondhand marketplace. Runs only informal `RFD-` referral codes today — **no structured creator program yet.**
2. [[Vintage Reseller Creator Ecosystem]] — the audience: nano/micro reseller-creators whose bale-unboxing and thrift-haul content already sells the format. They're *already buyers* of stock.
3. [[Affiliate Program Playbooks]] — the operating manual: activation rate is the one real metric, GMV follows a power law, seed-then-concentrate, personalise briefs but don't over-script. (Half the open web here is blogspam — marked.)
4. [[Competitor Creator Programs]] — the differentiation map: Whatnot is the benchmark; Vinted has *nothing*; nobody fuses commission with wholesale sourcing.

## The FR ops layer (2026-07-09 Perplexity sweep — feeds the live engine)

Operational ground truth for the French discovery/outreach/brief pipeline:

1. [[FR Reseller Vocabulary and Hashtags]] — the scrape's keyword seeds. ⚠️ Weakest lane; hypothesis list that the discovery run itself validates (Brain proposes → scrape verifies).
2. [[FR Resale Platform Landscape]] — Vinted 0%-fee volume lane (pros camouflage as closet-cleaners), Whatnot FR = live-selling hub, Vestiaire = luxury. Platform presence → scoring signals.
3. [[FR Creator Content Formats]] — hauls-with-storytelling rising, generic hauls fading; bale unboxing IS the product demo. → brief rules.
4. [[TikTok Shop France]] — live since 2025-03; **81.7% affiliate dependency, €31.98 avg unit price**. France is structurally affiliate-first: exec-summary stat.
5. [[Wholesale Sourcing and Buying Triggers FR-EU]] — named grossistes, the complaint list (opaque sorting, fake Grade A, MOQs), switch triggers. → outreach ammunition.

## 🎯 The strategic thesis (why this case study wins)

Three findings converge into one wedge:

- **Fleek has no structured creator program** ([[Fleek Company Profile]]) — greenfield, not a fix-up.
- **Its creators are already buyers** ([[Vintage Reseller Creator Ecosystem]]) — sourcing is their #1 time-sink, so promoting Fleek helps them *operationally*, before any commission.
- **No competitor can copy the obvious offer** ([[Competitor Creator Programs]]) — rivals pay for *either* sales *or* content; **only a wholesale marketplace can pay commission AND give wholesale sourcing margin in one relationship.**

→ The pitch: a creator program where the reward is *become a better-stocked reseller who also earns commission*. The [[Affiliate Program Playbooks]] tell you how to run it at scale — **activation % as the north star** (which is exactly Fleek's own JD headline metric), a small top tier carrying GMV, one operator running many segmented campaigns via tooling not headcount. That's the Content Brain.

## How this feeds the engine

| Vault insight | Content Brain component |
|---|---|
| Activation % is the north-star metric | Segmentation + activation targeting |
| GMV power law (20% → 80%) | Budget engine (reallocate to best-CAC segments) |
| Personalise briefs, don't over-script | Brief Generator agent |
| Creators are already buyers (wedge) | The core value-prop / positioning |
| Per-partner CAC, recalculated | Feedback loop agent |

## Biggest gaps to fill next (research backlog)

- **Reddit/Discord practitioner sentiment** — blocked in this sweep across every lane. Needs a browser/Reddit-capable pass. *Top priority — it's the missing primary-source voice.* (2026-07-09 FR sweep confirmed: no public FR communities findable via search; likely private Facebook groups — « vente mode vintage France », « achat-revente vêtements ».)
- ~~**TikTok Shop** resale/thrift affiliate mechanics~~ → swept 2026-07-09: [[TikTok Shop France]]. Remaining: resale-category restrictions + creator-side commission % ranges.
- **Named UK/FR reseller creators** shortlist — Perplexity couldn't produce verified handles (2026-07-09). **Being built empirically by the discovery engine's first Apify run** — the scrape IS the seed list.
- **Wholesale-supplier referral programs** — Fleek's closest analogues. Still unswept.
- **Hashtag validation table** — after the first discovery run, write actual per-tag result counts back into [[FR Reseller Vocabulary and Hashtags]].

## Meta

- **Agent**: `~/.claude/agents/research-scout.md` (reusable, token-capped: ≤6 searches / ≤8 fetches / ≤1,200 words per scout). Re-run any lane by spawning it with a new topic.
- **Provenance**: every claim links its source; single-sourced or blocked-fetch claims are marked *(unverified)* — kept honest, not laundered.
- **Log**: [[FLEEK BRAIN Log]]
