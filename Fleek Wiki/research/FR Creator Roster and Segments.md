# FR Creator Roster and Segments

> The live creator roster — 49 French reseller-creators discovered, enriched and scored by the engine, ingested from Airtable ("Fleek Affiliate Ecosystem" → Creators) on 2026-07-09. This is the **empirical** creator layer; [[French Reseller Creator Shortlist]] is the press-sourced complement.
> ⚠️ Fields are the engine's *analysis* of each creator (bio, keywords, score rationale) — **not raw post transcripts**. Deeper post-level ingest needs Apify (quota-blocked).
Part of [[index]] · siblings: [[French Reseller Creator Shortlist]], [[FR Reseller Vocabulary and Hashtags]], [[Supplier and B2B Referral Mechanics]]

### 🚨 Scoring bug found 2026-07-09 — an active Fleek affiliate is scored as a cold prospect

**`juliacourcelle`** sits here as `Score 62 · Stage: Prospect · Outreach Status: Not started`. The post-level scrape ([[Creator Post-Level Signals]]) shows she has promoted **Fleek in 25 of 25 recent videos** (`joinfleek.app.link`, code `RFD-JULIA`), ongoing. She is not a prospect — she is an **active, unmanaged affiliate**.

**Fixes this implies for the engine:**
1. **Existing-affiliate check** in discovery — scan bio/description links for `joinfleek` / `RFD-` and auto-set `Stage = Active affiliate`.
2. **Recency-weighted reach** in scoring — `JosephTorregrossa` scores **78** on a channel whose recent videos median **514 views**. Follower count and lifetime views both mislead.
3. **Sponsored-post signal** — 26/300 TikTok posts were sponsored (concentrated in `lina_momo_`, `jbaptistebc`), proving brand-deal willingness. The grossiste accounts take zero — they *are* the brand.

### ⚠️ The strategic tension this roster exposes

**Fleek's highest-intent creators are largely incumbent sourcing-monetizers.** *(Now confirmed with their actual funnel links — see the incumbent-funnel map on [[Creator Post-Level Signals]]: Bartorico → resellpro.net + 198 Amazon affiliate links; Joseph Torregrossa → profimy-academie.com; Felix Beauregard → resellvinted.com; Enzo → supply-lab.)* The top scorers already sell supplier access to the exact audience Fleek wants:
- `felixbeauregard` (82) — *"already funnels his audience to his own 'private suppliers'"*
- `JosephTorregrossa` (78) — monetizes courses + affiliate links to wholesale sourcing
- `Bartorico` (72) — runs a paid reselling course ("Resell Pro") with its own supplier funnel
- `jf_vintagewholesalefr` (74) — **is a competing French vintage wholesaler (since 1982)**

This refines the vault's greenfield thesis: the **creator-program space is empty** ([[Competitor Creator Programs]]), but the **creator-audience space is already monetized** by educators and suppliers selling sourcing access. → the pitch to these accounts is **partnership / rev-share / supply-partner**, not "promote us instead of your own funnel." The clean-conversion targets are the *sourcing vloggers* and *live sellers* who document buying but don't sell access.

### Segment taxonomy + economics (the scoring layer)

| Segment | n | Avg score | Avg predicted CAC | Read |
|---|---|---|---|---|
| **Sourcing vlogger** | 5 | **70** | £89 | Highest-scoring. Documents buying wholesale on camera — the bale-unboxing/déballage format ([[FR Creator Content Formats]]). Cleanest fit. |
| **Live seller** | 6 | 64 | **£58** | Whatnot/TikTok live; audience primed for referral offers. Best CAC-to-score ratio. |
| **Reseller educator** | 9 | 64 | £122 | High intent **but** competes with own funnels (see tension above). Priciest CAC. |
| **Thrift flipper** | 10 | 57 | £56 | Cheap to acquire; smaller stock appetite. |
| **Wholesale buyer** | 11 | 55 | £75 | *Already buys bulk* — warmest intent, but several are suppliers themselves. |
| **Vinted seller** | 4 | 48 | £89 | Closet-clearers scaling up; thinnest wholesale intent. |
| **General fashion** | 4 | 42 | £119 | Weakest fit — dilute audience, high CAC. |

**Counter-intuitive:** "Wholesale buyer" scores *lowest of the serious segments* (55) despite being the warmest on paper — because the cohort contains competing grossistes. **Sourcing vloggers score highest** and are the segment to lead with.

### The wholesale-buyer cohort (already buying stock)
`jf_vintagewholesalefr` (74, IG 16.7k — vintage wholesale, friperie en gros, made-in-USA) · `mimifrip` (72, TT 18.1k — kids friperie, premier choix) · `TrafiquantDeTextile` (68, YT 8k — **ballot vintage unboxing + profit breakdown**) · `fripenlignes` (68, TT 13.3k — **10€/kilo, Whatnot live, Paris shop**) · `fripeinstoregrossiste` (62) · `sososolyspam` (54 — destockage, **Aubervilliers**) · `turquie_chez_vous` (52 — Turkey sourcing) · plus `christastore229`, `miraculeux_grossiste_dmg`, `sino4852`, `fragrandor93` (accessories/parfum — off-category).

Note the named real-world anchors that match the vault's independent research: **Aubervilliers** (the wholesale market in [[FR Bale Sourcing Playbook]]), **ballot** unboxing, **10€/kilo**, **Whatnot live**.

### Top targets (score · segment · why)
- **alex_yedder** (82 · Sourcing vlogger · YT 182k · **CAC £12**) — films **€1,500 hauls at grossistes** in French. Best score-to-CAC on the board. *Risk: audience skews aspirational streetwear.*
- **felixbeauregard** (82 · Educator · YT 90k · CAC £350) — teaches Vinted resale, audience actively buying inventory. *Risk: own supplier funnel.*
- **JosephTorregrossa** (78 · Educator · YT 43k · CAC £12) — teaches wholesale sourcing for Vinted resale.
- **mathuzumaki** (74 · Sourcing vlogger · YT 28.6k · CAC £180) — visits wholesale suppliers to help friperie/Vinted resellers find stock.
- **lina_momo_** (72 · Live seller · TT 196k · CAC £90) — Whatnot live seller whose audience already responds to referral offers.
- **Bartorico** (72 · Educator · YT 27.5k · CAC £22) — independently surfaced in the Reddit sweep as the FR "teach the resale business" voice ([[French Reseller Community Sentiment]]). **Cross-validated.**

### What they actually talk about (content-keyword frequency, n=49)
**friperie (16)** · vinted (9) · secondhand (8) · achat revente (6) · reselling (5) · **grossiste (5)** · revente (4) · whatnot (3) · vente en gros (3) · destockage (3) · fournisseur (3) · seconde main (3) · streetwear (3) · louis vuitton (3) · luxury resale (2) · wholesale sourcing (2) · grossiste friperie (2) · formation (2) · friperie en ligne (2) · astuces vente (2).

→ **"friperie" is the single dominant term**, confirming the FR-native steer. Sourcing vocabulary (grossiste, vente en gros, destockage, fournisseur, ballot) is pervasive — these creators speak the [[FR Bale Sourcing Playbook]] language natively.

### Outreach reality
Contact routes: **DM 38 · Bio email 6 · Link-in-bio 5.** Only 6/49 have a scrapeable email → **DM-first outreach** is the operating assumption, not an email sequence. (Answers the "do we need Apollo?" question: mostly no.)

### Open questions / gaps
- **No raw post/video content ingested** — Airtable holds the engine's enrichment, not transcripts. Post-level ingest (captions, hooks, actual claims) needs **Apify** (quota-blocked). This is the next real depth step.
- `Audience` populated on only **33/49**; `Contact Email` on 6/49.
- Predicted CAC is model-estimated, **not observed** — no spend yet to validate (£12 vs £350 spread is untested).
- Several "Wholesale buyer" records are accessories/parfum grossistes, off Fleek's category — segment needs a sub-filter.

Feeds: **scoring** (segment economics — lead with sourcing vloggers, not wholesale buyers), **outreach** (DM-first; partnership framing for educators/suppliers), **positioning** (the incumbent-monetizer tension), **discovery** (validated terms → [[FR Reseller Vocabulary and Hashtags]]).

### Sources
- Airtable base **"Fleek Affiliate Ecosystem"** → `Creators` (49 records), read 2026-07-09. Raw snapshot: `_raw/airtable_creators_2026-07-09.json`.
- Produced by `scripts/run_discovery.py` (Apify TikTok/YT scrape → Claude enrich+score against the Brain's rubric → Airtable upsert).
