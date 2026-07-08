"""Deterministic segmentation and per-segment aggregates."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from .models import Creator, Post, SegmentStats


def segment_stats(
    creators: list[Creator], posts: list[Post], since_days: int = 30, today: date | None = None
) -> list[SegmentStats]:
    today = today or date(2026, 7, 1)
    cutoff = today - timedelta(days=since_days)
    creators_by_id = {c.id: c for c in creators}

    seg_creators: dict[str, set[str]] = defaultdict(set)
    for c in creators:
        seg_creators[c.segment].add(c.id)

    agg: dict[str, dict] = defaultdict(
        lambda: {"posted": set(), "posts": 0, "views": 0, "clicks": 0, "signups": 0,
                 "first_orders": 0, "revenue": 0.0, "spend": 0.0}
    )
    for p in posts:
        if p.posted < cutoff or p.creator_id not in creators_by_id:
            continue
        seg = creators_by_id[p.creator_id].segment
        a = agg[seg]
        a["posted"].add(p.creator_id)
        a["posts"] += 1
        for k in ("views", "clicks", "signups", "first_orders"):
            a[k] += getattr(p, k)
        a["revenue"] += p.revenue
        a["spend"] += p.spend

    stats = []
    for seg, ids in seg_creators.items():
        a = agg[seg]
        stats.append(
            SegmentStats(
                segment=seg,
                creators=len(ids),
                creators_posted=len(a["posted"]),
                posts=a["posts"],
                views=a["views"],
                clicks=a["clicks"],
                signups=a["signups"],
                first_orders=a["first_orders"],
                revenue=round(a["revenue"], 2),
                spend=round(a["spend"], 2),
            )
        )
    return sorted(stats, key=lambda s: s.spend, reverse=True)


def creator_history(creator: Creator, posts: list[Post], limit: int = 12) -> list[Post]:
    own = [p for p in posts if p.creator_id == creator.id]
    return sorted(own, key=lambda p: p.posted, reverse=True)[:limit]
