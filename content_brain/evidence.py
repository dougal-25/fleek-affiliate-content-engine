"""Real-creator evidence: the inputs a brief is built from.

The synthetic roster (`store.py`) is for measuring the loop. This module is for briefing
*real* French creators from what was actually scraped: their Airtable record, their posts,
their hashtags, and the trend notes the wiki keeps current.

What we have and what we don't — stated plainly, because the brief must not pretend:

| Deck says      | We actually have                                              |
|----------------|---------------------------------------------------------------|
| transcript     | captions (TikTok) and titles + descriptions (YouTube)         |
| past videos    | 588 real posts with view/like/comment counts                  |
| best creatives | Fleek's three named top partners as archetypes, not assets    |
| referral perf  | only for creators already carrying a Fleek code (e.g. Julia)  |
| trending fmts  | dated, cited wiki pages                                       |

Everything below is read from `Fleek Wiki/_raw/`. Nothing is invented.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import date

from .models import Creator, Lifecycle

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(REPO_ROOT, "Fleek Wiki", "_raw")
RESEARCH = os.path.join(REPO_ROOT, "Fleek Wiki", "research")

CREATORS_JSON = os.path.join(RAW, "airtable_creators_2026-07-09.json")
TIKTOK_JSONL = os.path.join(RAW, "apify_tiktok_posts_2026-07-09.jsonl")
YOUTUBE_JSONL = os.path.join(RAW, "apify_youtube_posts_2026-07-09.jsonl")

# Fleek's own named top performers (mission/task-brief.md). These are archetypes to
# emulate, not creative assets we hold. The brief must say so rather than imply a library.
FLEEK_ARCHETYPES = [
    "@behindthesale — sourcing transparency: shows real unit costs and margins on camera",
    "@theliveneedham — live selling: converts during the stream, not after it",
    "@juliacrcl — reseller education: teaches the business, sells the supply chain",
]

# Trend context. Cited wiki pages, read at brief time so a refreshed wiki changes the brief.
TREND_PAGES = [
    "FR Creator Content Formats.md",
    "Creator Post-Level Signals.md",
    "FR Reseller Vocabulary and Hashtags.md",
]


def _norm(handle: str | None) -> str:
    return (handle or "").strip().lstrip("@").lower()


def _tier(followers: int) -> str:
    if followers < 10_000:
        return "nano"
    if followers < 100_000:
        return "micro"
    if followers < 500_000:
        return "mid"
    if followers < 1_000_000:
        return "macro"
    return "mega"


@dataclass
class BriefEvidence:
    """Everything the brief generator reads about one real creator."""

    creator: Creator
    airtable_record_id: str
    profile_url: str
    strength: str
    weakness: str
    content_keywords: list[str]
    predicted_cac: float | None
    top_posts: list[dict] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)
    trend_note: str = ""
    referral_code: str | None = None
    referral_evidence: str | None = None
    referral_post_count: int = 0

    @property
    def has_referral_history(self) -> bool:
        return self.referral_code is not None

    def posts_block(self, limit: int = 8) -> str:
        if not self.top_posts:
            return "No post-level evidence scraped for this creator."
        lines = []
        for p in self.top_posts[:limit]:
            lines.append(
                f"- [{p['views']:,} views · {p['likes']:,} likes · {p['comments']:,} comments] "
                f"{p['text'][:220].strip()}"
            )
        return "\n".join(lines)

    def evidence_provenance(self) -> str:
        """What the model is allowed to treat as fact, and what it must not assume."""
        parts = [
            "Post text is the creator's own captions (TikTok) or titles+descriptions (YouTube). "
            "It is NOT a spoken transcript — do not quote it as speech.",
            "Fleek reference creatives are archetypes (named top partners), not an asset library. "
            "Do not tell the creator to 'look at the Fleek creative folder' — it does not exist.",
        ]
        if self.has_referral_history:
            parts.append(
                f"This creator ALREADY carries a live Fleek referral code: {self.referral_code}, "
                f"in {self.referral_post_count} of {len(self.top_posts)} scraped posts. "
                "Use that exact code. Never invent a new one."
            )
        else:
            parts.append(
                "No Fleek referral history exists for this creator yet. Do not cite past "
                "conversion numbers for them — there are none. This is brief #1."
            )
        return "\n".join(f"- {p}" for p in parts)


def _load_creator_records() -> list[dict]:
    with open(CREATORS_JSON) as f:
        return json.load(f)


def _load_posts() -> dict[str, list[dict]]:
    """Normalise both scrapes into one shape keyed by lowercase handle."""
    by_handle: dict[str, list[dict]] = {}

    if os.path.exists(TIKTOK_JSONL):
        with open(TIKTOK_JSONL) as f:
            for line in f:
                if not line.strip():
                    continue
                p = json.loads(line)
                h = _norm(p.get("author"))
                if not h:
                    continue
                by_handle.setdefault(h, []).append({
                    "text": p.get("text") or "",
                    "full_text": p.get("text") or "",  # TikTok captions are never truncated
                    "views": p.get("playCount") or 0,
                    "likes": p.get("diggCount") or 0,
                    "comments": p.get("commentCount") or 0,
                    "hashtags": p.get("hashtags") or [],
                    "posted": p.get("createTimeISO") or "",
                })

    if os.path.exists(YOUTUBE_JSONL):
        with open(YOUTUBE_JSONL) as f:
            for line in f:
                if not line.strip():
                    continue
                p = json.loads(line)
                h = _norm(p.get("channelUsername"))
                if not h:
                    continue
                title = p.get("title") or ""
                desc = p.get("description") or ""
                by_handle.setdefault(h, []).append({
                    # `text` is trimmed for the prompt; `full_text` keeps the whole description
                    # so referral-code detection isn't an artifact of our own truncation.
                    "text": f"{title}\n{desc[:400]}".strip(),
                    "full_text": f"{title}\n{desc}".strip(),
                    "views": p.get("viewCount") or 0,
                    "likes": p.get("likes") or 0,
                    "comments": p.get("commentsCount") or 0,
                    "hashtags": [],
                    "posted": p.get("date") or "",
                })

    for posts in by_handle.values():
        posts.sort(key=lambda p: p["views"], reverse=True)
    return by_handle


def _find_referral_code(posts: list[dict]) -> tuple[str | None, str | None, int]:
    """Detect an existing Fleek referral code in the creator's own post text.

    This is how the engine learns a 'prospect' is really an active, unmanaged affiliate —
    exactly the Julia Courcelle case (see `Fleek Wiki/research/Creator Post-Level Signals.md`).

    Scans `full_text`, never the prompt-trimmed `text`: counting matches in a string we
    truncated ourselves would undercount and make an active partner look occasional.

    Returns (code, surrounding snippet, number of posts carrying it).
    """
    import re

    pattern = re.compile(r"\bRFD-[A-Z0-9]+\b", re.IGNORECASE)
    code: str | None = None
    snippet: str | None = None
    count = 0
    for p in posts:
        m = pattern.search(p.get("full_text") or p["text"])
        if not m:
            continue
        count += 1
        if code is None:
            code = m.group(0).upper()
            body = p.get("full_text") or p["text"]
            snippet = body[max(0, m.start() - 90):m.end() + 90].replace("\n", " ").strip()
    return code, snippet, count


def load_trend_note(max_chars: int = 24_000) -> str:
    """Current FR format/trend context, straight from the cited wiki pages.

    Deliberately generous: this text is the cached prompt prefix, and Opus 4.8 needs 4096+
    tokens before it caches anything at all. Trimming this to 'save tokens' costs cache hits
    and makes every brief more expensive, not less. See `llm.MIN_CACHEABLE_PREFIX_TOKENS`.
    """
    chunks = []
    for name in TREND_PAGES:
        path = os.path.join(RESEARCH, name)
        if not os.path.exists(path):
            continue
        with open(path) as f:
            body = f.read()
        chunks.append(f"### {name[:-3]}\n{body[:max_chars // len(TREND_PAGES)]}")
    return "\n\n".join(chunks) or "No trend pages found in the wiki."


def load_evidence(handle: str, lifecycle: Lifecycle | None = None) -> BriefEvidence:
    """Build the full evidence bundle for one real French creator, by handle."""
    target = _norm(handle)
    records = _load_creator_records()
    record = next((r for r in records if _norm(r["fields"].get("Handle")) == target), None)
    if record is None:
        known = sorted(_norm(r["fields"].get("Handle")) for r in records)
        raise SystemExit(f"No creator '{handle}' in the roster. Known handles: {', '.join(known)}")
    return evidence_for_record(record, lifecycle)


def evidence_for_record(record: dict, lifecycle: Lifecycle | None = None) -> BriefEvidence:
    """Same, from a record fetched live from Airtable.

    Post evidence still comes from the scraped `_raw/` files — Airtable holds the analysis,
    the vault holds the creator's actual words. A live record with no scraped posts still
    produces a brief; it just has thinner evidence, and `posts_block()` says so.
    """
    posts_by_handle = _load_posts()
    f = record["fields"]
    target = _norm(f.get("Handle"))
    posts = posts_by_handle.get(target, [])
    code, code_evidence, code_count = _find_referral_code(posts)

    # A creator already carrying a live Fleek code is an inherited partner, not a prospect —
    # regardless of what the Airtable Stage column says. Evidence beats the CRM.
    if lifecycle is None:
        lifecycle = "dormant" if code else "new"

    followers = int(f.get("Followers") or 0)
    keywords = [k.strip() for k in (f.get("Content Keywords") or "").split(",") if k.strip()]

    hashtags: list[str] = []
    for p in posts:
        for h in p["hashtags"]:
            if h not in hashtags:
                hashtags.append(h)

    creator = Creator(
        id=record["id"],
        handle=f.get("Handle") or target,
        tier=_tier(followers),
        channel=(f.get("Platform") or "tiktok").lower(),
        geo="FR",
        niche=keywords[0] if keywords else "vintage-fashion",
        lifecycle=lifecycle,
        followers=followers,
        joined=date(2026, 7, 1),
        monthly_gifting_cost=0.0,  # FR pilot: no gifting committed yet
        affiliate_rate=0.10,
    )

    return BriefEvidence(
        creator=creator,
        airtable_record_id=record["id"],
        profile_url=f.get("Profile URL") or "",
        strength=f.get("Strength") or "",
        weakness=f.get("Weakness") or "",
        content_keywords=keywords,
        predicted_cac=f.get("Predicted CAC"),
        top_posts=posts,
        hashtags=hashtags[:15],
        trend_note=load_trend_note(),
        referral_code=code,
        referral_evidence=code_evidence,
        referral_post_count=code_count,
    )


def creators_with_posts() -> list[str]:
    """Handles that have real post evidence — the only ones worth briefing for the demo."""
    posts_by_handle = _load_posts()
    out = []
    for r in _load_creator_records():
        h = _norm(r["fields"].get("Handle"))
        if posts_by_handle.get(h):
            out.append(h)
    return sorted(out)
