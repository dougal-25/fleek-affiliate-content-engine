"""Feedback Loop agent — post performance -> codified segment insights -> next cycle's briefs.

Deterministic aggregation decides WHAT the numbers are; the LLM decides WHAT THEY MEAN
(the codified play for next cycle). Insights are persisted and injected into brief generation.
"""

from __future__ import annotations

from collections import defaultdict

from .llm import get_llm
from .models import Creator, Post, SegmentInsight


def _format_hook_table(posts: list[Post]) -> str:
    agg: dict[tuple[str, str], dict] = defaultdict(lambda: {"posts": 0, "orders": 0, "spend": 0.0})
    for p in posts:
        a = agg[(p.format, p.hook_type)]
        a["posts"] += 1
        a["orders"] += p.first_orders
        a["spend"] += p.spend
    lines = []
    for (fmt, hook), a in sorted(agg.items(), key=lambda kv: -kv[1]["orders"]):
        cac = f"£{a['spend'] / a['orders']:.0f}" if a["orders"] else "no orders"
        lines.append(f"- {fmt} + {hook}: {a['posts']} posts, {a['orders']} first orders, CAC {cac}")
    return "\n".join(lines)


def codify_insights(
    creators: list[Creator], cycle_posts: list[Post], min_posts: int = 5
) -> list[SegmentInsight]:
    """Produce one insight per segment with enough volume this cycle."""
    by_segment: dict[str, list[Post]] = defaultdict(list)
    creators_by_id = {c.id: c for c in creators}
    for p in cycle_posts:
        if p.creator_id in creators_by_id:
            by_segment[creators_by_id[p.creator_id].segment].append(p)

    llm = get_llm()
    insights: list[SegmentInsight] = []
    for segment, posts in by_segment.items():
        if len(posts) < min_posts:
            continue
        prompt = f"""Codify what worked this cycle for segment {segment}.

Performance by format + hook combination:
{_format_hook_table(posts)}

Totals: {len(posts)} posts, {sum(p.first_orders for p in posts)} first orders,
£{sum(p.spend for p in posts):,.0f} spend, £{sum(p.revenue for p in posts):,.0f} revenue.

Set segment to "{segment}". Confidence: low <10 posts, medium 10-25, high >25."""
        result = llm.generate(prompt, SegmentInsight)
        insights.append(result if result is not None else _mock_insight(segment, posts))
    return insights


def _mock_insight(segment: str, posts: list[Post]) -> SegmentInsight:
    ranked = sorted(posts, key=lambda p: p.first_orders, reverse=True)
    best, worst = ranked[0], ranked[-1]
    n = len(posts)
    return SegmentInsight(
        segment=segment,
        what_worked=[f"{best.format} + {best.hook_type} ({best.first_orders} first orders)"],
        what_flopped=[f"{worst.format} + {worst.hook_type} ({worst.first_orders} first orders)"],
        recommended_play=f"Default next cycle's briefs to {best.format} with {best.hook_type} hooks.",
        confidence="low" if n < 10 else "medium" if n <= 25 else "high",
    )
