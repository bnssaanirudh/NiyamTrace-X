"""
packages/nlp/intake.py — Multilingual Intake Orchestrator (NiyamParse Week 3)

High-level entry point for the NiyamParse multilingual intake pipeline.
Orchestrates:
  1. LanguageIdentifier  — script + language + code-switch spans
  2. TextNormalizer      — canonical surface form for downstream parsing

Returns an IntakeResult that feeds directly into the pipeline's
contract_extracted event and the trace envelope's language_profile.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from packages.nlp.language_id import LanguageIdentifier
from packages.nlp.normalizer import TextNormalizer


@dataclass
class IntakeResult:
    """
    Output of the full multilingual intake pass for one utterance.
    """
    language_profile: dict[str, Any]
    normalized_text: str
    raw_text: str
    normalization: dict[str, Any]

    @property
    def primary_lang(self) -> str:
        mix = self.language_profile.get("primary_language_mix", ["eng_Latn"])
        return mix[0] if mix else "eng_Latn"

    @property
    def is_code_switched(self) -> bool:
        return len(self.language_profile.get("primary_language_mix", [])) > 1


class MultilingualIntake:
    """
    NiyamParse Week 3 intake orchestrator.
    """

    def __init__(self, model_dir: str | None = None) -> None:
        self._lang_id = LanguageIdentifier(model_dir)
        self._normalizer = TextNormalizer(model_dir)

    def process(self, raw_text: str) -> IntakeResult:
        """
        Run the full multilingual intake pipeline on one utterance.
        """
        # Step 1: Language identification
        lang_profile = self._lang_id.identify(raw_text)

        # Step 2: Normalization
        norm_result = self._normalizer.normalize(raw_text)

        return IntakeResult(
            language_profile=lang_profile,
            normalized_text=norm_result.get("normalized_text", raw_text),
            raw_text=raw_text,
            normalization=norm_result,
        )
