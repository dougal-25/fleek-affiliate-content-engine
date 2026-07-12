"""Turn raw Claude Code transcripts into the evidence pages the brief asks for.

Fleek's task brief: *"Show the tools, the actual prompts including the failures."*
This script is how we do that without paraphrasing ourselves into a flattering story.

    raw transcripts (outside the repo)  ->  manifest.json (hand-curated)  ->  evidence/*.md

Three properties, in priority order:

1. **Verbatim.** Prompts are quoted exactly as typed, with their real timestamps. The
   curation lives entirely in `manifest.json` — which exchanges to show, and what each
   one changed. The words themselves are never rewritten.
2. **Redacted at the source.** Every string leaving this script passes `redact()`. A
   human skim-reading 13 MB of transcript for API keys is not a security control.
3. **Deterministic.** Same inputs, byte-identical output. The evidence pages are
   regenerated, never hand-edited, so they cannot drift from what actually happened.

The raw transcripts deliberately live outside the working tree (see .gitignore). This
repo is public; the transcripts are not scrubbed. Only this script's output is.

    python scripts/extract_receipts.py            # regenerate deliverables/evidence/
    python scripts/extract_receipts.py --verify   # fail loudly if any secret survived
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = Path.home() / "claude-transcript-archive" / "fleek-2026-07-10"
EVIDENCE = REPO / "deliverables" / "evidence"
MANIFEST = EVIDENCE / "manifest.json"

# --------------------------------------------------------------------------------------
# Redaction. Applied to every string on its way out — prompts, responses, commands alike.
# --------------------------------------------------------------------------------------

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("anthropic-key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("openai-key", re.compile(r"sk-(?:proj-|live-)?[A-Za-z0-9]{32,}")),
    ("perplexity-key", re.compile(r"pplx-[A-Za-z0-9]{20,}")),
    ("apify-token", re.compile(r"apify_api_[A-Za-z0-9]{20,}")),
    ("airtable-pat", re.compile(r"\bpat[A-Za-z0-9]{14}\.[a-f0-9]{40,}")),
    ("airtable-key", re.compile(r"\bkey[A-Za-z0-9]{14}\b")),
    ("firecrawl-key", re.compile(r"\bfc-[a-f0-9]{30,}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}")),
    ("aws-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("bearer", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{30,}")),
    # Any VAR=value where VAR smells like a credential — catches shapes we haven't met.
    ("env-assignment", re.compile(r"(?m)\b([A-Z_]{4,}_(?:KEY|TOKEN|SECRET|PASSWORD))=(\S{8,})")),
]

HOME = re.compile(re.escape(str(Path.home())))


def redact(text: str) -> str:
    """Strip credentials and machine-specific paths. Never bypassed."""
    for name, pattern in SECRET_PATTERNS:
        if name == "env-assignment":
            text = pattern.sub(rf"\1=[REDACTED:{name}]", text)
        else:
            text = pattern.sub(f"[REDACTED:{name}]", text)
    return HOME.sub("~", text)


# --------------------------------------------------------------------------------------
# Reading the transcripts.
# --------------------------------------------------------------------------------------

HARNESS_PREFIXES = ("<", "Base directory for this skill", "Caveat:")
HARNESS_MARKERS = ("<system-reminder>", "local-command-caveat")


def _text_of(content: object) -> str | None:
    """Return the text of a genuine user prompt, or None if this record isn't one.

    Most `type:"user"` records are tool results or harness injections, not the human
    typing. Getting this filter right is the whole job — validated against all ten
    transcripts (59 real prompts out of 385 user records).
    """
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
            return None
        text = " ".join(
            b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
        )
    else:
        return None

    text = text.strip()
    if not text or text.startswith(HARNESS_PREFIXES):
        return None
    if any(marker in text[:120] for marker in HARNESS_MARKERS):
        return None
    return text


def load_sessions(archive: Path) -> dict[str, list[dict]]:
    """Map short session id (first 8 chars) -> its records, in order."""
    if not archive.is_dir():
        sys.exit(
            f"error: transcript archive not found at {archive}\n"
            "       The raw transcripts live outside this repo on purpose. See the module\n"
            "       docstring, or pass --archive."
        )
    sessions: dict[str, list[dict]] = {}
    for path in sorted(archive.glob("*.jsonl")):
        short = path.stem.split("__")[-1]
        records = []
        for line in path.open(errors="replace"):
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        sessions[short] = records
    if not sessions:
        sys.exit(f"error: no .jsonl transcripts in {archive}")
    return sessions


def find_prompt(records: list[dict], ts_prefix: str) -> tuple[str, str, str]:
    """Find the genuine user prompt whose timestamp starts with ts_prefix.

    Returns (timestamp, branch, verbatim_text).
    """
    for i, rec in enumerate(records):
        if rec.get("type") != "user" or not rec.get("timestamp", "").startswith(ts_prefix):
            continue
        text = _text_of(rec.get("message", {}).get("content"))
        if text is None:
            continue
        branch = rec.get("gitBranch") or _first_branch(records)
        return rec["timestamp"], branch, text
    raise LookupError(f"no genuine user prompt at timestamp {ts_prefix!r}")


def find_decision(records: list[dict], ts_prefix: str) -> tuple[str, list[str], str]:
    """Find an AskUserQuestion at ts_prefix. Returns (timestamp, questions, answer)."""
    pending: dict[str, tuple[str, list[str]]] = {}
    for rec in records:
        if rec.get("type") == "assistant":
            for block in rec.get("message", {}).get("content", []) or []:
                if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "AskUserQuestion":
                    questions = [q.get("question", "") for q in block["input"].get("questions", [])]
                    pending[block["id"]] = (rec.get("timestamp", ""), questions)
        elif rec.get("type") == "user":
            for block in rec.get("message", {}).get("content", []) or []:
                if isinstance(block, dict) and block.get("type") == "tool_result" and block.get("tool_use_id") in pending:
                    ts, questions = pending[block["tool_use_id"]]
                    if ts.startswith(ts_prefix):
                        return ts, questions, _stringify(block.get("content"))
    raise LookupError(f"no AskUserQuestion at timestamp {ts_prefix!r}")


def _stringify(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(b.get("text", "") for b in content if isinstance(b, dict))
    return str(content)


DISMISSED = "[User dismissed — do not proceed, wait for next instruction]"


def parse_answers(raw: str, questions: list[str]) -> list[str]:
    """Pull the chosen answers out of the harness's echo-back string.

    The harness returns: `Your questions have been answered: "<q1>"="<a1>", "<q2>"="<a2>".`
    Answers may themselves contain quotes, so we can't split naively — instead we anchor
    on the question text, which we already have from the tool_use record.
    """
    if DISMISSED in raw:
        return [DISMISSED] * len(questions)

    marks = []
    for q in questions:
        needle = f'"{q}"="'
        i = raw.find(needle)
        marks.append((i + len(needle), i) if i != -1 else (None, None))

    answers = []
    starts = sorted(m[1] for m in marks if m[1] is not None)
    for start, q_at in marks:
        if start is None:
            answers.append("(unrecorded)")
            continue
        later = [s for s in starts if s > q_at]
        end = later[0] if later else len(raw)
        chunk = raw[start:end]
        # trim the separator that precedes the next question, or the trailing sentence
        chunk = re.sub(r'"\s*,?\s*$', "", chunk.strip())
        chunk = chunk.split(". You can now continue")[0]
        answers.append(re.sub(r'"$', "", chunk.strip()).strip())
    return answers


def _first_branch(records: list[dict]) -> str:
    for rec in records:
        if rec.get("gitBranch"):
            return rec["gitBranch"]
    return "unknown"


def next_assistant_text(records: list[dict], after_ts: str, limit: int) -> str:
    """The first assistant prose following a prompt — what the model said back."""
    seen = False
    for rec in records:
        if not seen:
            seen = rec.get("timestamp", "") == after_ts
            continue
        if rec.get("type") != "assistant":
            continue
        for block in rec.get("message", {}).get("content", []) or []:
            if isinstance(block, dict) and block.get("type") == "text" and block.get("text", "").strip():
                text = " ".join(block["text"].split())
                return text[:limit] + ("…" if len(text) > limit else "")
    return ""


# --------------------------------------------------------------------------------------
# Rendering.
# --------------------------------------------------------------------------------------

BANNER = (
    "<!-- GENERATED by scripts/extract_receipts.py from the raw Claude Code transcripts.\n"
    "     Do not edit by hand — your changes will be overwritten. To change what appears\n"
    "     here, edit deliverables/evidence/manifest.json and re-run the script. -->\n"
)


def quote(text: str) -> str:
    return "\n".join("> " + line if line else ">" for line in text.strip().splitlines())


def render_section(section: dict, receipts: list[dict]) -> str:
    out = [BANNER, f"# {section['title']}", ""]
    out += [section["intro"], "", "---", ""]
    for r in receipts:
        out.append(f"## {r['label']}")
        out.append("")
        out.append(f"`{r['timestamp']}` · session `{r['session']}` · branch `{r['branch']}`")
        out.append("")
        if r["kind"] == "prompt":
            out.append("**What Doug typed, verbatim:**")
            out.append("")
            out.append(quote(r["prompt"]))
            out.append("")
            if r.get("response"):
                out.append("**What came back:**")
                out.append("")
                out.append(quote(r["response"]))
                out.append("")
        else:
            out.append("**The engine put a decision to Doug, and he answered:**")
            out.append("")
            for question, answer in zip(r["questions"], r["answers"]):
                out.append(f"> **Q.** {question}")
                out.append(">")
                out.append(f"> **A.** {answer}")
                out.append(">")
            out.append("")
        out.append(f"**What changed because of it:** {r['so_what']}")
        out.append("")
        out.append("---")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def render_index(sections: list[dict], counts: dict[str, int], archive: Path) -> str:
    total = sum(counts.values())
    out = [
        BANNER,
        "# Evidence — the receipts",
        "",
        "Fleek's brief: *\"Show the tools, the actual prompts **including the failures**.\"*",
        "",
        f"These pages hold {total} curated exchanges, quoted verbatim from the "
        f"{len(list(archive.glob('*.jsonl')))} real Claude Code sessions run between "
        "2026-07-09 and 2026-07-10 while this engine was built. Nothing is reconstructed "
        "after the fact; every quote carries the timestamp it was typed at.",
        "",
        "They are generated, not written. `scripts/extract_receipts.py` reads the raw "
        "transcripts against `manifest.json` and redacts every credential on the way out. "
        "The raw transcripts stay outside this repo — it is public, and they are not scrubbed.",
        "",
        "## Pages",
        "",
        "| Section | Receipts | What it shows |",
        "|---|---|---|",
    ]
    for s in sections:
        out.append(f"| [{s['title']}]({s['slug']}.md) | {counts[s['slug']]} | {s['shows']} |")
    out += [
        "",
        "## Regenerating",
        "",
        "```bash",
        "python scripts/extract_receipts.py            # rebuild these pages",
        "python scripts/extract_receipts.py --verify   # assert no secret survived",
        "```",
        "",
        f"Source archive: `{str(archive).replace(str(Path.home()), '~')}` (10 transcripts, 13.7 MB).",
        "",
    ]
    return "\n".join(out)


# --------------------------------------------------------------------------------------

def build(archive: Path) -> list[Path]:
    manifest = json.loads(MANIFEST.read_text())
    sessions = load_sessions(archive)
    by_slug: dict[str, list[dict]] = {s["slug"]: [] for s in manifest["sections"]}

    for entry in manifest["receipts"]:
        records = sessions.get(entry["session"])
        if records is None:
            sys.exit(f"error: manifest references unknown session {entry['session']!r}")
        try:
            if entry["kind"] == "prompt":
                ts, branch, text = find_prompt(records, entry["at"])
                receipt = {
                    "kind": "prompt",
                    "prompt": redact(text),
                    "response": redact(next_assistant_text(records, ts, entry.get("response_chars", 0)))
                    if entry.get("response_chars")
                    else "",
                }
            else:
                ts, questions, answer = find_decision(records, entry["at"])
                branch = _first_branch(records)
                limit = entry.get("answer_chars", 400)
                receipt = {
                    "kind": "decision",
                    "questions": [redact(q) for q in questions],
                    "answers": [
                        redact(a[:limit] + ("…" if len(a) > limit else ""))
                        for a in parse_answers(answer, questions)
                    ],
                }
        except LookupError as exc:
            sys.exit(f"error: {entry['id']}: {exc}")

        receipt.update(
            label=entry["label"],
            timestamp=ts,
            session=entry["session"],
            branch=(branch or "unknown").replace("claude/", ""),
            so_what=entry["so_what"],
        )
        by_slug[entry["section"]].append(receipt)

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    written = []
    for section in manifest["sections"]:
        path = EVIDENCE / f"{section['slug']}.md"
        path.write_text(render_section(section, by_slug[section["slug"]]))
        written.append(path)
    counts = {s["slug"]: len(by_slug[s["slug"]]) for s in manifest["sections"]}
    index = EVIDENCE / "index.md"
    index.write_text(render_index(manifest["sections"], counts, archive))
    written.append(index)
    return written


def verify() -> int:
    """Assert no credential survived into the generated pages. Exit 1 if one did."""
    bad = 0
    for path in sorted(EVIDENCE.glob("*.md")):
        text = path.read_text()
        for name, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                if "[REDACTED:" in match.group(0):
                    continue
                print(f"LEAK {path.name}:{text[:match.start()].count(chr(10)) + 1} rule={name}")
                bad += 1
    print(f"verify: {'FAIL' if bad else 'clean'} — {bad} unredacted match(es) across {len(list(EVIDENCE.glob('*.md')))} pages")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE, help="raw transcript directory")
    ap.add_argument("--verify", action="store_true", help="check generated pages for leaked secrets")
    args = ap.parse_args()

    if args.verify:
        return verify()

    written = build(args.archive)
    for path in written:
        print(f"wrote {path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
