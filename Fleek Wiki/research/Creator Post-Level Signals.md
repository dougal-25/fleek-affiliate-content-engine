# Creator Post-Level Signals

> What the top creators **actually post** — 588 real posts (300 TikTok captions/hashtags + 288 YouTube titles/descriptions) scraped via Apify on 2026-07-09 from the 24 highest-scoring on-category creators. This is the ground-truth layer beneath [[FR Creator Roster and Segments]] (which holds the engine's *analysis*, not their words).
> Spend: **$2.26 actual** (of a $5 free-tier hard cap; $2.74 left). Per-result quotes were $0.51 + $0.69 = $1.20 — **the actor's pay-per-result price excludes Apify platform/proxy usage, so budget ~2× the quoted rate.** Raw: `_raw/apify_tiktok_posts_2026-07-09.jsonl`, `_raw/apify_youtube_posts_2026-07-09.jsonl`.
Part of [[index]] · siblings: [[FR Creator Roster and Segments]], [[FR Reseller Vocabulary and Hashtags]], [[Competitor Creator Programs]], [[Supplier and B2B Referral Mechanics]]

## 🚨 Finding 1 — a named member of "the existing French community you inherited", running unmanaged

The task brief asks the candidate to activate *"the partners you recruit **and the existing French community you inherited**"*, and states *"a signed partner who never posts is worth nothing."* **This scrape found one of those inherited partners, by name, in the field.**

**Julia Courcelle** (YouTube, "Live seller", engine score 62, Airtable stage *"Prospect / Not started"*) promotes Fleek in **25 of 25** recent videos, ongoing (latest 2026-07-05). Verbatim from her descriptions:

> `🚀Fleek: https://joinfleek.app.link/PkYDOWspRRb` **`Code promo RFD-JULIA = 30€ sur votre première commande`**

**And in the same description she promotes a direct competitor:**
> `https://bestvintagewholesale.com/discount/JULIA10` — **`Code promo JULIA10 = 10% de réduction`**

This is **independent field evidence for the revised thesis** ([[Fleek Company Profile]], corrected against the JD: Fleek *has* a 1,000+ creator roster; the problem is **activation, not recruitment**). Three concrete consequences:

1. **She is posting, but nobody is managing her.** Fleek's link sits *beside a competitor's*, and the rival's code is **better branded** — `JULIA10` (personal, memorable) vs `RFD-JULIA` (system-generated). Unmanaged partners drift to whoever supports them best.
2. **The engine mis-scored an active affiliate as a cold prospect** — `Stage=Prospect · Outreach Status=Not started` on a creator who already sells Fleek. Discovery must scan for existing `joinfleek` / `RFD-` links and set `Stage = Active affiliate`.
3. **A ready-made deck artifact.** One screenshot of her description — Fleek and a competitor's code side by side — *is* the activation problem, evidenced from outside the company.

**Deck line this unlocks:** *"Your French community is already posting. It's just posting your competitor's code too."*

## 🚨 Finding 2 — Competing wholesalers DO run creator programs (falsifies a vault claim)

[[Supplier and B2B Referral Mechanics]] concluded bale/wholesale suppliers "almost never run public referral or affiliate programs — this is the whitespace." **The post data refutes that for the FR creator market.** Named, with link counts:

| Supplier promoted | By | Links | Mechanic |
|---|---|---|---|
| **bestvintagewholesale.com** | Julia Courcelle | 25 | personal discount code `JULIA10` (10% off) |
| **supply-lab.com** (`apply.supply-lab.com`) | Enzo Napiot | 21 | application funnel |
| **boxwholesalefrance.com** | TRFQNT | 4 | link-in-description |
| **wholesaler20.com** | Felix Beauregard | 1 | link-in-description |

Correction: the *whitespace* is not "no supplier runs a programme." It is that **no supplier runs a structured, tiered, supported programme** — they run ad-hoc discount codes. That's a narrower but still real wedge.

## 🚨 Finding 3 — Whatnot is aggressively acquiring these exact creators

- **72 whatnot.com description links** across the cohort — Julia Courcelle (50), Alex Yedder (22).
- On TikTok, **`#whatnotpartner` posts have a median 786,250 plays** (n=4) — the highest-performing tag in the entire 300-post sample; next best is `#storytime` at 219k.
- → Whatnot's FR creator partner programme is **active, funded, and its content outperforms everything else.** It is the competitor to beat, not a hypothetical benchmark. Updates [[Competitor Creator Programs]].

## Finding 4 — The platform split is a content split (this changes brief strategy)

Vocabulary counts from real captions/titles reveal two different worlds:

| Term | TikTok (300 posts) | YouTube (288 videos) |
|---|---|---|
| friperie | **44 tags + heavy** | 10 |
| kilo | **96** | 3 |
| premier / 1er choix | **60** | ~0 |
| vinted | 42 | **390** |
| revente / achat revente | 23 | **308** |
| fournisseur | 7 | **109** |
| formation (course) | ~0 | **87** |
| chine (China sourcing) | ~0 | **63** |
| whatnot | 29 | **123** |

**TikTok = friperie / au-kilo / live-selling.** **YouTube = Vinted-resale business, courses, suppliers, sneakers.** They are not the same audience. Briefs must be platform-native, and *YouTube is where the wholesale-buyer intent lives* — but also where the incumbent educators own the funnel.

## Finding 5 — The vault's trade vocabulary is supplier jargon, not creator language

[[FR Bale Sourcing Playbook]] documents `ballot`, `balle`, `crème`, `Grade A` from grossiste blogs. Creators barely use them:

- **TikTok**: `kilo` 96 · `premier choix`/`1er choix` 60 · `en gros` 33 — vs `ballot` **1**, `balle` **1**, `crème` **1**.
- **YouTube**: `fournisseur` 109 · `grossiste` 33 · `en gros` 24 — vs `ballot` **3**, `kilo` 3.

→ **Speak "au kilo / premier choix / en gros / fournisseur" in briefs and outreach.** `Ballot`/`crème`/`Grade A` is B2B supplier register — right for a supplier page, wrong for a creator DM.

## Finding 6 — Geo-tags are real in France (closes an "unverified" gap)

[[FR Creator Content Formats]] flagged geo-tagged content as **US-extrapolated, unverified**. Now measured: `#friperiemontpellier` **45** · `#vintagemontpellier` 21 · `#friperieparis` 11 · `#bonneadresseparis` 11. Geo-tagging is a live FR practice. **Gap closed empirically.**

New FR content genre the vault had no record of: **`#preparationcommande` (26)** — "order prep" videos (packing, sorting stock). Also `#asmrvintage` (13), `#liveshopping` (23), `#vintedtips` (29).

## The incumbent-funnel map (who owns these audiences today)

| Creator | Their own funnel / partners |
|---|---|
| **Bartorico** | `resellpro.net` (own course, 52) + **`amzn.to` × 198** (Amazon affiliate) |
| **Joseph Torregrossa** | `profimy-academie.com` (70), `josephtorregrossa.systeme.io` (62), Telegram (30) |
| **Felix Beauregard** | `resellvinted.com` (48 — own supplier/course) |
| **Enzo Napiot** | `apply.supply-lab.com` (20) |
| **Alex Yedder** | **whatnot.com (22)** + `alexyedder.com` (17) |
| **Julia Courcelle** | **whatnot.com (50) + joinfleek (25) + bestvintagewholesale (25)** |
| Gaspard D | Telegram (43) + systeme.io funnels |

→ Confirms and sharpens the incumbent-monetizer tension in [[FR Creator Roster and Segments]]: **every top YouTube creator already monetises an audience of resellers**, mostly via courses + supplier codes.

## Reach reality (the engine's scores don't track attention)

- `Joseph Torregrossa` — engine score **78**, but **median 514 views** on recent videos (channel lifetime 4.3M). High score, dead reach.
- `fripeinstoregrossiste` (TikTok) — **median 182 plays**. `lina_momo_` — **43,700**.
- **26/300 TikTok posts are sponsored** — concentrated in `lina_momo_` (12), `jbaptistebc` (6), `dresscodegap` (5). The grossiste accounts (`mimifrip`, `fripenlignes`, `fripeinstoregrossiste`) take **zero** brand deals — they *are* the brand.

→ **Add a recency-weighted reach signal to scoring.** Lifetime channel views and follower count both mislead.

## Open questions / gaps
- **Transcripts not pulled** (cost/volume) — what creators *say* on camera about suppliers is still unmined. `downloadSubtitles` on the YouTube actor would get it.
- **2 Instagram creators** (`jf_vintagewholesalefr`, `fripe_paradise`) not scraped this pass.
- Sneaker/streetwear contamination: `SunLight`, `Enzo Napiot`, `Math Uzumaki` are largely **sneaker resell**, not friperie — segment filter needed.
- Whether Julia's `RFD-JULIA` code was issued by Fleek or self-generated — unknown, and worth asking Fleek. *(unverified)*

Feeds: **positioning** ("you already have affiliates, unmanaged"; Whatnot is the live competitor), **scoring** (existing-affiliate check; recency-weighted reach), **outreach** (creator-native vocabulary; personalised codes), **briefs** (platform-split, geo-tags, `preparationcommande` genre), **discovery** (validated FR hashtags).

### Sources
- Apify `clockworks/tiktok-scraper` — 300 posts, 10 creators, 2026-07-09. Raw: `_raw/apify_tiktok_posts_2026-07-09.jsonl`
- Apify `streamers/youtube-scraper` — 288 videos, 12 channels, 2026-07-09. Raw: `_raw/apify_youtube_posts_2026-07-09.jsonl`
- Creator selection: score ≥62 + on-category segment, from `_raw/airtable_creators_2026-07-09.json`
- Ingest tool: `~/.claude/skills/wiki-knowledge-base-builder/scripts/apify_creator_posts.py`
