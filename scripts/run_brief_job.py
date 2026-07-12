#!/usr/bin/env python3
"""brief_generator job — the state-triggered half of the autonomy layer.

Trigger: a creator's Airtable `Stage` becomes `Onboarded` and their `Brief` is empty.
Action:  profile them from their real posts, generate a personalised brief, write it back
         to their record, and publish a shareable Notion page they can actually open.

Idempotent by construction: it only touches records where `Brief` is empty, so a re-run
after a crash picks up exactly the ones that didn't finish. That is the whole recovery
strategy (see `spec/autonomy-layer.md` §4) — re-running is always safe.

Usage:
    python scripts/run_brief_job.py --dry-run            # show who would be briefed
    python scripts/run_brief_job.py --limit 3            # brief the next 3
    python scripts/run_brief_job.py --handle juliacourcelle --force
    python scripts/run_brief_job.py --no-notion          # Airtable writeback only

Reads ANTHROPIC_API_KEY, AIRTABLE_API_KEY, NOTION_API_KEY, NOTION_BRIEFS_PAGE_ID from the
workspace .env. Never from code, never from chat.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from content_brain.brief_generator import generate_brief
from content_brain.engine_io import Airtable, load_env
from content_brain.evidence import evidence_for_record
from content_brain.llm import get_llm
from content_brain.notion_publish import NotionError, brief_to_markdown, publish_brief
from content_brain.profiler import build_profile_from_evidence
from content_brain.store import load_insights

TABLE = "Creators"
TRIGGER_STAGE = "Onboarded"

# Created on first run if absent. Versioned in code, not clicked into the UI.
BRIEF_FIELDS = [
    {"name": "Brief", "type": "multilineText"},
    {"name": "Brief URL", "type": "url"},
    {"name": "Brief Generated At", "type": "dateTime",
     "options": {"timeZone": "Europe/Paris",
                 "dateFormat": {"name": "iso"}, "timeFormat": {"name": "24hour"}}},
]

# Max Claude calls per run. A runaway loop must not be able to bill the whole roster.
MAX_BRIEFS_PER_RUN = 25


def targets(at: Airtable, handle: str | None, force: bool) -> list[dict]:
    if handle:
        records = at.select(TABLE, f"LOWER({{Handle}}) = '{handle.lower().lstrip('@')}'")
        if not records:
            raise SystemExit(f"No Airtable record with Handle '{handle}'")
        if not force and records[0]["fields"].get("Brief"):
            raise SystemExit(f"@{handle} already has a brief. Pass --force to regenerate.")
        return records
    formula = f"AND({{Stage}} = '{TRIGGER_STAGE}', {{Brief}} = '')"
    return at.select(TABLE, formula)


def brief_one(record: dict, publish: bool) -> dict:
    """Profile -> brief -> rendered payload for the Airtable record."""
    fields = record["fields"]
    handle = (fields.get("Handle") or "").lstrip("@")

    evidence = evidence_for_record(record)
    profile = build_profile_from_evidence(evidence)
    brief = generate_brief(
        evidence.creator,
        profile,
        load_insights(),
        campaign="FR launch — activation",
        evidence=evidence,
    )

    payload = {
        "Brief": brief_to_markdown(brief, handle),
        "Brief Generated At": datetime.now(timezone.utc).isoformat(),
    }
    if publish:
        payload["Brief URL"] = publish_brief(brief, handle)
    return {"brief": brief, "payload": payload, "handle": handle, "evidence": evidence}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="list targets, generate nothing")
    ap.add_argument("--limit", type=int, default=MAX_BRIEFS_PER_RUN)
    ap.add_argument("--handle", help="brief one named creator, ignoring the Stage trigger")
    ap.add_argument("--force", action="store_true", help="regenerate even if a brief exists")
    ap.add_argument("--no-notion", action="store_true", help="skip Notion; write Airtable only")
    args = ap.parse_args()

    load_env()
    key = os.environ.get("AIRTABLE_API_KEY")
    if not key:
        raise SystemExit("AIRTABLE_API_KEY not found in the workspace .env")

    at = Airtable(key)
    created = at.ensure_fields(TABLE, BRIEF_FIELDS)
    if created:
        print(f"Created Airtable fields: {', '.join(created)}")

    records = targets(at, args.handle, args.force)
    if not records:
        print(f"Nothing to do — no creators at Stage='{TRIGGER_STAGE}' with an empty Brief.")
        return

    limit = min(args.limit, MAX_BRIEFS_PER_RUN)
    if len(records) > limit:
        print(f"! {len(records)} creators match; capping this run at {limit}. "
              f"Re-run to process the remaining {len(records) - limit}.")
        records = records[:limit]

    print(f"{len(records)} creator(s) to brief:")
    for r in records:
        print(f"  - @{r['fields'].get('Handle')} (stage={r['fields'].get('Stage')})")
    if args.dry_run:
        print("\n--dry-run: stopping before any generation or write.")
        return

    llm = get_llm()
    if llm.mock:
        print("\n! ANTHROPIC_API_KEY not set — briefs will be deterministic templates, "
              "not personalised. This is NOT what ships.\n")

    publish = not args.no_notion
    ok, failed = 0, 0
    for r in records:
        handle = r["fields"].get("Handle")
        try:
            result = brief_one(r, publish)
        except NotionError as e:
            # Notion is the delivery surface, not the source of truth. Degrade, don't abort:
            # write the brief to Airtable so the work isn't lost, and flag the publish failure.
            print(f"  ! @{handle}: Notion publish failed ({e}). Retrying Airtable-only.")
            try:
                result = brief_one(r, publish=False)
            except Exception as inner:  # noqa: BLE001
                print(f"  x @{handle}: {inner}")
                failed += 1
                continue
        except Exception as e:  # noqa: BLE001
            print(f"  x @{handle}: {e}")
            failed += 1
            continue

        at.update(TABLE, r["id"], result["payload"])
        url = result["payload"].get("Brief URL", "(not published)")
        code = result["evidence"].referral_code or "new code"
        print(f"  ✓ @{handle} [{result['evidence'].creator.lifecycle}, {code}] -> {url}")
        print(f"      {llm.cache_report()}")
        ok += 1

    print(f"\n{ok} briefed, {failed} failed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
