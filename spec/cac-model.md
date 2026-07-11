# Spec — The CAC Model

Where every number in a predicted CAC comes from, which of them are real, and what the figure may and
may not be used for.

**Standing rule this page exists to honour** (`CLAUDE.md`): *LLMs for judgment, deterministic code for
money. Never let a model allocate spend.*

**Status:** designed 2026-07-10 against calibration data. Awaiting Doug's sign-off. Not yet implemented —
[run_discovery.py](../scripts/run_discovery.py) still asks Claude for `predicted_cac_gbp`, which this page
deletes.

---

## 1. CAC is already defined in this repo

[activation.py:28](../content_brain/activation.py) computes realised CAC:

```python
"cac": round(spend / orders, 2) if orders else None
```

Spend, divided by attributed first orders. [budget.py](../content_brain/budget.py) ranks segments by it. The
wiki agrees: *"CAC = total program cost (commissions + platform/network fees + agency + tech + creative) ÷ net
new customers"* — [Affiliate Program Playbooks.md](../Fleek%20Wiki/research/Affiliate%20Program%20Playbooks.md),
citing Acceleration Partners.

**Predicted CAC is not a new quantity.** It is a forward estimate of that same number, before any spend exists.

## 2. The model

```
expected_views   = median(playCount) over posts ≥ 7 days old          [MEASURED]
audience_fit     = (pro% × 1.00 + hobbyist% × 0.70 + consumer% × 0.02) / 100
qualified_reach  = expected_views × audience_fit
first_orders     = qualified_reach × FUNNEL_RATE                      [ASSUMPTION]
AOV              = (pro% × £240 + hobbyist% × £65) / (pro% + hobbyist%)
cost             = flat_fee + seeded_stock + commission_rate × AOV × first_orders

CAC              = cost / first_orders
                 = (flat_fee + seeded_stock) / first_orders  +  commission_rate × AOV
```

### One unknown, not three

The obvious decomposition is `views → code use → signup → first order`, three rates. We know none of them, and
multiplying three invented numbers produces false precision without adding information. They are collapsed into
a single `FUNNEL_RATE`: **expected first orders per qualified view.** One honest unknown beats three fake ones.

## 3. Provenance of every constant

| Input | Value | Where it comes from | Class |
|---|---|---|---|
| `expected_views` | per creator | Apify `playCount`, posts ≥7d old | **Measured** |
| `engagement_rate` | per creator | (likes+comments+shares) ÷ views | **Measured** |
| `audience_mix` | per creator | Claude, from sampled comments, with quotes | **Inferred + confidence** |
| `commission_rate` | 10% | Whatnot creator affiliate ceiling (10%, 65-day validation). Whatnot FR/EU seller commission is 6.67%+VAT; Vestiaire 10–15%. | **Wiki-cited** |
| `AOV` pro | £240 | Bale lots €30–249; raw ballot 10–50kg at €3–8/kg | **Wiki-cited** *(single-sourced)* |
| `AOV` hobbyist | £65 | Friptabox €24.99/5kg; Fripedingue €6.05–7.74/kg | **Wiki-cited** *(single-sourced)* |
| LTV:CAC target | ≥ 3:1 | Acceleration Partners | **Wiki-cited** |
| `audience_fit` weights | 1.00 / 0.70 / 0.02 | mine | **Assumption** |
| `FUNNEL_RATE` | 0.0005 central | **nobody's** — Fleek owns this | **Assumption** |
| `flat_fee`, `seeded_stock` | £0 or £150 | scenario, not policy | **Scenario** |

`£240 / £65` are already hardcoded at [generate_roster.py:88](../scripts/generate_roster.py) as
`aov = 65 * (1 - pro_share) + 240 * pro_share`. They sit inside the wiki's cited range and nobody cited it.
This page is that citation.

**Two traps.**

*The €31.98 trap.* The wiki records `€31.98 average unit price` for TikTok Shop France. That is a **consumer
retail unit price**, not Fleek's B2B wholesale order value. Using it as AOV would be a sourced-looking number
applied to the wrong thing — more dangerous than an honest guess. Fleek's first order is a *bale*.

*The synthetic trap.* [generate_roster.py:84](../scripts/generate_roster.py) hardcodes `signups = clicks * 0.2`
plus per-format `ctr`/`cvr` constants, under `RNG = random.Random(42)`. `run_campaign.py report` prints
"CAC by segment" computed from that. **Reproducible is not accurate.** Any slide showing those numbers must say
*synthetic simulation, illustrating the mechanism* — or not show them.

## 4. What the model says about the calibration set

`FUNNEL_RATE` pessimistic 0.0002 · central 0.0005 · optimistic 0.0012 (a 6× spread).

### Scenario A — pure revenue share, `flat_fee = £0`

| creator | ground truth | qualified reach | AOV | pess | central | opt |
|---|---|---|---|---|---|---|
| `@giu.cst` | **wrong fit** | 3,338 | £65 | **£6.50** | **£6.50** | **£6.50** |
| `@juliettekitsch` | **wrong fit** | 461 | £65 | £6.50 | £6.50 | £6.50 |
| `@nathanviall3` | wiki ref | 41,182 | £112 | £11.20 | £11.20 | £11.20 |
| `@juliacrcl` | **Fleek partner** | 10,374 | £170 | £17.00 | £17.00 | £17.00 |
| `@behindthesale` | **Fleek partner** | 2,316 | £194 | £19.40 | £19.40 | £19.40 |

With no fixed fee, `CAC = commission_rate × AOV`. It is **independent of reach, of audience quality, and of
`FUNNEL_RATE` entirely.** It ranks the two worst creators best, and Fleek's two known-good partners worst,
because consumers have low AOV. Optimising on this number selects against everything Fleek wants.

### Scenario B — `flat_fee = £150`

| creator | ground truth | qualified reach | AOV | pess | central | opt |
|---|---|---|---|---|---|---|
| `@nathanviall3` | wiki ref | 41,182 | £112 | £29.40 | **£18.50** | £14.20 |
| `@juliacrcl` | **Fleek partner** | 10,374 | £170 | £89.30 | £45.90 | £29.00 |
| `@giu.cst` | **wrong fit** | 3,338 | £65 | £231.20 | £96.40 | £43.90 |
| `@behindthesale` | **Fleek partner** | 2,316 | £194 | £343.20 | **£148.90** | £73.40 |
| `@juliettekitsch` | wrong fit | 461 | £65 | £1,635 | £657.90 | £277.90 |

Ranking is **identical** under all three funnel rates, in both scenarios. So ignorance of `FUNNEL_RATE` does
not destroy the ordering — but note this was *checked*, not assumed. Algebraically the constant only cancels
cleanly when AOV is equal across creators; it isn't. Always run the sensitivity table.

And `@behindthesale` — Fleek's best partner, 70% pro audience — comes **fourth**, worse than a creator with a
0% pro audience. Because his median reach is 2,644 views. **CAC is reach-weighted, and the brief is explicit
that trust beats reach.**

## 5. Therefore: CAC does not select the shortlist

Both scenarios rank Fleek's real partners badly, for different reasons. That is not a bug in the arithmetic; it
is what CAC *is*. It measures efficiency of spend, not quality of audience.

Three consequences.

**Report a band, never a point.** `£` / `££` / `£££` alongside `expected_first_orders_per_post`. The Airtable
field is currently `currency, precision 2` — `£42.17` is false precision wearing a suit. Precision 0, plus a
band and a confidence.

**Rank on fit; read CAC as a constraint.** Selection uses the fit score in
[discovery-scoring.md](discovery-scoring.md). CAC then answers *"can we afford this one?"*, and the answer
depends on what the acquired customer is worth.

**There is a pro premium, and it is correct.** The brief: pro resellers are *"fewer in number, much higher
value"*, and *"many think Fleek is for beginners… changing that perception is one of our hardest problems."*
Reaching pros costs more per acquisition, because pro-audience creators have tight, small audiences —
`@behindthesale`, 35k followers, 2,644 median views, 70% pro. Paying a higher CAC for a pro is rational. The
test is not CAC, it is **LTV:CAC ≥ 3:1 with a segment-specific ceiling**:

```
ceiling_pro       = LTV_pro       / 3        # Fleek supplies LTV_pro
ceiling_hobbyist  = LTV_hobbyist  / 3
```

A single channel-wide CAC target would quietly defund the pro segment, which is the segment Fleek says it most
needs to win. `budget.py` already ranks segments by CAC and would do exactly that. Segment-specific ceilings
are the fix, and they are the reason to keep `audience_mix` on every creator record.

## 6. Division of labour

| Who | Emits |
|---|---|
| **Claude** | `audience_mix` percentages, `creator_type`, `sourcing_intent_comments`, verbatim evidence quotes, `confidence` |
| **Python** | every arithmetic step above, the band, the sensitivity table |

The model never emits a figure with a currency symbol. `predicted_cac_gbp` is removed from `SCORE_SCHEMA`.

## 7. The day-one ask

Three numbers are Fleek's, not ours. Naming them is a stronger answer than inventing precision:

1. **Referral funnel rates** — views → code use → signup → first order. Replaces `FUNNEL_RATE` and turns every
   band into a figure.
2. **First-order AOV, split pro vs hobbyist.** We are inferring it from French bale prices in the wiki.
3. **LTV by segment.** Without it there is no CAC ceiling, only a CAC ranking — and §5 shows the ranking alone
   points the wrong way.

Until then: bands, sensitivity, and the provenance table above.

## 8. Airtable changes this implies

| Field | Change |
|---|---|
| `Predicted CAC` | precision 2 → 0; populated by Python, never by the model |
| `CAC Band` | **new** — `£` / `££` / `£££` |
| `Expected Orders / Post` | **new** — the volume number CAC hides |
| `Audience Mix` | **new** — pro / hobbyist / consumer percentages |
| `Audience Evidence` | **new** — verbatim comment quotes, so a card can be audited |
| `Engagement Rate` | **new** — measured, feeds reach, *not* the fit score |
| `Median Views` | **new** — the real reach input; followers are not |
| `Audience` | currently holds `bio[:500]` — the creator's own bio. A bug on any reading. |
| primary key | `Handle` → `platform:handle` (see [discovery-scoring.md](discovery-scoring.md) §7.4) |

## 9. Sources

- [activation.py](../content_brain/activation.py), [budget.py](../content_brain/budget.py) — the realised definition
- `Fleek Wiki/research/Affiliate Program Playbooks.md` — CAC method, LTV:CAC ≥ 3:1
- `Fleek Wiki/research/Competitor Creator Programs.md` — Whatnot 10% affiliate ceiling, 65-day validation
- `Fleek Wiki/research/FR Bale Sourcing Playbook.md` — bale pricing (flagged single-sourced in the wiki)
- `Fleek Wiki/research/FR Resale Platform Landscape.md` — Vestiaire 10–15%
- `data/calibration/2026-07-10T10-24-45/` — the measured inputs
