# The presentation deck — UI spec

**Status:** agreed 2026-07-10 · **Lives at:** `deliverables/deck/`
**Answers:** `mission/task-brief.md` · **Sources its facts from:** `mission/`, `Fleek Wiki/`, `deliverables/evidence/`

The artefact Fleek actually sits through: ~20 minutes presented live, then ~40 minutes of questions. Sent 24
hours ahead as required, so it must also read unattended.

**References:** none supplied — direction proposed and agreed via the framing questions below.

**Mood/feel:** an engineer's terminal wearing Fleek's colours. Dark ground to present, monospace for anything
the machine said or did — timestamps, prompts, commands, log lines — and Montserrat for argument and
narration. Restraint is still the trick: no gradients, no glow, no ornament that isn't carrying information —
the one permitted flourish is Fleek's halftone-dot motif, on the title and hero only.

> **Aesthetic pivot, 2026-07-10 (Doug):** first draft shipped as pure engineer's-terminal; Doug reviewed it
> and called for Fleek's own branding, per joinfleek.com. Brand values were **measured off the live site**,
> not guessed: yellow `#F8C642` (their Sign Up button), solid black `#0E0E0E` buttons with white text and
> 4px radius, Montserrat 700 for emphasis, white / `#F2F4F7` ground, yellow halftone-dot pattern as the
> signature motif. The structure (receipts, pushback strips, terminal blocks) is unchanged — the palette and
> type are theirs. The risk named when "Fleek-native" was first offered — reading as a pitch deck rather than
> an engineering artefact — is mitigated by keeping the mono/receipt spine.

**Hero moment:** slide 11, `2026-07-09T22:17`. Doug stops nine hours of work and asks whether the model has
read the brief. It answers, in its own words, that it has not. Then the two claims it had built on inference,
and the one that would have sunk the interview. This slide gets real theatre: the prompt lands first, the
model's admission second, the consequences third. Every other slide is quieter than this one on purpose.

**Anti-examples:** generic AI-slop (gradient blobs, purple-to-blue, "neural network" stock art); consultancy
pitch deck (pyramids, six-bullet slides, jargon); startup fundraise deck (hockey sticks, TAM); a README
rendered as slides (undesigned, code-block soup, no spine).

**Constraints:**
- 16:9, presented live, driven with arrow keys.
- **Dark by default; a light theme that print and PDF export use automatically.** Doug selected both "dark,
  presented live" and "light theme"; resolved this way so the deck he presents and the PDF he sends 24 hours
  ahead are the same artefact, not two that can drift.
- Vanilla HTML/CSS/JS. No framework, no CDN, no build step. Opens from `file://`.
- Speaker notes hidden by default. **Print produces two different documents, and confusing them would send
  Fleek stage directions about themselves:**
  - `index.html` → the **reviewer copy** they receive 24 hours ahead. No notes.
  - `index.html?notes` (or press `s`, then `p`) → the **presenter copy**, for rehearsal.
- Not required to work on a phone.

## Content rules

- **14 core slides**, appendix behind them. Twenty minutes is ~90 seconds a slide; 25+ slides means rushing
  the best material. If it runs past ~18 minutes when read aloud, cut a slide. Do not talk faster.
- **The deck cites, it does not restate.** Every number traces to a file: the metric to `mission/mission.md`,
  hashtags to `Fleek Wiki/`, receipts to `deliverables/evidence/`. Nothing is typed twice.
- **Synthetic and real data are never blurred.** The 1,000-creator roster, 39.3% activation and £25.53 CAC
  come from `run_campaign.py generate-data` and must be labelled *simulated* wherever they appear. What is
  real: 49 scored FR creators and 588 posts ingested from Airtable, 12 creators discovered via Apify, and
  every hashtag validated against real post data. Presenting simulation as fact is the same failure mode as
  the "no structured creator program" claim, and it is the one thing that would actually lose the room.
- **The pushback strip** recurs on each section slide: Doug's verbatim quote, its timestamp, one line on what
  changed. Small, consistent, unmissable. It is the deck's argument, accumulating.

## Slides

| # | Slide | Cites |
|---|---|---|
| 1 | Title | — |
| 2 | The one number: **# and % of partners posting each month** | `mission/mission.md` |
| 3 | How I worked — the engine, and the receipts | `evidence/how-i-worked.md` |
| 4 | Phase 0 — the knowledge base, and the hashtags it validated | `Fleek Wiki/`, `evidence/phase-0-knowledge.md` |
| 5 | Part 1 — Discovery: market profile, both channels, real gates + run numbers | `spec/discovery-engine.md`, `evidence/discovery.md` |
| 6 | Part 1b — the **live dashboard** (169 real scored creators) + shared link | `fleek-affiliate-dashboard.vercel.app`, `spec/creator-dashboard.md` |
| 7 | Part 2 — Outreach: value palette, first-name, never-sends, Julia flag | `scripts/run_outreach.py`, `spec/decisions/2026-07-10-outreach-drafts.md` |
| 8 | Part 3 — the real funnel (162/7/0) + the manual qualify gate | `scripts/qualify.py`, `spec/discovery-engine.md` |
| 9 | Part 4 — Activation: the brief generator | `content_brain/brief_generator.py` |
| 10 | Part 5 — CAC is a constraint not the selector; percentile bar | `spec/cac-model.md`, `spec/discovery-scoring.md` |
| 11 | **Hero — the moment I overruled the machine** | `evidence/hero-overruled.md` |
| 12 | The engine on autopilot — the scale answer | `spec/autonomy-layer.md` |
| 13 | Live demo — `run_campaign.py brief CRE-0042` | the terminal |
| 14 | Close — if I had six months | — |

## Build notes

- Tokens in `deliverables/deck/tokens.css`: colour, spacing scale, type scale, motion. No hardcoded hex or px
  in `deck.css`.
- Keyboard: `←`/`→` navigate, `s` toggles speaker notes, `t` toggles theme, `p` opens print view,
  `1`–`9`/`0` jump to a slide.
- Slide state in the URL hash, so a link can point at slide 11.
- **Type scales with the stage, not the viewport.** `font-size: 1.3cqw` sits on `.slide`, never on `.stage` —
  an element is never its own container-query container, so putting it on `.stage` silently resolves against
  the viewport and blows the layout apart on a short, wide screen (i.e. an unfamiliar projector).
  `1.3cqw` is tuned against the densest slide, `phase-0`; everything else is `em`-relative.
- Verified 2026-07-10: 14 slides, no overflow, nothing under the chrome, at 1280×800 and 2000×600.
  PDF export gives 14 pages, light theme forced, reviewer copy free of notes.
