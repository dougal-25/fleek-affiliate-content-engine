#!/usr/bin/env python3
"""
Build the Fleek Affiliate Ecosystem base — Creators + Runs tables — from code.

Why a script and not clicking: the whole pitch is "an engine, not a spreadsheet".
The schema is versioned, reproducible, and drops onto any Airtable account. Run it,
screenshot the result — that's a deck receipt.

Idempotent: skips a table if it already exists (safe to re-run).

Usage:
    python scripts/build_airtable_base.py
Reads AIRTABLE_API_KEY from the workspace .env (never hardcoded).
"""
import os
import sys
import json
import urllib.request
import urllib.error

BASE_NAME = "Fleek Affiliate Ecosystem"
ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
API = "https://api.airtable.com/v0/meta"


def load_key():
    # env first, then workspace .env
    key = os.environ.get("AIRTABLE_API_KEY")
    if key:
        return key.strip()
    with open(os.path.abspath(ENV_PATH)) as f:
        for line in f:
            if line.startswith("AIRTABLE_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("AIRTABLE_API_KEY not found in env or .env")


def api(method, path, key, body=None):
    url = f"{API}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        print(f"  ! {method} {path} -> {e.code}: {e.read().decode()[:300]}")
        raise


def sel(*names_colors):
    """Build singleSelect/multipleSelects choices. Pass (name, color) tuples."""
    return {"choices": [{"name": n, "color": c} for n, c in names_colors]}


# ---- Segment / stage vocabularies (from the Brain) ----
SEGMENTS = sel(
    ("Thrift flipper", "blueLight2"), ("Wholesale buyer", "cyanLight2"),
    ("Live seller", "tealLight2"), ("Reseller educator", "greenLight2"),
    ("Vinted seller", "yellowLight2"), ("Sourcing vlogger", "orangeLight2"),
    ("General fashion", "grayLight2"),
)
STAGES = sel(
    ("Prospect", "grayLight2"), ("Qualified", "blueLight2"),
    ("Contacted", "cyanLight2"), ("Responded", "tealLight2"),
    ("Call booked", "purpleLight2"), ("Contract", "pinkLight2"),
    ("Onboarded", "yellowLight2"), ("First post", "orangeLight2"),
    ("First sale", "redLight2"), ("Repeat posting", "greenLight2"),
)

CREATORS_FIELDS = [
    {"name": "Handle", "type": "singleLineText"},  # primary
    {"name": "Platform", "type": "singleSelect",
     "options": sel(("TikTok", "blueLight2"), ("Instagram", "pinkLight2"), ("YouTube", "redLight2"))},
    {"name": "Profile URL", "type": "url"},
    {"name": "Photo", "type": "multipleAttachments"},
    {"name": "Followers", "type": "number", "options": {"precision": 0}},
    {"name": "Audience", "type": "multilineText"},
    {"name": "Segment", "type": "singleSelect", "options": SEGMENTS},
    {"name": "Content Keywords", "type": "multilineText"},
    {"name": "Strength", "type": "multilineText"},
    {"name": "Weakness", "type": "multilineText"},
    {"name": "Score", "type": "number", "options": {"precision": 0}},
    {"name": "Score Breakdown", "type": "multilineText"},
    {"name": "Predicted CAC", "type": "currency", "options": {"precision": 2, "symbol": "£"}},
    {"name": "Confidence", "type": "singleSelect",
     "options": sel(("High", "greenLight2"), ("Medium", "yellowLight2"), ("Low", "redLight2"))},
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
    {"name": "Run", "type": "singleLineText"},  # primary
    {"name": "Job", "type": "singleSelect",
     "options": sel(("brain_refresh", "blueLight2"), ("discovery", "cyanLight2"),
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


def main():
    key = load_key()
    bases = api("GET", "/bases", key)["bases"]
    base = next((b for b in bases if b["name"] == BASE_NAME), None)
    if not base:
        sys.exit(f"Base '{BASE_NAME}' not found. Create it in Airtable first.")
    bid = base["id"]
    print(f"Base: {bid} ({BASE_NAME})")

    existing = {t["name"]: t for t in api("GET", f"/bases/{bid}/tables", key)["tables"]}
    print(f"Existing tables: {list(existing)}")

    plan = [
        ("Creators", "Every discovered creator + their score, funnel stage, outreach and brief.", CREATORS_FIELDS),
        ("Runs", "Observability: every engine job writes a row here. Stale = alarm.", RUNS_FIELDS),
    ]
    for name, desc, fields in plan:
        if name in existing:
            print(f"  = {name}: already exists, skipping")
            continue
        api("POST", f"/bases/{bid}/tables", key,
            {"name": name, "description": desc, "fields": fields})
        print(f"  + {name}: created ({len(fields)} fields)")

    print("\nDone. Base ready:", f"https://airtable.com/{bid}")


if __name__ == "__main__":
    main()
