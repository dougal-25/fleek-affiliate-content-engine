#!/usr/bin/env python3
"""
Approve creators — the human gate the discovery engine hands off to.

The engine RECOMMENDS (sets the Recommended star); qualifying is a deliberate human act. This is that
act as a first-class command: approve named creators, moving them Prospect -> Qualified — the state
the outreach-draft job consumes. Auto-qualification stays off by design (spec/discovery-engine.md §4);
this is the manual approval it hands off to.

You can approve a creator the engine did NOT recommend (human override) — it's allowed and flagged,
because the whole point of a human gate is judgment the gates can't encode.

Usage:
  .venv/bin/python scripts/qualify.py --list                     # the review queue (Recommended, pending)
  .venv/bin/python scripts/qualify.py @juliacrcl @saw2hands      # approve these (by handle)
  .venv/bin/python scripts/qualify.py --key tiktok:coco_duc      # approve one exact platform:handle
  .venv/bin/python scripts/qualify.py @juliacrcl -p instagram    # disambiguate a cross-platform handle
  .venv/bin/python scripts/qualify.py @someone --unqualify       # reverse an approval (back to Prospect)
  .venv/bin/python scripts/qualify.py @juliacrcl --dry-run       # show what would change, write nothing
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from content_brain.engine_io import load_env, Airtable, creator_key  # noqa: E402


def norm(h: str) -> str:
    return h.strip().lstrip("@").lower()


def index(recs: list[dict]) -> dict:
    """Map every creator to its record, keyed by Creator Key and by bare handle (handle may be
    ambiguous across platforms — resolved with --platform)."""
    by_key, by_handle = {}, {}
    for r in recs:
        f = r["fields"]
        key = (f.get("Creator Key") or "").lower()
        if key:
            by_key[key] = r
        h = norm(f.get("Handle") or "")
        by_handle.setdefault(h, []).append(r)
    return by_key, by_handle


def resolve(target: str, platform: str | None, by_key, by_handle) -> tuple[list[dict], str]:
    """Return (records, note). One record on success; [] on not-found; multiple on ambiguity."""
    if ":" in target:  # explicit Creator Key
        r = by_key.get(target.lower())
        return ([r], "") if r else ([], "no creator with that key")
    h = norm(target)
    if platform:
        r = by_key.get(creator_key(platform, h))
        return ([r], "") if r else ([], f"not found on {platform}")
    matches = by_handle.get(h, [])
    if len(matches) > 1:
        plats = ", ".join(sorted(m["fields"].get("Platform", "?") for m in matches))
        return (matches, f"on multiple platforms ({plats}) — pass --platform")
    return (matches, "" if matches else "not found")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("handles", nargs="*", help="creator handles (@name) or platform:handle keys")
    ap.add_argument("--key", action="append", default=[], help="approve by exact platform:handle")
    ap.add_argument("-p", "--platform", help="disambiguate a handle present on >1 platform")
    ap.add_argument("--list", action="store_true", help="show the review queue and exit")
    ap.add_argument("--unqualify", action="store_true", help="reverse: Qualified -> Prospect")
    ap.add_argument("--dry-run", action="store_true", help="show changes, write nothing")
    args = ap.parse_args()

    load_env()
    at = Airtable(os.environ["AIRTABLE_API_KEY"])
    recs = at.list_records("Creators")
    by_key, by_handle = index(recs)

    if args.list:
        queue = [r["fields"] for r in recs
                 if r["fields"].get("Recommended") and r["fields"].get("Stage") == "Prospect"]
        queue.sort(key=lambda f: -(f.get("Score") or 0))
        print(f"REVIEW QUEUE — {len(queue)} recommended, pending your approval\n")
        print(f"{'handle':<26}{'platform':<11}{'score':>6}{'followers':>10}  segment")
        print("-" * 78)
        for f in queue:
            print(f"@{f.get('Handle',''):<25}{f.get('Platform','?'):<11}{f.get('Score') or 0:>6}"
                  f"{(f.get('Followers') or 0):>10,}  {f.get('Segment','')}")
        print(f"\napprove with:  scripts/qualify.py @handle [@handle ...]")
        return

    targets = list(args.handles) + [f"{k}" for k in args.key]
    if not targets:
        sys.exit("nothing to approve. Pass handles, or --list to see the queue.")

    new_stage = "Prospect" if args.unqualify else "Qualified"
    verb = "unqualify" if args.unqualify else "approve"
    updates, skipped = [], []
    for t in targets:
        matches, note = resolve(t, args.platform, by_key, by_handle)
        if not matches:
            skipped.append(f"@{norm(t)}: {note}"); continue
        if len(matches) > 1:
            skipped.append(f"@{norm(t)}: {note}"); continue
        r = matches[0]; f = r["fields"]
        cur = f.get("Stage")
        if cur == new_stage:
            skipped.append(f"@{f.get('Handle')} ({f.get('Platform')}): already {new_stage}"); continue
        flag = ""
        if not args.unqualify and not f.get("Recommended"):
            flag = "  ⚠ not engine-recommended — approving on your judgment"
        updates.append((r["id"], f, flag))

    if skipped:
        print("skipped:")
        for s in skipped:
            print(f"  - {s}")
    if not updates:
        print(f"\nnothing to {verb}."); return

    print(f"\nwill {verb} ({new_stage}):")
    for _id, f, flag in updates:
        print(f"  @{f.get('Handle'):<24} {f.get('Platform'):<10} score={f.get('Score') or 0}{flag}")

    if args.dry_run:
        print("\n[dry-run] nothing written.")
        return

    n = at.update_records("Creators", [{"id": _id, "fields": {"Stage": new_stage}}
                                       for _id, _f, _fl in updates])
    if args.unqualify:
        print(f"\n{n} creator(s) moved back to Prospect.")
    else:
        print(f"\n{n} creator(s) approved -> Qualified. Now in the outreach queue "
              f"(the outreach-draft job drafts, never auto-sends).")


if __name__ == "__main__":
    main()
