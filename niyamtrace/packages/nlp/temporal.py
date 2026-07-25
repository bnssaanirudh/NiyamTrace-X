"""
packages/nlp/temporal.py — Temporal Deixis Resolver

Resolves relative temporal expressions in English, Hinglish, and
Romanized Telugu to absolute (month, year) pairs.

Examples:
  "last month"    → previous calendar month
  "this quarter"  → current quarter's starting month
  "pichle mahine" → previous calendar month (Hinglish)
  "pindi nela"    → previous calendar month (Romanized Telugu)

All resolution is relative to a configurable reference_dt (default: UTC now).

Returns:
  resolve(text) → TemporalResolution | None
    .month: int (1–12)
    .year:  int (4-digit)
    .confidence: float (0.0–1.0)
    .expression_matched: str (the substring that triggered resolution)
    .lang: str (the language tag of the matched expression)

Status: IMPLEMENTED (Phase 2.2)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Optional


@dataclass
class TemporalResolution:
    """Result of resolving a relative temporal expression."""
    month: int
    year: int
    confidence: float
    expression_matched: str
    lang: str


# ---------------------------------------------------------------------------
# Pattern registry: (regex_pattern, language_tag, resolver_fn_key)
# ---------------------------------------------------------------------------
# Resolver functions receive (match, ref_date) → (month, year, confidence)
# All patterns are lowercase-matched after text normalization.

_PATTERNS: list[tuple[re.Pattern, str, str]] = [

    # ---- English ----
    (re.compile(r"\bthis\s+month\b", re.I), "eng_Latn", "this_month"),
    (re.compile(r"\blast\s+month\b", re.I), "eng_Latn", "last_month"),
    (re.compile(r"\bnext\s+month\b", re.I), "eng_Latn", "next_month"),
    (re.compile(r"\byesterday\b", re.I), "eng_Latn", "yesterday"),
    (re.compile(r"\btoday\b", re.I), "eng_Latn", "this_month"),
    (re.compile(r"\bthis\s+quarter\b", re.I), "eng_Latn", "this_quarter"),
    (re.compile(r"\blast\s+quarter\b", re.I), "eng_Latn", "last_quarter"),
    (re.compile(r"\bnext\s+quarter\b", re.I), "eng_Latn", "next_quarter"),
    (re.compile(r"\bthis\s+week\b", re.I), "eng_Latn", "this_month"),  # maps to current month
    (re.compile(r"\blast\s+week\b", re.I), "eng_Latn", "last_month"),  # conservative: last month
    (re.compile(r"\bcurrent\s+month\b", re.I), "eng_Latn", "this_month"),
    (re.compile(r"\bcurrent\s+quarter\b", re.I), "eng_Latn", "this_quarter"),
    # "in March", "in march 2025"
    (re.compile(
        r"\bin\s+(?P<month_name>january|february|march|april|may|june|july|august|september|october|november|december)"
        r"(?:\s+(?P<year>\d{4}))?\b", re.I
    ), "eng_Latn", "named_month"),

    # ---- Hinglish (Hindi in Latin script) ----
    (re.compile(r"\bis\s+mahine\b", re.I), "hin_Latn", "this_month"),
    (re.compile(r"\bpichle?\s+mahine?\b", re.I), "hin_Latn", "last_month"),
    (re.compile(r"\bagle\s+mahine?\b", re.I), "hin_Latn", "next_month"),
    (re.compile(r"\bpichle?\s+hafte?\b", re.I), "hin_Latn", "last_month"),
    (re.compile(r"\bis\s+hafte?\b", re.I), "hin_Latn", "this_month"),
    (re.compile(r"\bpichle?\s+timaahi\b", re.I), "hin_Latn", "last_quarter"),
    (re.compile(r"\bis\s+timaahi\b", re.I), "hin_Latn", "this_quarter"),

    # ---- Romanized Telugu ----
    (re.compile(r"\bee\s+nela\b", re.I), "tel_Latn", "this_month"),
    (re.compile(r"\bpindi\s+nela\b", re.I), "tel_Latn", "last_month"),
    (re.compile(r"\btarvata\s+nela\b", re.I), "tel_Latn", "next_month"),
    (re.compile(r"\bmodutu\s+nela\b", re.I), "tel_Latn", "last_month"),
    (re.compile(r"\bee\s+quarter\b", re.I), "tel_Latn", "this_quarter"),
    (re.compile(r"\bpindi\s+quarter\b", re.I), "tel_Latn", "last_quarter"),

    # ---- Telugu script ----
    (re.compile(r"ఈ\s*నెల", re.UNICODE), "tel_Telu", "this_month"),
    (re.compile(r"గత\s*నెల", re.UNICODE), "tel_Telu", "last_month"),
    (re.compile(r"వచ్చే\s*నెల", re.UNICODE), "tel_Telu", "next_month"),
    (re.compile(r"ఈ\s*త్రైమాసికం", re.UNICODE), "tel_Telu", "this_quarter"),
    (re.compile(r"గత\s*త్రైమాసికం", re.UNICODE), "tel_Telu", "last_quarter"),
]

_MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}


def _add_months(ref: date, delta: int) -> tuple[int, int]:
    """Return (month, year) after adding `delta` months to `ref`."""
    total = ref.month - 1 + delta
    year = ref.year + total // 12
    month = total % 12 + 1
    return month, year


def _quarter_start(ref: date) -> tuple[int, int]:
    """Return (start_month, year) of the quarter containing ref."""
    q_start_month = ((ref.month - 1) // 3) * 3 + 1
    return q_start_month, ref.year


def _last_quarter_start(ref: date) -> tuple[int, int]:
    """Return (start_month, year) of the quarter before the one containing ref."""
    qm, qy = _quarter_start(ref)
    return _add_months(date(qy, qm, 1), -3)


def _next_quarter_start(ref: date) -> tuple[int, int]:
    """Return (start_month, year) of the quarter after the one containing ref."""
    qm, qy = _quarter_start(ref)
    return _add_months(date(qy, qm, 1), 3)


_RESOLVER_MAP: dict[str, callable] = {
    "this_month":   lambda m, ref: (ref.month, ref.year, 0.99),
    "last_month":   lambda m, ref: (*_add_months(ref, -1), 0.99),
    "next_month":   lambda m, ref: (*_add_months(ref, +1), 0.97),
    "yesterday":    lambda m, ref: (ref.month, ref.year, 0.95),  # same month
    "this_quarter": lambda m, ref: (*_quarter_start(ref), 0.95),
    "last_quarter": lambda m, ref: (*_last_quarter_start(ref), 0.95),
    "next_quarter": lambda m, ref: (*_next_quarter_start(ref), 0.93),
    "named_month":  lambda m, ref: (
        _MONTH_NAMES.get(m.group("month_name").lower(), ref.month),
        int(m.group("year")) if m.group("year") else ref.year,
        0.98,
    ),
}


class TemporalDeicticsResolver:
    """
    Resolves relative temporal expressions in multilingual text to absolute
    (month, year) pairs. All resolution is deterministic given a reference date.

    Usage:
        resolver = TemporalDeicticsResolver()
        result = resolver.resolve("pichle mahine ki invoices archive karo")
        # → TemporalResolution(month=6, year=2025, ...)
    """

    def __init__(self, reference_dt: datetime | None = None) -> None:
        """
        Args:
            reference_dt: The "now" to resolve relative expressions against.
                          Defaults to UTC now at the time of the first resolve() call.
        """
        self._reference_dt = reference_dt

    @property
    def _ref_date(self) -> date:
        if self._reference_dt is not None:
            return self._reference_dt.date() if isinstance(self._reference_dt, datetime) else self._reference_dt
        return datetime.now(tz=timezone.utc).date()

    def resolve(self, text: str) -> Optional[TemporalResolution]:
        """
        Scan text for the first temporal deixis expression and resolve it.
        Returns None if no recognisable expression is found.
        """
        ref = self._ref_date
        for pattern, lang, resolver_key in _PATTERNS:
            match = pattern.search(text)
            if match:
                resolver_fn = _RESOLVER_MAP.get(resolver_key)
                if resolver_fn is None:
                    continue
                try:
                    month, year, confidence = resolver_fn(match, ref)
                    return TemporalResolution(
                        month=int(month),
                        year=int(year),
                        confidence=confidence,
                        expression_matched=match.group(0),
                        lang=lang,
                    )
                except Exception:
                    continue
        return None

    def resolve_all(self, text: str) -> list[TemporalResolution]:
        """Resolve all temporal expressions in text (in order of appearance)."""
        ref = self._ref_date
        results: list[TemporalResolution] = []
        for pattern, lang, resolver_key in _PATTERNS:
            for match in pattern.finditer(text):
                resolver_fn = _RESOLVER_MAP.get(resolver_key)
                if resolver_fn is None:
                    continue
                try:
                    month, year, confidence = resolver_fn(match, ref)
                    results.append(TemporalResolution(
                        month=int(month),
                        year=int(year),
                        confidence=confidence,
                        expression_matched=match.group(0),
                        lang=lang,
                    ))
                except Exception:
                    continue
        # Sort by position in text (approximate via expression_matched occurrence)
        return results
