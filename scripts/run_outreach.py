#!/usr/bin/env python3
"""
Outreach drafts job — the engine's third stage.

Airtable creators -> recent posts + audience comments -> Claude extracts personalisation
variables -> Claude drafts a 3-touch French sequence -> back to Airtable as Status = Draft.

NOTHING IS SENT. There is no send code path in this file, and there will not be one. A human
reads the draft in Airtable, edits it, sends it themselves, and flips Status = Sent. That gate
is the audit trail. Crossing a score threshold triggers a *draft*, never a message.

The pipeline: discovery scores creators -> a HUMAN qualifies the ones worth pursuing
(Stage = Qualified, always a human act, always overridable) -> qualification triggers this job,
which DRAFTS the outreach. Qualification is the gate; scoring only surfaces candidates.

Three selection modes:
    --qualified             THE AGENT TRIGGER: every human-qualified creator not yet contacted.
                            This is the call a scheduler makes once the agent is active.
    --handles a b c         hand-pick specific creators (manual runs, the case study).
    --auto                  candidate-finder: everyone above the percentile bar (--top-pct,
                            default 50) — use it to decide who to qualify, NOT to send outreach.

The --auto bar is a percentile of the roster's live score distribution, not a fixed number:
calibrating against Fleek's named top partners showed one scoring 62 against a guessed bar of 70.
Known partners in the roster are FLAGGED on the draft, never silently dropped.

Every message is personalised: the creator's real FIRST NAME (never the @handle, never invented),
their recent posts, their audience's comments, and the live trends their content sits on.

Usage:
    .venv/bin/python scripts/run_outreach.py --qualified --dry-run       # the agent trigger
    .venv/bin/python scripts/run_outreach.py --handles gdefou --dry-run  # manual pick
    .venv/bin/python scripts/run_outreach.py --qualified                 # writes drafts to Airtable
"""
import argparse
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from content_brain import evidence  # noqa: E402
from content_brain.engine_io import (  # noqa: E402
    APIFY_STATS, CLAUDE_STATS, Airtable, claude_json, load_env,
)

RECEIPTS_DIR = Path(__file__).resolve().parents[1] / "data" / "outreach"

# Fleek's three named top-performing partners (mission/mission.md:76). They are FLAGGED, not
# excluded (Doug's call, 2026-07-10): nothing sends, so the human gate should SEE a known partner
# in the pipeline — with a loud banner on the draft — rather than lose them from it. A cold pitch
# to an existing partner is the wrong message; the banner says to reframe as re-activation.
KNOWN_PARTNERS = {"behindthesale", "theliveneedham", "juliacrcl"}
# Inferred from the name, NOT confirmed by Fleek — the flag says so.
SUSPECTED_ALIASES = {"juliacourcelle": "juliacrcl"}

EXTRACT_SYSTEM = """You extract personalisation variables for outreach to French secondhand-fashion
resellers. You are given a creator's recent posts and their audience's comments.

Hard rules:
- Every claim must be supported by a verbatim quote from the supplied evidence. No inference beyond
  what the text says. If the evidence does not support a field, set it to null.
- Quotes stay in their original language, exactly as written. Never translate inside `evidence`.
- Only cite posts from the evidence provided. It has already been filtered to a recency window;
  citing anything else is a factual error.
- The audience_question must be a real recurring theme in the comments, not a plausible one.
- first_name: give the creator's real first name ONLY if it is clearly present in the display name,
  bio or captions (e.g. display name "Julia Courcelle" -> "Julia"; a caption "moi c'est Léa"
  -> "Léa"). A brand/shop name is NOT a first name (e.g. "Code des Grands Friperie" -> null). If you
  are not sure it is a person's given name, return null. Never guess, never invent — a wrong name is
  worse than no name.

Reply with JSON only, no prose."""

EXTRACT_SCHEMA = """Return a JSON object:
{
  "first_name": "the creator's real given name if clearly present in the display name/bio/captions, else null",
  "sells": "one sentence: what they actually sell and to whom",
  "sourcing_signal": "how/where they source, or null if never mentioned",
  "audience_question": "the question their commenters keep asking, or null",
  "standout_post": {"url": str, "date": "YYYY-MM-DD", "views": int, "why": "why it outperformed"},
  "trend_hook": "the live FR resale trend their recent content sits on, or null",
  "register": "tu" or "vous",
  "angle": "the single most compelling reason THIS creator would reply to Fleek",
  "do_not_say": ["things that would offend or bore this specific creator"],
  "evidence": [{"quote": "verbatim", "source": "caption" or "comment" or "transcript"}]
}"""

# Long, stable, identical across every creator -> sent as a cached prefix. This is the difference
# between 10 creators and 1,000 costing the same per-creator system-prompt bill.
DRAFT_SYSTEM = """You write first-touch recruitment outreach to French secondhand-fashion resellers
on behalf of Fleek, a B2B marketplace selling graded secondhand clothing wholesale to resellers.

THE GOAL: make this creator want to (a) SOURCE their stock through Fleek and/or (b) bring the
resellers who follow them to Fleek and earn from it. One relationship, both sides — the creator is
the buyer, so sourcing margin funds the incentive; they aren't competing for a separate commission
budget. Competitors offer one or the other. You are opening a conversation, not closing it: ask for
a reply, then a short call. This person is not a partner yet — no referral codes, links or discounts
in a first touch.

FLEEK'S VALUE PALETTE — pick the ONE or TWO that fit THIS creator's niche and what the profile
flagged. Never list them all (a feature dump reads as a mail-merge); never invent a number or a
claim not stated here:
- DIRECT GLOBAL SUPPLY: a marketplace of 2,000+ verified suppliers across 100+ countries — they
  source direct, not off one middleman's shelf. Breadth of brand, era, style and price point one
  local grossiste can't match.
- DE-RISKED BUYING: "Make an Offer" to negotiate the price on a bundle or a single piece; low
  minimums (from ~10 pieces — test a supplier without committing to a blind bale); Buy-Now-Pay-Later
  up to 30 days after the goods arrive. (This is the honest version of "good pricing" — concrete
  mechanics, not a "we're cheaper" claim.)
- GRADING THEY CAN TRUST: every piece QC'd and graded at Fleek's hubs, now with Fleek Sort — AI
  grading trained on 4 years of data — so "grade A ordered" is "grade A received", backed by a Buyer
  Protection Policy. This is the direct answer to the trade's grading wound.
- THE RELATIONSHIP: they aren't left alone after they pay — Fleek handles customs and shipping, the
  in-app assistant (Fleeky) matches them to suppliers, and there is a real person managing the
  partnership. In FR specifically, poor communication/support is the #1 reason creators quit
  programs, so this is a genuine differentiator — not a throwaway line.
- EARN AS WELL AS BUY: they can bring their reseller audience to Fleek and earn on it — the
  affiliate/referral side of the same relationship.

FACTUAL DISCIPLINE: the only hard figures you may state are the ones above (2,000+ suppliers, 100+
countries, ~10-piece minimum, 30-day BNPL, 4 years of Fleek Sort data). Never invent commission
rates, discount amounts, percentages, or "cheaper/better than X" claims. If you assert any Fleek
benefit that is not spelled out in the palette above, add it to `human_check` so a human confirms it
before anything is sent.

THE FRENCH RESELLER'S WORLD (from the research wiki — use it, don't explain it):
- Trade vocabulary they use daily: balle / ballot (a compressed bale), au kilo, a la piece,
  original (unsorted raw stock), creme / extra creme (near-new top tier), grade A / B / C,
  tri / trie / 1er choix (sorting, sorted, first-pick), semi-grossiste (buys smaller lots),
  deballage (bale-unboxing content), colis mystere. Using the trade's words is the proof you know
  the trade. Using none of them marks you as an outsider marketer.
- Their wound: opaque grading. "Quand vous commandez un article dit grade A vous recevrez que du
  grade B." Bales arrive stained, misgraded, unsellable. 20-40% of a raw ballot is waste. This is
  the pain Fleek's AI grading answers — but state it as a fact about the trade, never as a
  sales pitch, and never claim their supplier specifically scammed them.
- THEIR STATUS: professional resellers believe Fleek is for beginners. This is the single biggest
  objection. Address a pro as a professional buyer, talking margin, grading consistency and
  sourcing reliability. Never "grow your side hustle." Never explain reselling to a reseller.

REGISTER: use the `register` variable. "vous" to a professional or an older/established seller;
"tu" only where their own content is informal and youth-facing. When in doubt, "vous".

NAME: if `first_name` is present, address them by it, naturally, the way a peer would (a bare
"Salut Julia," or worked into the first line) — NOT every touch, once is warmer than three times.
If `first_name` is null, open directly on their content and use no name at all. NEVER address them
by their @handle, and NEVER use a placeholder like [name] or "hey there" — a handle-as-name or an
empty bracket is the tell of a mail-merge and worse than no name.

VOICE: short. A DM, not a press release. No brand adjectives, no "I hope this finds you well",
no "I came across your profile and was blown away". Open on something only someone who watched
their content could say. Earn the second sentence.

LEAD WITH THEM, NOT WITH FLEEK: open every sequence on the creator's own niche and a specific
flagged observation — their standout post, what they actually sell, the question their audience
keeps asking — then bridge into the ONE value-palette item that fits it. The observation earns the
pitch; the pitch never leads.

THE THREE TOUCHES each take a DIFFERENT angle, drawing on DIFFERENT palette items — never "just
bumping this up":
  1. day 0  — their niche / a specific recent post → the single most relevant Fleek value for THEM
              + the one-line reason to talk.
  2. day 4  — a different, concrete value proof (the 2,000-supplier breadth, the grading answer,
              the de-risked buying, or an answer to their audience's recurring question). Assume
              touch 1 went unread, not refused.
  3. day 10 — the graceful close. Leave the door open, ask nothing, give one useful thing.

Write `fr` in natural French — idiomatic, not translated English. Then write `en_gloss` as a close
back-translation so a non-French reviewer can check the French says what it claims to say.

Reply with JSON only, no prose."""

DRAFT_SCHEMA = """Return a JSON object:
{
  "channel": "DM" or "Email",
  "touches": [
    {"n": 1, "send_day": 0,  "angle": "...", "fr": "...", "en_gloss": "..."},
    {"n": 2, "send_day": 4,  "angle": "...", "fr": "...", "en_gloss": "..."},
    {"n": 3, "send_day": 10, "angle": "...", "fr": "...", "en_gloss": "..."}
  ],
  "localisation_notes": ["choices made for FR that a UK message would not need"],
  "human_check": ["what a human must verify before sending: native-speaker language/register checks, AND any Fleek benefit claimed that is not a hard palette fact (e.g. exact support offer, pricing) — flag it for commercial confirmation"]
}"""


def known_partner_note(handle: str) -> str | None:
    h = handle.lower().lstrip("@")
    if h in KNOWN_PARTNERS:
        return ("KNOWN FLEEK PARTNER (mission/mission.md) — do not cold-pitch. "
                "Reframe as re-activation before anything is sent.")
    if h in SUSPECTED_ALIASES:
        return (f"POSSIBLE KNOWN PARTNER — may be @{SUSPECTED_ALIASES[h]}, named a top performer "
                f"in mission/mission.md. VERIFY the identity; if confirmed, a cold pitch is the "
                f"wrong message — reframe as re-activation.")
    return None


def score_bar(at: Airtable, args) -> tuple[int, str]:
    """The selection bar is a PERCENTILE of the roster's live score distribution, not a fixed
    number. Calibration found a known top partner scoring 62 against a guessed absolute bar of 70;
    Doug's call: set the bar where the known-good tier actually sits, then let activation raise the
    roster's scores so the same percentile becomes a rising absolute bar. --min-score overrides."""
    if args.min_score is not None:
        return args.min_score, f"absolute override (--min-score {args.min_score})"
    scores = sorted(
        (r["Score"] for r in at.list("Creators", max_records=200) if r.get("Score") is not None),
        reverse=True,
    )
    if not scores:
        raise SystemExit("No scored creators in the base — run discovery first")
    k = max(1, int(len(scores) * args.top_pct / 100))
    cutoff = scores[k - 1]
    return cutoff, f"top {args.top_pct:.0f}% of {len(scores)} scored creators"


def select(at: Airtable, args) -> tuple[list[dict], str]:
    if args.handles:
        clauses = ",".join(f'{{Handle}}="{h}"' for h in args.handles)
        formula = f"OR({clauses})"
        bar_note = "hand-picked"
    elif args.qualified:
        # The canonical agent trigger: a human qualified them, so draft the outreach. Qualification
        # IS the human gate — scoring only surfaces candidates; a person decides who to pursue.
        formula = 'AND({Outreach Status}="Not started",{Stage}="Qualified")'
        bar_note = "Stage=Qualified (human-qualified — the agent trigger)"
    else:
        cutoff, basis = score_bar(at, args)
        print(f"[outreach] score bar: {cutoff} ({basis})")
        parts = ['{Outreach Status}="Not started"', f"{{Score}}>={cutoff}"]
        if args.stage:
            parts.append(f'{{Stage}}="{args.stage}"')
        formula = f"AND({','.join(parts)})"
        bar_note = f"bar {cutoff} ({basis})"
    rows = at.list("Creators", formula=formula, max_records=100)
    rows.sort(key=lambda r: r.get("Score") or 0, reverse=True)
    return rows, bar_note


def extract_variables(row: dict, ev: dict, days: int) -> dict | None:
    posts = "\n".join(
        f"- [{p['date']}] {p['views']:,} views | {p['url']}\n  {p['text'][:300]}"
        for p in ev["posts"][:6]
    ) or "(none)"
    comments = "\n".join(f"- ({c['likes']} likes) {c['text']}" for c in ev["comments"][:20]) or "(none)"
    transcript = f"\nTranscript excerpt of a recent video:\n{ev['transcript'][:1500]}" if ev.get("transcript") else ""
    prompt = f"""Creator: @{row.get('Handle')} on {row.get('Platform')}
Profile display name: {ev.get('display_name') or '(none captured)'}
Followers: {row.get('Followers')} | Engine segment: {row.get('Segment')}
Bio: {(row.get('Audience') or '')[:300]}
What the scoring pass said — strength: {row.get('Strength')} | weakness: {row.get('Weakness')}

Their posts from the last {days} days (newest first):
{posts}

What their audience commented:
{comments}
{transcript}

{EXTRACT_SCHEMA}"""
    try:
        return claude_json(prompt, EXTRACT_SYSTEM, max_tokens=2000)
    except Exception as e:  # noqa: BLE001
        print(f"  ! extract failed @{row.get('Handle')}: {e}")
        return None


def draft_sequence(row: dict, variables: dict) -> dict | None:
    route = row.get("Contact Route") or "DM"
    prompt = f"""Write the outreach sequence.

Creator: @{row.get('Handle')} on {row.get('Platform')} ({row.get('Followers')} followers)
Contact route: {route}  (so channel should be {"Email" if route == "Bio email" else "DM"})
Engine segment: {row.get('Segment')}

Personalisation variables extracted from their own recent content:
{json.dumps(variables, ensure_ascii=False, indent=1)}

Every specific claim you make about them must trace to those variables. If `sourcing_signal` is
null, do not speculate about how they source.

{DRAFT_SCHEMA}"""
    try:
        return claude_json(prompt, DRAFT_SYSTEM, max_tokens=3000)
    except Exception as e:  # noqa: BLE001
        print(f"  ! draft failed @{row.get('Handle')}: {e}")
        return None


def format_for_airtable(drafts: dict, variables: dict) -> str:
    """The human's review surface. FR to send, EN to check it, and why it says what it says."""
    lines = [f"CHANNEL: {drafts.get('channel')}", ""]
    for t in drafts.get("touches", []):
        lines += [
            f"--- TOUCH {t.get('n')} · send day +{t.get('send_day')} · {t.get('angle')} ---",
            "",
            t.get("fr", ""),
            "",
            f"[EN check] {t.get('en_gloss', '')}",
            "",
        ]
    lines.append("LOCALISATION CHOICES:")
    lines += [f"  · {n}" for n in drafts.get("localisation_notes", [])]
    lines.append("")
    lines.append("NATIVE-SPEAKER QA — verify before sending:")
    lines += [f"  · {n}" for n in drafts.get("human_check", [])]
    lines.append("")
    name = variables.get("first_name")
    lines.append(f"Addressed as: {name}" if name else "Addressed as: (no first name found — opened on content)")
    lines.append(f"Grounded in: {variables.get('standout_post', {}).get('url')}")
    lines.append(f"Generated {dt.date.today().isoformat()} · engine draft, not sent")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--handles", nargs="+", help="hand-pick creators by Airtable Handle")
    mode.add_argument("--qualified", action="store_true",
                      help="THE AGENT TRIGGER: every human-qualified creator (Stage=Qualified) not "
                           "yet contacted. This is what a scheduler calls once the agent is active")
    mode.add_argument("--auto", action="store_true",
                      help="candidate-finder: every un-contacted creator above the percentile bar "
                           "(--top-pct) — use it to decide who to qualify, not to trigger outreach")
    ap.add_argument("--top-pct", type=float, default=50,
                    help="percentile bar for --auto: top N%% of the roster's live score "
                         "distribution. Default 50 — calibrated to where a known top partner "
                         "sits today; activation's job is to raise the roster so this same "
                         "percentile becomes a higher absolute bar")
    ap.add_argument("--min-score", type=int, default=None,
                    help="absolute score override; skips the percentile calculation")
    ap.add_argument("--stage", help="optionally narrow --auto to one funnel Stage, e.g. Qualified")
    ap.add_argument("--days", type=int, default=45, help="recency window for evidence")
    ap.add_argument("--posts-per-creator", type=int, default=6)
    ap.add_argument("--limit", type=int, default=10, help="cap creators per run (cost breaker)")
    ap.add_argument("--dry-run", action="store_true", help="scrape+draft, skip every write")
    args = ap.parse_args()

    print("=" * 72)
    print("  DRAFTS ONLY — NOTHING IS SENT. A human reviews, edits and sends from Airtable.")
    print("=" * 72)

    load_env()
    apify_token = os.environ["APIFY_API_TOKEN"]
    started = dt.datetime.now().isoformat(timespec="seconds")
    t0 = time.time()

    at = Airtable(os.environ["AIRTABLE_API_KEY"])
    rows, bar_note = select(at, args)
    print(f"\n[outreach] {len(rows)} creators matched")

    skipped: list[str] = []
    flags: dict[str, str] = {}
    for r in rows:
        note = known_partner_note(r.get("Handle") or "")
        if note:
            print(f"  ⚠ FLAG @{r.get('Handle')}: {note}")
            flags[r["Handle"]] = note
    rows = rows[:args.limit]
    print(f"[outreach] drafting for {len(rows)} (cap {args.limit})")
    if not rows:
        print("[outreach] nothing to do")
        return

    by_platform: dict[str, list[str]] = {}
    for r in rows:
        by_platform.setdefault(r.get("Platform") or "TikTok", []).append(r["Handle"])

    ev_all: dict[str, dict] = {}
    already_skipped: set[str] = set()
    for platform, handles in by_platform.items():
        print(f"[evidence] {platform}: {len(handles)} creators, last {args.days}d ...")
        try:
            ev_all |= evidence.gather(platform, handles, args.days, args.posts_per_creator, apify_token)
        except Exception as e:  # noqa: BLE001
            print(f"  ! {platform} evidence failed: {e}\n    → those creators are skipped, not drafted")
            for h in handles:
                skipped.append(f"@{h} ({platform} evidence failed)")
                already_skipped.add(h)

    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
    airtable_rows = []
    for r in rows:
        handle = r["Handle"]
        if handle in already_skipped:
            continue
        ev = ev_all.get(handle)
        if not ev or not ev["posts"]:
            print(f"  ⚠ SKIP @{handle}: no posts in the last {args.days}d — "
                  f"a stale personalisation is worse than none")
            skipped.append(f"@{handle} (no recent posts)")
            continue

        variables = extract_variables(r, ev, args.days)
        if not variables:
            continue
        drafts = draft_sequence(r, variables)
        if not drafts:
            continue

        body = format_for_airtable(drafts, variables)
        if handle in flags:
            body = f"⚠️ {flags[handle]}\n\n{body}"
        (RECEIPTS_DIR / f"{handle}.json").write_text(json.dumps({
            "handle": handle, "platform": r.get("Platform"), "generated": started,
            "window_days": args.days, "known_partner_flag": flags.get(handle),
            "evidence": ev, "variables": variables, "drafts": drafts,
        }, ensure_ascii=False, indent=1, default=str))

        airtable_rows.append({"Handle": handle, "Outreach Draft": body, "Outreach Status": "Draft"})
        mark = " ⚠ FLAGGED" if handle in flags else ""
        print(f"  ✓ @{handle:<26} {len(ev['posts'])} posts, {len(ev['comments'])} comments "
              f"→ 3 touches ({drafts.get('channel')}, register={variables.get('register')}){mark}")

    elapsed = time.time() - t0
    finished = dt.datetime.now().isoformat(timespec="seconds")

    if args.dry_run:
        print(f"\n[dry-run] {len(airtable_rows)} sequences drafted, no writes")
        if airtable_rows:
            print("\n" + "─" * 72)
            print(airtable_rows[0]["Outreach Draft"])
            print("─" * 72)
    else:
        n = at.upsert("Creators", airtable_rows, merge_on=["Handle"]) if airtable_rows else 0
        at.create("Runs", {
            "Run": f"outreach_drafts {started}", "Job": "outreach_drafts",
            "Started": started, "Finished": finished, "Status": "Success",
            "Items In": len(rows), "Items Out": n,
            "Notes": (f"{n} drafted, Status=Draft (not sent). selection: {bar_note}. "
                      f"flagged known partners: "
                      f"{'; '.join('@' + h for h in flags) or 'none'}. "
                      f"skipped: {'; '.join(skipped) or 'none'}"),
        })
        print(f"\n[outreach] {n} creators now Status=Draft in Airtable + Run row logged")
        print(f"[outreach] base: https://airtable.com/{at.base_id}")

    s, a = CLAUDE_STATS, APIFY_STATS
    per = len(airtable_rows) or 1
    print("\n=== SCALE RECEIPT ===")
    print(f"  creators drafted : {len(airtable_rows)}   skipped: {len(skipped)}")
    print(f"  Apify calls      : {a['calls']} across {len(by_platform)} platform(s), "
          f"{a['items']:,} items — batched, so this barely moves as creators grow")
    print(f"  Claude calls     : {s['calls']}  ({s['calls'] / per:.1f} per creator)")
    print(f"  tokens in/out    : {s['input_tokens']:,} / {s['output_tokens']:,}"
          f"   cached read: {s['cache_read_tokens']:,}")
    print(f"  elapsed          : {elapsed:.0f}s  ({elapsed / per:.0f}s per creator)")
    print(f"  → at 1,000 creators: still ~{a['calls']} Apify calls; Claude is the only per-creator "
          f"cost (2 calls) and halves again on the Batches API.")


if __name__ == "__main__":
    main()
