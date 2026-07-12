"""Partner Profiler agent — builds and refreshes the living profile of each creator.

Two entry points, because the evidence genuinely differs:

- `build_profile` — synthetic roster creators. We hold their full attribution funnel
  (views -> clicks -> first orders -> CAC), so the profile is grounded in conversion.
- `build_profile_from_evidence` — real French creators. We hold their posts and engagement
  but, for anyone not already carrying a Fleek code, **no attribution at all**. Passing
  them through `build_profile` would mean synthesising `first_orders=0` for every post,
  and the model would read that as "this creator never converts" rather than "we have
  never measured them." Different evidence, different prompt.
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from .llm import get_llm
from .models import Creator, PartnerProfile, Post, SegmentStats

if TYPE_CHECKING:  # avoids a circular import at runtime
    from .evidence import BriefEvidence


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


def build_profile_from_evidence(evidence: "BriefEvidence") -> PartnerProfile:
    """Profile a real French creator from scraped posts — no attribution funnel exists."""
    llm = get_llm()
    c = evidence.creator
    attribution = (
        f"They already carry a live Fleek referral code ({evidence.referral_code}) and are "
        f"posting with it unmanaged. Treat this as an inherited, active partner."
        if evidence.has_referral_history
        else "No Fleek referral history. There is NO conversion data for this creator — do not "
             "invent any. Judge ICP fit from their content and audience alone."
    )
    prompt = f"""Build a partner profile for this real French creator.

Creator: {c.handle} ({c.id}) — {evidence.profile_url}
Tier/channel/geo/niche: {c.tier} / {c.channel} / {c.geo} / {c.niche}
Followers: {c.followers:,} | Lifecycle: {c.lifecycle}

Attribution status: {attribution}

Discovery scoring notes:
- Strength: {evidence.strength}
- Weakness: {evidence.weakness}
- Predicted CAC: {evidence.predicted_cac or 'unknown'} EUR

Their real posts (their own captions/titles — not transcripts), best-performing first:
{evidence.posts_block(limit=12)}

Hashtags they use: {', '.join('#' + h for h in evidence.hashtags) or 'none captured'}

`conversion_track_record` must state honestly what we do and do not know. If there is no
attribution data, say that outright rather than implying poor performance.

Set creator_id to "{c.id}"."""
    result = llm.generate(prompt, PartnerProfile)
    return result if result is not None else _mock_profile_from_evidence(evidence)


def _mock_profile_from_evidence(evidence: "BriefEvidence") -> PartnerProfile:
    """Offline fallback for real creators. Formats inferred from their own post language."""
    c = evidence.creator
    text = " ".join(p["text"].lower() for p in evidence.top_posts)
    format_signals = {
        "haul": ["haul", "unboxing", "ballot", "colis", "lot"],
        "tutorial": ["comment", "astuce", "tuto", "guide", "conseil"],
        "day-in-the-life": ["journée", "semaine", "vlog", "avec moi"],
        "live-selling": ["live", "whatnot", "vente live", "enchère"],
        "review": ["test", "avis", "rentable"],
    }
    ranked = sorted(
        format_signals,
        key=lambda f: sum(text.count(w) for w in format_signals[f]),
        reverse=True,
    )
    best_formats = [f for f in ranked if any(w in text for w in format_signals[f])] or ["haul"]

    track = (
        f"Carries live Fleek code {evidence.referral_code} in {evidence.referral_post_count} "
        f"of {len(evidence.top_posts)} scraped posts. No first-order attribution wired up yet."
        if evidence.has_referral_history
        else f"{len(evidence.top_posts)} posts scraped; no Fleek attribution exists yet — unmeasured, not unproven."
    )
    risks = [] if not evidence.weakness else [evidence.weakness]
    if evidence.has_referral_history:
        risks.append("Promoting a competitor's code alongside Fleek's — unmanaged partner.")

    return PartnerProfile(
        creator_id=c.id,
        summary=(
            f"{c.tier.title()} {c.niche} creator on {c.channel} ({c.geo}), {c.followers:,} followers. "
            f"{evidence.strength[:160]}"
        ),
        audience_icp_fit=evidence.strength or "Unknown — no audience data captured.",
        best_formats=best_formats[:3],
        best_hooks=["result-first", "curiosity"],
        conversion_track_record=track,
        recommended_ask=f"One {best_formats[0]} post carrying their code this month.",
        risk_flags=risks,
        working_style_note="(mock mode — set ANTHROPIC_API_KEY for a real profile)",
    )


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
