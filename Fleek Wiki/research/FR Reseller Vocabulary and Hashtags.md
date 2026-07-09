# FR Reseller Vocabulary and Hashtags

> The French-language search vocabulary the discovery engine scrapes with — proposed by research, validated empirically by the scrape itself.
Part of [[index]] · siblings: [[FR Creator Content Formats]], [[FR Resale Platform Landscape]]

⚠️ **Reliability note:** this lane came back the weakest of the 2026-07-09 sweep — the source set was mostly English-language hashtag aggregators and the answer contained self-contradictions (it argued `#friperie` isn't a French word; it is — *friperie* = thrift shop). Everything below is a **working hypothesis list**, marked *(unverified)* as a set. The validation mechanism is the engine itself: hashtags that return real FR reseller content in the Apify scrape are confirmed; duds get dropped. Brain proposes → scrape verifies.

### Working hashtag list (v1 — for the discovery scrape)

**Core resale terms (high confidence — standard French):**
- `#friperie` — thrift shop; THE core FR thrift tag
- `#fripe` — colloquial short form (unverified)
- `#secondemain` — secondhand
- `#vinted` — platform tag, used by Vinted sellers [source](https://www.underpriced.app/blog/vinted-selling-guide-europe-2026)
- `#revente` — resale; leans professional reseller (unverified)
- `#sourcing` — English adopted by FR pros (unverified)

**Scene / niche tags (unverified — validate in scrape):**
- `#thriftfrance`, `#vintageparis`, `#modecirculaire` (circular fashion), `#modedurable`, `#secondechance`, `#vintagefrance`, `#friperieenligne`

**Caption phrases seen in FR resale content (unverified):**
- « ça c'est un vrai vintage » · « sourcing de folie » · « nouvelle collection friperie »

### Slang by user type (unverified sketch)
- Young resellers (18–25): #fripe, #ootdfr, GRWM formats
- Professional resellers: #revente, #vinted, #sourcing, #modecirculaire
- Eco-positioning sellers: #secondemain, #modecirculaire

### 2026-07-09 deep-read enrichment — confirmed vocabulary (upgrades the weak lane)

**Hashtags actually used by FR resale creators** (from deep-read creator content, higher confidence than v1):
`#friperie` `#friperieparis` `#friperiepascher` `#fripeparis` `#haulfriperie` `#vintagehaul` `#secondemain` `#secondemainvintage` `#balledefriperie` `#emmaus` (>80M views) `#defiriendeneuf` (~13K posts) `#freepstar` `#thrift`.

**Trade grade-vocabulary (the sourcing language — was entirely missing):**
- **balle / ballot** — compressed bale (10–50kg) · **au kilo** / **à la pièce** — by weight / by item
- **original** — unsorted raw stock (cheapest, riskiest) · **crème / extra crème** — near-new top tier
- **grade A / B / C** — like-new / light-wear / acceptable; **A+ CRÈME** = top-of-A
- **tri / trié / 1er choix** — sorting / sorted / first-pick · **dégriffé** — label removed
- **semi-grossiste** — buy smaller/cherry-picked lots · **déballage** — bale-unboxing content · **colis mystère** — mystery box
- Full definitions + economics on [[FR Bale Sourcing Playbook]].

**Retail shop-type vocabulary** (from the city maps):
- **friperie** (frip' / la fripe) — thrift shop · **dépôt-vente** — consignment · **ressourcerie / recyclerie** — reuse centre
- **friperie solidaire** — charity thrift (Emmaüs, Croix-Rouge) · **vente au kilo/au poids** — by weight
- **brocante** — flea/antiques market · **vide-grenier** — car-boot · **vide-dressing** — wardrobe-clearing sale · **braderie** — big street clearance (Lille) · **troc** — barter · **destock/déstockage** — clearance
- Full context on [[Paris Secondhand Retail Map]] + [[French Cities Secondhand Retail Map]].

**Correction logged**: v1 wrongly doubted `#friperie` — confirmed the core FR thrift tag.

### Open questions / gaps
- Real FR-native tag frequencies still unknown — **first scrape run reports back actual result counts per tag** (that table becomes a deck receipt).
- Live-selling vocabulary (Whatnot FR streams) — partial; `#whatnotfr` + déballage/live terms to validate.
- Add validated tags back to this page after each discovery run (engine feeds Brain, not just Brain feeds engine).

Feeds: **discovery** (Apify keyword seeds), **outreach** (caption vocabulary), **briefs** (native phrasing).

### Sources
- https://best-hashtags.com/hashtag/resale/ — EN aggregator, weak
- https://agencygdt.com/blog/best-tiktok-hashtags-for-clothing-brands/ — EN aggregator, weak
- https://www.underpriced.app/blog/vinted-selling-guide-europe-2026 — Vinted seller guide
- Full raw answer: `_raw/perplexity_fr_sweep_2026-07-09.jsonl` (Q1)
