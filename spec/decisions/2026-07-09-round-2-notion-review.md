# 2026-07-09 — Round 2: Doug's Notion review comments, applied

> [!IMPORTANT] **One row of this table was reversed the same day.** The *"Deck medium: Canva"* decision below
> was overturned at 16:32 on 2026-07-09 — *"lets ditch canva and or gamma for now — we can leverage claude"* —
> after Doug looked at competing Canva and Gamma drafts. The deck is vanilla HTML in the repo; see
> [2026-07-10-evidence-and-deck.md](2026-07-10-evidence-and-deck.md) and [../deck.md](../deck.md).
>
> The row is left standing rather than edited. A decision record that quietly agrees with the present is
> worth nothing — and this particular reversal is itself a receipt in the deck.

Second pass over the case-study approach, folding in comments left on the Notion mirror. Lifted out of
`deliverables/case-study-approach.md` §0.

| Comment | Change applied |
|---|---|
| Loom backup unnecessary — presenting live | Standalone Loom dropped. Short video demos embedded in the deck where live isn't practical (Kalodata walkthrough, agent build, terminal run). |
| AI conversations must be shown throughout, not just in an appendix | Receipts live **in** the slides. The appendix is demoted to an archive (full transcripts, failed prompts, rubric). Every section opens with a stack strip + receipts. |
| Is Apollo needed? Not all creators have bio emails | Honest reframe: Apollo is a B2B fallback for business-entity creators only. It does not scrape TikTok handles. Primary route = DMs + bio emails + link-in-bio via Firecrawl. |
| Apify vs Perplexity — why both? | **Perplexity teaches the engine; Apify feeds it.** Perplexity synthesises the web into the wiki. It cannot return 200 French TikTok profiles with follower counts and captions as JSON. Apify can, through an API, which is also what makes it schedulable. |
| Deck medium: HTML vs Canva vs Gamma | **Canva.** Edit flexibility, screenshots and links, embedded clips, already in the stack and MCP-connected. |
| Where is everything hosted? | One GitHub repo. Local via Claude Code today; GitHub Actions / Railway cron when autonomous. Per-section stack strips added to the deck. |
| (Voice note) Engine essence, scalable and automatable throughout | Fleek's own vocabulary adopted. A scale answer is pre-baked into every section. New "engine on autopilot" section covering the Monday-morning autonomy loop. |

**Naming note (added 2026-07-09, restructure):** Fleek uses *the Brain* for the whole affiliate content
engine. This repo therefore *is* the Brain — no subfolder claims the word. The research vault is
`Fleek Wiki/`. See `CLAUDE.md`.
