#!/usr/bin/env python3
"""
Audience classification — who is listening, judged from what they say.

Keyword counting fails here, and fails dangerously. "Mon vinted : clara23dp" (a viewer
advertising their own closet) and "quel site pour acheter un lot de vêtements ?" (a viewer
asking where to buy stock) both contain reseller vocabulary. Only the second is a Fleek customer.
The difference is the speech act, not the words, so a model does the judging.

The model returns LABELS and QUOTES. It is never asked for a number that touches money.

Run blind: the prompt does not say which creators Fleek already rates. If the labels line up
with the known-good partners anyway, the method works.

Usage:
    python scripts/classify_audience.py                 # latest calibration run
    python scripts/classify_audience.py --sample 80
"""
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from content_brain.engine_io import load_env, claude_json, save_artifact  # noqa: E402

SYSTEM = """You classify the AUDIENCE of a creator, not the creator. You are given comments left on
their videos.

Context: Fleek is a B2B marketplace selling wholesale secondhand clothing in bulk (bales, lots) to
resellers. Fleek's customers are people who BUY STOCK TO RESELL. Two customer types:
- pro_reseller: runs reselling as a business. Sources bundles by brand/category, live-sells,
  talks margin, sell-through, inventory, suppliers, volume.
- hobbyist_reseller: flips clothes as a side hustle, price-sensitive, learning. Asks beginner
  sourcing questions, wants to start, low volume.
- general_consumer: buys clothes to WEAR. Compliments, styling, "where did you get it", outfit talk.

Critical distinction, because it is where naive keyword matching fails:
- A viewer ASKING THE CREATOR where to source stock, about suppliers, bales, price per kilo, or how
  to start buying inventory => reseller intent. This is a Fleek customer.
- A viewer ADVERTISING THEIR OWN SHOP ("mon vinted: xyz", "check my page") is self-promotion. It is
  NOT sourcing intent, and usually indicates a casual seller offloading a wardrobe, not a buyer of
  wholesale stock. Do not count it as pro.
- A viewer complimenting an item or asking where to BUY THAT ITEM to wear => general_consumer.
- COORDINATED PROMOTIONAL SPAM: several different accounts praising the same named tool or app in
  near-identical testimonial language ("X made me my first 1k", "just use X, it's better"). These are
  bots, not audience. Exclude them from every count and name the tool in `spam_campaigns`. They read
  as pro because they mention sales; they are worth nothing.

WHEN THE CHANNEL CARRIES NO SIGNAL, SAY SO. Set `signal_quality` to:
- "insufficient" if the comments are mostly emoji, single-word keyword replies ("Guide", "Niche" —
  a comment-to-DM lead-magnet trigger), or giveaway entries. These reveal a posting mechanic, not an
  audience.
- "polluted" if spam or self-promo dominates what is left.
- "usable" otherwise.
For "insufficient" or "polluted", set `dominant` to "unknown", `confidence` to "Low", and leave
audience_mix at zeros. An absent audience is NOT a consumer audience. Guessing "general_consumer"
because nobody mentioned wholesale would discard a real pro reseller whose viewers reply "Guide" to
claim a free PDF. Refusing to answer is the correct answer.

Judge from evidence. Quote real comments. Reply with JSON only, no prose."""

SCHEMA = """Return JSON:
{
  "signal_quality": "usable" | "insufficient" | "polluted",
  "audience_mix": {"pro_reseller": int, "hobbyist_reseller": int, "general_consumer": int},
  "dominant": "pro_reseller" | "hobbyist_reseller" | "general_consumer" | "unknown",
  "sourcing_intent_comments": int,
  "self_promo_comments": int,
  "spam_comments": int,
  "spam_campaigns": [str],
  "evidence": [{"handle": str, "quote": str, "label": str, "why": str}],
  "fleek_awareness": bool,
  "confidence": "High" | "Medium" | "Low",
  "reasoning": str
}
audience_mix percentages must sum to 100 and must EXCLUDE spam. evidence: 3-5 entries, verbatim
quotes, mixed labels."""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", help="calibration run dir (default: latest)")
    ap.add_argument("--sample", type=int, default=70, help="comments shown to the model per creator")
    args = ap.parse_args()

    load_env()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY not found.")

    run_dir = args.run_dir or sorted(glob.glob(
        os.path.join(os.path.dirname(__file__), "..", "data", "calibration", "*")))[-1]

    norm_path = os.path.join(run_dir, "comments_normalised.json")
    if os.path.exists(norm_path):
        comments = json.load(open(norm_path))          # Instagram, or any already-normalised run
    else:
        from content_brain.engine_io import normalise_comments   # noqa: PLC0415
        raw = json.load(open(os.path.join(run_dir, "raw_comments.json")))
        videos = json.load(open(os.path.join(run_dir, "raw_videos.json")))
        owner = {v["webVideoUrl"]: (v.get("authorMeta") or {}).get("name")
                 for v in videos if v.get("webVideoUrl")}
        comments = normalise_comments(raw, "TikTok", post_owner=owner)
        save_artifact(run_dir, "comments_normalised", comments)

    by: dict[str, list[dict]] = {}
    for c in comments:
        by.setdefault(c["creator"], []).append(c)
    print(f"[classify] {len(comments):,} comments across {len(by)} creators "
          f"({os.path.relpath(run_dir)})")

    results = {}
    for handle, cs in sorted(by.items(), key=lambda x: -len(x[1])):
        # spread the sample across posts rather than taking the first N of one post
        step = max(1, len(cs) // args.sample)
        sample = cs[::step][:args.sample]
        lines = "\n".join(
            f"- @{c['commenter']} ({c['likes']} likes): {c['text'][:200]}"
            for c in sample if c["text"]
        )
        prompt = (f"Comments left on videos by a creator (handle withheld). "
                  f"{len(sample)} of {len(cs)} sampled.\n\n{lines}\n\n{SCHEMA}")
        print(f"[classify] @{handle}: {len(sample)} comments -> Claude...")
        try:
            results[handle] = claude_json(prompt, SYSTEM, max_tokens=2000)
        except Exception as e:  # noqa: BLE001
            print(f"  ! failed: {e}")

    if not results:
        sys.exit("[classify] every call failed — nothing written")
    save_artifact(run_dir, "audience", results)

    print(f"\n{'creator':<24}{'signal':>13}{'pro':>5}{'hob':>5}{'cons':>6}{'dominant':>19}{'src':>5}{'spam':>6}{'conf':>8}")
    print("-" * 100)
    for h, r in sorted(results.items(), key=lambda x: -x[1]["audience_mix"]["pro_reseller"]):
        m = r["audience_mix"]
        star = " \u2605fleek" if r.get("fleek_awareness") else ""
        sq = r.get("signal_quality", "usable")
        print(f"@{h:<23}{sq:>13}{m['pro_reseller']:>5}{m['hobbyist_reseller']:>5}{m['general_consumer']:>6}"
              f"{r['dominant']:>19}{r.get('sourcing_intent_comments', 0):>5}"
              f"{r.get('spam_comments', 0):>6}{r['confidence']:>8}{star}")
        if r.get("spam_campaigns"):
            print(f"      spam campaigns: {', '.join(r['spam_campaigns'])}")

    print("\nevidence:")
    for h, r in results.items():
        print(f"\n@{h} — {r['reasoning']}")
        for e in r.get("evidence", [])[:3]:
            print(f"   [{e['label']:<18}] @{e['handle']}: {e['quote'][:78]}")

    print(f"\n[classify] saved -> {os.path.relpath(run_dir)}/audience.json")


if __name__ == "__main__":
    main()
