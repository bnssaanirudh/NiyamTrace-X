"""
packages/fuzz/equivalence.py — Semantic Preservation Checker (Week 6)

Checks whether two text variants are semantically equivalent for the
purpose of NiyamTrace (i.e., they should produce identical gate decisions).

Two texts are considered equivalent if:
  1. All protected spans (IDs, amounts, numbers) match exactly.
  2. Token overlap (Jaccard after normalization) is above threshold.

This does NOT use any language model. It is deterministic.

Status: IMPLEMENTED (Week 6)
"""

from __future__ import annotations

import re
from dataclasses import dataclass


# Protected span pattern (same as in transforms.py)
# Matches structured IDs (INV-001, USR-X, etc.) but NOT plain words
# that happen to start with those 3-letter prefixes.
_PROTECTED_PATTERN = re.compile(
    r"(?:INV|USR|VEN|SR|REQ|TKT)[-_][A-Za-z0-9/]+"
    r"|(?:\u20b9|\$|\u20ac)\s*\d[\d,\.]*"
    r"|\b\d{1,4}[-/]\d{1,2}[-/]\d{1,4}\b"
    r"|\b\d+\b",
    re.IGNORECASE,
)

# Simple ASCII-safe tokens only (ignores non-ASCII script words)
_ASCII_TOKEN_PATTERN = re.compile(r"\b[a-z]{2,}\b")


@dataclass
class EquivalenceResult:
    """Result of the semantic preservation check."""
    equivalent: bool
    divergence_score: float           # 0.0 = identical, 1.0 = completely different
    protected_span_match: bool        # all protected spans present in both texts
    token_overlap: float              # Jaccard on normalized ASCII tokens
    reason: str


def _extract_protected_spans(text: str) -> set[str]:
    """Extract all protected spans from text."""
    return set(m.group().strip() for m in _PROTECTED_PATTERN.finditer(text))


def _ascii_tokens(text: str) -> set[str]:
    """Lowercase ASCII word tokens, 2+ chars."""
    return set(_ASCII_TOKEN_PATTERN.findall(text.lower()))


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


class SemanticPreservationChecker:
    """
    Checks whether two utterances are semantically equivalent for policy
    enforcement purposes.

    Equivalence requires:
      1. Protected spans are identical (same IDs, amounts, dates).
      2. Normalized ASCII token Jaccard >= token_threshold.
         (Non-ASCII script tokens are intentionally excluded — the Romanized
          and script forms of the same word look different in ASCII.)
    """

    def __init__(
        self,
        token_threshold: float = 0.20,
        require_protected_match: bool = True,
    ) -> None:
        self.token_threshold = token_threshold
        self.require_protected_match = require_protected_match

    def check(self, text_a: str, text_b: str) -> EquivalenceResult:
        """
        Compare text_a (typically canonical English) against text_b (variant).

        Returns EquivalenceResult with equivalence bool and divergence_score.
        divergence_score = 1 - (0.5 * span_match + 0.5 * token_overlap).
        """
        # 1. Protected span check
        spans_a = _extract_protected_spans(text_a)
        spans_b = _extract_protected_spans(text_b)
        protected_match = spans_a == spans_b

        # 2. ASCII token overlap
        tokens_a = _ascii_tokens(text_a)
        tokens_b = _ascii_tokens(text_b)
        token_overlap = _jaccard(tokens_a, tokens_b)

        # 3. Determine equivalence
        span_score = 1.0 if protected_match else 0.0
        divergence_score = 1.0 - (0.5 * span_score + 0.5 * token_overlap)

        equivalent = token_overlap >= self.token_threshold
        if self.require_protected_match:
            equivalent = equivalent and protected_match

        # Build reason
        if not protected_match:
            reason = (
                f"Protected span mismatch: {spans_a} vs {spans_b}."
            )
        elif token_overlap < self.token_threshold:
            reason = (
                f"Token overlap too low ({token_overlap:.2f} < {self.token_threshold}). "
                f"Texts may not be semantically equivalent."
            )
        else:
            reason = (
                f"Equivalent: protected spans match={protected_match}, "
                f"token_overlap={token_overlap:.2f}"
            )

        return EquivalenceResult(
            equivalent=equivalent,
            divergence_score=round(divergence_score, 4),
            protected_span_match=protected_match,
            token_overlap=round(token_overlap, 4),
            reason=reason,
        )
