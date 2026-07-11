#!/usr/bin/env python3
"""
Fleek Affiliate Dashboard — local server.

Serves the dashboard and proxies its data so the Airtable key never reaches the browser:

    /api/creators   live Airtable roster; falls back to the committed snapshot if offline
    /api/trends     keyword/hashtag intelligence computed from the 588 ingested posts
    /api/funnel     stage counts + compounding weekly history (snapshots itself on each run)
    /avatar/<h>     profile image proxy (unavatar.io), disk-cached, 404 -> client draws initials

Stdlib only. Run:  python3 dashboard/serve.py   then open http://localhost:8787
"""
import json
import math
import os
import re
import sys
import urllib.request
import urllib.error
import urllib.parse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DATA_DIR = os.path.join(HERE, "data")
AVATAR_DIR = os.path.join(DATA_DIR, "avatars")
HISTORY_PATH = os.path.join(DATA_DIR, "funnel_history.json")
SNAPSHOT = os.path.join(REPO, "Fleek Wiki", "_raw", "airtable_creators_2026-07-09.json")
RAW_DIR = os.path.join(REPO, "Fleek Wiki", "_raw")
# every ingested post file joins the pool automatically (tiktok / youtube / instagram)
POSTS = sorted(
    os.path.join(RAW_DIR, n) for n in (os.listdir(RAW_DIR) if os.path.isdir(RAW_DIR) else [])
    if n.startswith(("apify_tiktok", "apify_youtube", "apify_instagram")) and n.endswith(".jsonl"))
FLEEK_HANDLES = {"joinfleek"}  # Fleek's own accounts — their posts get the "fleek" source tag
BASE_NAME = "Fleek Affiliate Ecosystem"
PORT = int(os.environ.get("PORT", 8787))

STAGES = ["Prospect", "Qualified", "Contacted", "Responded", "Call booked",
          "Contract", "Onboarded", "First post", "First sale", "Repeat posting"]


def load_key():
    key = os.environ.get("AIRTABLE_API_KEY")
    if key:
        return key.strip()
    d = HERE
    for _ in range(8):  # walk up until the workspace .env (worktrees sit deeper than the main checkout)
        d = os.path.dirname(d)
        p = os.path.join(d, ".env")
        if os.path.exists(p):
            with open(p) as f:
                for line in f:
                    if line.startswith("AIRTABLE_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def http_get(url, key=None, timeout=15):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0 (Macintosh) FleekDashboard/1.0")  # unavatar 403s python-urllib
    if key:
        req.add_header("Authorization", f"Bearer {key}")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


_base_id = None


def fetch_creators_live(key):
    global _base_id
    if not _base_id:
        bases = json.loads(http_get("https://api.airtable.com/v0/meta/bases", key))["bases"]
        base = next(b for b in bases if b["name"] == BASE_NAME)
        _base_id = base["id"]
    records, offset = [], None
    while True:
        url = f"https://api.airtable.com/v0/{_base_id}/Creators?pageSize=100"
        if offset:
            url += f"&offset={offset}"
        page = json.loads(http_get(url, key))
        records += page.get("records", [])
        offset = page.get("offset")
        if not offset:
            return records


def get_creators():
    key = load_key()
    if key:
        try:
            data = {"source": "live", "fetched": now_iso(), "records": fetch_creators_live(key)}
            return enrich(data)
        except Exception as e:
            print(f"  ! live fetch failed ({e}); serving snapshot")
    with open(SNAPSHOT) as f:
        return enrich({"source": "snapshot", "fetched": "2026-07-09", "records": json.load(f)})


# ---- enrichment: audience-type tags + channel links, derived deterministically ----

AUDIENCE_RULES = [
    ("wholesale buyers", r"grossiste|wholesale|en gros|fournisseur|bulk|destockage|b2b"),
    ("aspiring resellers", r"formation|course|coaching|make money|de 0 [aà]|business|astuces vente|reselling tips|selling tips|monetize"),
    ("bargain hunters", r"bonplan|bon plan|pas ?cher|petit prix|deal|promo"),
    ("vintage lovers", r"vintage|friperie|fripe|retro|y2k|brocante"),
    ("live-shopping viewers", r"\blive\b|whatnot|videdressing live|vente live|liveshopping|auction"),
    ("sneakerheads", r"sneaker|deadstock|streetwear"),
    ("luxury-resale shoppers", r"luxury|louis vuitton|saint laurent|designer|authenticated|luxe"),
    ("eco-conscious shoppers", r"seconde ?main|secondhand|second-hand|upcycl|durable|sustainable"),
    ("fashion-inspo seekers", r"outfit|ootd|\blook\b|style|try-on|haul|dressing"),
]
AUDIENCE_RES = [(tag, re.compile(pat, re.I)) for tag, pat in AUDIENCE_RULES]

CHANNEL_PATTERNS = [
    ("TikTok", r"(?:https?://)?(?:www\.)?tiktok\.com/@([\w.\-]+)", "https://www.tiktok.com/@{}"),
    ("Instagram", r"(?:https?://)?(?:www\.)?instagram\.com/([\w.\-]+)", "https://www.instagram.com/{}"),
    ("Instagram", r"insta(?:gram)?\s*[:\s]\s*@?([\w.]{3,30})", "https://www.instagram.com/{}"),
    ("YouTube", r"(?:https?://)?(?:www\.)?youtube\.com/(@[\w.\-]+)", "https://www.youtube.com/{}"),
    ("Vinted", r"(?:https?://)?(?:www\.)?vinted\.\w+/member/([\w.\-]+)", "https://www.vinted.fr/member/{}"),
    ("Depop", r"(?:https?://)?(?:www\.)?depop\.com/([\w.\-]+)", "https://www.depop.com/{}"),
    ("Whatnot", r"(?:https?://)?(?:www\.)?whatnot\.com/user/([\w.\-]+)", "https://www.whatnot.com/user/{}"),
]
CHANNEL_RES = [(name, re.compile(pat, re.I), tmpl) for name, pat, tmpl in CHANNEL_PATTERNS]


def enrich(data):
    for r in data["records"]:
        f = r["fields"]
        signal = " ".join(str(f.get(k) or "") for k in
                          ("Content Keywords", "Audience", "Strength", "Segment"))
        f["_audience_tags"] = [tag for tag, rx in AUDIENCE_RES if rx.search(signal)][:3] \
            or ["general fashion audience"]

        channels = {}
        if f.get("Platform") and f.get("Profile URL"):
            channels[f["Platform"]] = f["Profile URL"]
        # auto-detect from bio + notes; manual additions via an Airtable "Channels" field
        # (one per line, "Platform: url" — wins over auto-detection)
        scan = " ".join(str(f.get(k) or "") for k in ("Audience", "Notes"))
        for name, rx, tmpl in CHANNEL_RES:
            m = rx.search(scan)
            if m and name not in channels:
                channels[name] = tmpl.format(m.group(1).rstrip("."))
        for line in str(f.get("Channels") or "").splitlines():
            if ":" in line:
                name, url = line.split(":", 1)
                if url.strip():
                    channels[name.strip().title()] = url.strip() if "//" in url \
                        else "https://" + url.strip()
        f["_channels"] = channels
    return data


# ---- inspiration: top-performing posts from the roster ----

FORMAT_RULES = [
    ("Live selling", r"\blive\b|whatnot|vente live|liveshopping|auction"),
    ("Bale unboxing", r"unboxing|balle?\b|ballot|d[ée]ballage"),
    ("Haul / try-on", r"haul|try.?on|essayage"),
    ("Tutorial / tips", r"astuce|tuto|guide|conseil|comment |tips|formation"),
    ("Sourcing vlog", r"sourcing|fournisseur|vlog|48h|visite"),
]
FORMAT_RES = [(name, re.compile(pat, re.I)) for name, pat in FORMAT_RULES]


# Relevance gate: a video must speak reselling/secondhand-fashion or it does not enter
# the inspiration wall, no matter how viral it went.
RELEVANT_RE = re.compile(
    r"friperie|fripe\b|vinted|seconde ?main|secondhand|second-hand|thrift|resell|revente"
    r"|achat.?revente|grossiste|wholesale|en gros|fournisseur|sourcing|balle\b|ballot"
    r"|d[ée]ballage|unboxing|whatnot|vide.?dressing|depop|vintage|streetwear|outfit|ootd"
    r"|haul|brocante|destockage|dressing|pi[èe]ce|v[êe]tement|mode\b|frip", re.I)

MAX_AGE_DAYS = 540      # "new": nothing older than ~18 months
MAX_PER_AUTHOR = 3      # diversity: no single creator dominates the wall
THUMBS_DIR = os.path.join(HERE, "thumbs")


def get_thumb(author, post_id):
    """Download + cache the video thumbnail via TikTok oEmbed (CDN URLs expire; files don't)."""
    cached = os.path.join(THUMBS_DIR, f"{post_id}.jpg")
    if os.path.exists(cached):
        return f"/thumbs/{post_id}.jpg"
    try:
        meta = json.loads(http_get(
            f"https://www.tiktok.com/oembed?url=https://www.tiktok.com/@{author}/video/{post_id}",
            timeout=10))
        body = http_get(meta["thumbnail_url"], timeout=10)
        if image_type(body):
            os.makedirs(THUMBS_DIR, exist_ok=True)
            with open(cached, "wb") as f:
                f.write(body)
            return f"/thumbs/{post_id}.jpg"
    except Exception:
        pass
    return None


def compute_inspiration(creators):
    """TikTok + Instagram (both natively embeddable), relevance-gated, ranked by how far a
    video outperforms its creator's own median — a repeatable technique, not a big account.
    Fleek's own accounts skip the vocabulary gate (their content is Fleek by definition) and
    get their own quota so the Fleek filter always has substance."""
    posts = [p for p in load_posts() if p["platform"] in ("TikTok", "Instagram") and p.get("id")]
    now = datetime.now(timezone.utc)

    med = {}
    for p in posts:
        med.setdefault(p["author"], []).append(p["views"])
    med = {a: sorted(v)[len(v) // 2] or 1 for a, v in med.items()}

    scored = []
    for p in posts:
        source = "fleek" if (p["author"] or "").lower() in FLEEK_HANDLES else "roster"
        text_all = (p["text"] or "") + " " + " ".join(p["tags"])
        if source == "roster" and not RELEVANT_RE.search(text_all):
            continue
        if p["views"] < (300 if source == "fleek" else 1000):
            continue
        try:
            age = (now - datetime.fromisoformat(p["date"].replace("Z", "+00:00"))).days
        except (TypeError, ValueError, AttributeError):
            continue
        if age > MAX_AGE_DAYS:
            continue
        ratio = p["views"] / max(med[p["author"]], 1)
        recency = 1.5 if age <= 90 else 1.2 if age <= 180 else 1.0
        score = math.sqrt(max(ratio, 0.1)) * math.log10(p["views"] + 10) * recency
        scored.append((score, ratio, age, source, p))

    scored.sort(key=lambda t: -t[0])
    top, per_author, n_fleek = [], Counter(), 0
    for score, ratio, age, source, p in scored:
        if source == "fleek":
            if n_fleek >= 12:
                continue
            n_fleek += 1
        else:
            if per_author[p["author"]] >= MAX_PER_AUTHOR:
                continue
            per_author[p["author"]] += 1
        eng = (p["likes"] + p["comments"] + p["shares"]) / max(p["views"], 1)
        try:
            weekday = datetime.fromisoformat(p["date"].replace("Z", "+00:00")).strftime("%A")
        except (TypeError, ValueError, AttributeError):
            weekday = None
        if p["platform"] == "TikTok":
            url = f"https://www.tiktok.com/@{p['author']}/video/{p['id']}"
            embed = f"https://www.tiktok.com/embed/v2/{p['id']}"
            thumb = get_thumb(p["author"], p["id"])
        else:  # Instagram — thumbnails were cached at ingest (CDN URLs expire fast)
            url = f"https://www.instagram.com/p/{p['id']}/"
            embed = f"https://www.instagram.com/p/{p['id']}/embed/"
            ig_thumb = os.path.join(THUMBS_DIR, f"ig_{p['id']}.jpg")
            thumb = f"/thumbs/ig_{p['id']}.jpg" if os.path.exists(ig_thumb) else None
        top.append({
            "author": p["author"], "platform": p["platform"], "source": source,
            "views": p["views"],
            "likes": p["likes"], "comments": p["comments"], "shares": p["shares"],
            "engagement": round(eng * 100, 2), "author_median_views": med[p["author"]],
            "weekday": weekday,
            "date": (p["date"] or "")[:10], "text": (p["text"] or "")[:160],
            "tags": p["tags"][:5],
            "format": next((n for n, rx in FORMAT_RES if rx.search(p["text"] or "")), "Post"),
            "url": url, "embed": embed, "thumb": thumb,
            "ratio": round(ratio, 1),
        })
        if len(top) >= 36:
            break
    return {"posts": top, "total_pool": len(posts), "gate": "relevance+recency, ranked by overperformance"}


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---- trends: computed from the ingested posts ----

HASHTAG_RE = re.compile(r"#(\w{3,30})", re.UNICODE)
STOP = {"fyp", "foryou", "pourtoi", "viral", "video", "youtube", "shorts", "tiktok"}


def load_posts():
    posts = []
    for path in POSTS:
        name = os.path.basename(path)
        platform = "TikTok" if "tiktok" in name else "Instagram" if "instagram" in name else "YouTube"
        if not os.path.exists(path):
            continue
        with open(path) as f:
            for line in f:
                r = json.loads(line)
                if platform == "Instagram":
                    caption = r.get("caption") or ""
                    tags = [t.lower() for t in (r.get("hashtags") or [])] \
                        or [t.lower() for t in HASHTAG_RE.findall(caption)]
                    date = r.get("timestamp")
                    views = int(r.get("videoPlayCount") or r.get("videoViewCount") or 0)
                    likes = int(r.get("likesCount") or 0)
                    comments = int(r.get("commentsCount") or 0)
                    shares = 0
                    author = r.get("ownerUsername") or ""
                    tags = [t for t in tags if len(t) >= 3 and t not in STOP]
                    posts.append({"platform": platform, "date": date, "views": views,
                                  "likes": likes, "comments": comments, "shares": shares,
                                  "author": author, "tags": tags,
                                  "text": caption.strip()[:180], "id": r.get("shortCode")})
                    continue
                if platform == "TikTok":
                    # hashtags: plain strings (2026-07-09 ingest) or {name:...} dicts (newer runs)
                    tags = [(t.get("name") if isinstance(t, dict) else t or "").lower()
                            for t in (r.get("hashtags") or [])]
                    tags = [t for t in tags if t]
                    text = r.get("text") or ""
                    date = r.get("createTimeISO")
                    views = int(r.get("playCount") or 0)
                    likes = int(r.get("diggCount") or 0)
                    comments = int(r.get("commentCount") or 0)
                    shares = int(r.get("shareCount") or 0)
                    author = r.get("author") or (r.get("authorMeta") or {}).get("name") or ""
                else:
                    text = (r.get("title") or "") + " " + (r.get("description") or "")
                    tags = [t.lower() for t in HASHTAG_RE.findall(text)]
                    date = r.get("date")
                    views = int(r.get("viewCount") or 0)
                    likes = int(r.get("likes") or 0)
                    comments = int(r.get("commentsCount") or 0)
                    shares = 0  # not captured by the YouTube scraper
                    author = r.get("channelUsername") or r.get("channelName") or ""
                tags = [t for t in tags if len(t) >= 3 and t not in STOP]
                posts.append({"platform": platform, "date": date, "views": views,
                              "likes": likes, "comments": comments, "shares": shares,
                              "author": author, "tags": tags,
                              "text": text.strip()[:180], "id": r.get("id")})
    return posts


def compute_trends():
    posts = load_posts()
    now = datetime.now(timezone.utc)
    recent_cut = now - timedelta(days=90)
    prior_cut = now - timedelta(days=180)

    vol, eng, recent, prior = Counter(), Counter(), Counter(), Counter()
    weekly = defaultdict(int)
    for p in posts:
        try:
            d = datetime.fromisoformat(p["date"].replace("Z", "+00:00"))
        except (TypeError, ValueError, AttributeError):
            continue
        for t in set(p["tags"]):
            vol[t] += 1
            eng[t] += p["views"]
            if d >= recent_cut:
                recent[t] += 1
            elif d >= prior_cut:
                prior[t] += 1
        if d >= now - timedelta(weeks=12):
            weekly[(d - timedelta(days=d.weekday())).strftime("%Y-%m-%d")] += 1

    rising = []
    for t, n in recent.most_common(60):
        if n >= 3:
            before = prior.get(t, 0)
            delta = n - before
            if delta > 0:
                rising.append({"tag": t, "recent": n, "prior": before, "delta": delta})
    rising.sort(key=lambda x: (-x["delta"], -x["recent"]))

    top_posts = sorted(
        (p for p in posts if p["views"] > 0), key=lambda p: -p["views"])[:12]

    return {
        "post_count": len(posts),
        "top_by_volume": [{"tag": t, "count": n} for t, n in vol.most_common(14)],
        "top_by_engagement": [{"tag": t, "views": v} for t, v in eng.most_common(14)],
        "rising": rising[:10],
        "weekly_posts": sorted(({"week": w, "count": c} for w, c in weekly.items()),
                               key=lambda x: x["week"]),
        "top_posts": top_posts,
    }


# ---- funnel: current stages + compounding history ----

def compute_funnel(creators):
    counts = Counter(r["fields"].get("Stage", "Prospect") for r in creators["records"])
    stages = {s: counts.get(s, 0) for s in STAGES}
    os.makedirs(DATA_DIR, exist_ok=True)
    history = []
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH) as f:
            history = json.load(f)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if creators["source"] == "live" and not any(h["date"] == today for h in history):
        history.append({"date": today, "stages": stages})
        with open(HISTORY_PATH, "w") as f:
            json.dump(history, f, indent=1)
    return {"stages": stages, "history": history, "source": creators["source"]}


# ---- avatars: proxy + disk cache ----

def image_type(b):
    if b[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        return "image/webp"
    if b[:3] == b"GIF":
        return "image/gif"
    return None


def get_avatar(handle, platform):
    safe = re.sub(r"[^\w.-]", "", handle)[:60]
    if not safe:
        return None
    cached = os.path.join(AVATAR_DIR, safe)
    if os.path.exists(cached):
        with open(cached, "rb") as f:
            return f.read()
    provider = "youtube" if platform.lower() == "youtube" else "tiktok"
    try:
        body = http_get(f"https://unavatar.io/{provider}/{safe}?fallback=false", timeout=8)
        if image_type(body):
            os.makedirs(AVATAR_DIR, exist_ok=True)
            with open(cached, "wb") as f:
                f.write(body)
            return body
    except Exception:
        pass
    return None


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=HERE, **kw)

    def log_message(self, fmt, *args):
        if "/avatar/" not in (args[0] if args else ""):
            super().log_message(fmt, *args)

    def send_json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        try:
            if path == "/api/creators":
                return self.send_json(get_creators())
            if path == "/api/trends":
                return self.send_json(compute_trends())
            if path == "/api/funnel":
                return self.send_json(compute_funnel(get_creators()))
            if path == "/api/inspiration":
                return self.send_json(compute_inspiration(get_creators()))
            if path.startswith("/avatar/"):
                handle = urllib.parse.unquote(path.split("/avatar/", 1)[1])
                platform = "youtube" if "platform=YouTube" in self.path else "tiktok"
                body = get_avatar(handle, platform)
                if body:
                    self.send_response(200)
                    self.send_header("Content-Type", image_type(body) or "image/jpeg")
                    self.send_header("Content-Length", str(len(body)))
                    self.send_header("Cache-Control", "max-age=86400")
                    self.end_headers()
                    return self.wfile.write(body)
                return self.send_json({"error": "no avatar"}, 404)
        except BrokenPipeError:
            return
        except Exception as e:
            return self.send_json({"error": str(e)}, 500)
        return super().do_GET()


def main():
    key = load_key()
    mode = "LIVE (Airtable key found)" if key else "SNAPSHOT (no AIRTABLE_API_KEY)"
    print(f"Fleek Affiliate Dashboard — {mode}")
    print(f"→ http://localhost:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    sys.exit(main())
