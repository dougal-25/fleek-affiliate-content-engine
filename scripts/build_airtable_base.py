#!/usr/bin/env python3
"""
Build and migrate the Fleek Affiliate Ecosystem base — schema as code.

Why a script and not clicking: the whole pitch is "an engine, not a spreadsheet". The schema is
versioned, reproducible, and drops onto any Airtable account. Run it, screenshot the result —
that's a deck receipt.

Idempotent in three ways, safe to re-run:
  - creates a table only if it is missing
  - adds only the fields an existing table lacks
  - backfills `Creator Key` only on rows that have none

`Creator Key` is the migration that matters. The base was keyed on `Handle`, and
`@behindthesale` on TikTok (Fleek's top partner) is a different person from `@behindthesale` on
Instagram (a real-estate coach, 110 followers). Upserting on Handle alone would have overwritten
one with the other the moment an Instagram source came online. See spec/discovery-scoring.md §7.4.

Usage:
    .venv/bin/python scripts/build_airtable_base.py --dry-run
    .venv/bin/python scripts/build_airtable_base.py
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from content_brain.engine_io import load_env, creator_key  # noqa: E402

BASE_NAME = "Fleek Affiliate Ecosystem"
API = "https://api.airtable.com/v0/meta"


def api(method, path, key, body=None):
    req = urllib.request.Request(f"{API}{path}",
                                 data=json.dumps(body).encode() if body else None, method=method)
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        print(f"  ! {method} {path} -> {e.code}: {e.read().decode()[:300]}")
        raise


def sel(*names_colors):
    return {"choices": [{"name": n, "color": c} for n, c in names_colors]}


SEGMENTS = sel(
    ("Thrift flipper", "blueLight2"), ("Wholesale buyer", "cyanLight2"),
    ("Live seller", "tealLight2"), ("Reseller educator", "greenLight2"),
    ("Vinted seller", "yellowLight2"), ("Sourcing vlogger", "orangeLight2"),
    ("General fashion", "grayLight2"),
)
STAGES = sel(
    ("Prospect", "grayLight2"), ("Qualified", "blueLight2"), ("Contacted", "cyanLight2"),
    ("Responded", "tealLight2"), ("Call booked", "purpleLight2"), ("Contract", "pinkLight2"),
    ("Onboarded", "yellowLight2"), ("First post", "orangeLight2"),
    ("First sale", "redLight2"), ("Repeat posting", "greenLight2"),
)
# Who they ARE (credibility gate) vs who WATCHES them (addressable market). Two fields, on purpose:
# @nathanviall3 is a pro creator with a 55%-hobbyist audience. One field hides that.
CREATOR_TYPE = sel(("Pro reseller", "greenLight2"), ("Hobbyist reseller", "yellowLight2"),
                   ("General fashion", "grayLight2"), ("Wholesaler / supplier", "redLight2"))
AUDIENCE_DOMINANT = sel(("Pro reseller", "greenLight2"), ("Hobbyist reseller", "yellowLight2"),
                        ("General consumer", "grayLight2"))
CONF = sel(("High", "greenLight2"), ("Medium", "yellowLight2"), ("Low", "redLight2"))
CAC_BAND = sel(("£", "greenLight2"), ("££", "yellowLight2"), ("£££", "redLight2"))

CREATORS_FIELDS = [
    {"name": "Handle", "type": "singleLineText"},  # primary
    {"name": "Creator Key", "type": "singleLineText"},   # platform:handle — the upsert key
    {"name": "Platform", "type": "singleSelect",
     "options": sel(("TikTok", "blueLight2"), ("Instagram", "pinkLight2"), ("YouTube", "redLight2"))},
    {"name": "Profile URL", "type": "url"},
    {"name": "Photo", "type": "multipleAttachments"},
    {"name": "Followers", "type": "number", "options": {"precision": 0}},
    {"name": "Median Views", "type": "number", "options": {"precision": 0}},
    {"name": "Engagement Rate", "type": "number", "options": {"precision": 4}},
    {"name": "Posts Per Week", "type": "number", "options": {"precision": 1}},
    {"name": "Audience", "type": "multilineText"},
    {"name": "Creator Type", "type": "singleSelect", "options": CREATOR_TYPE},
    {"name": "Audience Dominant", "type": "singleSelect", "options": AUDIENCE_DOMINANT},
    {"name": "Audience Pro %", "type": "number", "options": {"precision": 0}},
    {"name": "Audience Hobbyist %", "type": "number", "options": {"precision": 0}},
    {"name": "Audience Consumer %", "type": "number", "options": {"precision": 0}},
    {"name": "Audience Evidence", "type": "multilineText"},
    {"name": "Audience Confidence", "type": "singleSelect", "options": CONF},
    {"name": "Sourcing Intent per 100", "type": "number", "options": {"precision": 1}},
    {"name": "Fleek Aware", "type": "checkbox", "options": {"icon": "check", "color": "greenBright"}},
    {"name": "Fit Score", "type": "number", "options": {"precision": 0}},
    {"name": "Fit Breakdown", "type": "multilineText"},
    {"name": "Expected Orders Per Post", "type": "number", "options": {"precision": 2}},
    {"name": "CAC Band", "type": "singleSelect", "options": CAC_BAND},
    {"name": "Segment", "type": "singleSelect", "options": SEGMENTS},
    {"name": "Content Keywords", "type": "multilineText"},
    {"name": "Strength", "type": "multilineText"},
    {"name": "Weakness", "type": "multilineText"},
    {"name": "Score", "type": "number", "options": {"precision": 0}},
    {"name": "Score Breakdown", "type": "multilineText"},
    # Python computes this, never the model. Precision 0: £42.17 is false precision wearing a suit.
    {"name": "Predicted CAC", "type": "currency", "options": {"precision": 0, "symbol": "£"}},
    {"name": "Confidence", "type": "singleSelect", "options": CONF},
    {"name": "Stage", "type": "singleSelect", "options": STAGES},
    {"name": "Contact Email", "type": "email"},
    {"name": "Contact Route", "type": "singleSelect",
     "options": sel(("DM", "blueLight2"), ("Bio email", "cyanLight2"),
                    ("Link-in-bio", "tealLight2"), ("Apollo", "purpleLight2"))},
    {"name": "Outreach Draft", "type": "multilineText"},
    {"name": "Outreach Status", "type": "singleSelect",
     "options": sel(("Not started", "grayLight2"), ("Draft", "yellowLight2"), ("Sent", "greenLight2"))},
    {"name": "Brief", "type": "multilineText"},
    {"name": "Brief URL", "type": "url"},
    {"name": "Kalodata GMV", "type": "currency", "options": {"precision": 0, "symbol": "£"}},
    {"name": "Kalodata Trend", "type": "singleLineText"},
    {"name": "Source", "type": "singleLineText"},
    {"name": "Notes", "type": "multilineText"},
]

RUNS_FIELDS = [
    {"name": "Run", "type": "singleLineText"},
    {"name": "Job", "type": "singleSelect",
     "options": sel(("wiki_refresh", "blueLight2"), ("discovery", "cyanLight2"),
                    ("outreach_drafts", "yellowLight2"), ("brief_generator", "purpleLight2"),
                    ("weekly_report", "greenLight2"))},
    {"name": "Started", "type": "dateTime",
     "options": {"dateFormat": {"name": "iso"}, "timeFormat": {"name": "24hour"}, "timeZone": "Europe/London"}},
    {"name": "Finished", "type": "dateTime",
     "options": {"dateFormat": {"name": "iso"}, "timeFormat": {"name": "24hour"}, "timeZone": "Europe/London"}},
    {"name": "Status", "type": "singleSelect",
     "options": sel(("Running", "yellowLight2"), ("Success", "greenLight2"), ("Failed", "redLight2"))},
    {"name": "Items In", "type": "number", "options": {"precision": 0}},
    {"name": "Items Out", "type": "number", "options": {"precision": 0}},
    {"name": "Notes", "type": "multilineText"},
]

TABLES = [
    ("Creators", "Every discovered creator + their score, funnel stage, outreach and brief.", CREATORS_FIELDS),
    ("Runs", "Observability: every engine job writes a row here. Stale = alarm.", RUNS_FIELDS),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="report the diff, change nothing")
    args = ap.parse_args()

    load_env()
    key = os.environ.get("AIRTABLE_API_KEY")
    if not key:
        sys.exit("AIRTABLE_API_KEY not found in env or the nearest .env")

    bases = api("GET", "/bases", key)["bases"]
    base = next((b for b in bases if b["name"] == BASE_NAME), None)
    if not base:
        sys.exit(f"Base '{BASE_NAME}' not found. Create it in Airtable first.")
    bid = base["id"]
    print(f"Base: {bid} ({BASE_NAME})" + ("   [DRY RUN]" if args.dry_run else ""))

    existing = {t["name"]: t for t in api("GET", f"/bases/{bid}/tables", key)["tables"]}

    for name, desc, fields in TABLES:
        if name not in existing:
            if args.dry_run:
                print(f"  + would CREATE table {name} ({len(fields)} fields)")
                continue
            api("POST", f"/bases/{bid}/tables", key, {"name": name, "description": desc, "fields": fields})
            print(f"  + {name}: created ({len(fields)} fields)")
            continue

        tid = existing[name]["id"]
        have = {f["name"] for f in existing[name]["fields"]}
        missing = [f for f in fields if f["name"] not in have]
        if not missing:
            print(f"  = {name}: up to date ({len(have)} fields)")
            continue
        print(f"  ~ {name}: {len(missing)} field(s) to add: {', '.join(f['name'] for f in missing)}")
        if args.dry_run:
            continue
        for f in missing:
            api("POST", f"/bases/{bid}/tables/{tid}/fields", key, f)
            print(f"      + {f['name']} ({f['type']})")

    backfill_creator_key(bid, key, args.dry_run)
    print(f"\nDone. Base: https://airtable.com/{bid}")


def backfill_creator_key(bid: str, key: str, dry_run: bool):
    """Existing rows predate the key. Without this they would duplicate on the next upsert."""
    from content_brain.engine_io import Airtable
    at = Airtable(key)
    records = at.list_records("Creators")
    todo = []
    for r in records:
        f = r["fields"]
        if f.get("Creator Key") or not f.get("Handle"):
            continue
        todo.append({"id": r["id"],
                     "fields": {"Creator Key": creator_key(f.get("Platform") or "TikTok", f["Handle"])}})

    print(f"\nCreator Key backfill: {len(records)} rows, {len(todo)} need one")
    if not todo:
        return
    for t in todo[:5]:
        print(f"   {t['fields']['Creator Key']}")
    if len(todo) > 5:
        print(f"   ... and {len(todo) - 5} more")
    if dry_run:
        print("   [DRY RUN] not written")
        return
    print(f"   backfilled {at.update_records('Creators', todo)} rows")


if __name__ == "__main__":
    main()
