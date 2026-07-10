"""Shared engine plumbing: .env loading, Airtable upsert, Apify scrape, Claude JSON calls.

Kept deliberately small and dependency-light (requests + anthropic). Every engine job
(discovery, outreach_drafts, brief_generator) imports from here so the Airtable and LLM
wiring lives in one place, not copy-pasted.
"""
from __future__ import annotations

import json
import os
import re
import time
from typing import Any

import requests

AIRTABLE_BASE_NAME = "Fleek Affiliate Ecosystem"
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def find_env() -> str | None:
    """Walk up from this file looking for the workspace .env.

    A fixed ../../../.env resolves correctly from the real checkout but lands on
    `.claude/.env` when the repo is checked out as a git worktree — where it silently
    finds nothing and every job dies later on KeyError.
    """
    d = os.path.dirname(os.path.abspath(__file__))
    while True:
        candidate = os.path.join(d, ".env")
        if os.path.exists(candidate):
            return candidate
        parent = os.path.dirname(d)
        if parent == d:  # hit the filesystem root
            return None
        d = parent


def load_env() -> dict[str, str]:
    """Read the workspace .env into os.environ (once). Returns the parsed dict too."""
    parsed: dict[str, str] = {}
    path = find_env()
    if path:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                v = v.strip().strip('"').strip("'")
                parsed[k.strip()] = v
                os.environ.setdefault(k.strip(), v)
    return parsed


# ---------------- Apify ----------------

# Counted, not assumed — this number goes in the "how does this scale?" receipt.
APIFY_STATS = {"calls": 0, "items": 0}


def apify_run(actor: str, payload: dict, token: str, timeout: int = 600) -> list[dict]:
    """Run any Apify actor synchronously and return its dataset items.

    `actor` is the tilde form, e.g. "clockworks~tiktok-scraper".

    The token goes in the Authorization header, never the query string: `requests` embeds the
    full URL in HTTPError, so a `?token=` would print the secret into stdout and into every
    GitHub Actions log the moment a run fails.
    """
    APIFY_STATS["calls"] += 1
    url = f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items"
    r = requests.post(url, json=payload, timeout=timeout,
                      headers={"Authorization": f"Bearer {token}"})
    if r.status_code >= 400:
        # Apify puts the useful part (e.g. "field X must be one of ...") in the body.
        raise RuntimeError(f"Apify {actor} -> {r.status_code}: {r.text[:300]}")
    items = r.json()
    APIFY_STATS["items"] += len(items)
    return items


def apify_tiktok_scrape(hashtags: list[str], per_hashtag: int, token: str) -> list[dict]:
    """Run clockworks/tiktok-scraper synchronously; return raw video items."""
    return apify_run("clockworks~tiktok-scraper", {
        "hashtags": hashtags,
        "resultsPerPage": per_hashtag,
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False,
        "shouldDownloadSubtitles": False,
        "shouldDownloadSlideshowImages": False,
    }, token)


def videos_to_creators(videos: list[dict]) -> dict[str, dict]:
    """Collapse video rows into unique creators keyed by handle, aggregating evidence."""
    creators: dict[str, dict] = {}
    for v in videos:
        am = v.get("authorMeta") or {}
        handle = am.get("name")
        if not handle:
            continue
        c = creators.setdefault(handle, {
            "handle": handle,
            "nick": am.get("nickName"),
            "followers": am.get("fans"),
            "video_count": am.get("video"),
            "verified": am.get("verified"),
            "private": am.get("privateAccount"),
            "bio": am.get("signature") or "",
            "bio_link": am.get("bioLink"),
            "profile_url": am.get("profileUrl"),
            "avatar": am.get("originalAvatarUrl") or am.get("avatar"),
            "region": am.get("region"),
            "captions": [],
            "hashtags": set(),
            "langs": set(),
            "found_via": set(),
            "play_counts": [],
        })
        if v.get("text"):
            c["captions"].append(v["text"][:400])
        for h in (v.get("hashtags") or []):
            name = h.get("name") if isinstance(h, dict) else h
            if name:
                c["hashtags"].add(name)
        if v.get("textLanguage"):
            c["langs"].add(v["textLanguage"])
        if v.get("searchHashtag"):
            sh = v["searchHashtag"]
            c["found_via"].add(sh.get("name") if isinstance(sh, dict) else sh)
        if v.get("playCount"):
            c["play_counts"].append(v["playCount"])
    # finalise sets → lists, derive email
    for c in creators.values():
        c["hashtags"] = sorted(c["hashtags"])[:15]
        c["langs"] = sorted(c["langs"])
        c["found_via"] = sorted(x for x in c["found_via"] if x)
        m = EMAIL_RE.search(c["bio"])
        c["email"] = m.group(0) if m else None
    return creators


# ---------------- Airtable ----------------

class Airtable:
    def __init__(self, key: str):
        self.key = key
        self.h = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        self.base_id = self._find_base()
        self.tables = self._table_ids()

    def _find_base(self) -> str:
        r = requests.get("https://api.airtable.com/v0/meta/bases", headers=self.h, timeout=30)
        r.raise_for_status()
        for b in r.json()["bases"]:
            if b["name"] == AIRTABLE_BASE_NAME:
                return b["id"]
        raise SystemExit(f"Base '{AIRTABLE_BASE_NAME}' not found")

    def _table_ids(self) -> dict[str, str]:
        r = requests.get(f"https://api.airtable.com/v0/meta/bases/{self.base_id}/tables",
                         headers=self.h, timeout=30)
        r.raise_for_status()
        return {t["name"]: t["id"] for t in r.json()["tables"]}

    def upsert(self, table: str, records: list[dict], merge_on: list[str]) -> int:
        """Upsert records (list of {field: value}); merge on `merge_on`. Returns count."""
        tid = self.tables[table]
        url = f"https://api.airtable.com/v0/{self.base_id}/{tid}"
        done = 0
        for i in range(0, len(records), 10):  # API max 10/request
            batch = records[i:i + 10]
            body = {
                "performUpsert": {"fieldsToMergeOn": merge_on},
                "records": [{"fields": f} for f in batch],
                "typecast": True,
            }
            resp = requests.patch(url, headers=self.h, json=body, timeout=60)
            if resp.status_code >= 400:
                print(f"  ! Airtable {resp.status_code}: {resp.text[:300]}")
                resp.raise_for_status()
            done += len(batch)
            time.sleep(0.25)  # stay under 5 req/s
        return done

    def create(self, table: str, fields: dict) -> str:
        tid = self.tables[table]
        url = f"https://api.airtable.com/v0/{self.base_id}/{tid}"
        r = requests.post(url, headers=self.h, json={"fields": fields, "typecast": True}, timeout=60)
        r.raise_for_status()
        return r.json()["id"]

    def list(self, table: str, formula: str | None = None, max_records: int = 100) -> list[dict]:
        """Fetch records as plain field dicts. Follows pagination."""
        tid = self.tables[table]
        url = f"https://api.airtable.com/v0/{self.base_id}/{tid}"
        params: dict[str, Any] = {"pageSize": 100}
        if formula:
            params["filterByFormula"] = formula
        out: list[dict] = []
        while len(out) < max_records:
            r = requests.get(url, headers=self.h, params=params, timeout=30)
            r.raise_for_status()
            body = r.json()
            out.extend(rec["fields"] for rec in body["records"])
            offset = body.get("offset")
            if not offset:
                break
            params["offset"] = offset
            time.sleep(0.25)  # stay under 5 req/s
        return out[:max_records]


# ---------------- Claude ----------------

# Running tally so a job can print what it actually spent (the "how does this scale?" receipt).
CLAUDE_STATS = {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0}


def claude_json(prompt: str, system: str, max_tokens: int = 1500, cache: bool = True) -> Any:
    """Single Claude call that must return JSON. Robust parse with fenced-block fallback.

    `cache=True` marks the system prompt as an ephemeral cache breakpoint. Jobs that reuse
    one long system prompt across many creators (outreach, briefs) then pay for it once
    per 5-minute window instead of once per creator — which is what makes a 1,000-creator
    run affordable rather than theoretical.
    """
    import anthropic
    client = anthropic.Anthropic()
    system_block: Any = (
        [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
        if cache else system
    )
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=max_tokens,
        system=system_block,
        messages=[{"role": "user", "content": prompt}],
    )
    u = msg.usage
    CLAUDE_STATS["calls"] += 1
    CLAUDE_STATS["input_tokens"] += u.input_tokens
    CLAUDE_STATS["output_tokens"] += u.output_tokens
    CLAUDE_STATS["cache_read_tokens"] += getattr(u, "cache_read_input_tokens", 0) or 0
    text = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
        if m:
            return json.loads(m.group(1))
        m = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if m:
            return json.loads(m.group(1))
        raise
