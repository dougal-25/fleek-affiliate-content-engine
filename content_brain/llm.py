"""Claude client wrapper: structured outputs, prompt caching, and an offline mock mode.

Design notes
- `claude-opus-4-8` with adaptive thinking; structured outputs via `client.messages.parse`
  so agents return validated Pydantic objects, never hand-parsed JSON.
- The system prompt (Fleek context + style guide) is stable and cached with
  `cache_control: {"type": "ephemeral"}` — per-creator evidence goes after the breakpoint.
  At hundreds of briefs per cycle the cached prefix is most of the token bill.
- For full-roster runs the production path is the Message Batches API (50% cost,
  not latency-sensitive); this prototype calls sequentially for clarity.
- With no ANTHROPIC_API_KEY, `mock=True` and agents fall back to deterministic templates
  so the whole loop runs offline.
"""

from __future__ import annotations

import os
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = """\
You are Fleek's Content Brain — the AI engine behind the influencer channel of a B2B
secondhand-fashion marketplace. Fleek sells graded secondhand inventory wholesale to vintage
stores and resellers. The ICP is hobbyist and pro resellers in the UK and France; the channel
is measured on new buyers, CAC, payback, and first-order AOV — never on reach.

Voice and rules:
- Write briefs and profiles a busy creator or channel manager can act on immediately.
- Ground every claim in the evidence provided (their posts, their segment's numbers). Never
  invent performance data.
- Hooks must sound like the creator, not like a brand. Do's and don'ts must be specific,
  not generic social-media advice.
- For French creators (geo FR), write hooks and CTA copy in French; keep field labels and
  analysis in English.
- Success targets are always buyer-denominated (first orders, CAC), never views or likes.
"""


class LLM:
    def __init__(self) -> None:
        self.mock = not os.environ.get("ANTHROPIC_API_KEY")
        self._client = None
        if not self.mock:
            import anthropic

            self._client = anthropic.Anthropic()

    def generate(self, prompt: str, schema: type[T]) -> T | None:
        """Return a validated `schema` instance, or None in mock mode (caller falls back)."""
        if self.mock:
            return None
        response = self._client.messages.parse(
            model=MODEL,
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": prompt}],
            output_format=schema,
        )
        return response.parsed_output


_llm: LLM | None = None


def get_llm() -> LLM:
    global _llm
    if _llm is None:
        _llm = LLM()
    return _llm
