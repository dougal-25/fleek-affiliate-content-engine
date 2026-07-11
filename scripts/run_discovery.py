#!/usr/bin/env python3
"""
Discovery engine — builds the Roster the weekly cycle consumes.

Market-driven, multi-channel, one enrichment path. Reads a market profile
(content_brain/markets/<market>.py) for every market-specific thing — channels, hashtags, graph
seeds, follower band — so the engine itself is market-agnostic machinery. Adding a market = writing a
profile, not editing this file.

    load market profile
      -> SOURCE per channel  (tiktok: hashtag scrape · instagram: relatedProfiles graph walk)
      -> ENRICH (one path)   (free gates: lexicon · fashion-vertical · supplier · fleek-code;
                              TikTok also gets an LLM reseller/segment read from captions)
      -> SHORTLIST BAR       (genuine reseller AND clothing vertical AND not supplier => Qualified)
      -> SINK                (Airtable upsert on Creator Key; one Run row)

Comments are NOT part of discovery — they enrich a creator's profile later where rich, ignored where
thin (spec/discovery-engine.md). This stage decides who is in the roster and who makes the shortlist.

Usage:
    .venv/bin/python scripts/run_discovery.py --market france                       # both channels
    .venv/bin/python scripts/run_discovery.py --market france --channels tiktok     # one channel
    .venv/bin/python scripts/run_discovery.py --market france --dry-run             # no Airtable write
    .venv/bin/python scripts/run_discovery.py --market france --smoke               # tiny, cheap
"""
import argparse
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))  # sibling import: discover_instagram_graph
from content_brain.engine_io import (  # noqa: E402
    load_env, apify_tiktok_scrape, videos_to_creators, Airtable, claude_json, creator_key,
    save_artifact,
)
from content_brain.signals import (  # noqa: E402
    lexicon_profile, fleek_signals, bio_flags, is_supplier, in_fashion_vertical,
    passes_shortlist_bar,
)
from content_brain import markets  # noqa: E402
from discover_instagram_graph import run_graph_walk  # noqa: E402

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
  "score": int 0-100,            // reseller credibility 40, audience relevance 30, wholesale/sourcing content 20, professionalism 10
  "score_breakdown": "factor: points, ... (compact)",
  "confidence": one of ["High","Medium","Low"]
}"""
# The model emits labels and a coarse fit score — never a currency figure (spec/cac-model.md §6).


def enrich_tiktok(c: dict) -> dict | None:
    caps = "\n".join(f"- {t}" for t in c["captions"][:5]) or "(none captured)"
    prompt = f"""Creator to score:
handle: @{c['handle']}  ({c.get('nick')})
followers: {c.get('followers')}   videos: {c.get('video_count')}   verified: {c.get('verified')}
bio: {(c.get('bio') or '')[:300]}
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


def tiktok_fields(c: dict, e: dict) -> dict:
    """Map a TikTok creator + its LLM read to Airtable fields, applying the shortlist bar."""
    corpus = " ".join([c.get("bio") or "", " ".join(c.get("captions") or []),
                       " ".join(c.get("hashtags") or [])])
    fashion = in_fashion_vertical(corpus, f"{c.get('handle')} {c.get('bio_link') or ''}")
    supplier = is_supplier(c.get("bio") or "", None)
    lx, fk = lexicon_profile(corpus), fleek_signals(corpus)
    qualified = passes_shortlist_bar(is_reseller=bool(e.get("is_reseller")),
                                     fashion_vertical=fashion, likely_supplier=supplier)
    f = {
        "Handle": c["handle"], "Creator Key": creator_key("TikTok", c["handle"]),
        "Platform": "TikTok", "Profile URL": c.get("profile_url"), "Followers": c.get("followers"),
        "Segment": "Wholesaler / supplier" if supplier else e.get("segment"),
        "Content Keywords": ", ".join(e.get("content_keywords") or []),
        "Strength": e.get("strength"), "Weakness": e.get("weakness"),
        "Score": e.get("score"), "Score Breakdown": e.get("score_breakdown"),
        "Confidence": e.get("confidence"), "Fleek Aware": fk["mentions_fleek"],
        "Stage": "Qualified" if qualified else "Prospect",
        "Outreach Status": "Not started",
        "Source": "discovery/tiktok: " + ",".join(c.get("found_via") or []),
        "Audience": (c.get("bio") or "")[:500],
        "Notes": f"pro_terms={lx['pro_terms']} fashion={fashion} supplier={supplier} "
                 f"videos={c.get('video_count')} langs={','.join(c.get('langs') or [])}",
    }
    if c.get("avatar"):
        f["Photo"] = [{"url": c["avatar"]}]
    if c.get("email"):
        f["Contact Email"], f["Contact Route"] = c["email"], "Bio email"
    else:
        f["Contact Route"] = "Link-in-bio" if c.get("bio_link") else "DM"
    return {k: v for k, v in f.items() if v is not None}, qualified


SEGMENT_BY_FLAG = [("whatnot", "Live seller"), ("coaching", "Reseller educator"),
                   ("discord", "Reseller educator")]


def ig_fields(r: dict) -> tuple[dict, bool]:
    """Map a graph-walk row to Airtable fields, applying the shortlist bar.

    Instagram gets NO LLM audience read at discovery time (its comment sections are lead-magnet noise,
    spec/discovery-engine.md). The reseller judgment is the deterministic gates: pro vocabulary in a
    clothing-vertical account that is not a supplier.
    """
    is_reseller = r["pro_terms"] >= 1
    qualified = passes_shortlist_bar(is_reseller=is_reseller,
                                     fashion_vertical=r["fashion_vertical"],
                                     likely_supplier=r["likely_supplier"])
    flags = [k for k, v in r["bio_flags"].items() if v]
    seg = "Wholesaler / supplier" if r["likely_supplier"] else next(
        (s for flag, s in SEGMENT_BY_FLAG if flag in flags), "Thrift flipper")
    fit = min(100, r["pro_terms"] * 12 + len(flags) * 8 + (20 if r["mentions_fleek"] else 0))
    f = {
        "Handle": r["handle"], "Creator Key": r["creator_key"], "Platform": "Instagram",
        "Profile URL": r.get("profile_url"), "Followers": r.get("followers"),
        "Engagement Rate": r.get("engagement_rate"), "Posts Per Week": r.get("posts_per_week"),
        "Segment": seg, "Content Keywords": ", ".join(r.get("top_hashtags") or []),
        "Score": fit, "Confidence": "Medium" if qualified else "Low",
        "Fleek Aware": r["mentions_fleek"],
        "Strength": f"pro vocab x{r['pro_terms']}"
                    + (f", {'+'.join(flags)}" if flags else "")
                    + (", already mentions Fleek" if r["mentions_fleek"] else ""),
        "Stage": "Qualified" if qualified else "Prospect", "Outreach Status": "Not started",
        "Source": "discovery/instagram: " + ",".join(r.get("found_via") or []),
        "Audience": (r.get("bio") or "")[:500],
        "Notes": f"pro_terms={r['pro_terms']} cons_terms={r['consumer_terms']} "
                 f"fashion={r['fashion_vertical']} supplier={r['likely_supplier']} biz={r.get('business_category')}",
    }
    return {k: v for k, v in f.items() if v is not None}, qualified


def run_tiktok(profile, token, per, fmin, fmax, limit_enrich, run_dir):
    tags = profile["tiktok_hashtags"]
    print(f"[tiktok] scraping {len(tags)} hashtags x {per}: {tags}")
    videos = apify_tiktok_scrape(tags, per, token)
    save_artifact(run_dir, "tiktok_raw_videos", videos)
    creators = videos_to_creators(videos)
    print(f"[tiktok] {len(videos)} videos -> {len(creators)} unique creators")

    def fr_ok(c):
        langs = c.get("langs") or []
        return (not langs) or ("fr" in langs)
    kept = [c for c in creators.values()
            if fr_ok(c) and not c.get("private")
            and fmin <= (c.get("followers") or 0) <= fmax]
    kept.sort(key=lambda c: c.get("followers") or 0, reverse=True)
    kept = kept[:limit_enrich]
    print(f"[tiktok] {len(kept)} pass pre-filter -> enriching with Claude (cap {limit_enrich})")

    rows, qualified = [], 0
    for i, c in enumerate(kept, 1):
        e = enrich_tiktok(c)
        if not e:
            continue
        fields, q = tiktok_fields(c, e)
        rows.append(fields)
        qualified += q
        print(f"  {i}/{len(kept)} @{c['handle']:<20} {'QUALIFIED' if q else 'roster':<9} "
              f"score={e.get('score')} {fields.get('Segment')} ({c.get('followers')} f)")
    print(f"[tiktok] {len(rows)} creators, {qualified} qualified")
    return rows, len(videos)


def run_instagram(profile, token, max_candidates, run_dir, smoke):
    rows_raw, spend = run_graph_walk(profile, token, max_candidates,
                                     os.path.join(run_dir, "ig_graph"), smoke=smoke)
    rows, qualified = [], 0
    for r in rows_raw:
        if r.get("private") or not r.get("followers"):
            continue
        fields, q = ig_fields(r)
        rows.append(fields)
        qualified += q
    print(f"[instagram] {len(rows_raw)} walked -> {len(rows)} written, {qualified} qualified "
          f"(${spend:.2f} apify)")
    return rows, len(rows_raw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="france")
    ap.add_argument("--channels", nargs="+", help="override profile channels (tiktok instagram)")
    ap.add_argument("--per", type=int, default=15, help="tiktok results per hashtag")
    ap.add_argument("--limit-enrich", type=int, default=40, help="cap TikTok Claude calls")
    ap.add_argument("--max-candidates", type=int, default=60, help="cap IG graph candidates")
    ap.add_argument("--smoke", action="store_true", help="tiny, cheap shape check")
    ap.add_argument("--dry-run", action="store_true", help="scrape+score, skip Airtable write")
    args = ap.parse_args()

    load_env()
    token = os.environ["APIFY_API_TOKEN"]
    profile = markets.get(args.market)
    channels = [c.lower() for c in (args.channels or profile["channels"])]
    started = dt.datetime.now().isoformat(timespec="seconds")
    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    run_dir = os.path.join(os.path.dirname(__file__), "..", "data", "discovery", stamp)
    print(f"[discovery] market={profile['name']} channels={channels}"
          + ("  [SMOKE]" if args.smoke else "") + ("  [DRY RUN]" if args.dry_run else ""))

    per = 3 if args.smoke else args.per
    limit_enrich = 4 if args.smoke else args.limit_enrich
    max_cand = 6 if args.smoke else args.max_candidates

    rows, items_in, notes = [], 0, []
    if "tiktok" in channels:
        tk_rows, tk_in = run_tiktok(profile, token, per, profile["follower_min"],
                                    profile["follower_max"], limit_enrich, run_dir)
        rows += tk_rows
        items_in += tk_in
        notes.append(f"tiktok {len(tk_rows)}")
    if "instagram" in channels:
        ig_rows, ig_in = run_instagram(profile, token, max_cand, run_dir, args.smoke)
        rows += ig_rows
        items_in += ig_in
        notes.append(f"instagram {len(ig_rows)}")

    qualified = sum(1 for r in rows if r.get("Stage") == "Qualified")
    save_artifact(run_dir, "airtable_rows", rows)
    finished = dt.datetime.now().isoformat(timespec="seconds")

    if args.dry_run:
        print(f"\n[dry-run] {len(rows)} creators ({qualified} qualified), Airtable write skipped")
        print(json.dumps(rows[:2], indent=2, ensure_ascii=False))
        return

    at = Airtable(os.environ["AIRTABLE_API_KEY"])
    n = at.upsert("Creators", rows, merge_on=["Creator Key"]) if rows else 0
    at.create("Runs", {
        "Run": f"discovery {started}", "Job": "discovery",
        "Started": started, "Finished": finished, "Status": "Success",
        "Items In": items_in, "Items Out": n,
        "Notes": f"market={profile['name']} " + " · ".join(notes)
                 + f" · {qualified} qualified for shortlist",
    })
    print(f"\n[discovery] upserted {n} creators ({qualified} qualified) + logged Run row")
    print(f"[discovery] base: https://airtable.com/{at.base_id}")


if __name__ == "__main__":
    main()
