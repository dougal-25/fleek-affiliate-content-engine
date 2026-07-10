# Spec — Log

Dated record of design intent changing. Newest first. Decisions with reasoning get their own page in
`spec/decisions/`; this is the running thread.

---

## 2026-07-10 — The deck now wears Fleek's own branding

Doug reviewed the first draft ("good first draft") and called the aesthetic: follow joinfleek.com. Brand
values **measured off the live site with Playwright**, not guessed — yellow `#F8C642` (their Sign Up button),
button black `#0E0E0E`, surface grey `#F2F4F7`, Montserrat 700, 4px radii, halftone-dot motif. Details in
[`deck.md`](deck.md).

Because every colour lived in `tokens.css`, the rebrand was a token swap plus four accent edits — the
no-hardcoded-hex rule paying for itself. Montserrat is self-hosted (35KB variable woff2, OFL) so the deck
still opens from `file://` with no CDN. Yellow is graphics-only where contrast demands (text uses a dark-gold
derivative on light ground). The dot motif is title + hero only.

**Bug found by rendering the PDF, again:** in print, `.slide` was `position: static`, so the dot
pseudo-elements re-anchored to `.stage` — whose print height is the full 14-slide stack — and `height: 45%`
became a six-page dot band that blanked page 1 and tripled the file size. Fixed with `position: relative`;
the reviewer PDF re-verified page by page.

Content untouched — Doug is still building out sections; slide 6's Airtable link and the ~18-min timing cut
remain open.

---

## 2026-07-10 — The proof of how it was built is now part of the deliverable

The brief tests AI-nativeness and asks for *"the actual prompts including the failures."* The engine existed;
the evidence did not — `deliverables/evidence/` was named in the approach doc and empty. Three things landed,
in this order, because the order matters. Full reasoning:
[`decisions/2026-07-10-evidence-and-deck.md`](decisions/2026-07-10-evidence-and-deck.md).

**Preserve.** Nine sessions, 13.7 MB, 59 real prompts, in one place, outside git, and 30 days from automatic
deletion. Archived outside the working tree at `~/claude-transcript-archive/`; `cleanupPeriodDays: 365`.
Deliberately *not* `_evidence_raw/` in the repo behind a `.gitignore` line — this repo is public, and an ignore
rule prevents an accident, not a mistake.

**Secure.** `gitleaks` wired as pre-commit, pre-push and CI *before* the extractor was written. Both hooks
proved to block by planting a token. The archive audited: **zero real secrets** — every hit was a command
reading `.env`, never a value.

**Extract.** `scripts/extract_receipts.py` renders 17 curated exchanges verbatim from the raw transcripts,
redacting on the way out. Deterministic, so the pages regenerate rather than drift.

**Then the deck.** Vanilla HTML, 14 slides, dark to present and light to send —
[`deck.md`](deck.md). This **reverses the Canva decision** of 2026-07-09, per Doug the same day. The reversal
is logged on the original record, not backdated.

**Two bugs found by driving the deck rather than reading it:** `1.3cqw` sat on its own container-query
container and silently resolved against the viewport (26px type in a 1067px stage on a short, wide projector);
and the speaker notes were printing into the PDF that goes to Fleek — page 11 was instructing *them* to pause
for two seconds before speaking.

**And a stale claim, still live.** `Fleek Wiki/index.md`'s first pillar bullet still asserted *"no structured
creator program yet"* while the retraction sat fifty lines below in a `[!CAUTION]` block. Fixed.
**A correction that lives only in the footnotes is not a correction.**

---

## 2026-07-10 — The mission is real; two load-bearing claims were wrong

Doug supplied the JD and the case-study brief. Both are now captured verbatim in `mission/`, and
`mission/mission.md` is rewritten against them — the *awaiting sign-off* banner is gone.

Reading the sources against the repo surfaced two claims that had been built on inference:

1. **"Fleek has no structured creator program — greenfield, not a fix-up."** False. The JD describes a 1,000+
   creator roster built over two years, recruitment largely automated, running on an internal Content Brain.
   The wiki had inferred "no programme" from Fleek's *public surface* — the `RFD-` referral codes visible on
   joinfleek.com and TikTok. The programme exists; it isn't public. Corrected on
   `Fleek Wiki/research/Fleek Company Profile.md`, and the strategic thesis on `Fleek Wiki/index.md` revised
   and flagged for Doug's sign-off. **Method lesson recorded on the page:** absence of public evidence was
   treated as evidence of absence.

2. **"Anchor on activation; recruitment is a supporting motion."** Written into `deliverables/strategy.md`
   before the brief existed. The brief asks for both — Part 1 (discovery) is explicitly *"the core
   AI-nativeness test"*, and Part 5 splits budget across recruitment and re-activation. Corrected in place.

**What the sources add that the repo didn't have:** ~20,000 total addressable resellers (bounds every scale
claim); three named real top-performing partners (`@behindthesale`, `@theliveneedham`, `@juliacrcl`) that
should calibrate the scoring model instead of guessed archetypes; the exact attribution mechanic; and Fleek's
self-declared hardest problem — *pro resellers think Fleek is for beginners.* Nothing in the vault addresses
that yet, and it is the most interesting thing in the brief.

**Open:** the revised strategic thesis needs Doug's call before it drives the deck.

## 2026-07-09 — Repo restructured around mission / wiki / spec / code

**Why:** the repo had grown by accretion. Things got built, then a home was found for them. Three concrete
failures: the JD and task brief — the two documents this project is judged against — existed nowhere as
files, only as paraphrase inside two strategy docs. A half-finished vault rename had left git reporting 24
phantom deletions and the research agent pointing at a directory that no longer existed. And `docs/` was
sorting four different genres of document under one numbered sequence.

**What changed:**

- **`mission/` created.** `job-description.md` and `task-brief.md` land as placeholders awaiting the verbatim
  text. `mission.md` states what we build and how we're judged — stamped *awaiting sign-off* until the two
  sources are captured, because right now it's an inference drawn from `deliverables/strategy.md`.
- **The vault is one vault.** `FLEEK BRAIN/` → `Fleek Wiki/`, preserving git history (renames, not
  delete+add). An empty nested Obsidian vault created the night before — which is what breaks the parent's
  graph view — was retired to `_attic/`. `FLEEK BRAIN Index.md`/`Log.md` → `index.md`/`log.md`, and all 21
  notes' wikilinks repointed.
- **Naming settled.** Fleek uses *the Brain* for the whole affiliate content engine, so this repo *is* the
  Brain and no subfolder claims the word. The research vault is *the wiki*. Documented in `CLAUDE.md`.
  The `brain_refresh` job is now `wiki_refresh`.
- **`docs/` dissolved by genre.** Architecture, playbook and autonomy design → `spec/`. Strategy and the
  case-study approach → `deliverables/`. The two "what changed since draft 1" tables → `spec/decisions/`,
  where a decision record belongs.
- **The research agent is invocable.** `agents/brain_research_agent.md` → `.claude/agents/wiki-researcher.md`
  with frontmatter. It had been pointing at `FLEEK BRAIN/` and at `scripts/run_brain_research.py`, a script
  that does not exist — that claim is gone; the agent runs as a subagent.
- **`CLAUDE.md` and `spec/overview.md` written.** Neither existed.

**What deliberately did not change:** `content_brain/`, `scripts/` and `run_campaign.py` stay exactly where
they are. Wrapping working code in an `engine/` folder would look tidier and cost a round of Python import
breakage for zero functional gain. The code was never the mess.

**Open:** `mission/job-description.md` and `mission/task-brief.md` are empty. Until Doug pastes the verbatim
text, everything citing the mission is citing an inference.
