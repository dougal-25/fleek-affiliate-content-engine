# What a new French partner needs to hear that a UK one does not

**Answers:** `mission/task-brief.md` Part 2 — *"Tell us what a new French partner needs to hear that a
UK one does not. Localisation is more than translation."*
**Sourced from:** `Fleek Wiki/research/` — every claim below traces to a cited page.
**Implemented in:** `scripts/run_outreach.py` (the `DRAFT_SYSTEM` prompt) and
`content_brain/evidence.py`.

Translation moves the words. Localisation moves the argument. Four things change when the creator is
French, and each one is encoded in the drafting prompt rather than left to the model's instincts.

---

## 1. Speak the trade's vocabulary, or be marked as an outsider

French reselling has a precise working vocabulary that has no clean English equivalent, and using it
is the fastest credibility signal available. From
[FR Reseller Vocabulary and Hashtags](../Fleek%20Wiki/research/FR%20Reseller%20Vocabulary%20and%20Hashtags.md):

| Term | Means |
|---|---|
| **balle / ballot** | a compressed bale, 10–50kg |
| **original** | unsorted raw stock — cheapest, riskiest |
| **crème / extra crème** | near-new top tier |
| **grade A / B / C** | like-new / light-wear / acceptable |
| **tri / trié / 1er choix** | sorting / sorted / first-pick |
| **semi-grossiste** | buys smaller, cherry-picked lots |
| **déballage** | bale-unboxing content |
| **au kilo / à la pièce** | priced by weight / by item |

A UK message can say "wholesale bundles" and be understood. A French message that says
*"lots en gros"* instead of *"ballots"* announces that nobody involved has bought stock in France.
The engine's drafting prompt carries this table and is told: *using the trade's words is the proof
you know the trade.*

## 2. Lead into an open wound: grading is not trusted

This is the difference that matters most, and it does not exist in the UK pitch.

French resellers have been burned by opaque grading, repeatedly and publicly. From
[French Reseller Community Sentiment](../Fleek%20Wiki/research/French%20Reseller%20Community%20Sentiment.md):

> *"Quand vous commandez un article dit grade A et Grade B vous recevrez que du grade B et quand on
> les contacte ils font les morts."*

> *"Compte 20 à 40 % de pièces invendables sur Vinted dans un ballot brut (taches, trous, démodé,
> hors saison)."*

That page's own conclusion: **"the complaint list is pre-written outreach copy."** Fleek's AI grading
is the direct answer to the exact grievance the market already voices unprompted.

Two guardrails, both enforced in the prompt:
- State the 20–40% waste figure as **a fact about the trade**, never as an accusation that *their*
  supplier scammed them. We have no evidence about their supplier.
- Never turn it into a sales pitch. It is context that earns the second sentence, not the close.

## 3. Address a professional as a professional — the beginner problem

`mission/mission.md:80` records Fleek's own words: *"Many [pro resellers] think Fleek is for beginners
and not for them. Changing that perception is one of our hardest problems."*

This is a **positioning** problem, and outreach is where it is won or lost. So the prompt forbids the
entire register of growth-marketing encouragement — no *"grow your side hustle"*, no explaining
reselling to a reseller. A pro is addressed on margin, grading consistency and sourcing reliability,
because those are the only three things that would make a professional buyer change supplier.

The engine picks **`vous`** by default and only drops to `tu` when the creator's own content is
informal and youth-facing. Getting this backwards is not a grammar error — `tu` to an established
*grossiste* reads as a stranger being presumptuous, and `vous` to a 22-year-old on TikTok reads as a
brand. The register is extracted from the creator's own captions, not guessed from their follower
count.

## 4. There is no forum to meet them in — so the DM *is* the community touch

The research found something structurally different about the French market, and it is a
[weak lane deliberately marked as such](../Fleek%20Wiki/research/French%20Reseller%20Community%20Sentiment.md):

> Search surfaced **no** public FR reseller forums, Discords or subreddits — consistent with the
> finding that these are private Facebook groups. Community exchange happens *inside* Vinted and at
> physical events.

Named physical hubs: **Marché de la Mode Vintage de Lyon** (200+ stands) and **Le Salon du Vintage**
(Paris + ~12 cities).

The UK playbook of "meet them where they already congregate publicly" has no French equivalent. That
raises the stakes on the first touch: it is not one of several channels, it is the channel. It also
means the credible community offer is an *event* or a private group, not a public Discord — and the
brief notes French resellers already pay for private Discord coaching communities, so they will pay
for access to expertise.

## 5. The regulatory floor a UK creator never mentions

Live constraints that make a French message concrete:

- **EPR auto-enrolment** — selling in France without an EPR number triggers automatic fees from
  1%/order ([TikTok Shop France](../Fleek%20Wiki/research/TikTok%20Shop%20France.md), line 30). A UK
  reseller has no equivalent worry. Related: *Loi AGEC* and textile EPR via the Refashion
  eco-organism have put the sorting sector into a state-subsidised crisis, which is precisely why
  bale supply is unreliable
  ([French Secondhand Market Trends 2026](../Fleek%20Wiki/research/French%20Secondhand%20Market%20Trends%202026.md)).
- **TikTok Shop FR friction** — thin seller support, buyer-biased disputes, a 3–6 month learning
  curve on category restrictions
  ([French Reseller Community Sentiment](../Fleek%20Wiki/research/French%20Reseller%20Community%20Sentiment.md),
  sourced to Reddit r/TikTokshop and Lengow).

Naming one of these correctly, unprompted, does more for credibility than any adjective.

---

## What the human still does

The engine drafts. It does not send. Every draft lands in Airtable as `Outreach Status = Draft` with:

- the **French message** to send,
- an **English back-translation** so a non-native reviewer can verify the French says what it claims,
- the **localisation choices** the model made, stated explicitly,
- a **native-speaker QA list** — the specific idioms and register calls a French speaker must check.

That last item is the honest part. The engine can carry the trade's vocabulary and dodge the beginner
trap, but it cannot tell you whether *"elle tape juste"* reads as natural praise or as a foreigner
trying too hard. A native speaker settles that, and then a human presses send.

**AI translated → I localised → a native speaker QA'd.** All three steps are visible in the record.
