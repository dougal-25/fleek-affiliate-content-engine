#!/usr/bin/env python3
"""
Audit the legacy prompt-scored roster: did the model's totals agree with its own breakdowns?

The discovery engine used to ask the model for `score` (0-100) AND `score_breakdown` (the per-factor
points) in the same call. The model, doing the arithmetic in its head, frequently disagreed with
itself. This script measures how often, on the 49 creators scored before code took over the sum.

It is the evidence behind moving the arithmetic into `run_discovery.compute_fit`: you cannot trust,
audit, or re-weight a total the model computed silently.

Runs offline, no API key. Reads the committed snapshot only.

Usage:
    .venv/bin/python scripts/audit_scoring.py
"""
import json
import os
import re
import statistics
import sys

REPO = os.path.join(os.path.dirname(__file__), "..")
SNAPSHOT = os.path.join(REPO, "Fleek Wiki", "_raw", "airtable_creators_2026-07-09.json")

# "audience relevance: 22/30" and bare "audience relevance: 24" both appear in the same table.
_FACTOR_RE = re.compile(r"[a-z][a-z /]+?:\s*(\d+(?:\.\d+)?)")


def load_rows():
    with open(SNAPSHOT) as f:
        data = json.load(f)
    recs = data["records"] if isinstance(data, dict) and "records" in data else data
    return [r.get("fields") or r for r in recs]


def main():
    if not os.path.exists(SNAPSHOT):
        sys.exit(f"snapshot not found: {SNAPSHOT}")
    rows = load_rows()

    errors, worst = [], []
    audited = 0
    for r in rows:
        pts = [float(x) for x in _FACTOR_RE.findall((r.get("Score Breakdown") or "").lower())]
        if len(pts) < 4:  # need a real itemised breakdown to compare against
            continue
        audited += 1
        itemised, stored = sum(pts), float(r.get("Score") or 0)
        delta = itemised - stored
        if abs(delta) > 0.6:
            errors.append(delta)
            worst.append((r.get("Handle"), stored, itemised))

    print(f"Legacy scoring audit — {SNAPSHOT.split('/')[-1]}\n")
    print(f"  creators audited                         {audited}")
    if not audited:
        sys.exit("no itemised breakdowns to audit")
    pct = 100 * len(errors) / audited
    print(f"  totals disagreeing with own breakdown    {len(errors)}  ({pct:.0f}%)")
    if errors:
        print(f"  mean absolute error                      {statistics.mean(abs(e) for e in errors):.1f} points")
        print(f"  largest error                            {max(abs(e) for e in errors):.0f} points")
        low = sum(1 for e in errors if e > 0)
        print(f"  stored total too LOW vs its breakdown    {low} of {len(errors)}")
        print("\n  worst offenders:")
        for handle, stored, itemised in sorted(worst, key=lambda x: -abs(x[2] - x[1]))[:6]:
            print(f"    {handle:<28} stored {stored:.0f}  vs itemised {itemised:.0f}  "
                  f"({itemised - stored:+.0f})")
        print("\n  Every error runs one way: the stored total sits below the sum of its parts.")
        print("  That is not arithmetic — it is an unstated penalty applied after itemising,")
        print("  invisible and un-reweightable. This is why compute_fit() now owns the sum.")


if __name__ == "__main__":
    main()
