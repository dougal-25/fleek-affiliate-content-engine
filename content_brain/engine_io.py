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

AIRTABLE_BASE_NAME = "Fleek Affiliate Ecosystem"
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def find_env(start: str | None = None) -> str | None:
    """Nearest .env walking up from `start`. Counting `..` levels breaks inside a git
    worktree, where the repo sits deeper than in a normal checkout."""
    d = os.path.abspath(start or os.path.dirname(__file__))
    while True:
        candidate = os.path.join(d, ".env")
        if os.path.exists(candidate):
            return candidate
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def load_env() -> dict[str, str]:
    """Read the workspace .env into os.environ (once). Returns the parsed dict too."""
    parsed: dict[str, str] = {}
    path = find_env()
    if not path:
        return parsed
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


def save_artifact(run_dir: str, name: str, obj) -> str:
    """Persist a stage's output so a run can be replayed without paying to scrape again."""
    os.makedirs(run_dir, exist_ok=True)
    path = os.path.join(run_dir, f"{name}.json")
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
    return path


# ---------------- Apify ----------------

def apify_tiktok_scrape(hashtags: list[str], per_hashtag: int, token: str) -> list[dict]:
    """Run clockworks/tiktok-scraper synchronously; return raw video items."""
    url = ("https://api.apify.com/v2/acts/clockworks~tiktok-scraper/"
           "run-sync-get-dataset-items")
    payload = {
        "hashtags": hashtags,
        "resultsPerPage": per_hashtag,
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False,
        "shouldDownloadSubtitles": False,
        "shouldDownloadSlideshowImages": False,
    }
    r = requests.post(url, headers=_apify_headers(token), json=payload, timeout=600)
    if r.status_code >= 400:
        raise RuntimeError(f"apify tiktok-scraper -> {r.status_code}: {r.text[:300]}")
    return r.json()


APIFY = "https://api.apify.com/v2"


def _apify_headers(token: str) -> dict[str, str]:
    """Bearer auth, never `?token=` in the URL.

    A token in a query string is printed verbatim by requests' HTTPError message, so any 4xx
    leaks the credential into logs, tracebacks and terminal scrollback. It happened here on
    2026-07-10; the token was rotated. Headers are not echoed.
    """
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def apify_run(actor: str, payload: dict, token: str,
              poll_s: int = 5, timeout_s: int = 1800) -> tuple[list[dict], dict]:
    """Start an actor, wait for it, return (dataset items, run metadata).

    Unlike run-sync-get-dataset-items this hands back the run object, which carries
    `usageTotalUsd` and the run id — the two things a scheduled job needs to report cost
    and to write an honest Runs row.
    """
    h = _apify_headers(token)
    r = requests.post(f"{APIFY}/acts/{actor}/runs", headers=h, json=payload, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"apify {actor} start -> {r.status_code}: {r.text[:300]}")
    run = r.json()["data"]

    waited = 0
    while run["status"] in ("READY", "RUNNING"):
        if waited > timeout_s:
            raise TimeoutError(f"{actor} run {run['id']} still {run['status']} after {waited}s")
        time.sleep(poll_s)
        waited += poll_s
        rr = requests.get(f"{APIFY}/actor-runs/{run['id']}", headers=h, timeout=30)
        rr.raise_for_status()
        run = rr.json()["data"]

    if run["status"] != "SUCCEEDED":
        raise RuntimeError(f"{actor} run {run['id']} finished {run['status']}")

    items = requests.get(f"{APIFY}/datasets/{run['defaultDatasetId']}/items",
                         headers=h, params={"clean": "true"}, timeout=300)
    items.raise_for_status()
    return items.json(), run


def apify_tiktok_comments(post_urls: list[str], per_post: int, token: str,
                          replies_per_comment: int = 0) -> tuple[list[dict], dict]:
    """Comments for already-scraped videos. Takes URLs from a saved raw_videos.json, so
    building the audience picture never costs a second video scrape."""
    return apify_run("clockworks~tiktok-comments-scraper", {
        "postURLs": post_urls,
        "commentsPerPost": per_post,
        "topLevelCommentsPerPost": per_post,
        "maxRepliesPerComment": replies_per_comment,
    }, token)


def apify_tiktok_profiles(profiles: list[str], videos_per_profile: int, token: str,
                          comments_per_post: int = 0) -> list[dict]:
    """Scrape named profiles rather than hashtags. Used to calibrate the scorer against
    creators we already know are good, and to enrich seeds that arrive from a CSV."""
    url = ("https://api.apify.com/v2/acts/clockworks~tiktok-scraper/"
           "run-sync-get-dataset-items")
    payload = {
        "profiles": profiles,
        "resultsPerPage": videos_per_profile,
        "profileScrapeSections": ["videos"],
        "profileSorting": "latest",
        "commentsPerPost": comments_per_post,
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False,
        "shouldDownloadSubtitles": False,
        "shouldDownloadSlideshowImages": False,
    }
    r = requests.post(url, headers=_apify_headers(token), json=payload, timeout=900)
    if r.status_code >= 400:
        raise RuntimeError(f"apify tiktok-scraper (profiles) -> {r.status_code}: {r.text[:300]}")
    return r.json()


# ---------------- Instagram ----------------
# Two stages on purpose: hashtag posts carry the owner's handle but NOT their follower count or
# bio, so owners are resolved by a second profile call. That is the general shape — a source emits
# {handle, platform} seeds, and one enrichment path resolves them, whatever the source was.

def apify_instagram_hashtag_posts(hashtags: list[str], per_hashtag: int,
                                  token: str) -> tuple[list[dict], dict]:
    return apify_run("apify~instagram-hashtag-scraper", {
        "hashtags": hashtags,
        "resultsType": "posts",
        "resultsLimit": per_hashtag,
    }, token)


def apify_instagram_profiles(usernames: list[str], token: str) -> tuple[list[dict], dict]:
    return apify_run("apify~instagram-profile-scraper", {"usernames": usernames}, token)


def apify_instagram_comments(post_urls: list[str], per_post: int,
                             token: str) -> tuple[list[dict], dict]:
    """Instagram comments, so IG creators go through the same audience classifier as TikTok ones.
    Without this an Instagram creator could never be scored on the one signal that separates
    good from bad, and 'Instagram as a main factor' would be undeliverable."""
    return apify_run("apify~instagram-comment-scraper", {
        "directUrls": post_urls,
        "resultsLimit": per_post,
    }, token)


def normalise_comments(raw: list[dict], platform: str,
                       post_owner: dict[str, str] | None = None,
                       creator: str | None = None) -> list[dict]:
    """One shape for both platforms, so the classifier never learns the difference.

    TikTok comments carry `videoWebUrl`, so the owner is joined from the video map. Instagram
    comments carry no post identifier, so that scrape is run one creator at a time and the owner
    is passed in — every comment in the run belongs to them by construction.
    """
    out = []
    for c in raw:
        if platform == "TikTok":
            url = c.get("videoWebUrl")
            commenter, likes = c.get("uniqueId"), c.get("diggCount")
            owner = (post_owner or {}).get(url)
        else:
            url = c.get("postUrl") or c.get("url")
            commenter, likes = c.get("ownerUsername"), c.get("likesCount")
            owner = creator or (post_owner or {}).get(url)
        text = (c.get("text") or "").strip()
        if not text or not owner or commenter == owner:  # drop the creator replying to themselves
            continue
        out.append({"creator": owner, "platform": platform, "commenter": commenter,
                    "text": text, "likes": likes or 0, "post_url": url})
    return out


def ig_posts_to_creators(posts: list[dict]) -> dict[str, dict]:
    """Collapse hashtag posts into unique owners, keeping the evidence each post carries."""
    creators: dict[str, dict] = {}
    for p in posts:
        handle = p.get("ownerUsername")
        if not handle:
            continue
        c = creators.setdefault(handle, {
            "handle": handle,
            "platform": "Instagram",
            "nick": p.get("ownerFullName"),
            "captions": [],
            "hashtags": set(),
            "found_via": set(),
            "likes": [],
            "comments": [],
            "post_urls": [],
        })
        if p.get("caption"):
            c["captions"].append(p["caption"][:400])
        for h in (p.get("hashtags") or []):
            if h:
                c["hashtags"].add(str(h).lower().lstrip("#"))
        if p.get("likesCount") is not None and p["likesCount"] >= 0:
            c["likes"].append(p["likesCount"])
        if p.get("commentsCount") is not None and p["commentsCount"] >= 0:
            c["comments"].append(p["commentsCount"])
        if p.get("url"):
            c["post_urls"].append(p["url"])
        if p.get("_searchHashtag"):
            c["found_via"].add(p["_searchHashtag"])
    for c in creators.values():
        c["hashtags"] = sorted(c["hashtags"])[:15]
        c["found_via"] = sorted(c["found_via"])
    return creators


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

    def select(self, table: str, formula: str | None = None) -> list[dict]:
        """Fetch records, optionally filtered by an Airtable formula. Follows pagination."""
        tid = self.tables[table]
        url = f"https://api.airtable.com/v0/{self.base_id}/{tid}"
        out: list[dict] = []
        offset: str | None = None
        while True:
            params: dict[str, str] = {"pageSize": "100"}
            if formula:
                params["filterByFormula"] = formula
            if offset:
                params["offset"] = offset
            r = requests.get(url, headers=self.h, params=params, timeout=60)
            r.raise_for_status()
            body = r.json()
            out.extend(body.get("records", []))
            offset = body.get("offset")
            if not offset:
                return out
            time.sleep(0.25)  # stay under 5 req/s

    def list_records(self, table: str) -> list[dict]:
        """Unfiltered fetch — thin alias over select(), kept for existing callers."""
        return self.select(table)

    def update(self, table: str, record_id: str, fields: dict) -> None:
        """Patch one record by id. The ecosystem stays the source of truth."""
        tid = self.tables[table]
        url = f"https://api.airtable.com/v0/{self.base_id}/{tid}/{record_id}"
        r = requests.patch(url, headers=self.h, json={"fields": fields, "typecast": True}, timeout=60)
        if r.status_code >= 400:
            raise RuntimeError(f"Airtable {r.status_code} updating {record_id}: {r.text[:300]}")

    def update_records(self, table: str, updates: list[dict]) -> int:
        """updates: [{"id": rec_id, "fields": {...}}, ...]"""
        tid = self.tables[table]
        url = f"https://api.airtable.com/v0/{self.base_id}/{tid}"
        done = 0
        for i in range(0, len(updates), 10):
            batch = updates[i:i + 10]
            r = requests.patch(url, headers=self.h,
                               json={"records": batch, "typecast": True}, timeout=60)
            if r.status_code >= 400:
                print(f"  ! Airtable {r.status_code}: {r.text[:300]}")
                r.raise_for_status()
            done += len(batch)
            time.sleep(0.25)
        return done

    def field_names(self, table: str) -> set[str]:
        r = requests.get(f"https://api.airtable.com/v0/meta/bases/{self.base_id}/tables",
                         headers=self.h, timeout=30)
        r.raise_for_status()
        for t in r.json()["tables"]:
            if t["name"] == table:
                return {f["name"] for f in t["fields"]}
        raise RuntimeError(f"Table '{table}' not found in base")

    def ensure_fields(self, table: str, specs: list[dict]) -> list[str]:
        """Create any missing fields. Idempotent — safe to run on every job start.

        `specs` are Airtable field definitions, e.g.
        `{"name": "Brief", "type": "multilineText"}`. Returns the names actually created.
        """
        existing = self.field_names(table)
        tid = self.tables[table]
        created = []
        for spec in specs:
            if spec["name"] in existing:
                continue
            r = requests.post(
                f"https://api.airtable.com/v0/meta/bases/{self.base_id}/tables/{tid}/fields",
                headers=self.h, json=spec, timeout=30,
            )
            if r.status_code >= 400:
                raise RuntimeError(f"Airtable {r.status_code} creating field {spec['name']}: {r.text[:300]}")
            created.append(spec["name"])
            time.sleep(0.25)
        return created


def creator_key(platform: str, handle: str) -> str:
    """The upsert key. `@behindthesale` on TikTok is Fleek's top partner; `@behindthesale` on
    Instagram is a real-estate coach with 110 followers. Handle alone is not an identity."""
    return f"{(platform or '').strip().lower()}:{(handle or '').strip().lstrip('@').lower()}"


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
