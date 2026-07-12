"""
Vercel serverless function: POST /api/qualify → the manual-approval gate on the public site.

Mirrors scripts/qualify.py: the discovery engine RECOMMENDS, a human QUALIFIES (Prospect->Qualified).
Reversible (Qualified->Prospect). Approving a non-recommended creator is allowed but flagged.

SAFE BY DEFAULT: writes are DISABLED unless QUALIFY_TOKEN is set in the Vercel project env.
When set, every request must carry a matching X-Qualify-Token header. Body: {"key","stage"}.
(The Airtable key stays server-side, exactly as /api/data does.)
"""
import json
import os
import sys

from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from serve import set_stage  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def _send(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        required = (os.environ.get("QUALIFY_TOKEN") or "").strip()
        if not required:
            return self._send({"error": "qualification is disabled on this deployment "
                                        "(set QUALIFY_TOKEN to enable)"}, 403)
        if (self.headers.get("X-Qualify-Token") or "").strip() != required:
            return self._send({"error": "unauthorized"}, 401)
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
            return self._send(set_stage(body.get("handle"), body.get("stage")))
        except (KeyError, ValueError) as e:
            return self._send({"error": str(e)}, 400)
        except Exception as e:
            return self._send({"error": str(e)}, 500)
