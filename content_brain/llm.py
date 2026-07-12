"""Claude client wrapper: structured outputs, prompt caching, and an offline mock mode.

Design notes
- `claude-opus-4-8` with adaptive thinking; structured outputs via `client.messages.parse`
  so agents return validated Pydantic objects, never hand-parsed JSON.
- **Prompt caching, honestly.** The cacheable prefix is (stable system prompt + the cycle's
  shared context: FR trend pages, Fleek archetypes, style guide). Per-creator evidence goes
  after the breakpoint, so it never invalidates the prefix.

  The catch worth knowing: on `claude-opus-4-8` the **minimum cacheable prefix is 4096
  tokens**. Below that, `cache_control` is silently ignored — no error, just
  `cache_creation_input_tokens: 0`. The bare system prompt here is ~250 tokens, so marking
  it alone would have cached nothing while looking like it did. Passing the full trend pack
  as `cached_context` is what pushes the prefix over the line. `last_usage` exposes the
  cache counters so the claim is measured, not asserted — see `run_campaign.py brief-real`.
- **Batch API for scale:** generating briefs for the whole roster is not latency-sensitive —
  the Message Batches API runs it at 50% cost. The prototype runs sequentially for clarity;
  the production path is batching.
- **Mock mode:** with no API key, agents return deterministic template outputs so the whole
  loop is runnable and testable offline.
"""

from __future__ import annotations

import os
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

MODEL = "claude-opus-4-8"

# Opus 4.8 will not cache a prefix shorter than this. Documented so nobody "optimises"
# the shared context down and silently loses every cache hit.
MIN_CACHEABLE_PREFIX_TOKENS = 4096

SYSTEM_PROMPT = """\
You are Fleek's Content Brain — the AI engine behind the influencer channel of a B2B
secondhand-fashion marketplace. Fleek sells graded secondhand inventory wholesale to vintage
stores and resellers. The ICP is hobbyist and pro resellers in the UK and France; the channel
is measured on new buyers, CAC, payback, and first-order AOV — never on reach.

Voice and rules:
- Write briefs and profiles a busy creator or channel manager can act on immediately.
- Ground every claim in the evidence provided (their posts, their segment's numbers). Never
  invent performance data. If a creator has no Fleek history, say so rather than inventing one.
- Hooks must sound like the creator, not like a brand. Do's and don'ts must be specific,
  not generic social-media advice.
- For French creators (geo FR), write hooks, captions and CTA copy in French; keep field
  labels and analysis in English.
- Fleek's hardest positioning problem: pro resellers believe Fleek is for beginners. Never
  write copy that reinforces it.
- Success targets are always buyer-denominated (first orders, CAC), never views or likes.
"""


class LLM:
    def __init__(self) -> None:
        self.mock = not os.environ.get("ANTHROPIC_API_KEY")
        self.last_usage: Any = None
        self._client = None
        if not self.mock:
            import anthropic

            self._client = anthropic.Anthropic()

    def generate(self, prompt: str, schema: type[T], cached_context: str | None = None) -> T | None:
        """Return a validated `schema` instance, or None in mock mode (caller falls back).

        `cached_context` is content stable across every call in a cycle. It sits behind the
        cache breakpoint with the system prompt; per-creator evidence belongs in `prompt`.
        """
        if self.mock:
            return None

        system: list[dict] = [{"type": "text", "text": SYSTEM_PROMPT}]
        if cached_context:
            system.append({"type": "text", "text": cached_context})
        # Breakpoint on the last system block caches everything before it.
        system[-1]["cache_control"] = {"type": "ephemeral"}

        response = self._client.messages.parse(
            model=MODEL,
            max_tokens=16000,  # thinking and output share this budget
            thinking={"type": "adaptive"},
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_format=schema,
        )
        self.last_usage = response.usage
        return response.parsed_output

    def cache_report(self) -> str:
        """Human-readable cache outcome for the last call. A receipt, not a promise."""
        u = self.last_usage
        if u is None:
            return "mock mode — no API call made"
        written = getattr(u, "cache_creation_input_tokens", 0) or 0
        read = getattr(u, "cache_read_input_tokens", 0) or 0
        uncached = getattr(u, "input_tokens", 0) or 0
        total_prefix = written + read
        if total_prefix == 0:
            return (
                f"cache MISS (nothing cached): prefix under the {MIN_CACHEABLE_PREFIX_TOKENS}-token "
                f"minimum for {MODEL}. {uncached:,} input tokens billed at full rate."
            )
        if read:
            return f"cache HIT: {read:,} tokens read at ~0.1x, {uncached:,} billed full."
        return f"cache WRITE: {written:,} tokens stored at ~1.25x. Next call in 5min reads them."


_llm: LLM | None = None


def get_llm() -> LLM:
    global _llm
    if _llm is None:
        _llm = LLM()
    return _llm
