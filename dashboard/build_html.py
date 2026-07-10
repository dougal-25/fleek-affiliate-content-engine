#!/usr/bin/env python3
"""
Bake the dashboard into ONE self-contained HTML file — double-click to open, no server.

Pulls the roster fresh from Airtable (snapshot fallback), computes trends + funnel,
fetches/caches avatars, inlines every stylesheet, script, image and datum, and writes:

    dashboard/fleek-affiliate-dashboard.html

Refresh the data any time:  python3 dashboard/build_html.py
"""
import base64
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from serve import (HERE, compute_funnel, compute_trends, get_avatar,  # noqa: E402
                   get_creators, image_type)

OUT = os.path.join(HERE, "fleek-affiliate-dashboard.html")


def read(name):
    with open(os.path.join(HERE, name)) as f:
        return f.read()


def main():
    print("Fetching creators…")
    creators = get_creators()
    print(f"  {len(creators['records'])} creators ({creators['source']})")

    print("Computing funnel + trends…")
    funnel = compute_funnel(creators)
    trends = compute_trends()

    print("Embedding avatars (first run fetches; later runs hit the disk cache)…")
    avatars = {}
    for r in creators["records"]:
        f = r["fields"]
        handle = f.get("Handle")
        if not handle:
            continue
        body = get_avatar(handle, f.get("Platform", "TikTok"))
        if body:
            mime = image_type(body) or "image/jpeg"
            avatars[handle] = f"data:{mime};base64," + base64.b64encode(body).decode()
    print(f"  {len(avatars)}/{len(creators['records'])} photos (rest get branded initials)")

    data = {"creators": creators, "funnel": funnel, "trends": trends, "avatars": avatars}
    # </script> inside a JSON string would end the script block early
    payload = json.dumps(data).replace("</", "<\\/")

    html = read("index.html")
    html = html.replace('<link rel="stylesheet" href="tokens.css">',
                        "<style>\n" + read("tokens.css") + "\n</style>")
    html = html.replace('<link rel="stylesheet" href="style.css">',
                        "<style>\n" + read("style.css") + "\n</style>")
    html = html.replace('<script src="charts.js"></script>',
                        "<script>window.__DATA__ = " + payload + "</script>\n"
                        "<script>\n" + read("charts.js") + "\n</script>")
    html = html.replace('<script src="app.js"></script>',
                        "<script>\n" + read("app.js") + "\n</script>")

    with open(OUT, "w") as f:
        f.write(html)
    print(f"→ {OUT}  ({os.path.getsize(OUT) / 1e6:.1f} MB)")
    print("Double-click it (or drag into a browser). No server, works offline.")


if __name__ == "__main__":
    main()
