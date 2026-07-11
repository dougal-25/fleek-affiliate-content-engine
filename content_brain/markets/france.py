"""France market profile — the discovery engine's instruction set for the French reseller market.

Everything here is France-specific and evidence-backed. The engine reads this and nothing else that
is market-shaped. Sources are cited to the Fleek Wiki so a claim can be audited, not just trusted.

Channel priority (Doug, 2026-07-10): Instagram and TikTok are co-primary. YouTube is dropped from
active search for this pass (the long-form / pro-credibility channel — highest LTV per post but
lowest volume; existing YouTube creators stay in the roster). Vinted / Depop / Whatnot are *context*
platforms — a mention in a bio marks a working reseller; they are not scraped as discovery sources.

The channel split is deliberately NOT a fixed weight. At discovery time we have no performance data,
so forcing a ratio would bias the roster on a guess. TikTok and Instagram run co-primary; once the
feedback loop measures CAC-by-channel (spec/cac-model.md, content_brain/budget.py), the budget engine
learns the real split per market. Prior now, measured later — same discipline as the CAC model.
"""
from __future__ import annotations

NAME = "France"
WIKI_INDEX = "Fleek Wiki/index.md"  # the France research context; a 2nd market gets its own

# Channels searched this pass. Co-primary, no weight. YouTube intentionally absent (see module docstring).
ACTIVE_CHANNELS = ["tiktok", "instagram"]

# Presence of these in a bio/caption is a reseller signal, not a discovery source.
CONTEXT_PLATFORMS = ["vinted", "depop", "whatnot", "vestiaire", "leboncoin"]

# Nano creators matter here — trust density is highest in the small tier, and the brief says trust
# beats reach. Floor low, ceiling generous.
FOLLOWER_MIN = 1_000
FOLLOWER_MAX = 500_000

# ---- TikTok: hashtag seeds ----
# Demand-side tags (what resellers DO), not supply-side (#grossiste returns wholesalers — see
# spec/discovery-scoring.md §7). This proven set returned 12 real FR resellers on 2026-07-09.
# Source: "Fleek Wiki/research/FR Reseller Vocabulary and Hashtags.md" + the first live run.
TIKTOK_HASHTAGS = ["friperie", "vinted", "secondemain", "revente", "fripe",
                   "thriftfrance", "revendeuse", "achatrevente"]

# ---- Instagram: graph-walk seeds ----
# Instagram hashtag discovery failed twice (suppliers, then real-estate jargon). The graph walk from
# a KNOWN-GOOD creator works — @juliacrcl's relatedProfiles surfaced @zozrsl, @saw2hands, @whatnot_fr.
# Weight recommendations from verified pros 3x: the graph inherits the seed's audience, so a lifestyle
# seed returns lifestyle accounts.
IG_SEEDS_KNOWN_GOOD = ["juliacrcl", "nathanvialle", "zozrsl", "saw2hands", "felix_brgd"]
IG_SEEDS_DISCOVERED_PRO = ["tikvinted_", "resellelitee_", "matthias_achatrevente", "lebarbuluxe",
                           "cashandrepair", "whatnot_fr"]
# Press-sourced (Fleek Wiki/research/French Reseller Creator Shortlist.md). Unverified handles; a miss
# is data, not an error.
IG_SEEDS_WIKI = ["bichettekids", "claravictorya", "juliettekitsch", "alichuree", "veryfrip",
                 "nawalbonnefoy", "chamellow", "blackmaroccan", "mangoandsalt", "rubipigeon"]

IG_SEEDS = IG_SEEDS_KNOWN_GOOD + IG_SEEDS_DISCOVERED_PRO + IG_SEEDS_WIKI
IG_SEED_WEIGHT = {**{s: 3 for s in IG_SEEDS_KNOWN_GOOD},
                  **{s: 3 for s in IG_SEEDS_DISCOVERED_PRO},
                  **{s: 1 for s in IG_SEEDS_WIKI}}

# The reseller archetypes worth partnering with — the shapes the shortlist is hunting. Used to label,
# not to gate. From "Fleek Wiki/research/FR Creator Content Formats.md" and the shortlist page.
ARCHETYPES = [
    "Bale unboxer",        # films a wholesale bale being opened — literally Fleek's product demo
    "Sourcing vlogger",    # vide-maison / brocante / grossiste sourcing trips
    "Live seller",         # Whatnot / live reselling operator
    "Reseller educator",   # teaches margins, sourcing, "how I make X reselling"
    "Thrift flipper",      # buys-to-flip on Vinted/Depop
]

# The whole profile, consumed by the engine.
PROFILE = {
    "name": NAME,
    "wiki_index": WIKI_INDEX,
    "channels": ACTIVE_CHANNELS,
    "context_platforms": CONTEXT_PLATFORMS,
    "follower_min": FOLLOWER_MIN,
    "follower_max": FOLLOWER_MAX,
    "tiktok_hashtags": TIKTOK_HASHTAGS,
    "ig_seeds": IG_SEEDS,
    "ig_seed_weight": IG_SEED_WEIGHT,
    "archetypes": ARCHETYPES,
}
