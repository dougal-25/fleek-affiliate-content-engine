#!/usr/bin/env python3
"""
Prepare the static assets the Vercel deployment needs. Run before `vercel deploy`
(and re-run after a new ingest or when avatars change):

    python3 dashboard/make_static.py

Writes:
    api/_static/trends.json ­— precomputed from the committed post jsonl (static source)
    api/_static/inspiration.json — same
    api/_static/funnel_baseline.json — history snapshots accrued locally, deployed as baseline
    api/_static/creators_snapshot.json — offline fallback for /api/data
    avatars/<handle>.<ext> + api/_static/avatars.json — cached photos as real static files
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline import (AVATAR_DIR, HERE, HISTORY_PATH, SNAPSHOT, compute_inspiration,  # noqa: E402
                      compute_trends, enrich, image_type)

STATIC = os.path.join(HERE, "api", "_static")
AVATARS_OUT = os.path.join(HERE, "avatars")
EXT = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}


def main():
    os.makedirs(STATIC, exist_ok=True)
    os.makedirs(AVATARS_OUT, exist_ok=True)

    with open(SNAPSHOT) as f:
        creators = enrich({"source": "snapshot", "fetched": "2026-07-09", "records": json.load(f)})
    # the deployed snapshot is pre-redacted — emails/outreach never enter the deployment bundle
    for r in creators["records"]:
        r["fields"].pop("Contact Email", None)
        r["fields"].pop("Outreach Draft", None)

    jobs = {
        "trends.json": compute_trends(),
        "inspiration.json": compute_inspiration(creators),
        "creators_snapshot.json": creators,
        "funnel_baseline.json": json.load(open(HISTORY_PATH)) if os.path.exists(HISTORY_PATH) else [],
    }

    manifest = {}
    if os.path.isdir(AVATAR_DIR):
        for name in os.listdir(AVATAR_DIR):
            path = os.path.join(AVATAR_DIR, name)
            with open(path, "rb") as f:
                head = f.read(16)
            ext = EXT.get(image_type(head))
            if not ext:
                continue
            shutil.copyfile(path, os.path.join(AVATARS_OUT, name + ext))
            manifest[name] = f"/avatars/{name}{ext}"
    jobs["avatars.json"] = manifest

    for name, obj in jobs.items():
        with open(os.path.join(STATIC, name), "w") as f:
            json.dump(obj, f)
        print(f"  api/_static/{name}")
    print(f"  {len(manifest)} avatar files → avatars/")


if __name__ == "__main__":
    main()
