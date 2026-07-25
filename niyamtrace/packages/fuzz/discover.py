"""
packages/fuzz/discover.py — Minimal Failing Variant Discovery (Week 6)

Binary-searches for the minimal variant (smallest text transformation)
that causes a gate decision divergence vs. the canonical English result.

Algorithm:
  1. Start with the canonical English text (no divergence expected).
  2. Apply incremental word substitutions from the target language table.
  3. At each step, run the pipeline on the partially-translated variant.
  4. Return the first partial translation that triggers divergence.

If no variant triggers divergence (ideal case), returns None.

Status: IMPLEMENTED (Week 6)
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from typing import Any, Callable

from packages.fuzz.comparator import DivergenceReport, TraceComparator


@dataclass
class MinimalFailingVariant:
    """The minimal text variant that causes gate divergence."""
    text: str                          # the minimal failing text
    language: str                      # target language of this variant
    substitution_count: int            # how many words were substituted
    divergence_report: DivergenceReport


class MinimalVariantDiscoverer:
    """
    Discovers the minimal variant that causes a gate decision divergence.

    Takes a pipeline runner callable so it can be used in tests with
    injected DB connections.
    """

    def __init__(self, comparator: TraceComparator | None = None) -> None:
        self._comparator = comparator or TraceComparator()

    def discover(
        self,
        canonical_text: str,
        canonical_result: Any,             # PipelineResult for canonical English
        target_language: str,
        word_table: dict[str, str],        # word substitution table EN→target
        pipeline_runner: Callable[[str], Any],  # fn(text) → PipelineResult
        variant_group_id: str,
    ) -> MinimalFailingVariant | None:
        """
        Incrementally translate the canonical text, word by word, and check
        for divergence after each substitution.

        Args:
            canonical_text:    English reference text.
            canonical_result:  PipelineResult from running canonical_text.
            target_language:   Language tag for the target (e.g. "tel_Latn").
            word_table:        Dict mapping English words to target language.
            pipeline_runner:   Callable that runs the pipeline on a text string.
            variant_group_id:  Shared group ID for this variant cluster.

        Returns:
            MinimalFailingVariant if divergence found, else None.
        """
        # Tokenize canonical (split on word boundaries, keep non-word separators)
        tokens = re.split(r"(\W+)", canonical_text)
        current_tokens = list(tokens)

        substitution_count = 0
        for i, token in enumerate(tokens):
            token_lower = token.lower().strip()
            if token_lower in word_table and word_table[token_lower] != token_lower:
                # Apply this substitution
                current_tokens[i] = word_table[token_lower]
                substitution_count += 1
                candidate_text = "".join(current_tokens)

                # Run pipeline on this candidate
                candidate_result = pipeline_runner(candidate_text)

                # Compare with canonical
                report = self._comparator.compare(
                    canonical_result=canonical_result,
                    variant_result=candidate_result,
                    canonical_language="eng_Latn",
                    variant_language=target_language,
                    variant_group_id=variant_group_id,
                )

                if report.diverged:
                    return MinimalFailingVariant(
                        text=candidate_text,
                        language=target_language,
                        substitution_count=substitution_count,
                        divergence_report=report,
                    )

        # No divergence found across all substitutions
        return None


class BatchVariantDiscoverer:
    """
    Runs minimal variant discovery across an entire scenario dataset.
    """
    def __init__(self, discoverer: MinimalVariantDiscoverer | None = None) -> None:
        self.discoverer = discoverer or MinimalVariantDiscoverer()

    def discover_dataset(
        self,
        scenarios: list[dict[str, Any]],
        pipeline_runner: Callable[[str], Any],
    ) -> list[MinimalFailingVariant]:
        """
        Runs discovery on all canonical English ALLOW scenarios in the dataset.
        Tests across hin_Latn, tel_Latn, and tel_Telu.
        """
        from packages.fuzz.transforms import _TABLE_MAP

        results = []
        canonicals = [
            s for s in scenarios 
            if s.get("language") == "eng_Latn" 
            and "allow" in s.get("tags", [])
        ]

        for scenario in canonicals:
            canonical_text = scenario.get("raw_text", "")
            if not canonical_text:
                continue

            canonical_result = pipeline_runner(canonical_text)

            for target_language, word_table in _TABLE_MAP.items():
                variant_group_id = f"fuzz_{scenario.get('id', 'unknown')}_{target_language}"
                
                minimal_failing = self.discoverer.discover(
                    canonical_text=canonical_text,
                    canonical_result=canonical_result,
                    target_language=target_language,
                    word_table=word_table,
                    pipeline_runner=pipeline_runner,
                    variant_group_id=variant_group_id
                )
                
                if minimal_failing:
                    results.append(minimal_failing)

        return results
