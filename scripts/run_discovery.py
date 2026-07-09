#!/usr/bin/env python3
"""
Discovery job — the engine's first stage.

Brain keywords -> Apify TikTok scrape -> FR filter -> Claude enrich+score -> Airtable.
Writes a Run row to the Runs table (observability). Idempotent: creators upsert on Handle,
so re-running refreshes rather than duplicates.

Usage:
    .venv/bin/python scripts/run_discovery.py                 # default FR hashtags
    .venv/bin/python scripts/run_discovery.py --hashtags friperie vinted --per 15
    .venv/bin/python scripts/run_discovery.py --limit-enrich 20   # cap Claude calls
"""
import argparse
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from content_brain.engine_io import (  # noqa: E402
    load_env, apify_tiktok_scrape, videos_to_creators, Airtable, claude_json,
)

# FR reseller seed hashtags — from FLEEK BRAIN / FR Reseller Vocabulary and Hashtags.
# The scrape itself validates which of these actually return reseller content.
DEFAULT_HASHTAGS = ["friperie", "vinted", "secondemain", "revente", "fripe", "thriftfrance"]

SCORE_SYSTEM = """You are Fleek's Content Brain, scoring creators as potential affiliate partners for a
B2B secondhand-fashion wholesale marketplace. Fleek sells graded secondhand clothing in bulk to
resellers. The best partners are French resellers/thrifters who ALREADY buy and resell stock — not
generic fashion influencers. Score for one outcome only: will this creator drive reseller signups at
low CAC. Judge from the evidence; never invent numbers. Reply with JSON only, no prose."""

SCORE_SCHEMA = """Return a JSON object:
{
  "is_reseller": bool,            // true only if they actually resell/thrift/source clothing
  "segment": one of ["Thrift flipper","Wholesale buyer","Live seller","Reseller educator","Vinted seller","Sourcing vlogger","General fashion"],
  "content_keywords": [up to 6 short tags describing their content],
  "strength": "one sentence — why they'd convert reseller signups",
  "weakness": "one sentence — the risk or gap",
  "score": int 0-100,            // weighted: audience relevance 30, reseller credibility 25, posting consistency 15, wholesale content 10, engagement 10, professionalism 10
  "score_breakdown": "factor: points, ... (compact)",
  "confidence": one of ["High","Medium","Low"],
  "predicted_cac_gbp": number    // rough £ CAC estimate to activate them
}"""


def enrich(c: dict) -> dict | None:
    caps = "\n".join(f"- {t}" for t in c["captions"][:5]) or "(none captured)"
    prompt = f"""Creator to score:
handle: @{c['handle']}  ({c.get('nick')})
followers: {c.get('followers')}   videos: {c.get('video_count')}   verified: {c.get('verified')}
bio: {c.get('bio')[:300]}
found via hashtags: {', '.join(c.get('found_via') or [])}
their hashtags: {', '.join(c.get('hashtags') or [])}
languages: {', '.join(c.get('langs') or [])}
recent captions:
{caps}

{SCORE_SCHEMA}"""
    try:
        return claude_json(prompt, SCORE_SYSTEM, max_tokens=1200)
    except Exception as e:  # noqa: BLE001
        print(f"  ! enrich failed @{c['handle']}: {e}")
        return None


def to_airtable_fields(c: dict, e: dict) -> dict:
    photo = [{"url": c["avatar"]}] if c.get("avatar") else None
    f = {
        "Handle": c["handle"],
        "Platform": "TikTok",
        "Profile URL": c.get("profile_url"),
        "Followers": c.get("followers"),
        "Segment": e.get("segment"),
        "Content Keywords": ", ".join(e.get("content_keywords") or []),
        "Strength": e.get("strength"),
        "Weakness": e.get("weakness"),
        "Score": e.get("score"),
        "Score Breakdown": e.get("score_breakdown"),
        "Predicted CAC": e.get("predicted_cac_gbp"),
        "Confidence": e.get("confidence"),
        "Stage": "Prospect",
        "Outreach Status": "Not started",
        "Source": "discovery: " + ",".join(c.get("found_via") or []),
        "Audience": (c.get("bio") or "")[:500],
        "Notes": f"videos={c.get('video_count')} verified={c.get('verified')} langs={','.join(c.get('langs') or [])}",
    }
    if c.get("email"):
        f["Contact Email"] = c["email"]
        f["Contact Route"] = "Bio email"
    elif c.get("bio_link"):
        f["Contact Route"] = "Link-in-bio"
    else:
        f["Contact Route"] = "DM"
    if photo:
        f["Photo"] = photo
    return {k: v for k, v in f.items() if v is not None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hashtags", nargs="+", default=DEFAULT_HASHTAGS)
    ap.add_argument("--per", type=int, default=12, help="results per hashtag")
    ap.add_argument("--min-followers", type=int, default=3000)
    ap.add_argument("--max-followers", type=int, default=200000)
    ap.add_argument("--limit-enrich", type=int, default=40, help="cap Claude calls (cost breaker)")
    ap.add_argument("--dry-run", action="store_true", help="scrape+score, skip Airtable write")
    args = ap.parse_args()

    load_env()
    apify_token = os.environ["APIFY_API_TOKEN"]
    started = dt.datetime.now().isoformat(timespec="seconds")

    print(f"[discovery] scraping {len(args.hashtags)} hashtags x {args.per}: {args.hashtags}")
    videos = apify_tiktok_scrape(args.hashtags, args.per, apify_token)
    print(f"[discovery] {len(videos)} videos scraped")

    creators = videos_to_creators(videos)
    print(f"[discovery] {len(creators)} unique creators")

    # deterministic pre-filter: FR-leaning, follower band, public
    def fr_ok(c):
        langs = c.get("langs") or []
        return (not langs) or ("fr" in langs)
    kept = [c for c in creators.values()
            if fr_ok(c) and not c.get("private")
            and (c.get("followers") or 0) >= args.min_followers
            and (c.get("followers") or 0) <= args.max_followers]
    kept.sort(key=lambda c: c.get("followers") or 0, reverse=True)
    print(f"[discovery] {len(kept)} pass pre-filter (FR, {args.min_followers}-{args.max_followers} followers)")

    kept = kept[:args.limit_enrich]
    print(f"[discovery] enriching {len(kept)} with Claude (cap {args.limit_enrich})...")
    rows, resellers = [], 0
    for i, c in enumerate(kept, 1):
        e = enrich(c)
        if not e:
            continue
        if not e.get("is_reseller"):
            print(f"  - @{c['handle']} scored non-reseller, skipped")
            continue
        resellers += 1
        rows.append(to_airtable_fields(c, e))
        print(f"  {i}/{len(kept)} @{c['handle']} score={e.get('score')} {e.get('segment')} ({c.get('followers')} followers)")

    finished = dt.datetime.now().isoformat(timespec="seconds")
    if args.dry_run:
        print(f"\n[dry-run] {len(rows)} reseller creators scored, Airtable write skipped")
        print(json.dumps(rows[:2], indent=2, ensure_ascii=False))
        return

    at = Airtable(os.environ["AIRTABLE_API_KEY"])
    n = at.upsert("Creators", rows, merge_on=["Handle"]) if rows else 0
    at.create("Runs", {
        "Run": f"discovery {started}",
        "Job": "discovery",
        "Started": started, "Finished": finished,
        "Status": "Success",
        "Items In": len(videos), "Items Out": n,
        "Notes": f"{len(creators)} unique -> {len(kept)} pre-filtered -> {resellers} resellers upserted. "
                 f"hashtags={','.join(args.hashtags)}",
    })
    print(f"\n[discovery] upserted {n} creators to Airtable + logged Run row")
    print(f"[discovery] base: https://airtable.com/{at.base_id}")


if __name__ == "__main__":
    main()
