"""Activation metrics and cycle targeting — the headline metric and who gets briefed next."""

from __future__ import annotations

from datetime import date, timedelta

from .models import Creator, Post

TODAY = date(2026, 7, 1)


def activation_summary(creators: list[Creator], posts: list[Post], days: int = 30) -> dict:
    cutoff = TODAY - timedelta(days=days)
    posted = {p.creator_id for p in posts if p.posted >= cutoff}
    lifecycle: dict[str, int] = {}
    for c in creators:
        lifecycle[c.lifecycle] = lifecycle.get(c.lifecycle, 0) + 1
    period_posts = [p for p in posts if p.posted >= cutoff]
    orders = sum(p.first_orders for p in period_posts)
    spend = sum(p.spend for p in period_posts)
    revenue = sum(p.revenue for p in period_posts)
    return {
        "roster": len(creators),
        "partners_posted": len(posted),
        "activation_pct": round(100 * len(posted) / len(creators), 1) if creators else 0,
        "posts": len(period_posts),
        "first_orders": orders,
        "cac": round(spend / orders, 2) if orders else None,
        "aov": round(revenue / orders, 2) if orders else None,
        "lifecycle_mix": dict(sorted(lifecycle.items())),
    }


def next_cycle_targets(creators: list[Creator], limit: int | None = None) -> list[Creator]:
    """Who to brief this cycle, in priority order.

    1. new       — get to first post fast (short activation window)
    2. at_risk   — cheapest saves: they were posting a month ago
    3. active    — the always-on monthly brief
    4. dormant   — re-activation batch (bounded, they get the special brief variant)
    Core partners are excluded: they're managed high-touch, not via the batch engine.
    """
    priority = {"new": 0, "at_risk": 1, "active": 2, "dormant": 3}
    targets = [c for c in creators if c.lifecycle in priority]
    targets.sort(key=lambda c: (priority[c.lifecycle], -c.followers))
    return targets[:limit] if limit else targets
