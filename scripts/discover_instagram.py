#!/usr/bin/env python3
"""
Instagram discovery source — runs alongside the TikTok source, not instead of it.

Calibration settled this empirically: of Fleek's three named partners, @behindthesale and
@juliacrcl are on TikTok and @theliveneedham returned no TikTok data at all. A TikTok-only engine
is blind to a third of Fleek's own known-good partners. An Instagram-only engine would have missed
the two we measured.

Hashtags are tagged pro / hobbyist / consumer at the SOURCE. The brief asks for "a deliberate mix
across pro reseller audiences and hobbyist reseller audiences", and #balledefriperie (bale) and
#grossiste (wholesaler) surface different people than #haulfriperie does. Stratify where the
candidates enter, not only where the shortlist is picked.

Deliberately does NOT write to Airtable. `run_discovery.py` upserts with merge_on=["Handle"], so an
Instagram @nathanvialle would silently overwrite the TikTok @nathanvialle. The key must become
platform:handle first. This job scrapes, scores the free signals, and persists artifacts.

Usage:
    .venv/bin/python scripts/discover_instagram.py --smoke     # 2 hashtags, 10 posts, 10 profiles
    .venv/bin/python scripts/discover_instagram.py
"""
import argparse
import datetime as dt
import os
import statistics
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from content_brain.engine_io import (  # noqa: E402
    load_env, apify_instagram_hashtag_posts, apify_instagram_profiles,
    ig_posts_to_creators, save_artifact,
)
from content_brain.signals import lexicon_profile, fleek_signals, bio_flags  # noqa: E402

# Tagged by who they attract. The tag is a hypothesis the scrape tests, and the first version of
# this table was WRONG in an instructive way.
#
# 2026-07-10, smoke run: #grossiste and #balledefriperie were tagged "pro" because *wholesaler* and
# *bale* are pro words. They returned @ramzi_gros__, @kelisegroup, @sifcol.sifcol — wholesalers
# advertising stock, at 80-2,000 followers. Not creators at all.
#
# The lesson: hashtags have a SIDE. Suppliers tag their own posts with the words for what they sell.
# Resellers tag theirs with the words for what they DO. Discovery wants the demand side. The wiki
# had already recorded this ("Search mostly returned wholesale suppliers, not creators") and the
# hypothesis was written anyway.
SUPPLY_SIDE = {"grossiste", "balledefriperie", "vetementengros"}  # kept, but for the competitor map

HASHTAGS = {
    "achatrevente": "pro",           # buy-to-resell — @juliacrcl's own top hashtag
    "revendeuse": "pro",             # "I am a reseller" — self-description, demand side
    "reventevinted": "pro",
    "friperie": "hobbyist",
    "secondemain": "hobbyist",
    "haulfriperie": "consumer",      # haul = watching someone show clothes
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-hashtag", type=int, default=40)
    ap.add_argument("--max-profiles", type=int, default=40, help="cost breaker on the profile pass")
    ap.add_argument("--hashtags", nargs="+", help="override the table (all treated as untagged)")
    ap.add_argument("--min-followers", type=int, default=1000,
                    help="below this a follower ratio is noise, not a signal")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    load_env()
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        sys.exit("APIFY_API_TOKEN not found.")

    if args.hashtags:
        tags = {t.lstrip("#"): HASHTAGS.get(t.lstrip("#"), "untagged") for t in args.hashtags}
    else:
        tags = dict(list(HASHTAGS.items())[:2]) if args.smoke else HASHTAGS
    per = 10 if args.smoke else args.per_hashtag
    max_profiles = 10 if args.smoke else args.max_profiles

    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    run_dir = os.path.join(os.path.dirname(__file__), "..", "data", "discovery_ig", stamp)

    # One run per hashtag, so found_via is real rather than inferred.
    all_posts, spend = [], 0.0
    for tag, lean in tags.items():
        posts, run = apify_instagram_hashtag_posts([tag], per, token)
        spend += run.get("usageTotalUsd") or 0.0
        for p in posts:
            p["_searchHashtag"] = tag
        all_posts.extend(posts)
        print(f"[ig] #{tag:<18} ({lean:<8}) {len(posts):>3} posts   ${run.get('usageTotalUsd', 0):.4f}")

    save_artifact(run_dir, "raw_posts", all_posts)
    creators = ig_posts_to_creators(all_posts)
    print(f"\n[ig] {len(all_posts)} posts -> {len(creators)} unique creators")

    # Rank seeds by how many pro-leaning hashtags surfaced them, then by post count.
    def pro_tags(c):
        return sum(1 for t in c["found_via"] if tags.get(t) == "pro")
    seeds = sorted(creators.values(), key=lambda c: (pro_tags(c), len(c["post_urls"])), reverse=True)
    seeds = seeds[:max_profiles]
    print(f"[ig] resolving {len(seeds)} profiles (followers/bio need a second call)...")

    profiles, prun = apify_instagram_profiles([c["handle"] for c in seeds], token)
    spend += prun.get("usageTotalUsd") or 0.0
    save_artifact(run_dir, "raw_profiles", profiles)
    pmap = {p.get("username"): p for p in profiles if p.get("username")}

    # The profile actor returns an error STUB for a missing handle rather than raising:
    # {"username": "...", "error": "not_found"}. Without this guard it scores as a real creator
    # with 0 followers. @theliveneedham surfaced it.
    errored = [p.get("username") for p in profiles if p.get("error")]
    if errored:
        print(f"[ig] unresolvable, skipped: {', '.join(errored)}")

    rows = []
    for c in seeds:
        p = pmap.get(c["handle"], {})
        if p.get("error") or p.get("followersCount") is None:
            continue
        followers = p.get("followersCount") or 0
        bio = p.get("biography") or ""
        # The external URL carries signal the bio doesn't: @zozrsl's paid Discord lives there,
        # and a vinted.fr/member/... link says "I sell on Vinted" without saying it.
        links = " ".join(str(u) for u in [p.get("externalUrl"), p.get("externalUrls")] if u)
        corpus = bio + " " + links + " " + " ".join(c["captions"]) + " " + " ".join(c["hashtags"])
        eng = None
        if followers and c["likes"]:
            inter = statistics.median(c["likes"]) + (statistics.median(c["comments"]) if c["comments"] else 0)
            eng = round(inter / followers, 4)
        rows.append({
            "handle": c["handle"], "platform": "Instagram",
            "profile_url": p.get("url"), "followers": followers,
            "posts_count": p.get("postsCount"), "private": p.get("private"),
            "verified": p.get("verified"), "business_category": p.get("businessCategoryName"),
            "external_url": p.get("externalUrl"), "bio": bio[:300],
            "found_via": c["found_via"], "hashtag_lean": [tags.get(t) for t in c["found_via"]],
            "posts_seen": len(c["post_urls"]), "engagement_rate": eng,
            **lexicon_profile(corpus), **fleek_signals(corpus),
            "bio_flags": bio_flags(corpus),
        })

    rows.sort(key=lambda r: (r["mentions_fleek"], r["pro_ratio"], r["pro_terms"]), reverse=True)
    save_artifact(run_dir, "creators", rows)

    print(f"\n{'handle':<24}{'followers':>10}{'eng%':>7}{'pro':>5}{'cons':>6}{'ratio':>7}  via / signals")
    print("-" * 104)
    for r in rows[:25]:
        thin = r["followers"] < args.min_followers
        eng = "—" if (thin or not r["engagement_rate"]) else f"{r['engagement_rate'] * 100:.1f}"
        via = ",".join(r["found_via"][:2])
        extra = [k for k, v in r["bio_flags"].items() if v]
        if r["mentions_fleek"]:
            extra.append("★FLEEK")
        if r["private"]:
            extra.append("private")
        if r["business_category"]:
            extra.append(f"biz:{r['business_category'][:18]}")
        if thin:
            extra.append("micro")
        print(f"@{r['handle']:<23}{r['followers']:>10,}{eng:>7}{r['pro_terms']:>5}"
              f"{r['consumer_terms']:>6}{r['pro_ratio']:>7}  {via}"
              + (f"  +{','.join(extra)}" if extra else ""))

    print(f"\n[ig] apify spend this run: ${spend:.3f}")
    print(f"[ig] artifacts -> {os.path.relpath(run_dir)}/  (no Airtable write: key is still Handle-only)")


if __name__ == "__main__":
    main()
