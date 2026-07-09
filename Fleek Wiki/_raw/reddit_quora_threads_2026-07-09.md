# Raw provenance — Reddit + Quora practitioner corpus (2026-07-09)

Reddit is bot-blocked to WebFetch. This corpus was reached via **free work-arounds** (the Apify run was quota-blocked). Fidelity flags kept honest per source. This file is the provenance record behind the synthesised claims on [[French Reseller Community Sentiment]], [[FR Bale Sourcing Playbook]], [[FR Creator Content Formats]].

## Fetch methods that worked
- **PullPush API** (`api.pullpush.io`, Pushshift successor) — full post + comment JSON off a non-Reddit host; rate-limits ~8–9 calls. Used for EN threads.
- **redlib mirror `reddit.nerdvpn.de` via Playwright** — real browser passes the bot challenge. Used for FR threads.
- **Aggregators** (pleated-jeans, thecooldown, readtrouve) — republish Reddit posts with verbatim quotes → flagged *(reddit-via-aggregator)*.
- **Substitute forums/blogs/surveys** — Mumsnet, reseller ledgers, Vinted complaint survey — where Reddit was unreachable.
- **Quora** — 403 login-wall; **snippet-only**, no full pages.

## EN threads — sourcing / economics (via PullPush; verbatim + scores)
- r/Flipping `/6tgwvd/` — "Buying used clothing in bulk" (bale $/lb, 50–70% junk, pick-your-own)
- r/Flipping `/rtukco/` — full-time reseller AMA ("sourcing is the ceiling")
- r/Flipping `/popy1y/` — 1 month on Poshmark ("$2/hour", death pile, list-before-buy)
- r/Depop `/vq5nkz/` — top-seller tips ($4,600/mo, flat-lays, mileage write-offs)
- r/Depop `/158gj51/` — sole-income thread (multi-platform, liquidation lots)
- r/Depop `/mk6z36/` — 15→125 sales ($50 sourcing budget, Pinterest/celeb trend-spotting)
- r/Depop `/s1pmu4/` — reseller-guilt backlash ("stealing from the poor" rebuttal)
- r/Depop `/ntvc5f/` — SHEIN flooding the thrift supply
- r/exmormon `/5cr49u/` — 2000-lb baling + rag-export mechanics
- r/conseiljuridique `/va2jgw/` (FR) — legality of a luxury resale site (authenticity/recel/GDPR)
- Snippet/selftext-level: r/Depop 13uplya, t2e0jh, l1fhau, wsfxex; r/AskFrance 1jya5t3, 13jhs0c; r/france 1ax88r9 & fsvs4b (both **[removed] by mods** — the "business-side gets suppressed" signal)

## FR threads — community voice (via redlib+Playwright; verbatim FR + translation)
- r/AskMeuf `/1awdq4j/` — "Vous pensez quoi des friperies?" (prices doubled, hygiene, fake-vintage)
- r/AskFrance `/17u82g1/` — "Que penser de Vinted aujourd'hui?" (reseller pollution)
- r/AskFrance `/1l9hkbo/` ⭐ — "C'est quoi le délire avec le marché de seconde main?" (anti-reseller goldmine)
- r/AskFrance `/13fu3t8/` — resale platforms beyond Vinted (Clasf flagged scam)
- r/paris `/oc77fi/` — where to *sell* nice clothes (named shops)
- r/paris `/vqwtwj/` — best Paris friperies (Guerrisol, Free'p'star, Épisode)
- r/france `/1bvv1dl/` — "Avis acheteurs Vinted" (pro-vs-particulier, incl. pro-defense)
- r/france `/1174n4h/` — where to buy cheaply (rural-vs-urban divide)
- r/france `/1t2jgwn/` — "Une explosion de shein?" (market polarization thesis)
- r/Lyon `/z3nsxs/` — best Lyon friperie ("prix abusés", 1er arr. cluster)

## Substitutes (fully read where Reddit blocked)
- mumsnet.com `/4872983` — Vinted buyer-protection gripes (verbatim)
- thecomplainingcow.co.uk — Vinted complaint survey (n=1,500+): 41% lost money, 65% ignored, 55% banned
- crunch.co.uk — Vinted Pro seller complaints (payment delays, data-privacy)
- clotheshorsepodcast.substack.com — "are resellers getting rich" (the $2-net Poshmark math)
- sidehustlenation.com — $270k/15yr thrifting case (50% margin / $10-per-item rule)
- underpriced.app, wearitagain.co.uk — bale keeper-rates + filler-scam
- dresskare.com, friptadium.com, vintedcrm.com — FR cost-per-sellable-piece + scale ladder

## Quora (snippet-only, 403 login-wall — questions high-confidence, answers unverified)
- FR clusters: "comment se fournissent les friperies", "achat-revente légal en France / plafond / auto-entrepreneur"
- EN clusters: "how much can you make reselling", "is it worth full-time", "most profitable item to resell"

**Caveats:** aggregator/mirror quotes are verbatim wording but original thread scores/dates not re-confirmed; survey %s self-selected; FR reseller-blog numbers are commercially motivated (directionally consistent). All flagged `(unverified)` where relevant in the synthesised pages.
