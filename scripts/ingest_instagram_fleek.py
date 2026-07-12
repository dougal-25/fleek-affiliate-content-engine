#!/usr/bin/env python3
"""
One-time ingest (2026-07-11): Instagram posts for the roster's IG creators + Fleek's own
accounts (@joinfleek on Instagram AND TikTok), so the inspiration wall can mix community
videos with Fleek's own best performers.

Writes (immutable once written, like every _raw file):
    Fleek Wiki/_raw/apify_instagram_posts_2026-07-11.jsonl
    Fleek Wiki/_raw/apify_tiktok_fleek_2026-07-11.jsonl

Also downloads Instagram thumbnails immediately to dashboard/thumbs/ — IG CDN URLs are
signed and expire within days, so the ingest moment is the only reliable time to fetch them.

Usage: python3 scripts/ingest_instagram_fleek.py   (APIFY_API_TOKEN from workspace .env)
"""
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RAW = os.path.join(REPO, "Fleek Wiki", "_raw")
THUMBS = os.path.join(REPO, "dashboard", "thumbs")

IG_PROFILES = [
    "whynot.boutiques", "jf_vintagewholesalefr", "gabyparis.fr",
    "bizitza_secondemain", "fripe_paradise",
    "intemporal_paris", "g.defou",     # auto-detected in TikTok creators' bios
    "joinfleek",                        # Fleek's own account
]
FLEEK_TIKTOK = "joinfleek"


def load_token():
    tok = os.environ.get("APIFY_API_TOKEN")
    if tok:
        return tok.strip()
    d = HERE
    for _ in range(8):
        d = os.path.dirname(d)
        p = os.path.join(d, ".env")
        if os.path.exists(p):
            with open(p) as f:
                for line in f:
                    if line.startswith("APIFY_API_TOKEN="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("APIFY_API_TOKEN not found")


def api(method, url, body=None, timeout=60):
    req = urllib.request.Request(url, method=method,
                                 data=json.dumps(body).encode() if body else None)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def run_actor(token, actor, payload, label):
    print(f"→ {label}: starting {actor}…")
    run = api("POST", f"https://api.apify.com/v2/acts/{actor}/runs?token={token}", payload)["data"]
    run_id = run["id"]
    for _ in range(120):  # up to ~10 min
        time.sleep(5)
        status = api("GET", f"https://api.apify.com/v2/actor-runs/{run_id}?token={token}")["data"]
        if status["status"] in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            break
    print(f"  run {status['status']}")
    if status["status"] != "SUCCEEDED":
        return []
    items = api("GET",
                f"https://api.apify.com/v2/datasets/{status['defaultDatasetId']}/items?token={token}&format=json",
                timeout=120)
    print(f"  {len(items)} items")
    return items


def fetch_thumb(url, name):
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Macintosh) FleekDashboard/1.0")
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read()
        if body[:3] == b"\xff\xd8\xff" or body[:8] == b"\x89PNG\r\n\x1a\n" or body[8:12] == b"WEBP":
            os.makedirs(THUMBS, exist_ok=True)
            with open(os.path.join(THUMBS, name), "wb") as f:
                f.write(body)
            return True
    except Exception:
        pass
    return False


def main():
    token = load_token()
    os.makedirs(RAW, exist_ok=True)

    ig_path = os.path.join(RAW, "apify_instagram_posts_2026-07-11.jsonl")
    tt_path = os.path.join(RAW, "apify_tiktok_fleek_2026-07-11.jsonl")
    if os.path.exists(ig_path) or os.path.exists(tt_path):
        sys.exit("raw files for 2026-07-11 already exist — _raw is immutable, not re-running")

    ig_items = run_actor(token, "apify~instagram-scraper", {
        "directUrls": [f"https://www.instagram.com/{h}/" for h in IG_PROFILES],
        "resultsType": "posts",
        "resultsLimit": 30,
    }, f"Instagram ({len(IG_PROFILES)} profiles)")

    videos = [i for i in ig_items if i.get("type") in ("Video", "Reel") or i.get("videoViewCount")]
    thumbs = 0
    with open(ig_path, "w") as f:
        for i in videos:
            f.write(json.dumps(i, ensure_ascii=False) + "\n")
            sc = i.get("shortCode")
            if sc and i.get("displayUrl") and fetch_thumb(i["displayUrl"], f"ig_{sc}.jpg"):
                thumbs += 1
    print(f"  kept {len(videos)} videos → {os.path.basename(ig_path)} ({thumbs} thumbnails cached)")

    tt_items = run_actor(token, "clockworks~tiktok-scraper", {
        "profiles": [FLEEK_TIKTOK],
        "resultsPerPage": 60,
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False,
    }, "TikTok @joinfleek")
    with open(tt_path, "w") as f:
        for i in tt_items:
            f.write(json.dumps(i, ensure_ascii=False) + "\n")
    print(f"  {len(tt_items)} posts → {os.path.basename(tt_path)}")


if __name__ == "__main__":
    main()
