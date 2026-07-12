# The Autonomy Layer — hosting, triggers, recovery, breakers, observability

**Status:** designed, not yet built (deliberately). The framework rule: the engine's jobs run manually first (Claude Code, this week's case study); the autonomy layer is added per job once the manual version has proven itself. This doc is the design — and the deck slide that backs "the engine on autopilot".

## The five jobs the engine runs

| Job | What it does | Trigger | Writes to |
|---|---|---|---|
| `wiki_refresh` | Perplexity research pass on the wiki's trend questions → dated trends note appended to the wiki | Cron: Mon 06:00 | Repo (markdown, git commit) |
| `discovery` | Apify run seeded with wiki keywords → Claude enrichment → scoring → upsert Prospects | Cron: Mon 07:00 (after wiki_refresh) | Airtable |
| `outreach_drafts` | FR drafts for newly Qualified creators → Status = Draft | Cron: daily | Airtable |
| `brief_generator` | Personalised brief for creators whose Stage = Onboarded and Brief = empty → brief + Notion share page | Poll: hourly Airtable query | Airtable + Notion |
| ↳ **built** `scripts/run_brief_job.py` | Idempotent (only empty-`Brief` records), capped at 25 Claude calls/run, degrades to Airtable-only if Notion fails. `--dry-run`, `--handle`, `--no-notion`. Airtable path verified live; Claude + Notion not yet fired — see `spec/log.md` 2026-07-10. | | |
| `weekly_report` | Funnel counts, CAC by segment, run health → summary page | Cron: Fri 16:00 | Notion |

All five are the SAME Python scripts run manually today — the layer changes *who presses enter*, not the code.

## 1. Hosting — GitHub Actions (decided)

Scheduled workflows in the repo that already holds the code.

**Why GitHub Actions over Railway/VPS:** zero new infrastructure (code is already on GitHub); cron built in; secrets manager built in; every run keeps its logs (observability for free); manual "Run workflow" button doubles as the human trigger; free-tier minutes are far beyond what weekly jobs need. Railway cron is the fallback if a job ever needs to run long or always-on — same scripts, different scheduler, nothing rewritten.

**Access:** repo is private; Doug's GitHub account is the only operator. Anyone Fleek-side would be added as a repo collaborator — access to the engine IS repo access. No separate admin panel to secure.

## 2. Secrets & access

- Local dev: workspace `.env` (as now). Never committed (`.gitignore` already covers it).
- Autonomous: keys move into **GitHub Actions Secrets** — `ANTHROPIC_API_KEY`, `PERPLEXITY_API_KEY`, `APIFY_TOKEN`, `AIRTABLE_API_KEY`, `NOTION_API_KEY`. Encrypted, masked in logs, never in code.
- Blast-radius rule: each key is the least-privileged token available (e.g. Airtable personal access token scoped to the one base).

## 3. Triggers

- **Time-based** (brain, discovery, drafts, report): plain cron in the workflow file.
- **State-based** (briefs): hourly **poll** of Airtable — "Stage = Onboarded AND Brief is empty". A poll beats a webhook here: no endpoint to host, no missed-webhook failure mode, and an hourly SLA is more than fine for onboarding. (Webhooks are the upgrade if briefs ever need to be instant.)
- **Human**: every workflow also has a manual Run button in the GitHub UI.

## 4. Self-recovery

The strategy is **idempotency, then retry** — not cleverness:

- Every job is safe to re-run: discovery *upserts* by creator handle (no duplicates); briefs only generate where Brief is empty; brain notes are dated files; reports overwrite the week's page.
- API calls get simple retry-with-backoff in code (Apify/Claude/Airtable hiccups).
- If a run still fails, GitHub emails the failure and the next scheduled run picks up where things left off — because re-running is always safe, recovery = re-run.

## 5. Circuit-breakers

- **Kill switch:** an `ENGINE_ENABLED` flag (GitHub Actions variable) checked at the top of every job. One click stops the whole engine.
- **Spend caps:** hard-coded per-run ceilings — max Apify results per run, max Claude calls per run, monthly budget check before any run starts.
- **Flood cap:** max new Prospects per discovery run (start: 50) so one bad keyword can't flood the funnel.
- **Quality breaker:** if enrichment classifies under ~30% of a scrape as actual resellers, abort and flag — that's a bad-input signal, not a bigger-scrape signal.
- **Human gates (unchanged, permanent):** nothing sends outreach, signs, or spends money autonomously. The engine proposes; humans approve.

## 6. Observability

- **Runs table in Airtable:** every job writes one row — job name, start/finish, items in/out, errors. The ecosystem dashboard doubles as the ops dashboard; a stale Runs table is itself the alarm.
- **GitHub Actions history:** full logs per run, green/red per job, email on failure.
- **Weekly report job** is the human-readable rollup: funnel movement, CAC by segment, run health.

## 7. Rollout — SPRINT MODE (decided 2026-07-09: live by 13:00 on 2026-07-10)

This is a case-study demo, not a production migration — the staged-rollout caution is scratched. Target state by 13:00 tomorrow:

1. **LIVE on GitHub Actions cron, with real run logs:** `wiki_refresh` + `discovery`. The runs fire tonight so the logs exist before the interview — the autonomy slide shows evidence, not intention.
2. **Built as workflows, fired on demand:** `outreach_drafts` + `brief_generator` — run live in the room via the manual dispatch button (stronger theatre than a cron log anyway).
3. **Stretch:** `weekly_report`.
4. **The one permanent gate:** outreach auto-DRAFTS at full speed but never auto-SENDS to real creators — a case-study bot spamming Fleek's actual market is the one way this backfires in the room. "The engine proposes, humans approve" is the answer they want to hear.

For the deck's 30/60/90 slide: the per-job staged rollout story still applies to *their* production infra — present tonight's sprint as proof the layer works, and the staged sequence as how it lands safely inside Fleek.

## 8. Scale answers (for the inevitable questions)

- **More geos:** same jobs, `geo` parameter — UK + FR is a config change, not a build.
- **10× creators:** Airtable is the v1 data layer; at tens of thousands of rows it's swapped for Postgres (Supabase) behind the same scripts. Views/dashboard rebuild is the only real cost.
- **Fleek's own infra:** the whole layer is "Python + cron + a database" — it drops onto whatever they run internally. Nothing here is bespoke to Doug's laptop; that's the point of the design.
