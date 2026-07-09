# Enrichment Leads Backlog

> The compounding engine of the vault. Every deep-read source names more sources — they land here as the next pass's fuel. This is the "compound" step of the enrichment loop (see method below). Working doc, newest leads on top.
Part of [[index]].

## The enrichment method (agreed 2026-07-09)
**Job-first, not source-first.** Start from a decision the engine must make → reverse-search a French, named-detail-rich **primary source** → deep-read the actual page (WebFetch, not snippets) → synthesise with the `Feeds:` guard (no claim without a downstream job) → **log the leads it spawned here**. Run mode: **manual deep-read passes on demand** (chosen over auto-codify — prove it a few more times first). Veins in priority: creator-trail · practitioner voice · market data & regulation · geo/retail map.

The demon to avoid: **hoarding** — pages that read rich but feed no decision. The `Feeds:` line is the guard.

---

## Open leads (next passes)

### Creator-trail (verify + expand)
- **Verify live** (handles/counts are source-reported, not profile-checked): Nathan Vialle, Bichette Kids, Giulia Castellucci @giu.cst, Emmanuelle Sits, Clara Victorya, Juliette Kitsch, Rosa Boh-neur, Rubi Pigeon. → [[French Reseller Creator Shortlist]]
- **Search-only, unverified TikTok handles to check manually**: @goldenconnexion, @kenza.wldrf (Marseille hauls), @shapnhr, @zoebcr, @heirnathalie, @bygaby06, @bartorico_ (teaches the resale business — high value).
- **Cross-reference**: do the 12 Airtable-scraped creators overlap with any named here? (The reconciliation flagged since the first deep-dive.)
- Deep-read the **@bartorico_** and **VintedCRM/Nathan Vialle** how-to content for tactics + more supplier names.

### Reddit / community (tooling now in place)
- ✅ **First Reddit pass done 2026-07-09** (via free routes — PullPush API + redlib-mirror-via-Playwright) → [[French Reseller Community Sentiment]] + subreddit congregation map. ~21 threads.
- 🔧 **Apify Reddit actor built + wired**: `~/.claude/skills/wiki-knowledge-base-builder/scripts/apify_reddit.py` (`trudax/reddit-scraper-lite`), now the mandated Reddit-fetch method in the skill (SKILL.md Stage 4b). **Live 300-run was quota-blocked** — Apify monthly free credit exhausted ("Monthly usage hard limit exceeded"), no charge. **Re-run after monthly reset or top-up** for scores/dates + cities not yet mined (Marseille, Bordeaux, Toulouse, Nantes) + reseller-operator subs (r/vinted_france, r/forum_vinted_france).
- **Ingest recipes worth keeping** (free fallbacks if Apify is down): PullPush API (`api.pullpush.io`, rate-limited ~8 calls); redlib mirror `reddit.nerdvpn.de` via Playwright.

### Practitioner voice (deepen)
- **Documentary**: "Fripes-business : au cœur du circuit international des vêtements usagés" (YouTube uHEcieYGM6c) — transcript not yet captured.
- **Ironbale** (YouTube @ironbale_fr) — grossiste-run bale channel, page failed to load; retry.
- Quora answer-bodies (login-walled) — only if the *questions* we mapped prove insufficient; needs a logged-in browser, low priority.

### Market data & regulation (fill definitional gaps)
- **Paywalled/403 on this pass, headline-only**: FashionNetwork FR, bpifrance bigmedia ("5 chiffres seconde main"), mystudies platform comparison, Xerfi DIS72 forecast. Revisit via browser/archive.
- Resolve the **market-size scope split** (all-goods €14bn vs fashion €6bn) against one methodology before it goes in a deck.
- **Refashion** éco-contribution rate card + how it hits bale suppliers specifically.

### Geo/retail map (extend)
- Cities not yet mapped: **Nice, Rennes, Montpellier, Grenoble.**
- Which cities the scraped creators operate in → merge geo map with creator map.

### Supply-side (Fleek's competitive set)
- Deep-profile the reseller-facing grossistes as direct competitors: **Friptadium, La Friperie de Martine, Fripedingue, Once Again, DHEM, Pawpick, Jonathan Frip's.** Do any run referral/affiliate programs? (→ [[Supplier and B2B Referral Mechanics]] currently says bale suppliers mostly don't — verify against these named ones.)
- **Five Vintage** (TikTok-native pop-up "friperies géantes") — closest thing to a content-led wholesale competitor; deep-read.

---

## Done (leads harvested → pages)
- 2026-07-09: Paris Substack → [[Paris Secondhand Retail Map]]
- 2026-07-09: 4-agent deep-read → [[French Cities Secondhand Retail Map]], [[FR Bale Sourcing Playbook]], + enriched creator/market/sentiment/vocabulary pages.
- 2026-07-09: Reddit/Quora pass (free routes) → enriched [[French Reseller Community Sentiment]] (voice + congregation map), [[FR Bale Sourcing Playbook]] (bale ground-truth), [[FR Creator Content Formats]] (haul-engagement drivers). Raw: [[reddit_quora_threads_2026-07-09]]. Apify actor built for future scaled runs.

Feeds: **the loop itself** — this page is what a follow-up pass (manual or a future recurring agent) pulls its targets from.
