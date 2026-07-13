#!/usr/bin/env python3
"""
Judge-variance test — is the model's per-factor rating stable enough to score on?

Since compute_fit() moved the arithmetic into code, the four LLM ratings ARE the score. If the same
creator, judged repeatedly from identical evidence, comes back 8/10 then 5/10 on a factor, the
ranking is a coin flip. This checks it before we trust the shortlist.

Method: run the real judging path (`run_discovery.enrich_tiktok`) N times on the same creator, at the
temperature we actually score at, and report the spread per factor. Two creators — evidence-rich and
evidence-thin — because the worry is that the judge invents confidence when evidence runs out.

PASS: max spread on any factor <= 2 points (0-10 scale).

Usage:
    .venv/bin/python scripts/test_judge_variance.py            # 5 runs each
    .venv/bin/python scripts/test_judge_variance.py --runs 3
Needs ANTHROPIC_API_KEY (from the workspace .env). ~2 API calls per run per creator.
"""
import argparse
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from content_brain.engine_io import load_env  # noqa: E402
import run_discovery as disc  # noqa: E402

RAW = os.path.join(os.path.dirname(__file__), "..", "Fleek Wiki", "_raw",
                   "apify_tiktok_posts_2026-07-09.jsonl")
FACTORS = ["reseller_credibility", "audience_relevance", "wholesale_sourcing", "professionalism"]


def creators_from_raw():
    """Group the TikTok corpus by author into the shape enrich_tiktok expects."""
    by: dict[str, list[str]] = {}
    with open(RAW) as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            h = r.get("author")
            if h:
                by.setdefault(h, []).append(r.get("text") or "")
    made = {}
    for h, texts in by.items():
        made[h] = {
            "handle": h, "nick": h, "followers": None, "video_count": len(texts),
            "verified": False, "bio": "", "found_via": ["friperie"], "hashtags": [],
            "langs": ["fr"], "captions": [t for t in texts if t.strip()],
        }
    return made


def run_creator(c: dict, runs: int) -> float:
    label = f"@{c['handle']}"
    print(f"\n{'=' * 66}\n{label}  ({len(c['captions'])} captions)\n{'=' * 66}")
    ratings = {f: [] for f in FACTORS}
    reseller = []
    for i in range(runs):
        e = disc.enrich_tiktok(c)
        if not e:
            print(f"  run {i + 1}: FAILED")
            continue
        reseller.append(bool(e.get("is_reseller")))
        cells = []
        for f in FACTORS:
            raw = e.get(f)
            r = raw.get("rating") if isinstance(raw, dict) else raw
            if r is not None:
                ratings[f].append(float(r))
                cells.append(f"{f.split('_')[0][:4]}={float(r):.0f}")
        print(f"  run {i + 1}: {'  '.join(cells)}   reseller={e.get('is_reseller')}")

    print(f"\n  {'factor':<24}{'min':>5}{'max':>5}{'spread':>8}")
    worst = 0.0
    for f in FACTORS:
        v = ratings[f]
        if not v:
            print(f"  {f:<24}   no data")
            continue
        spread = max(v) - min(v)
        worst = max(worst, spread)
        flag = "  <-- exceeds 2" if spread > 2 else ""
        print(f"  {f:<24}{min(v):>5.0f}{max(v):>5.0f}{spread:>8.0f}{flag}")
    if len(set(reseller)) > 1:
        print(f"  !! is_reseller flipped: {reseller}")
    print(f"\n  worst spread for {label}: {worst:.0f}  ({'PASS' if worst <= 2 else 'FAIL'})")
    return worst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=5)
    args = ap.parse_args()
    load_env()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY not found in env or workspace .env")

    made = creators_from_raw()
    ranked = sorted(made.values(), key=lambda c: sum(len(t) for t in c["captions"]))
    thin, rich = ranked[0], ranked[-1]

    print(f"Judge-variance — {args.runs} runs per creator, production temperature.")
    worst = max(run_creator(rich, args.runs), run_creator(thin, args.runs))
    print(f"\n{'#' * 66}\nVERDICT: worst spread = {worst:.0f} points")
    print("PASS — ratings are stable enough to score on." if worst <= 2 else
          "FAIL — coarsen the scale or average N samples per creator before trusting the rank.")
    print("#" * 66)


if __name__ == "__main__":
    main()
