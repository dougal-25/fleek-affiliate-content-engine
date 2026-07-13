"""Brief Generator agent — profile + segment insights + real post evidence -> personalised brief.

Two input paths, one output:

- **Synthetic** (`generate_brief(creator, profile, insights)`) — the loop demo on the
  1,000-creator roster. Measures activation, CAC, feedback.
- **Real** (`generate_brief(..., evidence=BriefEvidence)`) — briefs a named French creator
  from their actual scraped posts, hashtags, Airtable record and the wiki's trend pages.

The evidence bundle carries its own provenance rules (see `evidence.py`), and they go into
the prompt verbatim. The model is told what it may treat as fact and what it must not
assume — captions are not transcripts, archetypes are not an asset library, and a creator
with no Fleek history has no conversion numbers to cite.
"""

from __future__ import annotations

import itertools

from .brief_evidence import FLEEK_ARCHETYPES, BriefEvidence
from .llm import get_llm
from .models import Brief, ContentIdea, Creator, PartnerProfile, SegmentInsight

_counter = itertools.count(1)


def _next_id(creator_id: str) -> str:
    return f"BRF-{creator_id[-4:]}-{next(_counter):03d}"


def _referral_code(creator: Creator, evidence: BriefEvidence | None) -> str:
    """Never invent a code for a creator who already has one in the field."""
    if evidence is not None and evidence.referral_code:
        return evidence.referral_code
    return f"FLEEK-{creator.id[-4:]}"


def _evidence_block(evidence: BriefEvidence | None) -> str:
    if evidence is None:
        return "No real post evidence — synthetic roster creator."
    lines = [
        f"Profile: {evidence.profile_url}",
        f"Discovery score rationale — strength: {evidence.strength}",
        f"Discovery score rationale — weakness: {evidence.weakness}",
        f"Content keywords: {', '.join(evidence.content_keywords) or 'none recorded'}",
        f"Predicted CAC at discovery: {evidence.predicted_cac or 'unknown'} EUR",
        "",
        "Their highest-performing recent posts (their own words, not a transcript):",
        evidence.posts_block(),
    ]
    if evidence.hashtags:
        lines += ["", f"Hashtags they actually use: {', '.join('#' + h for h in evidence.hashtags)}"]
    if evidence.referral_evidence:
        lines += [
            "",
            "!! This creator is ALREADY promoting Fleek, unmanaged. Verbatim from their post:",
            f'   "{evidence.referral_evidence}"',
        ]
    return "\n".join(lines)


def _cycle_context(evidence: BriefEvidence | None) -> str | None:
    """Content identical for every brief in a cycle: the trend pack and Fleek's archetypes.

    Sent as a cached system block. Its size is the point — Opus 4.8 won't cache a prefix
    under 4096 tokens, and the trend pack is what carries it over the line.
    """
    if evidence is None:
        return None
    return (
        "## Fleek's top-performing partner archetypes\n"
        "Patterns to emulate. These are named partners, NOT an asset library you can link to.\n"
        + "\n".join("- " + a for a in FLEEK_ARCHETYPES)
        + "\n\n## Current French reselling trends and formats (from the research wiki)\n"
        + evidence.trend_note
    )


def generate_brief(
    creator: Creator,
    profile: PartnerProfile,
    insights: list[SegmentInsight],
    campaign: str = "always-on activation",
    offer: str = "10% off first wholesale order with the creator's unique code",
    evidence: BriefEvidence | None = None,
) -> Brief:
    llm = get_llm()
    brief_id = _next_id(creator.id)
    code = _referral_code(creator, evidence)

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

    provenance = (
        evidence.evidence_provenance()
        if evidence
        else "- Synthetic creator. Treat the profile as the only evidence."
    )

    # Stable across every brief in this cycle -> sits behind the prompt-cache breakpoint.
    # Per-creator evidence stays in the user prompt, after it.
    cached_context = _cycle_context(evidence)

    prompt = f"""Write a personalised campaign brief.

Campaign: {campaign}
Offer / CTA mechanics: {offer}. Their referral code is {code}.
Lifecycle context: {lifecycle_note}

Creator: {creator.handle} — {creator.tier} / {creator.channel} / {creator.geo} / {creator.niche}

## Evidence rules — read before writing
{provenance}

## Their partner profile
{profile.model_dump_json(indent=1)}

## Their real post evidence
{_evidence_block(evidence)}

## Codified insights for their segment ({creator.segment}) from the last cycle
{insight_block}

## What the brief must do
- Three content ideas that could only have been written for THIS creator. Each cites the
  evidence that makes it fit them.
- The do_not_mention list is not boilerplate. Fleek's hardest positioning problem is that pro
  resellers believe Fleek is for beginners. Anything that reinforces that belief goes on the
  list. So does any competitor code the creator is currently promoting.
- Captions and hooks in French. Analysis, labels and reasoning in English.
- Success target is denominated in first orders and CAC, never views.

Set brief_id to "{brief_id}", creator_id to "{creator.id}", campaign to "{campaign}"."""

    result = llm.generate(prompt, Brief, cached_context=cached_context)
    return result if result is not None else _mock_brief(brief_id, creator, profile, campaign, code, evidence)


def _mock_brief(
    brief_id: str,
    creator: Creator,
    profile: PartnerProfile,
    campaign: str,
    code: str,
    evidence: BriefEvidence | None = None,
) -> Brief:
    """Offline fallback. Deterministic, so the loop runs without an API key.

    This is a template, and it looks like one. It exists so the pipeline is testable, not so
    briefs can be shipped without a model. The whole point of Section 4 is that the real
    briefs do NOT look like this.
    """
    fmt = profile.best_formats[0]
    hook = profile.best_hooks[0]
    fr = creator.geo == "FR"  # UK creators get English copy; only FR gets French
    competitor_warning = (
        ["Do not mention any competing wholesaler's discount code in the same post"]
        if evidence and evidence.referral_evidence
        else []
    )
    if fr:
        hooks = [
            f"({hook}) Ce que j'ai vraiment payé pour tout ce lot {creator.niche}…",
            f"({hook}) J'ai sourcé tout mon restock au même endroit — voici les chiffres.",
            f"({hook}) Tu revends en France ? Regarde ça avant ton prochain achat.",
        ]
        captions = [
            f"Le vrai prix de mon restock. Code {code} pour -10% sur ta première commande. "
            f"#friperie #achatrevente #grossiste",
            f"Sourcer en gros, sans y passer le week-end. Code {code} en bio. "
            f"#revente #secondemain #friperieengros",
        ]
        ideas = [
            (f"Le vrai prix d'un restock {creator.niche}",
             f"A {fmt} breaking down what the whole restock actually cost, unit by unit."),
            ("Je source mon stock en direct", "Live-sourcing walkthrough ending on the code."),
            ("Ce que je paie vs ce que je revends", "Margin maths on screen, receipts visible."),
        ]
    else:
        hooks = [
            f"({hook}) What I actually paid for this entire {creator.niche} haul…",
            f"({hook}) I sourced my whole restock from one place — here's the maths.",
            f"({hook}) Reselling in the UK? Watch this before your next buy.",
        ]
        captions = [
            f"What my restock really cost. Code {code} for 10% off your first order. "
            f"#thrifthaul #reseller #wholesale",
            f"Sourcing in bulk without losing my weekend. Code {code} in bio. "
            f"#reselling #secondhand #vintagewholesale",
        ]
        ideas = [
            (f"What a {creator.niche} restock really costs",
             f"A {fmt} breaking down what the whole restock actually cost, unit by unit."),
            ("Sourcing my stock on camera", "Live-sourcing walkthrough ending on the code."),
            ("What I pay vs what I resell for", "Margin maths on screen, receipts visible."),
        ]

    return Brief(
        brief_id=brief_id,
        creator_id=creator.id,
        campaign=campaign,
        objective=f"Drive first wholesale orders from {creator.geo} resellers via one {fmt} post.",
        content_ideas=[
            ContentIdea(
                title=ideas[0][0],
                premise=ideas[0][1],
                why_this_creator=f"Their {fmt} posts outperform; {hook} hooks convert for them.",
            ),
            ContentIdea(
                title=ideas[1][0],
                premise=ideas[1][1],
                why_this_creator="Their audience already responds to sourcing content.",
            ),
            ContentIdea(
                title=ideas[2][0],
                premise=ideas[2][1],
                why_this_creator="Transparency is the proven conversion mechanic in this segment.",
            ),
        ],
        hooks=hooks,
        format=fmt,
        talking_points=[
            "Open on the real cost per unit, on screen",
            "Say who this is for: resellers running a business, not casual shoppers",
            "Show the grading of the inventory, not just the pile",
            f"Give the code {code} before the 60-second mark",
            "Close on the deadline",
        ],
        thumbnail_direction=(
            "Creator holding one graded piece, price sticker visible, hard price number as "
            "text overlay. No brand logo — the number earns the click."
        ),
        cta_stack=[
            f"Code {code} — 10% off first wholesale order",
            "Link in bio to the graded inventory feed",
            "Deadline: code expires end of month",
            f"Affiliate: {creator.affiliate_rate:.0%} of first-order revenue",
        ],
        example_captions=captions,
        posting_schedule=(
            "Post Wednesday evening (their strongest window), code live for 30 days, "
            "one reminder story at day 7."
        ),
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
        do_not_mention=competitor_warning + [
            "Never say Fleek is 'for beginners' or 'easy to start with' — pro resellers read that as not-for-me",
            "Don't promise specific resale margins; show your own numbers instead",
            "Don't claim exclusive or guaranteed stock",
        ],
        reference_examples=[
            f"Your own best 90-day post ({fmt}/{hook})",
            "Archetype: @behindthesale — real unit costs shown on camera",
        ],
        success_target="10+ first orders at CAC under segment average",
    )
