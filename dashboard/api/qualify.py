"""
Vercel serverless function: POST /api/qualify → manual qualification on the public site.

The discovery engine RECOMMENDS (scores prospects); a human QUALIFIES (Prospect->Qualified).
Reversible (Qualified->Prospect). Approving a below-recommend-line creator is allowed but flagged.

This only flips a creator's Stage label in Airtable — it never contacts anyone (outreach is a
separate, draft-only step). One-click by design: this is a case-study prototype, and a reversible
status change on a demo base doesn't warrant an auth wall. The Airtable key stays server-side.
Body: {"handle","stage"}.
"""
import json
import os
import sys

from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from pipeline import set_stage  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def _send(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
            return self._send(set_stage(body.get("handle"), body.get("stage")))
        except (KeyError, ValueError) as e:
            return self._send({"error": str(e)}, 400)
        except Exception as e:
            return self._send({"error": str(e)}, 500)
