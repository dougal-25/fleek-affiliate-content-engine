# Spec — Discovery & Scoring

How the engine decides which creators reach the shortlist, what each signal is worth, and which
signals were tested and discarded.

**Judged against:** `mission/mission.md`. The brief calls Part 1 *"the core AI-nativeness test"* and asks
for *"a deliberate mix across pro reseller audiences and hobbyist reseller audiences."*

**Status:** rubric calibrated 2026-07-10 against Fleek's three named partners and a French reference set.
Raw evidence in `data/calibration/2026-07-10T10-24-45/`. Awaiting Doug's sign-off before it drives Airtable.

---

## 1. Two scores, not one

The current scorer in [run_discovery.py](../scripts/run_discovery.py) emits a single 0–100 number that
welds together two unrelated questions. The calibration data forces them apart.

| Score | Question | Used for |
|---|---|---|
| **Fit** | Will this creator's audience become Fleek customers? | Shortlist selection |
| **Activation risk** | Will this creator actually post once signed? | Outreach priority, post-signature management |

`@juliacrcl` posts **0.2 times a week** — once every five weeks — and is one of Fleek's top-performing
partners. The current scorer awards *"posting consistency: 15 points"*, which would penalise a known-good
partner. Cadence predicts activation, not conversion. The brief already treats these separately:
*"a signed partner who never posts is worth nothing"* is a health metric about people you have already
signed, not a predictor of whether their audience converts.

## 2. Two fields, not one

Pro / hobbyist / general-consumer is **Fleek's customer taxonomy** (task brief, *Context: how Fleek works*).
It describes the people watching, not the person posting. Both matter, and they differ:

- **`creator_type`** — is this person genuinely a reseller? The *trust* gate. The brief: *"Creators who
  genuinely resell and show their real sourcing, process and tips convert far better."*
- **`audience_mix`** — who watches? The *addressable market*. This is what Fleek actually buys.

The gap between them is where the value is. `@nathanviall3` is unambiguously a pro creator — bulk-buys on
Vinted, live-sells on Whatnot. His audience measured **20% pro / 55% hobbyist**. He is a *hobbyist-acquisition*
partner. One field cannot say this, and Fleek's hardest problem — *"pro resellers think Fleek is for
beginners"* — is an **audience** problem. It is solved by creators whose *viewers* are pros. Those are rare
and expensive, and they are invisible to a single-field model.

## 3. The signal ladder

Cheap signals wide at the top of the funnel; expensive signals narrow at the bottom. Nothing paid runs on a
candidate that a free filter can reject.

| Stage | Source | Cost | Role |
|---|---|---|---|
| 1. Text signals | bio, captions, hashtags, `externalUrl` | free | Wide prefilter, **generous recall**. Never a judge. |
| 2. Reach & engagement | `playCount`, likes, comments | included in scrape | Feeds the CAC model, **not** the fit score |
| 3. Comments | `clockworks/tiktok-comments-scraper`, `apify/instagram-comment-scraper` | $1.25–2.30 / 1k | The audience evidence |
| 4. Audience classification | Claude, on sampled comments | ~1 call/creator | The **only** signal that separates good from bad |
| 5. Whatnot confirmation | community actor, shortlist only | ~10 calls total | Confirms `creator_type = pro` |

Stage 1 is a prefilter with known false negatives. `@zozrsl`'s bio — *"Revendeur Vinted à plein temps
(+100K€ générés)"* — scored **0** until `revendeur` was added to the lexicon, and his paid Discord was in
`externalUrl`, not the bio. `@nathanvialle`'s Instagram bio (*"Je vends des vêtements pour vivre"*) still
scores 0. **Never reject on stage 1 alone; it exists to cut cost, not to decide.**

## 4. Sampling rules for comments

The sample must be the *audience*, not the internet.

- **Drop viral outliers** — posts with plays above 5× the creator's median. A `#fyp` hit is watched by people
  who do not follow them. This removed 8 of `@giu.cst`'s 20 videos.
- **Spread across posts**, cap per post. Never take 300 comments from one video.
- **Measure views only on posts ≥ 7 days old.** `profileSorting=latest` returns posts that have not finished
  accumulating views. `@behindthesale`'s median read 1,039 on a 3-video sample and 2,644 once fresh posts
  were excluded.

Adequacy is bounded by the creator, not by our settings: `@behindthesale` has only 286 comments across 20
videos. We sampled 132 and the classifier returned **High** confidence. The two creators with the *most*
comments (207, 179) returned **Medium** — because their audiences are genuinely mixed, not because the sample
was thin. Target ≈ **100+ comments across 10+ non-viral posts**.

## 5. The fit rubric

```
FIT (0–100) = audience 50 + sourcing intent 20 + creator credibility 20 + fleek warmth 10
```

| Component | Pts | Definition | Why |
|---|---|---|---|
| Audience quality | 50 | `50 × (pro% + 0.8 × hobbyist%) / 100` | The only separating signal. Hobbyists are real Fleek customers but *"lower volume, price sensitive"* — hence 0.8, not 1.0. |
| Sourcing intent | 20 | `20 × min(1, comments-per-100 asking where to source / 6)` | Direct buying intent for a wholesale marketplace. |
| Creator credibility | 20 | `12 × min(1, pro_ratio / 3)` + `8` if Whatnot/Discord/coaching | The trust gate. `pro_ratio` = pro terms ÷ consumer terms in their own content. |
| Fleek warmth | 10 | `10` if they already mention Fleek or carry an `RFD-` code | A warm lead, not a cold one. |

`confidence` is a **gate, not points**. A `Low`-confidence audience classification cannot enter the shortlist
without human review.

### Validation

| creator | ground truth | audience | intent | credibility | warmth | **FIT** |
|---|---|---|---|---|---|---|
| `@behindthesale` | **Fleek partner** | 45.0 | 10.1 | 12.0 | 10 | **77.1** |
| `@juliacrcl` | **Fleek partner** | 34.5 | 14.9 | 12.0 | 10 | **71.4** |
| `@nathanviall3` | wiki reference | 32.0 | 19.3 | 12.0 | 0 | 63.3 |
| `@giu.cst` | wrong fit | 8.0 | 0.0 | 2.0 | 0 | **10.0** |
| `@juliettekitsch` | wrong fit | 1.2 | 0.0 | 0.0 | 0 | **1.2** |

Both known-good partners rank first and second; both wrong-fit creators score below 10.

**This is a consistency check, not out-of-sample validation.** The rubric leans on `audience_mix`, and
`audience_mix` was produced by the classifier. The genuine out-of-sample result is that the classifier ran
**blind** — it never saw which creators Fleek rates — and independently flagged both partners as Fleek-aware
from their comments alone. That is the evidence that the method works; the table above only shows the weights
don't undo it.

## 6. What does not score, and why

Every one of these is intuitive, and every one is contradicted by the data.

| Signal | `behindthesale` (good) | `giu.cst` (bad) | Verdict |
|---|---|---|---|
| Followers | 35,200 | **253,200** | No separation. `mission/mission.md`: *"Follower count is not a scoring factor."* |
| Engagement rate | 5.7% | **8.1%** | **Inverted.** The worst fit has the highest engagement. |
| Views per follower | 0.08 | 0.09 | No separation. `@juliettekitsch` scores 8.24 and is a dormant consumer account. |
| Posts per week | 5.2 | 0.1 | Belongs to activation risk. `@juliacrcl` = 0.2 and is a top partner. |

Engagement rate is still computed — it feeds reach in [cac-model.md](cac-model.md) — but it is **not** a fit
signal. Putting it in the fit score would have promoted `@giu.cst` to the top of the shortlist.

Sorting by followers is worse than useless: [run_discovery.py:131](../scripts/run_discovery.py) sorts
descending by followers and then truncates to `--limit-enrich`, so the Claude budget is spent on the largest
accounts first. That is the exact opposite of *"trust matters more than reach."*

## 7. Hypotheses tested and rejected

Kept because the brief asks to see *"the ones that failed and what you changed."* These are real.

**1. A pro:consumer keyword ratio over comments identifies a reseller audience.**
Rejected. It scored `@giu.cst` at **9.5× pro** — her comments are full of *"mon vinted : clara23dp"*, viewers
advertising their own closets. The word matched; the intent was absent. The blind classifier returned **0% pro,
High confidence**, correctly reading them as self-promotion by casual sellers, not sourcing intent. *A viewer
asking the creator where to source has buying intent; a viewer advertising their own shop does not.* Speech act,
not vocabulary — which is why this stage needs a model.

**2. Wholesale words find wholesale-adjacent creators.**
Rejected. `#grossiste` and `#balledefriperie` on Instagram returned `@ramzi_gros__`, `@kelisegroup`,
`@sifcol.sifcol` — wholesalers advertising their own stock, 80–2,000 followers. **Hashtags have a side.**
Suppliers tag posts with the words for what they *sell*; resellers tag theirs with the words for what they *do*.
Discovery wants the demand side. The wiki had already recorded this and the hypothesis was written anyway.
`SUPPLY_SIDE` tags are retained in [discover_instagram.py](../scripts/discover_instagram.py) for the competitor
map, not for discovery.

**3. `#achatrevente` and `#revendeuse` find French resellers.**
Rejected. *Achat-revente* is generic French business jargon: the tag returned `@investimus.app` (real estate)
and `@berms_international` (cosmetics). `#revendeuse` returned MLM cosmetics sellers. Three tags yielded 27
posts total.

**4. The same handle on two platforms is the same person.**
Rejected. `@behindthesale` on TikTok is Fleek's top partner. `@behindthesale` on Instagram is a real-estate
coaching duo with 110 followers. The Airtable key **must** be `platform:handle`; upserting on `Handle` alone
would overwrite a top partner with a stranger. Cross-platform identity is a *hypothesis flagged for human
review*, never an automatic merge.

## 8. Sources and their roles

Discovery is many thin sources emitting `{handle, platform}`; enrichment is one path. Scaling to 10,000 means
adding sources, not rebuilding the machine — which is the brief's *"how would you take this from 10 to 10,000"*.

| Source | Yield | Role |
|---|---|---|
| TikTok hashtags (`clockworks/tiktok-scraper`) | 90 videos → 79 creators → 12 resellers | **Primary discovery.** The lane that produces. |
| Instagram graph walk (`relatedProfiles` from a known-good seed) | 28 handles from `@juliacrcl`, incl. `@zozrsl`, `@whatnot_fr`, `@united.vintage` | **Primary Instagram discovery.** High signal density. Populated for only 1 of 3 seeds. |
| Instagram profile resolution (`apify/instagram-profile-scraper`) | followers, bio, `externalUrl`, `businessCategoryName` | **Enrichment for creators found anywhere.** TikTok bios often name the IG handle. |
| Instagram hashtags (`apify/instagram-hashtag-scraper`) | 27 posts from 3 tags, low precision | **Weak tertiary.** Throttled and polluted. |
| Seed CSV (Whatnot sellers, wiki names) | manual | **First-class input,** not an exception. |

`@theliveneedham` — one of Fleek's three named partners — exists on **neither** TikTok nor Instagram
(`error: not_found`). The handle implies live selling. A hand-seeded list is not a workaround; it is the only
route to a third of Fleek's own known-good partners.

Whatnot cannot be scraped live. Two-step instead: regex for `whatnot` across bio, `externalUrl` and captions
(free, on data already scraped), then a community actor on the final shortlist only. Note that Whatnot presence
proves `creator_type = pro` — a live-seller sells *garments* to viewers, so it says nothing about their audience
being resellers. This is the two-field distinction in its sharpest form.

## 9. Known gaps

- The rubric is calibrated on **n = 5**, of which 2 are ground truth. It is an anchor, not a training set.
- `relatedProfiles` populated for 1 of 3 seeds; the graph walk needs a fallback.
- Instagram comment costs ($1.90–2.30/1k) are ~1.8× TikTok's measured $1.25/1k.
- `@bichettekids` unresolved on TikTok; `@claravictorya`'s TikTok handle is squatted (1 follower). The wiki's
  press-sourced handles are unverified, exactly as it warned.
- No test suite. Same debt as the rest of `content_brain/`.

## 10. Sources

- `mission/task-brief.md`, `mission/mission.md` — the pro/hobbyist taxonomy, the three named partners, trust > reach
- `Fleek Wiki/research/FR Reseller Vocabulary and Hashtags.md` — the FR lexicon
- `Fleek Wiki/research/French Reseller Creator Shortlist.md` — the reference set, and its own accuracy warning
- `data/calibration/2026-07-10T10-24-45/` — raw videos, features, 758 comments, blind audience classifications
- [content_brain/signals.py](../content_brain/signals.py) — the lexicon, versioned in one place
