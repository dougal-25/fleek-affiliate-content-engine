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

### ✅ VALIDATED — the hashtag table, from the live discovery run (2026-07-09)

The loop closed: **the engine fed the Brain back.** These are the seed terms that actually returned *qualified* FR reseller-creators into Airtable (n=49). This is the deck receipt.

| Seed term | Qualified creators found | Verdict |
|---|---|---|
| `secondemain` | 7 | ⭐ top producer |
| `vendeur vinted astuces` (phrase) | 7 | ⭐ top producer — phrases beat tags |
| `revente` | 5 | strong |
| `friperieengros` | 4 | strong — highest sourcing-intent |
| `friperie` | 3 | core term |
| `friperieenligne` · `revendeur` · `ventelive` · `whatnotfrance` · `fripe` · `grossiste` · `vivre de la revente` | 2 each | productive |

**Confirmed by content, not just search:** across the 49 creators' content keywords, **`friperie` is the single most common term (16 mentions)**, then `vinted` (9), `secondhand` (8), `achat revente` (6), `grossiste` (5). Sourcing vocabulary (grossiste, vente en gros, destockage, fournisseur, ballot) is pervasive.

**Learnings for the next scrape:**
- **Intent phrases outperform bare hashtags** — "vendeur vinted astuces" and "vivre de la revente" pulled as well as any tag, and pulled *higher-scoring* creators (educators, sourcing vloggers).
- `friperieengros` is the highest-precision sourcing tag (finds wholesale-buyer intent, not shoppers).
- `whatnotfrance` + `ventelive` are the live-selling doorway — **`#whatnotfr` now validated** in its `whatnotfrance` form.
- Full roster + segment economics: [[FR Creator Roster and Segments]].

### ✅ v3 — measured from 588 real posts (2026-07-09 post-level scrape)

**Top TikTok hashtags actually used** (n=300 posts, 10 creators): `#friperiemontpellier` 45 · `#friperie` 44 · `#vinted` 42 · `#friperieengros` 30 · `#friperiedequalité` 29 · `#friperieenfants` 29 · `#vintedtips` 29 · `#preparationcommande` 26 · `#vintage` 26 · `#achatrevente` 23 · `#liveshopping` 23 · `#friperieaukilo` 22 · `#vintagemontpellier` 21 · `#secondemainvintage` 19 · `#friperieenligne` 18 · `#achatreventevinted` 16 · `#fairedelargent` 14 · `#asmrvintage` 13 · `#friperieparis` 11 · `#bonneadresseparis` 11.

**Highest-reach tag by a distance: `#whatnotpartner` — median 786,250 plays** (n=4). Geo-tags are real (Montpellier, Paris).

### ⚠️ Correction — the trade vocabulary is SUPPLIER jargon, not creator language

[[FR Bale Sourcing Playbook]] documents `ballot / balle / crème / Grade A` from grossiste blogs. **Creators barely say those words.** Measured:

| Creators say (TikTok) | n | Blogs say | n |
|---|---|---|---|
| `kilo` | **96** | `ballot` | 1 |
| `live` | 92 | `balle` | 1 |
| `premier choix` / `1er choix` | **60** | `crème` | 1 |
| `en gros` | 33 | `palette` | 1 |

On YouTube: `fournisseur` **109** · `grossiste` 33 · `en gros` 24 — vs `ballot` 3, `kilo` 3.

→ **Outreach + briefs must speak "au kilo / premier choix / en gros / fournisseur."** Keep `ballot`/`crème`/`Grade A` for supplier-facing pages only.

**Platform vocabulary split:** TikTok = `friperie`, `kilo`, `premier choix`, `live`. YouTube = `vinted` (390), `revente` (189), `achat revente` (119), `fournisseur` (109), `formation` (87), `chine` (63). Different worlds → different seeds, different briefs.

### Open questions / gaps
- Per-tag *post volumes* (platform-wide) still unmeasured — we have per-creator usage, not tag reach across TikTok.
- **Spoken** vocabulary (video transcripts) still unmined — `downloadSubtitles` on the YouTube actor would get it.
- Keep appending validated terms after each discovery run (engine feeds Brain, not just Brain feeds engine).

Feeds: **discovery** (Apify keyword seeds — now evidence-ranked), **outreach** (caption vocabulary), **briefs** (native phrasing).

### Sources
- https://best-hashtags.com/hashtag/resale/ — EN aggregator, weak
- https://agencygdt.com/blog/best-tiktok-hashtags-for-clothing-brands/ — EN aggregator, weak
- https://www.underpriced.app/blog/vinted-selling-guide-europe-2026 — Vinted seller guide
- Full raw answer: `_raw/perplexity_fr_sweep_2026-07-09.jsonl` (Q1)
