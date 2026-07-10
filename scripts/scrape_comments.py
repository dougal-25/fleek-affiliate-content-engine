#!/usr/bin/env python3
"""
Comments pass — the audience evidence.

Captions tell you what the creator says. Comments tell you who is listening. That distinction is
the whole reason `creator_type` and `audience_mix` are separate fields: a pro reseller can have an
audience of hobbyists, and Fleek's hardest problem (pro resellers think Fleek is for beginners) is
an audience problem, not a creator problem.

Reads videos from a saved calibration run — no second video scrape — and pulls their comments.

Two sampling rules, both to make the sample the *audience* rather than the internet:
  - drop a creator's viral outliers (plays > OUTLIER_X * their median). A #fyp hit is watched by
    people who don't follow them, and their comments describe TikTok, not the audience.
  - spread across many videos rather than deep on one. Cap per post, not per creator.

Usage:
    python scripts/scrape_comments.py --probe        # 2 videos, 20 comments — measures true $/1k
    python scripts/scrape_comments.py                # full pass over the latest calibration run
"""
import argparse
import glob
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from content_brain.engine_io import (  # noqa: E402
    load_env, apify_tiktok_comments, save_artifact,
)

OUTLIER_X = 5.0      # plays above this multiple of a creator's median = viral, excluded
MIN_COMMENTS = 3     # a video with fewer than this tells us nothing about the audience


def pick_videos(videos: list[dict], per_creator: int) -> dict[str, list[dict]]:
    """Group by creator, drop viral outliers, take the most recent survivors."""
    by: dict[str, list[dict]] = {}
    for v in videos:
        h = (v.get("authorMeta") or {}).get("name")
        if h and v.get("webVideoUrl"):
            by.setdefault(h, []).append(v)

    picked = {}
    for h, vs in by.items():
        plays = [v.get("playCount") or 0 for v in vs if v.get("playCount")]
        if not plays:
            continue
        ceiling = statistics.median(plays) * OUTLIER_X
        keep = [v for v in vs
                if (v.get("playCount") or 0) <= ceiling
                and (v.get("commentCount") or 0) >= MIN_COMMENTS]
        keep.sort(key=lambda v: v.get("createTimeISO") or "", reverse=True)
        dropped = len(vs) - len(keep)
        if keep:
            picked[h] = keep[:per_creator]
            if dropped:
                print(f"  @{h}: {len(vs)} videos, dropped {dropped} "
                      f"(viral >{ceiling:,.0f} plays, or <{MIN_COMMENTS} comments), using {len(picked[h])}")
    return picked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", help="calibration run dir (default: latest)")
    ap.add_argument("--videos-per-creator", type=int, default=12)
    ap.add_argument("--per-post", type=int, default=50, help="max top-level comments per video")
    ap.add_argument("--probe", action="store_true", help="2 videos, 20 comments — measure real cost")
    args = ap.parse_args()

    load_env()
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        sys.exit("APIFY_API_TOKEN not found.")

    run_dir = args.run_dir or (sorted(glob.glob(
        os.path.join(os.path.dirname(__file__), "..", "data", "calibration", "*")))[-1])
    videos = json.load(open(os.path.join(run_dir, "raw_videos.json")))
    print(f"[comments] source: {os.path.relpath(run_dir)}  ({len(videos)} videos, already paid for)")

    picked = pick_videos(videos, args.videos_per_creator)
    urls, expected = [], 0
    for h, vs in picked.items():
        for v in vs:
            urls.append(v["webVideoUrl"])
            expected += min(v.get("commentCount") or 0, args.per_post)

    per_post = args.per_post
    if args.probe:
        urls, per_post = urls[:2], 20
        expected = 40

    print(f"[comments] {len(urls)} videos, cap {per_post}/post -> ~{expected:,} comments expected")
    if not urls:
        sys.exit("no eligible videos")

    comments, run = apify_tiktok_comments(urls, per_post, token)
    cost = run.get("usageTotalUsd")
    save_artifact(run_dir, "probe_comments" if args.probe else "raw_comments", comments)

    n = len(comments)
    print(f"\n[comments] {n:,} comments  |  run {run['id']}  |  cost ${cost:.4f}"
          if cost is not None else f"\n[comments] {n:,} comments | run {run['id']}")
    if cost and n:
        print(f"[comments] MEASURED price: ${cost / n * 1000:.2f} per 1,000 comments")
        full = sum(min(v.get("commentCount") or 0, args.per_post)
                   for vs in picked.values() for v in vs)
        print(f"[comments] full pass would be ~{full:,} comments -> ~${cost / n * full:.2f}")

    by_creator: dict[str, int] = {}
    url_owner = {v["webVideoUrl"]: h for h, vs in picked.items() for v in vs}
    for c in comments:
        h = url_owner.get(c.get("videoWebUrl"), "?")
        by_creator[h] = by_creator.get(h, 0) + 1
    print("\ncomments per creator:")
    for h, k in sorted(by_creator.items(), key=lambda x: -x[1]):
        print(f"  @{h:<18}{k:>6,}")

    print("\nsample comments (raw — read before designing the classifier):")
    for c in comments[:12]:
        print(f"  [{c.get('diggCount', 0):>4} likes] @{(c.get('uniqueId') or '?')[:18]:<18} "
              f"{(c.get('text') or '')[:90]}")

    print(f"\n[comments] saved to {os.path.relpath(run_dir)}/")


if __name__ == "__main__":
    main()
