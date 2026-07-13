#!/usr/bin/env python3
"""
Fleek Affiliate Dashboard — local dev server (HTTP only).

Serves the static dashboard and proxies its data so the Airtable key never reaches the
browser. All data/compute logic lives in pipeline.py; this file is just the request handler.

    /api/creators   live Airtable roster; snapshot fallback if offline
    /api/trends     hashtag intelligence from the ingested posts
    /api/funnel     stage counts + compounding weekly history
    /api/inspiration  relevance-gated, overperformance-ranked video wall
    /api/qualify    POST — manual approval: move ONE creator Prospect<->Qualified
    /avatar/<h>     profile image proxy (unavatar.io), disk-cached

Stdlib only. Run:  python3 dashboard/serve.py   then open http://localhost:8787
"""
import json
import os
import sys
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from pipeline import (HERE, compute_funnel, compute_inspiration, compute_trends,
                      get_avatar, get_creators, image_type, load_key, set_stage)

PORT = int(os.environ.get("PORT", 8787))


def read_static_json(name, default):
    """Read a precomputed snapshot from api/_static (same source api/data.py serves on Vercel)."""
    try:
        with open(os.path.join(HERE, "api", "_static", name)) as f:
            return json.load(f)
    except OSError:
        return default


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=HERE, **kw)

    def log_message(self, fmt, *args):
        if "/avatar/" not in (args[0] if args else ""):
            super().log_message(fmt, *args)

    def send_json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        try:
            if path == "/api/creators":
                return self.send_json(get_creators())
            if path == "/api/trends":
                return self.send_json(compute_trends())
            if path == "/api/funnel":
                return self.send_json(compute_funnel(get_creators()))
            if path == "/api/inspiration":
                return self.send_json(compute_inspiration(get_creators()))
            if path == "/api/briefs":
                return self.send_json(read_static_json("briefs.json", {"creators": []}))
            if path.startswith("/avatar/"):
                handle = urllib.parse.unquote(path.split("/avatar/", 1)[1])
                platform = "youtube" if "platform=YouTube" in self.path else "tiktok"
                body = get_avatar(handle, platform)
                if body:
                    self.send_response(200)
                    self.send_header("Content-Type", image_type(body) or "image/jpeg")
                    self.send_header("Content-Length", str(len(body)))
                    self.send_header("Cache-Control", "max-age=86400")
                    self.end_headers()
                    return self.wfile.write(body)
                return self.send_json({"error": "no avatar"}, 404)
        except BrokenPipeError:
            return
        except Exception as e:
            return self.send_json({"error": str(e)}, 500)
        return super().do_GET()

    def do_POST(self):
        # Local dev writes are ungated (localhost is Doug's own machine). The public
        # deployment gates the same action behind QUALIFY_TOKEN — see api/qualify.py.
        if self.path.split("?")[0] != "/api/qualify":
            return self.send_json({"error": "not found"}, 404)
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
            return self.send_json(set_stage(body.get("handle"), body.get("stage")))
        except (KeyError, ValueError) as e:
            return self.send_json({"error": str(e)}, 400)
        except BrokenPipeError:
            return
        except Exception as e:
            return self.send_json({"error": str(e)}, 500)


def main():
    key = load_key()
    mode = "LIVE (Airtable key found)" if key else "SNAPSHOT (no AIRTABLE_API_KEY)"
    print(f"Fleek Affiliate Dashboard — {mode}")
    print(f"→ http://localhost:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    sys.exit(main())
