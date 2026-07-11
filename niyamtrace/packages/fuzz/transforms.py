"""
packages/fuzz/transforms.py — Multilingual Variant Generator (Week 6)

Given a canonical English utterance, generates semantically equivalent
variants in: Hinglish (Hindi in Latin), Romanized Telugu, Telugu script.

Design:
  - Deterministic rule-based transforms, no model inference.
  - Uses the same word substitution tables as the NLP normalizer (inverted)
    so that the intake pipeline can round-trip each variant back correctly.
  - Protected spans (IDs, numbers, dates) are preserved verbatim.
  - Each variant carries a variant_group_id linking it to the canonical.

Status: IMPLEMENTED (Week 6)
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Literal

Language = Literal["eng_Latn", "hin_Latn", "tel_Latn", "tel_Telu"]

# ---------------------------------------------------------------------------
# Word-level substitution tables (English → target language)
# ---------------------------------------------------------------------------

_EN_TO_HIN_LATN: dict[str, str] = {
    "archive": "archive",
    "block": "block",
    "access": "access",
    "invoices": "invoices",
    "for": "ke liye",
    "vendor": "vendor",
    "change": "change",
    "limit": "limit",
    "the": "ka",
    "next": "agle",
    "days": "din",
    "do": "mat",
    "not": "karo",
}

_EN_TO_TEL_LATN: dict[str, str] = {
    "archive": "archive",
    "block": "block",
    "access": "access",
    "invoices": "invoices",
    "for": "ki",
    "vendor": "vendor",
    "change": "change",
    "limit": "limit",
    "the": "ni",
    "next": "next",
    "days": "rojula",
    "do": "cheyyi",
    "not": "cheyyaku",
}

_EN_TO_TEL_TELU: dict[str, str] = {
    "archive": "ఆర్కైవ్",
    "block": "బ్లాక్",
    "access": "యాక్సెస్",
    "invoices": "ఇన్వాయిస్లు",
    "for": "కు",
    "vendor": "విక్రేత",
    "change": "చేంజ్",
    "limit": "లిమిట్",
    "the": "ని",
    "next": "నెక్స్ట్",
    "days": "రోజులు",
    "do": "చేయి",
    "not": "చేయొద్దు",
}

_TABLE_MAP: dict[Language, dict[str, str]] = {
    "hin_Latn": _EN_TO_HIN_LATN,
    "tel_Latn": _EN_TO_TEL_LATN,
    "tel_Telu": _EN_TO_TEL_TELU,
}

# Regex for protected spans — these are never translated
# Matches structured IDs like INV-001, USR-X, VEN-42 (requires separator)
# but NOT plain words like 'invoices', 'vendor' that start with those prefixes.
_PROTECTED_PATTERN = re.compile(
    r"(?:INV|USR|VEN|SR|REQ|TKT)[-_][A-Za-z0-9/]+"
    r"|(?:\u20b9|\$|\u20ac)\s*\d[\d,\.]*"
    r"|\b\d{1,4}[-/]\d{1,2}[-/]\d{1,4}\b"
    r"|\b\d+\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class VariantRequest:
    """A single variant of a canonical English utterance."""
    raw_text: str                    # variant text in target language
    source_text: str                 # original canonical English
    variant_group_id: str            # groups all variants + canonical together
    language: Language               # target language tag
    actor_id: str = ""
    actor_role: str = ""
    transform_trace: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Transform engine
# ---------------------------------------------------------------------------


class VariantTransformer:
    """
    Generates multilingual variants of a canonical English utterance.

    Protected spans (IDs, amounts, numbers, dates) are preserved verbatim.
    Words not in the substitution table are also passed through unchanged
    (graceful degradation).
    """

    def generate(
        self,
        canonical_text: str,
        actor_id: str = "",
        actor_role: str = "",
        variant_group_id: str | None = None,
        languages: list[Language] | None = None,
    ) -> list[VariantRequest]:
        """
        Generate variants for the given canonical English text.

        Args:
            canonical_text:   The canonical English utterance.
            actor_id:         Actor ID to propagate into VariantRequest.
            actor_role:       Actor role to propagate.
            variant_group_id: If None, generates a fresh UUID.
            languages:        Target languages. Defaults to all three variants.

        Returns:
            List of VariantRequest objects (one per language).
        """
        group_id = variant_group_id or str(uuid.uuid4())
        target_langs: list[Language] = languages or ["hin_Latn", "tel_Latn", "tel_Telu"]

        variants: list[VariantRequest] = []
        for lang in target_langs:
            translated, trace = self._translate(canonical_text, lang)
            variants.append(
                VariantRequest(
                    raw_text=translated,
                    source_text=canonical_text,
                    variant_group_id=group_id,
                    language=lang,
                    actor_id=actor_id,
                    actor_role=actor_role,
                    transform_trace=trace,
                )
            )
        return variants

    def _translate(self, text: str, lang: Language) -> tuple[str, list[str]]:
        """
        Translate text into target language using substitution table.
        Protected spans are kept verbatim.
        Returns (translated_text, transform_trace_list).
        """
        table = _TABLE_MAP.get(lang, {})
        trace: list[str] = [f"word_substitution:{lang}"]

        # Split text into tokens preserving protected spans
        parts: list[str] = []
        last_end = 0
        for match in _PROTECTED_PATTERN.finditer(text):
            # Translate text before match (preserves original spacing)
            before = text[last_end : match.start()]
            if before:
                translated_before = self._translate_words(before, table)
                # Ensure there's a trailing space before the protected span
                # if the original text had one (prevents 'vendor4421' merging)
                if before.endswith(" ") and not translated_before.endswith(" "):
                    translated_before += " "
                parts.append(translated_before)
            # Keep protected span verbatim — preserve surrounding whitespace
            parts.append(match.group())
            # Add a trailing space after the span if original text had one
            if last_end + len(before if before else "") + len(match.group()) < len(text):
                next_char = text[match.end()] if match.end() < len(text) else ""
                if next_char == " ":
                    parts.append(" ")
            last_end = match.end()

        # Trailing text
        remaining = text[last_end:]
        if remaining:
            parts.append(self._translate_words(remaining, table))

        translated = "".join(parts).strip()
        # Normalize whitespace
        translated = re.sub(r"\s+", " ", translated)
        return translated, trace

    @staticmethod
    def _translate_words(text: str, table: dict[str, str]) -> str:
        """Translate each word using the table; unknown words pass through.
        Non-word characters (spaces, punctuation) are preserved exactly."""
        if not text.strip():
            return text  # preserve pure whitespace/empty strings as-is
        words = text.split()
        out = []
        for word in words:
            # Strip leading/trailing punctuation for lookup
            stripped = word.strip(".,;:!?()")
            translated = table.get(stripped.lower(), stripped)
            # Re-attach punctuation
            lstrip_count = len(word) - len(word.lstrip(".,;:!?()"))
            rstrip_count = len(word) - len(word.rstrip(".,;:!?()"))
            prefix = word[:lstrip_count]
            suffix = word[len(word) - rstrip_count:] if rstrip_count else ""
            out.append(f"{prefix}{translated}{suffix}")
        # Reconstruct with a leading space if original text started with space
        result = " ".join(out)
        if text and text[0] == " " and not result.startswith(" "):
            result = " " + result
        return result
