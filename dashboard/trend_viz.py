"""
Trends-page visualisations computed from the ingested posts (pure functions, no IO).

Three views, each answering one question the brief generator cares about:
  compute_stream        — what's rising?      (per-tag weekly mentions → streamgraph)
  compute_cooccurrence  — what clusters?      (tags linked when they share a post → network)
  compute_movers        — what's biggest & fastest? (% change vs N weeks ago + sparkline)

Called by pipeline.compute_trends with the shared post list. Kept out of pipeline.py so
that file stays under the 500-line limit.
"""
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone

WEEKS = 10          # window for the streamgraph / sparklines
STREAM_TAGS = 7     # bands in the streamgraph
NODE_TAGS = 16      # nodes in the co-occurrence map
MIN_EDGE = 4        # tags must co-occur this often to draw an edge
MOVERS = 8          # rows in the movers list
LOOKBACK = 3        # movers compare the latest week vs this many weeks earlier

# tags a post carries that say nothing about a trend
NOISE = {"fyp", "foryou", "pourtoi", "viral", "video", "shorts", "tiktok", "reels"}

# four families, first match wins — the light-theme analogue of the reference's
# Sound / Aesthetic / Format / Vibe
CATEGORY_RULES = [
    ("Sourcing", r"grossiste|wholesale|gros|fournisseur|friperie|fripe|balle|ballot|destock|sourcing|bulk|stock|depot"),
    ("Platform", r"vinted|whatnot|depop|insta|videdressing|ebay|\blive\b|liveshop|marketplace"),
    ("Format", r"haul|unbox|deball|tuto|astuce|formation|guide|tips|conseil|vlog|routine|review"),
    ("Style", r"vintage|y2k|streetwear|luxe|luxury|mode|seconde|secondhand|retro|outfit|ootd|drip|fashion|sneaker|nike|adidas"),
]
CATEGORY_RES = [(name, re.compile(pat, re.I)) for name, pat in CATEGORY_RULES]


def _categorise(tag):
    for name, rx in CATEGORY_RES:
        if rx.search(tag):
            return name
    return "Style"


def _week_index(date_str, now):
    """0 = current week, increasing into the past; None if unparseable/out of window."""
    try:
        d = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (TypeError, ValueError, AttributeError):
        return None
    return (now.date() - d.date()).days // 7


def _clean_tags(post):
    return [t for t in dict.fromkeys(post.get("tags") or []) if len(t) >= 3 and t not in NOISE]


def compute_stream(posts, now=None):
    now = now or datetime.now(timezone.utc)
    freq = Counter()
    per = defaultdict(lambda: [0] * WEEKS)  # tag -> [oldest..newest]
    for p in posts:
        w = _week_index(p.get("date"), now)
        tags = _clean_tags(p)
        for t in tags:
            if w is not None and 0 <= w < WEEKS:
                per[t][WEEKS - 1 - w] += 1
        # weight recent activity so a rising tag beats a big-but-stale one
        if w is not None and 0 <= w < WEEKS:
            for t in tags:
                freq[t] += 1
    top = [t for t, _ in freq.most_common(STREAM_TAGS)]
    return {
        "weeks": [f"W{i + 1}" for i in range(WEEKS)],
        "series": [{"tag": t, "values": per[t]} for t in top],
    }


def compute_cooccurrence(posts, now=None):
    freq = Counter()
    cooc = Counter()
    for p in posts:
        tags = _clean_tags(p)[:8]
        for t in tags:
            freq[t] += 1
        for i, a in enumerate(tags):
            for b in tags[i + 1:]:
                cooc[tuple(sorted((a, b)))] += 1
    top = [t for t, _ in freq.most_common(NODE_TAGS)]
    tset = set(top)
    nodes = [{"tag": t, "count": freq[t], "category": _categorise(t)} for t in top]
    edges = [{"a": a, "b": b, "weight": w}
             for (a, b), w in cooc.items() if a in tset and b in tset and w >= MIN_EDGE]
    return {"nodes": nodes, "edges": edges}


def compute_movers(posts, now=None):
    now = now or datetime.now(timezone.utc)
    freq = Counter()
    per = defaultdict(lambda: [0] * WEEKS)
    for p in posts:
        w = _week_index(p.get("date"), now)
        if w is None or not (0 <= w < WEEKS):
            continue
        for t in _clean_tags(p):
            per[t][WEEKS - 1 - w] += 1
            freq[t] += 1

    rows = []
    for t, _ in freq.most_common(60):
        series = per[t]
        recent = sum(series[-LOOKBACK:])                 # last 3 weeks
        prior = sum(series[-2 * LOOKBACK:-LOOKBACK])     # the 3 weeks before that
        if prior < 3:                                    # need a real baseline; skips one-week spikes
            continue
        pct = round(((recent - prior) / prior) * 100)
        rows.append({"tag": t, "pct": pct, "direction": "up" if pct >= 0 else "down",
                     "spark": series, "category": _categorise(t)})
    rows.sort(key=lambda r: -r["pct"])
    # show the biggest gainers and the sharpest fallers, like the reference
    return (rows[:MOVERS - 2] + rows[-2:]) if len(rows) > MOVERS else rows
