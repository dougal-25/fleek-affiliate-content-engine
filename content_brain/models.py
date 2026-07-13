"""Data model for the Content Brain.

Deterministic entities (Creator, Post) are generated/measured; LLM entities
(PartnerProfile, Brief, SegmentInsight) are produced by agents with structured outputs.
"""

from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

Tier = Literal["nano", "micro", "mid", "macro", "mega"]
Channel = Literal["tiktok", "youtube", "instagram"]
Geo = Literal["UK", "FR"]
Lifecycle = Literal["new", "active", "at_risk", "dormant", "core"]

NICHES = [
    "vintage-fashion",
    "thrift-hauls",
    "reseller-education",
    "streetwear",
    "sustainability",
    "live-selling",
]

FORMATS = ["haul", "tutorial", "storytime", "unboxing", "day-in-the-life", "review"]
HOOK_TYPES = ["curiosity", "result-first", "contrarian", "personal-story", "how-to"]


class Creator(BaseModel):
    id: str
    handle: str
    tier: Tier
    channel: Channel
    geo: Geo
    niche: str
    lifecycle: Lifecycle
    followers: int
    joined: date
    monthly_gifting_cost: float  # amortised product gifting per active month
    affiliate_rate: float  # % of first-order revenue paid as incentive

    @property
    def segment(self) -> str:
        return f"{self.tier}/{self.channel}/{self.geo}/{self.niche}"


class Post(BaseModel):
    creator_id: str
    posted: date
    format: str
    hook_type: str
    brief_id: Optional[str] = None  # None = un-briefed organic post
    views: int
    clicks: int
    signups: int
    first_orders: int
    revenue: float  # first-order revenue attributed to this post
    spend: float  # gifting amortisation + affiliate payouts for this post

    @property
    def cac(self) -> Optional[float]:
        return self.spend / self.first_orders if self.first_orders else None

    @property
    def aov(self) -> Optional[float]:
        return self.revenue / self.first_orders if self.first_orders else None


class PartnerProfile(BaseModel):
    """Living profile of a creator — the engine's memory of what works for them."""

    creator_id: str
    summary: str = Field(description="Two sentences: who they are and why they matter to Fleek")
    audience_icp_fit: str = Field(description="How well their audience matches hobbyist/pro resellers, with evidence")
    best_formats: list[str] = Field(description="Formats that outperform for this creator, best first")
    best_hooks: list[str] = Field(description="Hook types that outperform for this creator, best first")
    conversion_track_record: str = Field(description="One sentence on their funnel: views->clicks->orders vs segment norm")
    recommended_ask: str = Field(description="What to ask them to post next month and why")
    risk_flags: list[str] = Field(description="Risks: dormancy, declining engagement, off-ICP audience, etc. Empty if none")
    working_style_note: str = Field(description="One line on how to work with them (tone, cadence, incentive sensitivity)")


class ContentIdea(BaseModel):
    """One of the three concrete post concepts a brief proposes."""

    title: str = Field(description="The post's working title, in the creator's language")
    premise: str = Field(description="One sentence: what happens in the post and why their audience watches")
    why_this_creator: str = Field(description="The evidence from THEIR posts that makes this idea fit them specifically")


class Brief(BaseModel):
    """Personalised campaign brief.

    Covers the JD's field list (hook, format, full CTA stack, do's and don'ts, reference
    examples) plus the outputs Section 4 of the deck promises: three content ideas,
    thumbnail direction, talking points, a do-not-mention list, example captions, and a
    posting schedule.

    `do_not_mention` is the load-bearing one. Fleek's hardest problem, in their words, is
    that pro resellers think Fleek is for beginners. A brief that lets a creator say
    "great for anyone starting out" actively damages the positioning.
    """

    brief_id: str
    creator_id: str
    campaign: str
    objective: str = Field(description="One sentence: what this post should achieve, in buyer terms")
    content_ideas: list[ContentIdea] = Field(description="Exactly three distinct post concepts, best first")
    hooks: list[str] = Field(description="Three hook options written in the creator's own register")
    format: str = Field(description="The single recommended format, chosen from their proven winners")
    talking_points: list[str] = Field(description="4-6 points to cover on camera, ordered as they should be said")
    thumbnail_direction: str = Field(description="What the thumbnail/cover frame shows: subject, text overlay, why it earns the click")
    cta_stack: list[str] = Field(description="Ordered CTA stack: discount code, link placement, deadline, incentive framing")
    example_captions: list[str] = Field(description="Two ready-to-post captions in the creator's language, with hashtags")
    posting_schedule: str = Field(description="When to post and why, tied to their audience's actual activity or the campaign deadline")
    dos: list[str] = Field(description="3-5 specific do's grounded in what has worked for them")
    donts: list[str] = Field(description="3-5 specific don'ts grounded in what has flopped for them or their segment")
    do_not_mention: list[str] = Field(description="Things this creator must NOT say: off-positioning claims, competitor codes, unsupported promises, brand-safety lines")
    reference_examples: list[str] = Field(description="Reference posts to emulate — their own best post first, then Fleek partner archetypes")
    success_target: str = Field(description="The measurable bar, e.g. '15+ first orders at CAC under EUR45'")


class SegmentInsight(BaseModel):
    """What the feedback agent codified about a segment this cycle."""

    segment: str
    what_worked: list[str]
    what_flopped: list[str]
    recommended_play: str = Field(description="The single change to make in next cycle's briefs for this segment")
    confidence: Literal["low", "medium", "high"] = Field(description="Based on post volume behind the insight")


class SegmentStats(BaseModel):
    """Deterministic per-segment aggregates for a period."""

    segment: str
    creators: int
    creators_posted: int
    posts: int
    views: int
    clicks: int
    signups: int
    first_orders: int
    revenue: float
    spend: float

    @property
    def activation_pct(self) -> float:
        return 100.0 * self.creators_posted / self.creators if self.creators else 0.0

    @property
    def cac(self) -> Optional[float]:
        return self.spend / self.first_orders if self.first_orders else None

    @property
    def aov(self) -> Optional[float]:
        return self.revenue / self.first_orders if self.first_orders else None


class BudgetLine(BaseModel):
    segment: str
    current_share: float
    proposed_share: float
    proposed_amount: float
    decision: Literal["scale", "hold", "test", "kill"]
    rationale: str
