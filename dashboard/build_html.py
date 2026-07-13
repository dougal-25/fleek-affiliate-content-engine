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
from pipeline import (HERE, compute_funnel, compute_inspiration, compute_trends,  # noqa: E402
                      get_avatar, get_creators, image_type)

OUT = os.path.join(HERE, "fleek-affiliate-dashboard.html")


def read(name):
    with open(os.path.join(HERE, name)) as f:
        return f.read()


def main():
    print("Fetching creators…")
    creators = get_creators()
    print(f"  {len(creators['records'])} creators ({creators['source']})")

    print("Computing funnel + trends + inspiration…")
    funnel = compute_funnel(creators)
    trends = compute_trends()
    inspiration = compute_inspiration(creators)

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

    # inline video thumbnails so the single file stays fully offline
    for p in inspiration["posts"]:
        if p.get("thumb"):
            path = os.path.join(HERE, p["thumb"].lstrip("/"))
            if os.path.exists(path):
                with open(path, "rb") as f:
                    p["thumb"] = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()
            else:
                p["thumb"] = None

    data = {"creators": creators, "funnel": funnel, "trends": trends,
            "inspiration": inspiration, "avatars": avatars}
    # </script> inside a JSON string would end the script block early
    payload = json.dumps(data).replace("</", "<\\/")

    html = read("index.html")
    logo_path = os.path.join(HERE, "assets", "fleek-logo.webp")
    with open(logo_path, "rb") as f:
        logo_uri = "data:image/webp;base64," + base64.b64encode(f.read()).decode()
    html = html.replace('src="assets/fleek-logo.webp"', f'src="{logo_uri}"')
    html = html.replace('<link rel="stylesheet" href="tokens.css">',
                        "<style>\n" + read("tokens.css") + "\n</style>")
    html = html.replace('<link rel="stylesheet" href="style.css">',
                        "<style>\n" + read("style.css") + "\n</style>")
    html = html.replace('<link rel="stylesheet" href="trends.css">',
                        "<style>\n" + read("trends.css") + "\n</style>")
    html = html.replace('<script src="charts.js"></script>',
                        "<script>window.__DATA__ = " + payload + "</script>\n"
                        "<script>\n" + read("charts.js") + "\n</script>")
    for script in ("translations.js", "helpers.js", "views.js", "app.js"):
        html = html.replace(f'<script src="{script}"></script>',
                            "<script>\n" + read(script) + "\n</script>")

    with open(OUT, "w") as f:
        f.write(html)
    print(f"→ {OUT}  ({os.path.getsize(OUT) / 1e6:.1f} MB)")
    print("Double-click it (or drag into a browser). No server, works offline.")


if __name__ == "__main__":
    main()
