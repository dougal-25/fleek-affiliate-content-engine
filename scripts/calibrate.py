#!/usr/bin/env python3
"""
Calibration scrape — measure what a known-good partner actually looks like.

Fleek named three top-performing partners in the task brief. The scorer was written against
guessed archetypes instead. This job scrapes those three plus a French reference set drawn from
`Fleek Wiki/research/French Reseller Creator Shortlist.md`, and prints the observable features
side by side, so the scoring rubric can be written from evidence rather than imagination.

It writes every stage to data/calibration/<timestamp>/ before doing anything else with it. A
re-score then costs nothing; only a re-scrape costs money.

Nothing here touches Airtable and nothing is scored yet. This is a measurement, not a decision.

Usage:
    python scripts/calibrate.py --smoke                  # 1 profile, 3 videos, no comments
    python scripts/calibrate.py                          # all 8 profiles, 12 videos each
    python scripts/calibrate.py --comments 15            # also pull comments (audience evidence)
"""
import argparse
import datetime as dt
import os
import statistics
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from content_brain.engine_io import (  # noqa: E402
    load_env, apify_tiktok_profiles, save_artifact,
)
from content_brain.signals import (  # noqa: E402
    lexicon_profile, fleek_signals, bio_flags,
)

# The brief's three. Platform is an assumption — TikTok is Fleek's main creator channel, but the
# brief never says. A miss here is itself a finding: it means they live elsewhere.
FLEEK_PARTNERS = ["behindthesale", "theliveneedham", "juliacrcl"]

# French reference set, from the wiki. Handles are press-sourced and flagged there as unverified.
FR_REFERENCE = ["nathanviall3", "bichettekids", "giu.cst", "claravictorya", "juliettekitsch"]

def features(videos: list[dict], min_age_days: int = 7) -> dict:
    """Collapse one profile's videos into the observable feature vector.

    Views are measured only on posts older than `min_age_days`. A post scraped a day after it
    went up has not finished accumulating views, and `profileSorting=latest` returns exactly
    those. Including them drags the median down by several multiples.
    """
    am = videos[0].get("authorMeta") or {}
    today = dt.date.today()
    plays, rates, dates, tags, captions, langs = [], [], [], set(), [], set()
    sponsored = 0

    for v in videos:
        if v.get("text"):
            captions.append(v["text"])
        if v.get("textLanguage"):
            langs.add(v["textLanguage"])
        if v.get("isSponsored") or v.get("isAd"):
            sponsored += 1
        for h in (v.get("hashtags") or []):
            name = h.get("name") if isinstance(h, dict) else h
            if name:
                tags.add(name.lower())

        iso = v.get("createTimeISO")
        if not iso:
            continue
        d = dt.date.fromisoformat(iso[:10])
        dates.append(d)
        if (today - d).days < min_age_days:
            continue  # too fresh to count views
        p = v.get("playCount") or 0
        if p:
            plays.append(p)
            eng = (v.get("diggCount") or 0) + (v.get("commentCount") or 0) + (v.get("shareCount") or 0)
            rates.append(eng / p)

    bio = am.get("signature") or ""
    corpus = bio + " " + " ".join(captions) + " " + " ".join(tags)

    cadence = None
    if len(dates) >= 2:
        span = (max(dates) - min(dates)).days
        cadence = round(len(dates) / (span / 7), 1) if span >= 7 else None

    followers = am.get("fans") or 0
    median_views = int(statistics.median(plays)) if plays else 0

    return {
        "handle": am.get("name"),
        "nick": am.get("nickName"),
        "followers": followers,
        "videos_sampled": len(videos),
        "videos_view_eligible": len(plays),
        "median_views": median_views,
        # Views per follower. Low = a tight audience; high = algorithmic reach beyond it.
        "view_through_rate": round(median_views / followers, 3) if followers else None,
        "engagement_rate": round(statistics.median(rates), 4) if rates else None,
        "posts_per_week": cadence,
        "verified": am.get("verified"),
        "languages": sorted(langs),
        "sponsored_posts": sponsored,
        **fleek_signals(corpus),
        "bio": bio[:300],
        "bio_link": am.get("bioLink"),
        "top_hashtags": sorted(tags)[:12],
        **lexicon_profile(corpus),
        "bio_flags": bio_flags(corpus),
        "sample_captions": captions[:3],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--videos", type=int, default=20, help="videos per profile")
    ap.add_argument("--comments", type=int, default=0, help="comments per video (0 = skip)")
    ap.add_argument("--min-age-days", type=int, default=7, help="ignore views on posts younger than this")
    ap.add_argument("--smoke", action="store_true", help="1 profile, 3 videos — shape check")
    args = ap.parse_args()

    load_env()
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        sys.exit("APIFY_API_TOKEN not found. Checked the nearest .env walking up from content_brain/.")

    profiles = FLEEK_PARTNERS[:1] if args.smoke else FLEEK_PARTNERS + FR_REFERENCE
    videos_per = 3 if args.smoke else args.videos
    comments = 0 if args.smoke else args.comments

    est = len(profiles) * videos_per / 1000 * 1.70
    print(f"[calibrate] {len(profiles)} profiles x {videos_per} videos "
          f"(comments/post={comments}) — est. ${est:.2f} at $1.70/1k results")
    print(f"[calibrate] profiles: {', '.join(profiles)}")

    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    run_dir = os.path.join(os.path.dirname(__file__), "..", "data", "calibration", stamp)

    videos = apify_tiktok_profiles(profiles, videos_per, token, comments_per_post=comments)
    raw_path = save_artifact(run_dir, "raw_videos", videos)
    print(f"[calibrate] {len(videos)} video rows -> {os.path.relpath(raw_path)}")

    by_handle: dict[str, list[dict]] = {}
    for v in videos:
        h = (v.get("authorMeta") or {}).get("name")
        if h:
            by_handle.setdefault(h, []).append(v)

    missing = [p for p in profiles if p.lower() not in {k.lower() for k in by_handle}]
    if missing:
        print(f"[calibrate] NO TIKTOK DATA for: {', '.join(missing)} "
              f"(wrong platform, renamed, or private — a finding, not an error)")

    feats = {h: features(vs, args.min_age_days) for h, vs in by_handle.items()}
    save_artifact(run_dir, "features", feats)

    print(f"\n{'handle':<20}{'followers':>10}{'med.views':>11}{'v/f':>7}{'eng%':>7}{'/wk':>6}{'lang':>6}  signals")
    print("-" * 104)
    for group, names in (("FLEEK PARTNER (known-good)", FLEEK_PARTNERS), ("FR REFERENCE (wiki)", FR_REFERENCE)):
        print(f"— {group} —")
        for name in names:
            f = next((v for k, v in feats.items() if k.lower() == name.lower()), None)
            if not f:
                print(f"  {name:<18}{'—':>10}   (no tiktok data)")
                continue
            hits = f["lexicon_hits"]
            pro = len(hits["fr_pro"]) + len(hits["en_pro"])
            cons = len(hits["fr_consumer"]) + len(hits["en_consumer"])
            sig = f"pro:{pro} cons:{cons}"
            flags = [k for k, on in f["bio_flags"].items() if on]
            if flags:
                sig += " +" + ",".join(flags)
            if f["fleek_referral_codes"]:
                sig += "  ★FLEEK:" + ",".join(f["fleek_referral_codes"])
            if f["sponsored_posts"]:
                sig += f"  ads:{f['sponsored_posts']}"
            eng = f"{f['engagement_rate'] * 100:.1f}" if f["engagement_rate"] else "—"
            lang = ",".join(f["languages"][:2]) or "—"
            print(f"  {f['handle']:<18}{f['followers']:>10,}{f['median_views']:>11,}"
                  f"{f['view_through_rate'] or 0:>7}{eng:>7}{str(f['posts_per_week'] or '—'):>6}{lang:>6}  {sig}")

    print(f"\n[calibrate] artifacts in {os.path.relpath(run_dir)}/  (re-score is free from here)")


if __name__ == "__main__":
    main()
