"""Publish a Brief as a shareable Notion page — the link the creator actually receives.

Why Notion and not the Airtable record: the record is Fleek's, the page is the creator's.
A creator should never need a seat in the ops tool to read their own brief.

Uses the Notion REST API directly (`requests`) rather than an MCP connector, because this
job has to run unattended on a scheduler. Interactive OAuth is not available to a cron.
"""

from __future__ import annotations

import os

import requests

from .models import Brief

NOTION_VERSION = "2022-06-28"
API = "https://api.notion.com/v1"


class NotionError(RuntimeError):
    pass


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _text(content: str) -> list[dict]:
    """Notion caps a single rich-text object at 2000 chars."""
    return [{"type": "text", "text": {"content": content[:2000]}}]


def _h2(title: str) -> dict:
    return {"object": "block", "type": "heading_2",
            "heading_2": {"rich_text": _text(title)}}


def _para(body: str) -> dict:
    return {"object": "block", "type": "paragraph",
            "paragraph": {"rich_text": _text(body)}}


def _bullet(body: str) -> dict:
    return {"object": "block", "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": _text(body)}}


def _numbered(body: str) -> dict:
    return {"object": "block", "type": "numbered_list_item",
            "numbered_list_item": {"rich_text": _text(body)}}


def _callout(body: str, emoji: str) -> dict:
    return {"object": "block", "type": "callout",
            "callout": {"rich_text": _text(body), "icon": {"type": "emoji", "emoji": emoji}}}


def brief_to_blocks(brief: Brief, creator_handle: str) -> list[dict]:
    """Render a Brief as Notion blocks, in the order a creator would read them."""
    blocks: list[dict] = [
        _callout(f"{brief.objective}  —  target: {brief.success_target}", "🎯"),
        _h2("Three ideas — pick one"),
    ]
    for i, idea in enumerate(brief.content_ideas, 1):
        blocks.append(_numbered(f"{idea.title} — {idea.premise}"))
        blocks.append(_para(f"Why you: {idea.why_this_creator}"))

    blocks += [_h2("Hooks"), *[_bullet(h) for h in brief.hooks]]
    blocks += [_h2("Format"), _para(brief.format)]
    blocks += [_h2("Talking points"), *[_numbered(t) for t in brief.talking_points]]
    blocks += [_h2("Thumbnail"), _para(brief.thumbnail_direction)]
    blocks += [_h2("Call to action"), *[_numbered(c) for c in brief.cta_stack]]
    blocks += [_h2("Example captions"), *[_para(c) for c in brief.example_captions]]
    blocks += [_h2("When to post"), _para(brief.posting_schedule)]
    blocks += [_h2("Do"), *[_bullet(d) for d in brief.dos]]
    blocks += [_h2("Don't"), *[_bullet(d) for d in brief.donts]]

    blocks.append(_h2("Please don't mention"))
    for item in brief.do_not_mention:
        blocks.append(_callout(item, "🚫"))

    blocks += [_h2("Reference"), *[_bullet(r) for r in brief.reference_examples]]
    blocks.append(_para(f"Brief {brief.brief_id} · generated for @{creator_handle} by Fleek's Content Brain"))
    return blocks


def brief_to_markdown(brief: Brief, creator_handle: str) -> str:
    """Plain-text rendering for the Airtable record. Same content, no Notion needed."""
    lines = [
        f"# Brief {brief.brief_id} — @{creator_handle}",
        f"Campaign: {brief.campaign}",
        f"Objective: {brief.objective}",
        f"Target: {brief.success_target}",
        "",
        "## Three ideas",
    ]
    for i, idea in enumerate(brief.content_ideas, 1):
        lines += [f"{i}. {idea.title} — {idea.premise}", f"   Why you: {idea.why_this_creator}"]

    def section(title: str, items: list[str]) -> None:
        lines.extend(["", f"## {title}"] + [f"- {x}" for x in items])

    section("Hooks", brief.hooks)
    lines += ["", f"## Format", brief.format]
    section("Talking points", brief.talking_points)
    lines += ["", "## Thumbnail", brief.thumbnail_direction]
    section("CTA stack", brief.cta_stack)
    section("Example captions", brief.example_captions)
    lines += ["", "## When to post", brief.posting_schedule]
    section("Do", brief.dos)
    section("Don't", brief.donts)
    section("DO NOT MENTION", brief.do_not_mention)
    section("Reference", brief.reference_examples)
    return "\n".join(lines)


def publish_brief(
    brief: Brief,
    creator_handle: str,
    parent_page_id: str | None = None,
    token: str | None = None,
) -> str:
    """Create a Notion page for this brief. Returns its shareable URL.

    The page is created under `parent_page_id` (a Notion page the integration can access).
    Sharing is a Notion-side setting: the parent's share settings are inherited, so the
    operator controls who can open the link. We never flip a page public from code.
    """
    token = token or os.environ.get("NOTION_API_KEY")
    if not token:
        raise NotionError("NOTION_API_KEY not set — cannot publish to Notion.")
    parent_page_id = parent_page_id or os.environ.get("NOTION_BRIEFS_PAGE_ID")
    if not parent_page_id:
        raise NotionError(
            "NOTION_BRIEFS_PAGE_ID not set. Create a Notion page to hold the briefs, share it "
            "with the integration, and put its page id in .env."
        )

    blocks = brief_to_blocks(brief, creator_handle)

    # Notion accepts at most 100 child blocks per request. A long brief exceeds that, and
    # silently dropping the tail would delete the do-not-mention list — so we page the rest
    # in with follow-up appends rather than truncating.
    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "properties": {"title": [{"type": "text", "text": {"content": f"Brief — @{creator_handle}"}}]},
        "children": blocks[:100],
    }
    r = requests.post(f"{API}/pages", headers=_headers(token), json=payload, timeout=60)
    if r.status_code >= 400:
        raise NotionError(f"Notion {r.status_code}: {r.text[:400]}")
    page = r.json()

    for start in range(100, len(blocks), 100):
        chunk = blocks[start:start + 100]
        ra = requests.patch(
            f"{API}/blocks/{page['id']}/children",
            headers=_headers(token),
            json={"children": chunk},
            timeout=60,
        )
        if ra.status_code >= 400:
            raise NotionError(
                f"Notion {ra.status_code} appending blocks {start}-{start + len(chunk)}: {ra.text[:300]}"
            )

    return page["url"]
