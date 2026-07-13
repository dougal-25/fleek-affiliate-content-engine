"""Budget engine — deterministic weekly reallocation on two signals: CAC and posting rate.

The "trading desk": rank segments by confidence-adjusted CAC, move budget stepwise toward
winners, ring-fence a test budget for under-observed segments, flag kills. No LLM here —
money decisions are code + human sign-off.

Two signals, not one. Fleek is judged on *% of partners posting each month*, and posts lead
orders by weeks (post -> signup -> first order). So a segment with blown CAC but *climbing*
posting is held for a cycle, not killed — pausing it would starve reactivation, which is the
whole game. CAC alone would pause exactly the motion the headline metric rewards.
"""

from __future__ import annotations

from .models import BudgetLine, SegmentStats

MAX_WEEKLY_SHIFT = 0.25   # a segment's share moves at most ±25% per week
TEST_POOL = 0.20          # ring-fenced for segments without enough data
MIN_ORDERS_FOR_SIGNAL = 8  # below this, CAC is noise -> "test"
KILL_CAC_MULTIPLIER = 2.0  # CAC > 2x channel average with signal -> kill
CLIMB_MARGIN = 2.0         # activation must rise >2 percentage points to count as "climbing"


def plan_budget(
    stats: list[SegmentStats],
    weekly_budget: float,
    prev_activation: dict[str, float] | None = None,
) -> list[BudgetLine]:
    """prev_activation maps segment -> prior-period activation %. Omit it and the engine
    steers on CAC alone (a high-CAC segment is killed on signal, as before). Supply it and
    a high-CAC segment whose posting is climbing is held for a cycle instead of killed."""
    prev_activation = prev_activation or {}
    active = [s for s in stats if s.spend > 0]
    total_spend = sum(s.spend for s in active) or 1.0
    total_orders = sum(s.first_orders for s in active)
    channel_cac = (sum(s.spend for s in active) / total_orders) if total_orders else None

    signal = [s for s in active if s.first_orders >= MIN_ORDERS_FOR_SIGNAL and s.cac]
    testing = [s for s in active if s not in signal]

    def over_cac(s: SegmentStats) -> bool:
        return channel_cac is not None and s.cac > KILL_CAC_MULTIPLIER * channel_cac

    def climbing(s: SegmentStats) -> bool:
        prev = prev_activation.get(s.segment)
        return prev is not None and s.activation_pct > prev + CLIMB_MARGIN

    lines: list[BudgetLine] = []

    # Core pool: inverse-CAC weighting, capped movement vs current share.
    # Kill only if CAC is blown AND posting isn't climbing — climbing high-CAC is held, not killed.
    core_pool = weekly_budget * (1 - TEST_POOL)
    keep = [s for s in signal if not over_cac(s) or climbing(s)]
    inv_total = sum(1 / s.cac for s in keep) or 1.0
    for s in signal:
        current = s.spend / total_spend
        if s not in keep:
            lines.append(BudgetLine(
                segment=s.segment, current_share=round(current, 3), proposed_share=0.0,
                proposed_amount=0.0, decision="kill",
                rationale=f"CAC £{s.cac:.0f} > {KILL_CAC_MULTIPLIER:.0f}x channel avg "
                          f"(£{channel_cac:.0f}) on {s.first_orders} orders; posting flat",
            ))
            continue
        target = (1 / s.cac) / inv_total
        bounded = max(current * (1 - MAX_WEEKLY_SHIFT), min(current * (1 + MAX_WEEKLY_SHIFT), target))
        if over_cac(s) and climbing(s):
            prev = prev_activation[s.segment]
            decision = "hold"
            rationale = (f"CAC £{s.cac:.0f} > {KILL_CAC_MULTIPLIER:.0f}x channel (£{channel_cac:.0f}) "
                         f"but posting climbing {prev:.0f}%→{s.activation_pct:.0f}% — orders lag posts, hold a cycle")
        else:
            decision = "scale" if bounded > current * 1.05 else "hold"
            rationale = f"CAC £{s.cac:.0f} vs channel £{channel_cac:.0f}; {s.first_orders} orders"
        lines.append(BudgetLine(
            segment=s.segment, current_share=round(current, 3), proposed_share=round(bounded, 3),
            proposed_amount=round(core_pool * bounded / max(sum(
                max(x.spend / total_spend * (1 - MAX_WEEKLY_SHIFT),
                    min(x.spend / total_spend * (1 + MAX_WEEKLY_SHIFT), (1 / x.cac) / inv_total))
                for x in keep), 1e-9), 2),
            decision=decision,
            rationale=rationale,
        ))

    # Test pool: split across low-signal segments, capped per segment
    if testing:
        per_test = weekly_budget * TEST_POOL / len(testing)
        for s in testing:
            lines.append(BudgetLine(
                segment=s.segment, current_share=round(s.spend / total_spend, 3),
                proposed_share=round(TEST_POOL / len(testing), 3),
                proposed_amount=round(per_test, 2), decision="test",
                rationale=f"Only {s.first_orders} orders — under test budget with cap £{per_test:,.0f}",
            ))

    return sorted(lines, key=lambda l: l.proposed_amount, reverse=True)
