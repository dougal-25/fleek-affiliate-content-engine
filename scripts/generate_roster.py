"""Generate a synthetic 1,000-creator roster with 90 days of post history.

The simulation encodes realistic structure so the engine has something to learn:
- Each creator has a latent quality and a latent best format/hook; posts using them convert better.
- YouTube converts best per view (the JD's "compounding channel"), TikTok has reach, IG sits between.
- Micro/nano tiers have the best CAC; mega has reach but expensive, diluted audiences.
- ~half the roster is dormant (hasn't posted in 60+ days) — the activation opportunity.
"""

from __future__ import annotations

import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from content_brain.models import FORMATS, HOOK_TYPES, NICHES, Creator, Post  # noqa: E402

RNG = random.Random(42)
TODAY = date(2026, 7, 1)
DATA_DIR = Path(__file__).resolve().parents[1] / "data"

TIER_SPECS = {  # share of roster, follower range
    "nano": (0.40, (2_000, 10_000)),
    "micro": (0.35, (10_000, 100_000)),
    "mid": (0.17, (100_000, 500_000)),
    "macro": (0.06, (500_000, 1_000_000)),
    "mega": (0.02, (1_000_000, 4_000_000)),
}
# view-through as a fraction of followers, and click-through on views
CHANNEL_SPECS = {
    "tiktok": {"share": 0.45, "view_mult": (0.8, 3.0), "ctr": 0.0008, "cvr": 0.05},
    "youtube": {"share": 0.25, "view_mult": (0.15, 0.6), "ctr": 0.0025, "cvr": 0.11},
    "instagram": {"share": 0.30, "view_mult": (0.3, 1.0), "ctr": 0.0012, "cvr": 0.07},
}
# smaller creators have tighter, higher-trust audiences -> better click-through
TIER_TRUST = {"nano": 3.5, "micro": 2.5, "mid": 1.4, "macro": 1.0, "mega": 0.7}
GEO_SHARE = {"UK": 0.65, "FR": 0.35}
GIFTING_BY_TIER = {"nano": 40, "micro": 90, "mid": 250, "macro": 700, "mega": 2000}


def pick(weighted: dict[str, float]) -> str:
    return RNG.choices(list(weighted), weights=list(weighted.values()))[0]


def make_creators(n: int = 1000) -> list[Creator]:
    creators = []
    for i in range(n):
        tier = pick({t: s for t, (s, _) in TIER_SPECS.items()})
        lo, hi = TIER_SPECS[tier][1]
        channel = pick({c: s["share"] for c, s in CHANNEL_SPECS.items()})
        geo = pick(GEO_SHARE)
        niche = RNG.choice(NICHES)
        joined = TODAY - timedelta(days=RNG.randint(30, 720))
        creators.append(
            Creator(
                id=f"CRE-{i:04d}",
                handle=f"@{niche.split('-')[0]}_{geo.lower()}_{i:04d}",
                tier=tier,
                channel=channel,
                geo=geo,
                niche=niche,
                lifecycle="active",  # recomputed below from post history
                followers=RNG.randint(lo, hi),
                joined=joined,
                monthly_gifting_cost=GIFTING_BY_TIER[tier] * RNG.uniform(0.8, 1.2),
                affiliate_rate=RNG.choice([0.10, 0.12, 0.15]),
            )
        )
    return creators


def simulate_post(creator: Creator, posted: date, quality: float, best_format: str, best_hook: str) -> Post:
    spec = CHANNEL_SPECS[creator.channel]
    fmt = best_format if RNG.random() < 0.5 else RNG.choice(FORMATS)
    hook = best_hook if RNG.random() < 0.5 else RNG.choice(HOOK_TYPES)
    fit = (1.35 if fmt == best_format else 1.0) * (1.25 if hook == best_hook else 1.0)

    views = int(creator.followers * RNG.uniform(*spec["view_mult"]) * quality)
    clicks = int(views * spec["ctr"] * TIER_TRUST[creator.tier] * fit * RNG.uniform(0.6, 1.5))
    signups = int(clicks * 0.2 * RNG.uniform(0.6, 1.4))
    # pro resellers (rarer, higher AOV) mix in more on YouTube
    pro_share = {"youtube": 0.35, "instagram": 0.2, "tiktok": 0.12}[creator.channel]
    orders = int(signups * spec["cvr"] * fit * RNG.uniform(0.5, 1.5))
    aov = 65 * (1 - pro_share) + 240 * pro_share
    revenue = orders * aov * RNG.uniform(0.8, 1.2)
    spend = creator.monthly_gifting_cost / 2 + revenue * creator.affiliate_rate
    return Post(
        creator_id=creator.id,
        posted=posted,
        format=fmt,
        hook_type=hook,
        views=views,
        clicks=clicks,
        signups=signups,
        first_orders=orders,
        revenue=round(revenue, 2),
        spend=round(spend, 2),
    )


def make_posts(creators: list[Creator]) -> list[Post]:
    posts = []
    for c in creators:
        quality = RNG.lognormvariate(0, 0.4)
        best_format, best_hook = RNG.choice(FORMATS), RNG.choice(HOOK_TYPES)
        # posting propensity: ~28% consistent, ~22% sporadic, ~50% dormant
        r = RNG.random()
        if r < 0.28:
            n_posts, window = RNG.randint(4, 12), 90
        elif r < 0.50:
            n_posts, window = RNG.randint(1, 3), 90
        else:
            n_posts, window = RNG.randint(0, 2), 30  # old posts only -> dormant
        for _ in range(n_posts):
            days_ago = RNG.randint(0, window) if window == 90 else RNG.randint(60, 90)
            posts.append(simulate_post(c, TODAY - timedelta(days=days_ago), quality, best_format, best_hook))
    return posts


def assign_lifecycles(creators: list[Creator], posts: list[Post]) -> None:
    last_post: dict[str, date] = {}
    buyers: dict[str, int] = {}
    for p in posts:
        last_post[p.creator_id] = max(p.posted, last_post.get(p.creator_id, date.min))
        buyers[p.creator_id] = buyers.get(p.creator_id, 0) + p.first_orders
    cutoff = sorted(buyers.values(), reverse=True)[max(1, len(buyers) // 10)] if buyers else 0
    for c in creators:
        days_since = (TODAY - last_post[c.id]).days if c.id in last_post else 999
        if (TODAY - c.joined).days <= 45:
            c.lifecycle = "new"
        elif buyers.get(c.id, 0) >= cutoff and days_since <= 45:
            c.lifecycle = "core"
        elif days_since <= 30:
            c.lifecycle = "active"
        elif days_since <= 60:
            c.lifecycle = "at_risk"
        else:
            c.lifecycle = "dormant"


def main() -> None:
    creators = make_creators()
    posts = make_posts(creators)
    assign_lifecycles(creators, posts)
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "roster.json").write_text(
        json.dumps([c.model_dump(mode="json") for c in creators], indent=1)
    )
    (DATA_DIR / "posts.json").write_text(
        json.dumps([p.model_dump(mode="json") for p in posts], indent=1)
    )
    by_lc: dict[str, int] = {}
    for c in creators:
        by_lc[c.lifecycle] = by_lc.get(c.lifecycle, 0) + 1
    print(f"Wrote {len(creators)} creators, {len(posts)} posts to {DATA_DIR}")
    print("Lifecycle mix:", dict(sorted(by_lc.items())))


if __name__ == "__main__":
    main()
