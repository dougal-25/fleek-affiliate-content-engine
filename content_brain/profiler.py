"""Partner Profiler agent — builds and refreshes the living profile of each creator."""

from __future__ import annotations

from collections import Counter

from .llm import get_llm
from .models import Creator, PartnerProfile, Post, SegmentStats


def _post_evidence(posts: list[Post]) -> str:
    if not posts:
        return "No posts in the last 90 days."
    lines = []
    for p in posts:
        cac = f"£{p.cac:.0f}" if p.cac else "n/a"
        lines.append(
            f"- {p.posted} | {p.format} / {p.hook_type} hook | {p.views:,} views -> "
            f"{p.clicks} clicks -> {p.first_orders} first orders | CAC {cac} | rev £{p.revenue:,.0f}"
        )
    return "\n".join(lines)


def build_profile(
    creator: Creator, posts: list[Post], segment: SegmentStats | None
) -> PartnerProfile:
    llm = get_llm()
    seg_line = (
        f"Segment benchmark ({segment.segment}, last 30d): activation {segment.activation_pct:.0f}%, "
        f"CAC {'£%.0f' % segment.cac if segment.cac else 'n/a'}, "
        f"AOV {'£%.0f' % segment.aov if segment.aov else 'n/a'}."
        if segment
        else "No segment benchmark available."
    )
    prompt = f"""Build a partner profile for this creator.

Creator: {creator.handle} ({creator.id})
Tier/channel/geo/niche: {creator.tier} / {creator.channel} / {creator.geo} / {creator.niche}
Followers: {creator.followers:,} | Lifecycle: {creator.lifecycle} | Joined: {creator.joined}
Gifting cost: £{creator.monthly_gifting_cost:.0f}/mo | Affiliate rate: {creator.affiliate_rate:.0%}

{seg_line}

Their recent posts (newest first):
{_post_evidence(posts)}

Set creator_id to "{creator.id}"."""
    result = llm.generate(prompt, PartnerProfile)
    return result if result is not None else _mock_profile(creator, posts)


def _mock_profile(creator: Creator, posts: list[Post]) -> PartnerProfile:
    """Deterministic offline fallback: ranks formats/hooks by orders-per-post."""
    fmt_orders: Counter[str] = Counter()
    hook_orders: Counter[str] = Counter()
    for p in posts:
        fmt_orders[p.format] += p.first_orders
        hook_orders[p.hook_type] += p.first_orders
    best_formats = [f for f, _ in fmt_orders.most_common(3)] or ["haul"]
    best_hooks = [h for h, _ in hook_orders.most_common(3)] or ["result-first"]
    total_orders = sum(p.first_orders for p in posts)
    risk = [] if creator.lifecycle in ("active", "core", "new") else [f"lifecycle: {creator.lifecycle}"]
    return PartnerProfile(
        creator_id=creator.id,
        summary=(
            f"{creator.tier.title()} {creator.niche} creator on {creator.channel} ({creator.geo}), "
            f"{creator.followers:,} followers; {total_orders} attributed first orders in 90d."
        ),
        audience_icp_fit=f"{creator.niche} audience on {creator.channel}; ICP fit inferred from conversion history.",
        best_formats=best_formats,
        best_hooks=best_hooks,
        conversion_track_record=f"{len(posts)} posts, {total_orders} first orders in the last 90 days.",
        recommended_ask=f"One {best_formats[0]} post with a {best_hooks[0]} hook this month.",
        risk_flags=risk,
        working_style_note="(mock mode — set ANTHROPIC_API_KEY for a real profile)",
    )
