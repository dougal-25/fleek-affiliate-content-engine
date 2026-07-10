"""Cheap, deterministic text signals — the free tier of the funnel.

These run on every candidate before a single paid comment scrape or model call, because they cost
nothing and they throw away most of the noise. They are NOT the audience classifier: keyword
matching cannot tell "mon vinted : clara23dp" (a viewer advertising their own closet) from "quel
site pour acheter un lot de vêtements ?" (a viewer asking where to buy stock). Both contain
reseller vocabulary; only the second is a Fleek customer. That judgment needs a model, and it lives
in scripts/classify_audience.py.

What these signals DO tell you is what the *creator* talks about — which is a credibility gate, not
an audience measurement. Keep the two apart.

Calibrated 2026-07-10 against Fleek's named partners (@behindthesale, @juliacrcl) and two
deliberate non-fits (@giu.cst, @juliettekitsch). See data/calibration/ and spec/discovery-scoring.md.
"""
from __future__ import annotations

import re

# Kept per-language on purpose. The brief's named partners post in English; the discovery funnel is
# French. Scoring weights come from what the two lexicons have in COMMON (the behaviour: sourcing,
# margin, volume). The terms themselves are market-local and do not transfer.
LEXICON = {
    # FR — from "Fleek Wiki/research/FR Reseller Vocabulary and Hashtags.md" and the sourcing playbook.
    # "revendeur"/"revendeuse" added 2026-07-10: @zozrsl's bio reads "Revendeur Vinted à plein
    # temps (+100K€ générés)" — a textbook pro — and the lexicon scored him 0. The noun for the
    # person was missing; only the verb for the act was present.
    "fr_pro": ["grossiste", "balle", "ballot", "kilo", "/kg", "marge", "stock", "lot de",
               "revente", "revendeur", "revendeuse", "achat revente", "plein temps",
               "fournisseur", "sourcing", "invendu", "rentab", "chiffre d'affaire",
               "en gros", "vide-maison", "brocante", "whatnot"],
    "fr_consumer": ["tenue", "look", "ootd", "trouvé", "porter", "style", "inspo", "je porte"],
    # EN — derived from @behindthesale's own bio and captions, not guessed.
    "en_pro": ["reseller", "resell", "wholesale", "bundle", "bale", "sourcing", "supplier",
               "margin", "profit", "inventory", "stock", "flip", "bulk", "make more sales",
               "tips", "per kg", "whatnot"],
    "en_consumer": ["outfit", "ootd", "styling", "wearing", "my style", "thrift find", "fit check"],
}

BIO_FLAGS = {
    "whatnot": ["whatnot"],          # live-selling => the CREATOR is a pro. Says nothing about audience.
    "discord": ["discord"],          # French resellers pay for Discord coaching (task brief)
    "coaching": ["coaching", "formation", "mentorat", "accompagnement", "my course", "ebook"],
}

# Fleek's attribution mechanic, observable in captions:
#   "Use code RFD-BEHINDTHESALE for £££ off your first order"
# @juliacrcl carries no code in her captions but tags #fleek, so the code alone is not enough.
RFD_RE = re.compile(r"\bRFD-[A-Z0-9_]+\b", re.I)
FLEEK_RE = re.compile(r"(?:^|[\s#@])fleek\b", re.I)


def hits(text: str, terms: list[str]) -> list[str]:
    t = text.lower()
    return [w for w in terms if w in t]


def lexicon_profile(corpus: str) -> dict:
    """Per-lexicon term hits, plus the pro:consumer counts that separated every calibration creator."""
    found = {k: hits(corpus, terms) for k, terms in LEXICON.items()}
    pro = len(found["fr_pro"]) + len(found["en_pro"])
    consumer = len(found["fr_consumer"]) + len(found["en_consumer"])
    return {
        "lexicon_hits": found,
        "pro_terms": pro,
        "consumer_terms": consumer,
        # >1 means they talk business more than they talk clothes. Every known-good partner scored >1.
        "pro_ratio": round(pro / consumer, 2) if consumer else (float(pro) if pro else 0.0),
    }


def fleek_signals(corpus: str) -> dict:
    """Is this creator ALREADY a Fleek affiliate? A hit is a warm lead, not a cold one."""
    codes = sorted({c.upper() for c in RFD_RE.findall(corpus)})
    return {
        "fleek_referral_codes": codes,
        "mentions_fleek": bool(codes) or bool(FLEEK_RE.search(corpus)),
    }


def bio_flags(corpus: str) -> dict[str, bool]:
    return {k: bool(hits(corpus, terms)) for k, terms in BIO_FLAGS.items()}
