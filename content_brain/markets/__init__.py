"""Market profiles — the per-market "consistent instruction" for the discovery engine.

The engine (scripts/run_discovery.py) is market-agnostic machinery. Everything specific to a market
— which channels to search, which hashtags seed the scrape, which handles seed the graph walk, the
follower band, the context platforms — lives in a profile here. France is the only live market;
adding Germany means writing markets/germany.py and reusing the engine unchanged.

See spec/discovery-engine.md for the architecture.
"""
from __future__ import annotations

from . import france

PROFILES = {"france": france.PROFILE}


def get(name: str):
    key = name.strip().lower()
    if key not in PROFILES:
        raise SystemExit(f"unknown market '{name}'. known: {', '.join(PROFILES)}")
    return PROFILES[key]
