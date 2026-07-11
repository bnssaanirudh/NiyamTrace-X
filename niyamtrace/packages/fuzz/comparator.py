"""
packages/fuzz/comparator.py — Paired Trace Comparator (Week 6)

Compares two pipeline traces (from the same variant_group_id) and detects
cross-lingual gate decision divergence.

Divergence = two semantically equivalent requests produced different gate
verdicts (ALLOW vs BLOCK, or different BLOCK reason codes).

Status: IMPLEMENTED (Week 6)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DivergenceReport:
    """Report produced by comparing two traces."""
    variant_group_id: str
    canonical_language: str
    variant_language: str
    canonical_verdict: str
    variant_verdict: str
    diverged: bool
    divergence_type: str            # "verdict_flip" | "reason_code_diff" | "none"
    canonical_reason_code: str
    variant_reason_code: str
    canonical_trace_id: str
    variant_trace_id: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "variant_group_id": self.variant_group_id,
            "canonical_language": self.canonical_language,
            "variant_language": self.variant_language,
            "canonical_verdict": self.canonical_verdict,
            "variant_verdict": self.variant_verdict,
            "diverged": self.diverged,
            "divergence_type": self.divergence_type,
            "canonical_reason_code": self.canonical_reason_code,
            "variant_reason_code": self.variant_reason_code,
            "canonical_trace_id": self.canonical_trace_id,
            "variant_trace_id": self.variant_trace_id,
            "details": self.details,
        }


def _extract_gate_info(events: list) -> tuple[str, str]:
    """
    Extract (verdict, reason_code) from a list of TraceEvents.
    Returns ("UNKNOWN", "UNKNOWN") if gate_decision event not found.
    """
    for event in events:
        if event.event_type == "gate_decision":
            payload = event.payload
            return (
                payload.get("verdict", "UNKNOWN"),
                payload.get("reason_code", "UNKNOWN"),
            )
    return ("UNKNOWN", "UNKNOWN")


class TraceComparator:
    """
    Compares two PipelineResult objects from the same variant_group_id.

    Usage:
        comparator = TraceComparator()
        report = comparator.compare(
            canonical_result,
            variant_result,
            canonical_language="eng_Latn",
            variant_language="tel_Latn",
            variant_group_id="...",
        )
    """

    def compare(
        self,
        canonical_result: Any,   # PipelineResult
        variant_result: Any,     # PipelineResult
        canonical_language: str,
        variant_language: str,
        variant_group_id: str,
    ) -> DivergenceReport:
        """
        Compare gate decisions between canonical and variant pipeline results.

        Divergence types:
          "verdict_flip"     — ALLOW vs BLOCK (or ESCALATE), the most severe
          "reason_code_diff" — Same verdict class but different reason codes
          "none"             — No divergence

        Args:
            canonical_result:    PipelineResult for the canonical English input.
            variant_result:      PipelineResult for the variant (non-English) input.
            canonical_language:  Language tag for canonical (e.g. "eng_Latn").
            variant_language:    Language tag for variant (e.g. "tel_Latn").
            variant_group_id:    Shared group ID for this variant cluster.
        """
        can_verdict, can_reason = _extract_gate_info(canonical_result.events)
        var_verdict, var_reason = _extract_gate_info(variant_result.events)

        # Classify divergence
        if can_verdict != var_verdict:
            diverged = True
            divergence_type = "verdict_flip"
        elif can_reason != var_reason:
            diverged = True
            divergence_type = "reason_code_diff"
        else:
            diverged = False
            divergence_type = "none"

        return DivergenceReport(
            variant_group_id=variant_group_id,
            canonical_language=canonical_language,
            variant_language=variant_language,
            canonical_verdict=can_verdict,
            variant_verdict=var_verdict,
            diverged=diverged,
            divergence_type=divergence_type,
            canonical_reason_code=can_reason,
            variant_reason_code=var_reason,
            canonical_trace_id=canonical_result.trace_id,
            variant_trace_id=variant_result.trace_id,
            details={
                "canonical_task_id": canonical_result.task_id,
                "variant_task_id": variant_result.task_id,
            },
        )

    def compare_many(
        self,
        canonical_result: Any,
        variant_results: list[Any],
        canonical_language: str,
        variant_languages: list[str],
        variant_group_id: str,
    ) -> list[DivergenceReport]:
        """
        Compare canonical against multiple variants.
        Returns one DivergenceReport per variant.
        """
        reports: list[DivergenceReport] = []
        for variant_result, lang in zip(variant_results, variant_languages):
            report = self.compare(
                canonical_result=canonical_result,
                variant_result=variant_result,
                canonical_language=canonical_language,
                variant_language=lang,
                variant_group_id=variant_group_id,
            )
            reports.append(report)
        return reports
