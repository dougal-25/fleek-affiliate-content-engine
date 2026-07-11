"""Recent-evidence gatherer — what a creator actually posted, and what their audience said back.

Personalisation is only worth the API call if the evidence is *recent*. A message referencing a
creator's six-month-old haul reads worse than a generic one: it proves you looked and didn't care.
So the recency window is a gate, not a preference — a creator with no in-window posts is skipped,
never drafted from stale material.

Two design notes:

- **Batched per platform, not per creator.** All handles on a platform go into one actor run. This
  is the scale answer: drafting for 1,000 creators costs the same 2 Apify calls per platform as
  drafting for 2. Only the Claude calls scale per creator.
- **The client-side date filter is the guarantee.** Each actor has its own recency parameter and its
  own name for it; we pass them as an optimisation, then filter on the normalised date regardless.
  Actor schemas drift. The window must not.

Platform asymmetry, verified against the live Apify API (2026-07-10): TikTok's comment scraper
accepts `profiles` directly, so it's one call. Instagram's and YouTube's require post/video URLs,
so those are two-step — fetch posts, then feed their URLs to the comment scraper. Transcripts exist
only on YouTube (`downloadSubtitles`); TikTok and Instagram have none, and we don't pretend otherwise.
"""
from __future__ import annotations

import datetime as dt
import re
from typing import Any

from .engine_io import apify_run

TIKTOK_HANDLE_RE = re.compile(r"tiktok\.com/@([^/?#]+)")
POST_TEXT_KEYS = ("text", "caption", "title", "desc")
COMMENT_TEXT_KEYS = ("text", "comment", "content")
DATE_KEYS = ("createTimeISO", "timestamp", "date", "uploadDate", "createTime")
VIEW_KEYS = ("playCount", "viewCount", "videoPlayCount", "likesCount", "diggCount")
URL_KEYS = ("webVideoUrl", "url", "postUrl", "link")
# The post/video a comment sits under. Every actor names this differently: YouTube says pageUrl,
# Instagram postUrl, TikTok submittedVideoUrl. Guessing one of them silently drops every comment.
PARENT_URL_KEYS = ("pageUrl", "postUrl", "videoWebUrl", "submittedVideoUrl", "videoUrl", "url")


def _first(d: dict, keys: tuple[str, ...]) -> Any:
    """Read the first key that carries a truthy value. Actors rename fields between builds."""
    for k in keys:
        v = d.get(k)
        if v:
            return v
    return None


def _as_date(value: Any) -> dt.date | None:
    if not value:
        return None
    if isinstance(value, (int, float)):  # epoch seconds
        return dt.datetime.fromtimestamp(value, tz=dt.timezone.utc).date()
    text = str(value).replace("Z", "+00:00")
    try:
        return dt.datetime.fromisoformat(text).date()
    except ValueError:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"):
            try:
                return dt.datetime.strptime(str(value)[:19], fmt).date()
            except ValueError:
                continue
    return None


def _norm_post(item: dict) -> dict:
    return {
        "text": (_first(item, POST_TEXT_KEYS) or "")[:600],
        "date": _as_date(_first(item, DATE_KEYS)),
        "views": _first(item, VIEW_KEYS) or 0,
        "url": _first(item, URL_KEYS),
    }


def _norm_comment(item: dict, post_url: str | None = None) -> dict:
    return {
        "text": (_first(item, COMMENT_TEXT_KEYS) or "")[:300],
        "likes": item.get("diggCount") or item.get("likesCount") or item.get("voteCount") or 0,
        "on_post_url": post_url or _first(item, PARENT_URL_KEYS),
    }


def _usable_comment(item: dict) -> bool:
    """Actors emit error rows inline (e.g. {'error': 'VIDEO_UNAVAILABLE'}), and the creator's own
    replies are not audience voice. Both would otherwise land in the evidence as empty or misleading."""
    if item.get("error") or item.get("authorIsChannelOwner"):
        return False
    return bool(_first(item, COMMENT_TEXT_KEYS))


def _attach_comments(out: dict[str, dict], comments: list[dict], url_owner: dict[str, str]) -> None:
    """Route each comment to the creator whose post it sits under."""
    for c in comments:
        if not _usable_comment(c):
            continue
        parent = _first(c, PARENT_URL_KEYS)
        handle = url_owner.get(parent)
        if handle:
            out[handle]["comments"].append(_norm_comment(c, parent))


def _in_window(posts: list[dict], cutoff: dt.date) -> list[dict]:
    """Drop undated and out-of-window posts. Undated is dropped on purpose: we cannot prove it's
    recent, and 'probably recent' is exactly the claim this gate exists to refuse."""
    kept = [p for p in posts if p["date"] and p["date"] >= cutoff]
    return sorted(kept, key=lambda p: p["date"], reverse=True)


def _blank(handles: list[str]) -> dict[str, dict]:
    return {h: {"posts": [], "comments": [], "transcript": None, "display_name": None}
            for h in handles}


# ---------------- TikTok: one call for posts, one for comments ----------------

def _tiktok(handles: list[str], cutoff: dt.date, per_profile: int, token: str) -> dict[str, dict]:
    out = _blank(handles)
    videos = apify_run("clockworks~tiktok-scraper", {
        "profiles": handles,
        "resultsPerPage": per_profile,
        "profileSorting": "latest",
        "excludePinnedPosts": True,
        "oldestPostDateUnified": cutoff.isoformat(),
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False,
        "shouldDownloadSubtitles": False,
        "shouldDownloadSlideshowImages": False,
    }, token)
    for v in videos:
        am = v.get("authorMeta") or {}
        handle = (am.get("name") or "").lstrip("@")
        if handle in out:
            out[handle]["posts"].append(_norm_post(v))
            out[handle]["display_name"] = out[handle]["display_name"] or am.get("nickName")

    comments = apify_run("clockworks~tiktok-comments-scraper", {
        "profiles": handles,
        "resultsPerPage": 3,
        "topLevelCommentsPerPost": 12,
        "maxRepliesPerComment": 0,
    }, token)
    # A comment item names the video it sits under, not the creator. Every TikTok video URL
    # embeds the creator: tiktok.com/@gdefou/video/123 — so read the handle straight off it.
    lower = {h.lower(): h for h in out}
    for c in comments:
        if not _usable_comment(c):
            continue
        c_norm = _norm_comment(c)
        m = TIKTOK_HANDLE_RE.search(str(c_norm["on_post_url"] or ""))
        handle = lower.get(m.group(1).lower()) if m else None
        if handle:
            out[handle]["comments"].append(c_norm)

    for h in out:
        out[h]["posts"] = _in_window(out[h]["posts"], cutoff)
    return out


# ---------------- Instagram: posts first, then comments on those post URLs ----------------

def _instagram(handles: list[str], cutoff: dt.date, per_profile: int, token: str) -> dict[str, dict]:
    out = _blank(handles)
    posts = apify_run("apify~instagram-scraper", {
        "directUrls": [f"https://www.instagram.com/{h}/" for h in handles],
        "resultsType": "posts",
        "resultsLimit": per_profile,
        "onlyPostsNewerThan": cutoff.isoformat(),
        "addParentData": False,
    }, token)
    for p in posts:
        handle = (p.get("ownerUsername") or "").lstrip("@")
        if handle in out:
            out[handle]["posts"].append(_norm_post(p))
            out[handle]["display_name"] = out[handle]["display_name"] or p.get("ownerFullName")

    for h in out:
        out[h]["posts"] = _in_window(out[h]["posts"], cutoff)

    post_urls = [p["url"] for e in out.values() for p in e["posts"][:3] if p["url"]]
    if not post_urls:
        return out
    comments = apify_run("apify~instagram-comment-scraper", {
        "directUrls": post_urls,
        "resultsLimit": 12 * len(handles),
        "includeNestedComments": False,
    }, token)
    url_owner = {p["url"]: h for h, e in out.items() for p in e["posts"] if p["url"]}
    _attach_comments(out, comments, url_owner)
    return out


# ---------------- YouTube: videos (+ subtitles) first, then comments on those video URLs ----------

def _youtube(handles: list[str], cutoff: dt.date, per_profile: int, token: str,
             transcripts: bool = True) -> dict[str, dict]:
    out = _blank(handles)
    videos = apify_run("streamers~youtube-scraper", {
        "startUrls": [{"url": f"https://www.youtube.com/@{h}/videos"} for h in handles],
        "maxResults": per_profile,
        "sortingOrder": "date",  # actor enum: relevance | rating | date | views
        "downloadSubtitles": transcripts,
        "subtitlesLanguage": "fr",
        "subtitlesFormat": "plaintext",
    }, token)
    by_handle_url: dict[str, str] = {}
    for v in videos:
        handle = (v.get("channelUsername") or v.get("channelName") or "").lstrip("@")
        match = next((h for h in out if h.lower() == handle.lower()), None)
        if not match:
            # channelName can be a display name; fall back to matching the channel URL
            match = next((h for h in out if h.lower() in str(v.get("channelUrl") or "").lower()), None)
        if not match:
            continue
        post = _norm_post(v)
        # a YouTube video's "text" is its description; the title carries more signal
        post["text"] = f"{v.get('title') or ''}\n{(v.get('text') or '')[:400]}".strip()
        out[match]["posts"].append(post)
        out[match]["display_name"] = out[match]["display_name"] or v.get("channelName")
        subs = v.get("subtitles")
        if transcripts and subs and not out[match]["transcript"]:
            first = subs[0] if isinstance(subs, list) and subs else None
            body = (first or {}).get("plaintext") or (first or {}).get("srt") if isinstance(first, dict) else None
            if body:
                out[match]["transcript"] = str(body)[:4000]
        if post["url"]:
            by_handle_url.setdefault(post["url"], match)

    for h in out:
        out[h]["posts"] = _in_window(out[h]["posts"], cutoff)

    video_urls = [p["url"] for e in out.values() for p in e["posts"][:3] if p["url"]]
    if not video_urls:
        return out
    comments = apify_run("streamers~youtube-comments-scraper", {
        "startUrls": [{"url": u} for u in video_urls],
        "maxComments": 12,
        "sortCommentsBy": "TOP_COMMENTS",
    }, token)
    _attach_comments(out, comments, by_handle_url)
    return out


ADAPTERS = {"TikTok": _tiktok, "Instagram": _instagram, "YouTube": _youtube}


def gather(platform: str, handles: list[str], days: int, per_profile: int,
           token: str) -> dict[str, dict]:
    """Recent posts + audience comments (+ YouTube transcript) for every handle on one platform.

    Returns {handle: {"posts": [...], "comments": [...], "transcript": str|None}} with posts
    newest-first and strictly inside the `days` window. Raises on an unknown platform — a silent
    empty result would let a job draft from no evidence at all.
    """
    if platform not in ADAPTERS:
        raise ValueError(f"No evidence adapter for platform {platform!r}. "
                         f"Known: {', '.join(ADAPTERS)}")
    if not handles:
        return {}
    cutoff = dt.date.today() - dt.timedelta(days=days)
    return ADAPTERS[platform](handles, cutoff, per_profile, token)
