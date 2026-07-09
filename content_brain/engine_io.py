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
import urllib.parse
from typing import Any

import requests

ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
AIRTABLE_BASE_NAME = "Fleek Affiliate Ecosystem"
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def load_env() -> dict[str, str]:
    """Read the workspace .env into os.environ (once). Returns the parsed dict too."""
    parsed: dict[str, str] = {}
    path = os.path.abspath(ENV_PATH)
    if os.path.exists(path):
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

def apify_tiktok_scrape(hashtags: list[str], per_hashtag: int, token: str) -> list[dict]:
    """Run clockworks/tiktok-scraper synchronously; return raw video items."""
    url = (
        "https://api.apify.com/v2/acts/clockworks~tiktok-scraper/"
        f"run-sync-get-dataset-items?token={urllib.parse.quote(token)}"
    )
    payload = {
        "hashtags": hashtags,
        "resultsPerPage": per_hashtag,
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False,
        "shouldDownloadSubtitles": False,
        "shouldDownloadSlideshowImages": False,
    }
    r = requests.post(url, json=payload, timeout=600)
    r.raise_for_status()
    return r.json()


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


# ---------------- Claude ----------------

def claude_json(prompt: str, system: str, max_tokens: int = 1500) -> Any:
    """Single Claude call that must return JSON. Robust parse with fenced-block fallback."""
    import anthropic
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
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
