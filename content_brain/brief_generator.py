"""Brief Generator agent — profile + segment insights + campaign spec -> personalised brief."""

from __future__ import annotations

import itertools

from .llm import get_llm
from .models import Brief, Creator, PartnerProfile, SegmentInsight

_counter = itertools.count(1)


def _next_id(creator_id: str) -> str:
    return f"BRF-{creator_id[-4:]}-{next(_counter):03d}"


def generate_brief(
    creator: Creator,
    profile: PartnerProfile,
    insights: list[SegmentInsight],
    campaign: str = "always-on activation",
    offer: str = "10% off first wholesale order with the creator's unique code",
) -> Brief:
    llm = get_llm()
    brief_id = _next_id(creator.id)
    relevant = [i for i in insights if i.segment == creator.segment]
    insight_block = (
        "\n".join(
            f"- worked: {'; '.join(i.what_worked)} | flopped: {'; '.join(i.what_flopped)} | "
            f"play: {i.recommended_play} (confidence: {i.confidence})"
            for i in relevant
        )
        or "No segment insights yet — first cycle."
    )
    lifecycle_note = {
        "dormant": "This is a RE-ACTIVATION brief: acknowledge the gap warmly, lead with what's "
                   "new at Fleek and their own best past post, make the ask small and the incentive warm.",
        "at_risk": "They're going quiet — keep the ask light and reference their recent win.",
        "new": "This is their FIRST brief: optimise for getting a first post live within 14 days.",
    }.get(creator.lifecycle, "Standard monthly activation brief.")

    prompt = f"""Write a personalised campaign brief.

Campaign: {campaign}
Offer / CTA mechanics: {offer}. Their unique code is FLEEK-{creator.id[-4:]}.
Lifecycle context: {lifecycle_note}

Creator: {creator.handle} — {creator.tier} / {creator.channel} / {creator.geo} / {creator.niche}

Their partner profile:
{profile.model_dump_json(indent=1)}

Codified insights for their segment ({creator.segment}) from the last cycle:
{insight_block}

Set brief_id to "{brief_id}", creator_id to "{creator.id}", campaign to "{campaign}"."""
    result = llm.generate(prompt, Brief)
    return result if result is not None else _mock_brief(brief_id, creator, profile, campaign)


def _mock_brief(brief_id: str, creator: Creator, profile: PartnerProfile, campaign: str) -> Brief:
    fmt = profile.best_formats[0]
    hook = profile.best_hooks[0]
    return Brief(
        brief_id=brief_id,
        creator_id=creator.id,
        campaign=campaign,
        objective=f"Drive first wholesale orders from {creator.geo} resellers via one {fmt} post.",
        hooks=[
            f"({hook}) What I actually paid for this entire {creator.niche} haul…",
            f"({hook}) I sourced my whole restock from one place — here's the maths.",
            f"({hook}) Reselling in {creator.geo}? Watch this before your next buy.",
        ],
        format=fmt,
        cta_stack=[
            f"Code FLEEK-{creator.id[-4:]} — 10% off first wholesale order",
            "Link in bio to the graded inventory feed",
            "Deadline: code expires end of month",
            f"Affiliate: {creator.affiliate_rate:.0%} of first-order revenue",
        ],
        dos=[
            f"Use your proven {fmt} format",
            "Show real unit prices on screen",
            "Say who it's for: resellers, not casual shoppers",
        ],
        donts=[
            "Don't read brand copy verbatim",
            "Don't bury the code after the 60-second mark",
            "Don't pitch it as retail shopping",
        ],
        reference_examples=[
            f"Your own best 90-day post ({fmt}/{hook})",
            "Segment winner: top thrift-haul short from your cohort last cycle",
        ],
        success_target="10+ first orders at CAC under segment average",
    )
