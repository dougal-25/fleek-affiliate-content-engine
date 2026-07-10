#!/usr/bin/env python3
"""
Instagram comments pass — the audience evidence, for Instagram creators.

Same purpose as scrape_comments.py, different actor. Runs one actor call per creator, because
Instagram comment records carry no post identifier: a shared run would return a pile of comments
with no way to say whose they are. Per-creator runs make ownership structural, and give a per-creator
cost line for free.

Instagram comments cost ~$1.90-2.30/1k against TikTok's measured $1.25/1k, so this is the most
expensive stage in the funnel. It therefore runs LAST and NARROW: only on creators a free signal has
already argued for. Everything dropped is printed — a cap that hides what it cut reads as coverage.

Reuses post URLs from a graph-walk run. No post is scraped twice.

Usage:
    .venv/bin/python scripts/scrape_comments_ig.py --probe          # 1 creator, 1 post
    .venv/bin/python scripts/scrape_comments_ig.py --max-creators 14
"""
import argparse
import glob
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from content_brain.engine_io import (  # noqa: E402
    load_env, apify_instagram_comments, normalise_comments, save_artifact,
)

MIN_COMMENTS = 3      # a post with fewer says nothing about the audience
OUTLIER_X = 5.0       # likes above this multiple of the creator's median = viral, excluded


def worth_classifying(r: dict, min_followers: int) -> tuple[bool, str]:
    """The gate before the most expensive stage. Recall-generous: the lexicon has known false
    negatives (@zozrsl scored 0 until 'revendeur' was added), so any flag rescues a creator."""
    if r["likely_supplier"]:
        return False, "supplier (competitor map, not a partner)"
    if r["private"]:
        return False, "private"
    if not r["post_urls"]:
        return False, "no posts"
    if r["followers"] < min_followers:
        return False, f"under {min_followers:,} followers"
    flagged = any(r["bio_flags"].values()) or r["mentions_fleek"]
    if r["pro_terms"] == 0 and not flagged:
        return False, "no pro term, no whatnot/discord/coaching/fleek flag"
    return True, ""


def pick_posts(r: dict, per_creator: int) -> list[str]:
    counts = r["post_comment_counts"]
    likes = [r["median_likes"]] if r["median_likes"] else []
    ceiling = (statistics.median(likes) * OUTLIER_X) if likes else float("inf")
    urls = [u for u, n in counts.items() if n >= MIN_COMMENTS]
    urls.sort(key=lambda u: -counts[u])
    # drop the single biggest post: a viral hit is watched by people who don't follow them
    if len(urls) > 2 and counts[urls[0]] > ceiling:
        urls = urls[1:]
    return urls[:per_creator]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", help="graph-walk run dir (default: latest)")
    ap.add_argument("--max-creators", type=int, default=14)
    ap.add_argument("--posts-per-creator", type=int, default=6)
    ap.add_argument("--per-post", type=int, default=25)
    ap.add_argument("--min-followers", type=int, default=1000)
    ap.add_argument("--probe", action="store_true")
    args = ap.parse_args()

    load_env()
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        sys.exit("APIFY_API_TOKEN not found.")

    run_dir = args.run_dir or sorted(glob.glob(
        os.path.join(os.path.dirname(__file__), "..", "data", "discovery_ig", "graph_*")))[-1]
    rows = json.load(open(os.path.join(run_dir, "creators.json")))
    print(f"[ig-comments] source: {os.path.relpath(run_dir)} ({len(rows)} creators, already paid for)")

    keep, drop = [], []
    for r in rows:
        ok, why = worth_classifying(r, args.min_followers)
        (keep if ok else drop).append((r, why))

    keep.sort(key=lambda x: (x[0]["mentions_fleek"], x[0]["pro_ratio"], x[0]["pro_terms"]), reverse=True)
    cut = keep[args.max_creators:]
    keep = keep[:args.max_creators]

    print(f"\n[ig-comments] {len(keep)} to classify, {len(drop) + len(cut)} skipped")
    for r, why in drop:
        print(f"   - @{r['handle']:<24} {why}")
    for r, _ in cut:
        print(f"   - @{r['handle']:<24} below --max-creators cut (pro_terms={r['pro_terms']})")

    if args.probe:
        keep = keep[:1]
        args.posts_per_creator, args.per_post = 1, 10

    all_comments, spend = [], 0.0
    for r, _ in keep:
        urls = pick_posts(r, args.posts_per_creator)
        if not urls:
            print(f"[ig-comments] @{r['handle']}: no eligible posts")
            continue
        out_name = "probe_comments_ig" if args.probe else "comments_normalised"
        try:
            raw, run = apify_instagram_comments(urls, args.per_post, token)
        except Exception as e:  # noqa: BLE001
            # A crash here used to discard every creator already paid for. Keep what we bought.
            print(f"[ig-comments] @{r['handle']}: FAILED — {e}")
            if all_comments:
                save_artifact(run_dir, out_name, all_comments)
                print(f"[ig-comments] kept {len(all_comments)} comments bought so far")
            raise
        spend += run.get("usageTotalUsd") or 0.0
        norm = normalise_comments(raw, "Instagram", creator=r["handle"])
        all_comments.extend(norm)
        save_artifact(run_dir, out_name, all_comments)   # persist after every paid call
        print(f"[ig-comments] @{r['handle']:<24}{len(urls):>3} posts -> {len(norm):>4} comments "
              f"  ${run.get('usageTotalUsd', 0):.4f}")
        if args.probe:
            print("   raw keys:", sorted(raw[0].keys()) if raw else "(none)")

    save_artifact(run_dir, "probe_comments_ig" if args.probe else "comments_normalised", all_comments)
    n = len(all_comments)
    print(f"\n[ig-comments] {n:,} comments  |  apify spend ${spend:.3f}"
          + (f"  ({spend / n * 1000:.2f} per 1,000)" if n else ""))
    print("\nsample:")
    for c in all_comments[:8]:
        print(f"  @{c['creator']:<20} <- @{(c['commenter'] or '?')[:18]:<18} {c['text'][:70]}")
    print(f"\n[ig-comments] saved -> {os.path.relpath(run_dir)}/")


if __name__ == "__main__":
    main()
