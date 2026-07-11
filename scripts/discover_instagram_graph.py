#!/usr/bin/env python3
"""
Instagram discovery by graph walk — seeded from creators we have verified, not hashtags we guessed.

Hashtag discovery on Instagram failed twice (spec/discovery-scoring.md §7): supply-side tags returned
wholesalers advertising stock, and #achatrevente returned real-estate accounts. Meanwhile a single
profile call on @juliacrcl — a known-good Fleek partner — returned 28 `relatedProfiles` including
@zozrsl (full-time Vinted reseller, paid Discord, 1,763 followers), @whatnot_fr and @united.vintage.
Instagram's own "similar accounts" graph is a better source than its hashtag index.

The profile scraper also returns `latestPosts` (12, with captions, hashtags and post URLs), so a
graph-walked creator arrives with everything the free lexicon needs AND the post URLs the comments
pass needs. No separate post scrape.

Two stages, both cheap: seeds -> relatedProfiles -> profiles of the candidates.

Usage:
    .venv/bin/python scripts/discover_instagram_graph.py --smoke
    .venv/bin/python scripts/discover_instagram_graph.py --max-candidates 40
"""
import argparse
import datetime as dt
import os
import statistics
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from content_brain.engine_io import (  # noqa: E402
    load_env, apify_instagram_profiles, save_artifact, creator_key,
)
from content_brain.signals import (  # noqa: E402
    lexicon_profile, fleek_signals, bio_flags, is_supplier, in_fashion_vertical,
)
from content_brain import markets  # noqa: E402

# Seeds and their weights are market-specific and now live in the market profile
# (content_brain/markets/france.py). Supplier detection and the clothing-vertical gate live in
# content_brain/signals.py. This script is market-agnostic machinery.


def profile_features(p: dict) -> dict:
    bio = p.get("biography") or ""
    links = " ".join(str(u) for u in [p.get("externalUrl"), p.get("externalUrls")] if u)
    posts = p.get("latestPosts") or []
    captions = [q.get("caption") or "" for q in posts]
    tags = sorted({str(t).lower().lstrip("#") for q in posts for t in (q.get("hashtags") or [])})
    likes = [q["likesCount"] for q in posts if (q.get("likesCount") or 0) > 0]
    coms = [q["commentsCount"] for q in posts if (q.get("commentsCount") or 0) > 0]
    followers = p.get("followersCount") or 0
    corpus = " ".join([bio, links, " ".join(captions), " ".join(tags)])

    eng = None
    if followers and likes:
        eng = round((statistics.median(likes) + (statistics.median(coms) if coms else 0)) / followers, 4)

    cadence = None
    stamps = sorted(q["timestamp"][:10] for q in posts if q.get("timestamp"))
    if len(stamps) >= 2:
        span = (dt.date.fromisoformat(stamps[-1]) - dt.date.fromisoformat(stamps[0])).days
        cadence = round(len(stamps) / (span / 7), 1) if span >= 7 else None

    return {
        "handle": p.get("username"), "platform": "Instagram",
        "creator_key": creator_key("Instagram", p.get("username") or ""),
        "full_name": p.get("fullName"), "followers": followers,
        "posts_count": p.get("postsCount"), "private": p.get("private"),
        "verified": p.get("verified"), "business_category": p.get("businessCategoryName"),
        "profile_url": p.get("url"), "external_url": p.get("externalUrl"),
        "bio": bio[:300], "engagement_rate": eng, "posts_per_week": cadence,
        "median_likes": int(statistics.median(likes)) if likes else 0,
        # post_urls feed the comments pass — the only signal that separates good from bad
        "post_urls": [q["url"] for q in posts if q.get("url")],
        "post_comment_counts": {q["url"]: q.get("commentsCount") or 0 for q in posts if q.get("url")},
        "top_hashtags": tags[:12], "sample_captions": captions[:3],
        "likely_supplier": is_supplier(bio, p.get("businessCategoryName")),
        "fashion_vertical": in_fashion_vertical(corpus, f"{p.get('username')} {links}"),
        **lexicon_profile(corpus), **fleek_signals(corpus), "bio_flags": bio_flags(corpus),
    }


def fetch(names: list[str], token: str, label: str) -> tuple[list[dict], float]:
    profiles, run = apify_instagram_profiles(names, token)
    cost = run.get("usageTotalUsd") or 0.0
    bad = [p.get("username") for p in profiles if p.get("error") or p.get("followersCount") is None]
    ok = [p for p in profiles if not p.get("error") and p.get("followersCount") is not None]
    print(f"[graph] {label}: {len(ok)}/{len(names)} resolved  ${cost:.4f}")
    if bad:
        print(f"[graph]   unresolvable: {', '.join(str(b) for b in bad)}")
    return ok, cost


def run_graph_walk(profile: dict, token: str, max_candidates: int, run_dir: str,
                   smoke: bool = False) -> tuple[list[dict], float]:
    """Seeds -> relatedProfiles -> candidate profiles -> enriched, ranked rows. Returns (rows, spend).

    Importable by the orchestrator (scripts/run_discovery.py). Reads seeds/weights from the market
    profile, so the same machinery serves any market.
    """
    seeds = profile["ig_seeds"][:3] if smoke else profile["ig_seeds"]
    seed_weight = profile["ig_seed_weight"]

    seed_profiles, spend = fetch(seeds, token, "seeds")
    save_artifact(run_dir, "raw_seed_profiles", seed_profiles)

    seen = {s.lower() for s in seeds}
    candidates: dict[str, list[str]] = {}
    for p in seed_profiles:
        rel = p.get("relatedProfiles") or []
        print(f"[graph]   @{p['username']}: {len(rel)} relatedProfiles")
        for r in rel:
            u = (r.get("username") or "").lower()
            if u and u not in seen:
                candidates.setdefault(u, []).append(p["username"])

    if not candidates:
        print("[graph] no relatedProfiles returned — the graph is not always populated. "
              "Seeds still scored below.")

    def weight(u: str) -> tuple[int, int]:
        return (sum(seed_weight.get(s, 1) for s in candidates[u]), len(candidates[u]))

    ranked = sorted(candidates, key=weight, reverse=True)[:max_candidates]
    dropped = len(candidates) - len(ranked)
    print(f"[graph] {len(candidates)} candidates -> resolving {len(ranked)}")
    if dropped:
        # never truncate silently: say whose recommendations were cut and how strong they were
        cut = sorted(set(candidates) - set(ranked), key=weight, reverse=True)
        by_seed: dict[str, int] = {}
        for u in cut:
            for s in candidates[u]:
                by_seed[s] = by_seed.get(s, 0) + 1
        print(f"[graph]   DROPPED {dropped} by --max-candidates: "
              + ", ".join(f"{s}×{n}" for s, n in sorted(by_seed.items(), key=lambda x: -x[1])))

    cand_profiles, c2 = (fetch(ranked, token, "candidates") if ranked else ([], 0.0))
    spend += c2
    save_artifact(run_dir, "raw_candidate_profiles", cand_profiles)

    rows = []
    for p in seed_profiles + cand_profiles:
        f = profile_features(p)
        f["found_via"] = (["seed"] if p["username"].lower() in seen
                          else [f"related:{s}" for s in candidates.get(p["username"].lower(), [])])
        rows.append(f)
    rows.sort(key=lambda r: (r["mentions_fleek"], not r["likely_supplier"], r["pro_ratio"],
                             r["followers"]), reverse=True)
    save_artifact(run_dir, "creators", rows)
    return rows, spend


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="france")
    ap.add_argument("--max-candidates", type=int, default=40, help="cost breaker on stage 2")
    ap.add_argument("--smoke", action="store_true", help="known-good seeds only")
    args = ap.parse_args()

    load_env()
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        sys.exit("APIFY_API_TOKEN not found.")

    profile = markets.get(args.market)
    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    run_dir = os.path.join(os.path.dirname(__file__), "..", "data", "discovery_ig", f"graph_{stamp}")

    rows, spend = run_graph_walk(profile, token, args.max_candidates, run_dir, smoke=args.smoke)

    print(f"\n{'handle':<24}{'followers':>10}{'eng%':>7}{'pro':>5}{'cons':>6}{'posts':>7}  signals")
    print("-" * 108)
    for r in rows:
        eng = f"{r['engagement_rate'] * 100:.1f}" if r["engagement_rate"] else "—"
        tags = [k for k, v in r["bio_flags"].items() if v]
        if r["mentions_fleek"]:
            tags.append("★FLEEK")
        if r["likely_supplier"]:
            tags.append("SUPPLIER")
        if r["private"]:
            tags.append("private")
        via = r["found_via"][0] if r["found_via"] else "?"
        print(f"@{r['handle']:<23}{r['followers']:>10,}{eng:>7}{r['pro_terms']:>5}"
              f"{r['consumer_terms']:>6}{len(r['post_urls']):>7}  {via[:22]:<22}"
              + (" +" + ",".join(tags) if tags else ""))

    total_comments = sum(sum(r["post_comment_counts"].values()) for r in rows)
    print(f"\n[graph] apify spend: ${spend:.3f}")
    print(f"[graph] {len(rows)} creators, {total_comments:,} comments available for the audience pass")
    print(f"[graph] artifacts -> {os.path.relpath(run_dir)}/")


if __name__ == "__main__":
    main()
