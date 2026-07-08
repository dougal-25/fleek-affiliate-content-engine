"""Load/save the engine's data files (JSON on disk, stand-in for a real warehouse)."""

from __future__ import annotations

import json
from pathlib import Path

from .models import Brief, Creator, PartnerProfile, Post, SegmentInsight

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _load(name: str) -> list[dict]:
    path = DATA_DIR / name
    if not path.exists():
        raise SystemExit(f"{path} not found — run `python run_campaign.py generate-data` first")
    return json.loads(path.read_text())


def load_creators() -> list[Creator]:
    return [Creator.model_validate(d) for d in _load("roster.json")]


def load_posts() -> list[Post]:
    return [Post.model_validate(d) for d in _load("posts.json")]


def append_posts(new_posts: list[Post]) -> None:
    posts = _load("posts.json") + [p.model_dump(mode="json") for p in new_posts]
    (DATA_DIR / "posts.json").write_text(json.dumps(posts, indent=1))


def save_creators(creators: list[Creator]) -> None:
    (DATA_DIR / "roster.json").write_text(
        json.dumps([c.model_dump(mode="json") for c in creators], indent=1)
    )


def save_profile(profile: PartnerProfile) -> None:
    d = DATA_DIR / "profiles"
    d.mkdir(exist_ok=True)
    (d / f"{profile.creator_id}.json").write_text(profile.model_dump_json(indent=1))


def load_profile(creator_id: str) -> PartnerProfile | None:
    path = DATA_DIR / "profiles" / f"{creator_id}.json"
    return PartnerProfile.model_validate_json(path.read_text()) if path.exists() else None


def save_brief(brief: Brief) -> None:
    d = DATA_DIR / "briefs"
    d.mkdir(exist_ok=True)
    (d / f"{brief.brief_id}.json").write_text(brief.model_dump_json(indent=1))


def save_insights(insights: list[SegmentInsight]) -> None:
    (DATA_DIR / "insights.json").write_text(
        json.dumps([i.model_dump() for i in insights], indent=1)
    )


def load_insights() -> list[SegmentInsight]:
    path = DATA_DIR / "insights.json"
    if not path.exists():
        return []
    return [SegmentInsight.model_validate(d) for d in json.loads(path.read_text())]
