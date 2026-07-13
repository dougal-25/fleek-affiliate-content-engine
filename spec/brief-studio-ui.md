# Brief Studio — UI spec

The operator surface for the brief generator, designed as a **new tab in the affiliate
dashboard** (not a standalone tool). Doug's direction, 2026-07-12.

**References:** the affiliate dashboard itself — `dashboard/tokens.css`, `dashboard/style.css`,
`dashboard/charts.js`. Reuse its tokens, components, and chart style. Specifically the
cluster/trends charts and the existing `.lang-toggle`, `.channel-links`, `.contact-box`.

**Mood/feel:** Fleek's own marketplace aesthetic — white surfaces, coral/gold/plum, Montserrat,
gold accents. Confident operator tool, not a document. Light, scannable, data-forward.

**Hero moment:** **localisation made visible.** Every message we write for a French creator is
shown in French *with its English translation*, flipped by the dashboard's FR/EN toggle. A
reviewer who doesn't read French can see both what we wrote and what it says. This is the whole
point of the section — the engine doesn't just translate, it localises per creator and channel.

**Second pillar — channel-aware delivery:** creators are contacted differently. Some by email
(subject + body), some by DM (short). The outreach that carries the brief is formatted for the
right channel per the creator's `Contact Route`. Julia → DM, Félix → DM, Lina → email.

**Anti-examples:** the first mockup (green-ledger palette, three dense text columns). Too
overwhelming, too text-heavy, off-brand. What we're writing and *why* must be immediately clear.

**Constraints:** desktop-first (operator tool); Fleek brand tokens locked (`dashboard/tokens.css`);
reuse dashboard components and charts; progressive disclosure — lead with the message and the
why; push the full 14-field brief into a drawer.

## Build notes

- Density fix: the *messages* (hooks, captions, outreach) get the bilingual showcase — that's
  the hero and earns its space. Everything else (talking points, dos/don'ts, references) moves
  into a "Full brief" drawer so the main view stays light.
- Evidence shown as a chart (top-posts by views), not prose — the dashboard's `hBarChart` style.
- Do-not-mention stays visible but compact (chips/callouts), because it protects positioning.
- The FR/EN toggle is global (topbar), mirroring `dashboard/translations.js` `window.Lang`.
- Real data throughout: three generated briefs, real scraped posts, real referral codes.
