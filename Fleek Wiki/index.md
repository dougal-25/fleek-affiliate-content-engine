# Fleek Wiki — Index

The knowledge base behind the **Fleek affiliate content engine** — case-study prep for the **Influencer Marketing Manager** role at Fleek. This vault holds *research and evidence*; `spec/` holds design intent; the code in `content_brain/` holds *what/how*. Seeded 2026-07-09 by the `research-scout` agent (4 parallel web scouts, ~255k tokens). See [[log]].

## The four research pillars

1. [[Fleek Company Profile]] — who Fleek is: ~$50M raised per the JD (public sources total ~$45M, incl. the $25M Series B of 8 Jul 2026 — use Fleek's own number when speaking to Fleek), a16z/YC/eBay-backed, wholesale secondhand marketplace. Runs a **1,000+ creator roster on an internal Content Brain**, with recruitment largely automated; the public surface shows only informal `RFD-` codes, which is why this vault originally — and wrongly — inferred there was no programme. Corrected 2026-07-10 against `mission/job-description.md`.
2. [[Vintage Reseller Creator Ecosystem]] — the audience: nano/micro reseller-creators whose bale-unboxing and thrift-haul content already sells the format. They're *already buyers* of stock.
3. [[Affiliate Program Playbooks]] — the operating manual: activation rate is the one real metric, GMV follows a power law, seed-then-concentrate, personalise briefs but don't over-script. (Half the open web here is blogspam — marked.)
4. [[Competitor Creator Programs]] — the differentiation map: Whatnot is the benchmark; Vinted has *nothing*; nobody fuses commission with wholesale sourcing.

## The FR ops layer (2026-07-09 Perplexity sweep — feeds the live engine)

Operational ground truth for the French discovery/outreach/brief pipeline:

1. [[FR Reseller Vocabulary and Hashtags]] — the scrape's keyword seeds. ⚠️ Weakest lane; hypothesis list that the discovery run itself validates (Brain proposes → scrape verifies).
2. [[FR Resale Platform Landscape]] — Vinted 0%-fee volume lane (pros camouflage as closet-cleaners), Whatnot FR = live-selling hub, Vestiaire = luxury. Platform presence → scoring signals.
3. [[FR Creator Content Formats]] — hauls-with-storytelling rising, generic hauls fading; bale unboxing IS the product demo. → brief rules.
4. [[TikTok Shop France]] — live since 2025-03; **81.7% affiliate dependency, €31.98 avg unit price**. France is structurally affiliate-first: exec-summary stat. *(2026-07-09: +commission %s + By-Application resale gate.)*
5. [[Wholesale Sourcing and Buying Triggers FR-EU]] — named grossistes, the complaint list (opaque sorting, fake Grade A, MOQs), switch triggers. → outreach ammunition.

## The deep-dive layer (2026-07-09 second Perplexity sweep — 25 Q, France-primary)

A thorough enrichment pass to harden the foundation. Weighted to the four documented backlog gaps:

1. [[French Reseller Community Sentiment]] — **the practitioner voice** (#1 gap): real Trustpilot bale complaints ("Grade A" = dirty/stained/unsellable), named fripier "Jules", TikTok Shop = "most frustrating for support". The bale-complaint list is pre-written outreach copy.
2. [[French Reseller Creator Shortlist]] — **the seed list** (#2 gap): named FR micro creators — Na Nin Vintage (Hannah Stioui), @emmaverdierkremer, @veryfrip, Zoé Léger, Nawal Bonnefoy. Treat as hypotheses the discovery scrape verifies.
3. [[Supplier and B2B Referral Mechanics]] — **Fleek's analogues** (#3 gap): bale suppliers almost never run referral programs (= whitespace); Faire/Ankorstore mechanics to borrow; the commission-stacking edge only Fleek escapes.
4. [[Creator Affiliate Mechanics]] — **the operating manual, deeper**: FR is coupon-first not influencer-first; tiering/payout models; the activation playbook (14-day first-sale challenge, seeding, buddy system).
5. [[French Secondhand Market Trends 2026]] — **the "why now, why France" backdrop**: Vinted is France's biggest clothing retailer; +140% in 2yrs; anti-fast-fashion laws; social-first discovery.

## The deep-read layer (2026-07-09 — primary-source method: fetch + deep-read named sources, not AI summaries)

The richness upgrade. One Substack + a 4-agent fan-out over named French primary sources — the method that fixed the "not rich enough" thinness. Governed by the [[Enrichment Leads Backlog]] (job-first, `Feeds:`-guarded, run as manual passes).

1. [[Paris Secondhand Retail Map]] — 9 named boutiques + 5-tier taxonomy; the Marais/Rue de Turenne cluster gives geo-content a literal address.
2. [[French Cities Secondhand Retail Map]] — Lyon/Marseille/Bordeaux/Lille/Nantes/Toulouse/Strasbourg named shops, the national kilo-pricing standard (€20–60/kg), MMV Lyon + Braderie de Lille.
3. [[FR Bale Sourcing Playbook]] — the grossiste directory, grade vocabulary (crème/original/A-B-C), bale economics (x3–5 realistic, 20–40% waste), scam red-flags. The supply reality Fleek beats.
4. [[Enrichment Leads Backlog]] — the compounding to-do: leads every source spawned + the method itself.
- Also deep-enriched: [[French Reseller Creator Shortlist]] (Nathan Vialle bulk→Whatnot, Bichette Kids bale-unboxing), [[French Secondhand Market Trends 2026]] (institutional numbers + anti-fast-fashion law dated 29 Jun 2026), [[French Reseller Community Sentiment]] (verbatim grade-scam quotes), [[FR Reseller Vocabulary and Hashtags]] (trade + retail vocab).

## The empirical layer (2026-07-09 — the engine feeds the Brain back)

Ingested from the live Airtable roster the discovery engine built. This is where the loop closes: research proposed → scrape verified.

- [[FR Creator Roster and Segments]] — **49 scored FR reseller-creators**, segment taxonomy + economics (sourcing vloggers score highest at 70; wholesale buyers lowest of the serious segments at 55), the top targets, and DM-first outreach reality (only 6/49 have email).
- **⚠️ The tension it exposes**: Fleek's highest-intent creators (`felixbeauregard`, `JosephTorregrossa`, `Bartorico`, `jf_vintagewholesalefr`) are **incumbent sourcing-monetizers** — educators with their own supplier funnels, or competing grossistes. The *program* space is greenfield; the *audience* space is already monetized. → pitch partnership/rev-share, not "promote us instead."
- ✅ [[FR Reseller Vocabulary and Hashtags]] now carries the **validated hashtag table** (real per-term qualified-creator counts) — the deck receipt the founding sweep owed.
- [[Creator Post-Level Signals]] — **588 real posts** (300 TikTok + 288 YouTube) from the top 24 creators, $1.20 of Apify. The ground-truth layer. It **corrected four vault claims**:
  1. 🚨 **Julia Courcelle is a live, unmanaged Fleek affiliate** (`RFD-JULIA` in 25/25 videos) — *and promotes a competing wholesaler in the same description.* Field evidence for the JD's "roster, not activation" thesis. She sits in Airtable as a cold prospect → **scoring bug**.
  2. **Competing wholesalers DO run creator deals** (bestvintagewholesale, supply-lab, boxwholesalefrance) — falsifies the "suppliers never run referral programmes" whitespace claim in [[Supplier and B2B Referral Mechanics]]. The real whitespace: nobody runs a *structured* programme.
  3. **Whatnot's FR partner programme is active and dominant** — 72 links; `#whatnotpartner` median **786k plays**, the top tag in the sample.
  4. **Creator language ≠ supplier jargon**: they say `kilo` (96), `premier choix` (60), `en gros` (33); they never say `ballot`/`crème` (1 each). Also: **geo-tags are empirically real in France** (`#friperiemontpellier` 45) — closing an "unverified/US-extrapolated" gap.

## 🎯 The strategic thesis (why this case study wins)

> [!CAUTION] **Revised 2026-07-10.** The original first bullet read *"Fleek has no structured creator program —
> greenfield, not a fix-up."* That was inferred from Fleek's public surface and is **false**. The JD describes a
> 1,000+ creator roster, recruitment largely automated, running on an internal Content Brain. See the correction
> on [[Fleek Company Profile]] and the full list in `mission/mission.md`. The thesis below is the surviving
> version — **it needs Doug's sign-off before it drives the deck.**

Three findings converge into one wedge:

- **Fleek has the roster but not the activation** (`mission/job-description.md`) — 1,000+ creators, recruitment
  automated, and *"the next chapter is keep scaling recruiting while activating better at scale."* The problem
  is not finding creators. It's getting the ones they have to post.
- **Its creators are already buyers** ([[Vintage Reseller Creator Ecosystem]]) — sourcing is their #1 time-sink, so promoting Fleek helps them *operationally*, before any commission.
- **No competitor can copy the obvious offer** ([[Competitor Creator Programs]]) — rivals pay for *either* sales *or* content; **only a wholesale marketplace can pay commission AND give wholesale sourcing margin in one relationship.**

→ The pitch: a creator program where the reward is *become a better-stocked reseller who also earns commission*. The [[Affiliate Program Playbooks]] tell you how to run it at scale — **activation % as the north star** (which is exactly Fleek's own JD headline metric), a small top tier carrying GMV, one operator running many segmented campaigns via tooling not headcount. That's the Content Brain.

**The sharper wedge, unused so far:** Fleek's own hardest problem, in their words, is that *"many [pro
resellers] think Fleek is for beginners and not for them."* Pro resellers are fewer and much higher value. A
creator programme aimed at *pro* credibility — real sourcing, real margins, live-selling operators — attacks
the perception problem and the acquisition number at once. Nothing in this vault addresses it yet.

## How this feeds the engine

| Vault insight | Content Brain component |
|---|---|
| Activation % is the north-star metric | Segmentation + activation targeting |
| GMV power law (20% → 80%) | Budget engine (reallocate to best-CAC segments) |
| Personalise briefs, don't over-script | Brief Generator agent |
| Creators are already buyers (wedge) | The core value-prop / positioning |
| Per-partner CAC, recalculated | Feedback loop agent |

## Biggest gaps to fill next (research backlog)

- ~~**Reddit/Discord practitioner sentiment**~~ → ✅ **largely closed 2026-07-09**: [[French Reseller Community Sentiment]] now carries on-thread Reddit verbatim voice (via PullPush + redlib mirror — Reddit is bot-blocked to WebFetch) + a **subreddit congregation map** (closes the "where they congregate" lane) + the anti-reseller-sentiment goldmine. Apify Reddit actor built for a fuller scaled run (quota-blocked, pending reset). Remaining: private FB groups still unreached; Discord unmined.
- ~~**TikTok Shop** resale/thrift affiliate mechanics~~ → ✅ fully swept 2026-07-09: [[TikTok Shop France]] now has creator-side commission %s (10–25%, up to 50%) **and** the By-Application resale-category gate.
- **Named FR reseller creators** shortlist — 🟡 *partially closed 2026-07-09*: [[French Reseller Creator Shortlist]] has named FR micro creators (IG-heavy); **verified TikTok handles + live metrics still owed** — the Apify discovery run confirms/extends the list.
- ~~**Wholesale-supplier referral programs**~~ → ✅ swept 2026-07-09: [[Supplier and B2B Referral Mechanics]] — the finding is they mostly *don't exist* (the whitespace). Remaining: direct-competitor (BankandVogue etc.) terms.
- ~~**Hashtag validation table**~~ → ✅ **done 2026-07-09**: real per-term qualified-creator counts written back into [[FR Reseller Vocabulary and Hashtags]] from the 49-creator Airtable roster. Headline: intent *phrases* ("vendeur vinted astuces", "vivre de la revente") outperform bare hashtags; `friperieengros` is the highest-precision sourcing tag; `friperie` is the #1 content keyword (16/49).
- **Post-level creator content** — the roster holds the engine's *analysis*, not raw captions/transcripts. Ingesting what creators actually *say* needs Apify post-scraping (quota-blocked). New gap, 2026-07-09.
- **FR-specific virality/format metrics** — [[FR Creator Content Formats]] Q10 data is US-extrapolated; the scrape must measure FR empirically. (New gap surfaced 2026-07-09.)

## Meta

- **Agent**: `~/.claude/agents/research-scout.md` (reusable, token-capped: ≤6 searches / ≤8 fetches / ≤1,200 words per scout). Re-run any lane by spawning it with a new topic.
- **Provenance**: every claim links its source; single-sourced or blocked-fetch claims are marked *(unverified)* — kept honest, not laundered.
- **Log**: [[log]]
