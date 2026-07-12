"""
Vercel serverless function: GET /api/data → everything the dashboard needs, in one call.

- creators: LIVE from Airtable (AIRTABLE_API_KEY lives in Vercel env, never in the page),
  enriched exactly like the local server, falling back to the committed snapshot.
- PUBLIC REDACTION: contact emails and outreach drafts never leave this function.
- funnel: live stage counts + the committed local history as baseline.
- trends / inspiration / avatars manifest: precomputed by make_static.py (static sources).
"""
import json
import os
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from pipeline import STAGES, enrich, fetch_creators_live  # noqa: E402

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_static")
REDACT = ("Contact Email", "Outreach Draft")


def read_static(name, default):
    try:
        with open(os.path.join(STATIC, name)) as f:
            return json.load(f)
    except OSError:
        return default


def get_creators():
    key = os.environ.get("AIRTABLE_API_KEY", "").strip()
    if key:
        try:
            records = fetch_creators_live(key)
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            return enrich({"source": "live", "fetched": now, "records": records})
        except Exception:
            pass
    return read_static("creators_snapshot.json", {"source": "snapshot", "records": []})


def build_payload():
    creators = get_creators()
    for r in creators["records"]:
        for field in REDACT:
            r["fields"].pop(field, None)

    stages = {s: 0 for s in STAGES}
    for r in creators["records"]:
        stages[r["fields"].get("Stage", "Prospect")] = \
            stages.get(r["fields"].get("Stage", "Prospect"), 0) + 1
    history = read_static("funnel_baseline.json", [])
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if creators["source"] == "live" and not any(h["date"] == today for h in history):
        history = history + [{"date": today, "stages": stages}]

    return {
        "creators": creators,
        "funnel": {"stages": stages, "history": history, "source": creators["source"]},
        "trends": read_static("trends.json", {}),
        "inspiration": read_static("inspiration.json", {"posts": []}),
        "avatars": read_static("avatars.json", {}),
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps(build_payload()).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        # cache at the edge for a minute: fresh enough to demo stage moves on reload
        self.send_header("Cache-Control", "s-maxage=60, stale-while-revalidate=300")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
