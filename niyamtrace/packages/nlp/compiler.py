"""
packages/nlp/compiler.py — NiyamCompiler (NiyamTrace-X Upgrade)

Pipeline:
  LLM Extractor → Type Checker → Entity Linker → Repair Layer → ActionContract

Upgrades (#22, #23):
  - Confidence scoring: low-confidence slots (<0.5) trigger CLARIFY instead of silent failure.
  - Repair layer: a bounded 1-shot re-extraction attempt with an augmented prompt before
    defaulting to BLOCK, reducing over-blocking on recoverable errors.
"""

from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel
from datetime import datetime, timezone

from packages.contracts.schema import ActionContract, SourceSpan
from packages.nlp.intake import IntakeResult
from packages.nlp.provider import LLMProvider
from packages.nlp.prompts import PromptRegistry
from packages.nlp.entity_repository import EntityRepository
from packages.nlp.confidence import ConfidenceCalibrator
from packages.config import get_settings

class CandidateSlots(BaseModel):
    VENDOR_ID: Any = None
    MONTH: Any = None
    YEAR: Any = None
    AMOUNT: Any = None
    DURATION: Any = None
    ROLE: Any = None
    TARGET_ID: Any = None
    VENDOR_NAME: Any = None
    USER_ID: Any = None

class CandidateIntent(BaseModel):
    intent: str
    slots: CandidateSlots
    confidence: float

class CompilerResult(BaseModel):
    contract: ActionContract | None
    error_stage: str | None = None
    error_detail: str | None = None
    clarification_prompt: str | None = None
    # #22: extraction confidence, so callers can log/display it
    extraction_confidence: float | None = None
    # #23: whether repair layer was invoked
    repair_attempted: bool = False


class NiyamCompiler:
    def __init__(self, parser_version_suffix: str = "compiler-x", tenant_id: str = "default"):
        settings = get_settings()
        self.backend = settings.llm_backend
        self.parser_version = f"2.0.0-{parser_version_suffix}"
        
        self.provider = LLMProvider(backend=self.backend)
        self.entity_repo = EntityRepository(tenant_id=tenant_id)

    def _extract_candidate(self, normalized_text: str, reference_dt: datetime, repair_hint: str | None = None) -> CandidateIntent:
        """Stage 1: LLM Extractor."""
        if "mock" in self.parser_version:
            return CandidateIntent(
                intent="invoice.archive",
                slots=CandidateSlots(VENDOR_ID="4421", MONTH=3, YEAR=reference_dt.year),
                confidence=0.99
            )

        prompt = PromptRegistry.get_extraction_prompt(
            normalized_text=normalized_text, 
            current_year=reference_dt.year,
            repair_hint=repair_hint
        )
        return self.provider.generate(prompt, CandidateIntent)

    def _type_check(self, candidate: CandidateIntent) -> tuple[bool, str | None, str | None]:
        """Stage 2: Type Checker (Deterministic validation without crashing)"""
        slots = candidate.slots
        
        # Check MONTH
        if slots.MONTH is not None:
            try:
                m = int(slots.MONTH)
                if m < 1 or m > 12:
                    return False, "TypeChecker", f"MONTH must be between 1 and 12, got {m}"
                slots.MONTH = m
            except (ValueError, TypeError):
                return False, "TypeChecker", f"MONTH must be an integer, got '{slots.MONTH}'"
                
        # Check YEAR
        if slots.YEAR is not None:
            try:
                slots.YEAR = int(slots.YEAR)
            except (ValueError, TypeError):
                return False, "TypeChecker", f"YEAR must be an integer, got '{slots.YEAR}'"
                
        # Check AMOUNT
        if slots.AMOUNT is not None:
            try:
                slots.AMOUNT = float(slots.AMOUNT)
            except (ValueError, TypeError):
                return False, "TypeChecker", f"AMOUNT must be a float, got '{slots.AMOUNT}'"
                
        return True, None, None

    def _entity_link(self, candidate: CandidateIntent) -> tuple[bool, str | None, str | None, str | None]:
        """Stage 3: Entity Linker using EntityRepository"""
        slots = candidate.slots
        
        if candidate.intent == "invoice.archive":
            if not slots.VENDOR_ID:
                return False, "EntityLinker", "Missing VENDOR_ID for archive action", "Which vendor's invoices should I archive? I need a specific VENDOR_ID."
            if not slots.MONTH or not slots.YEAR:
                return False, "EntityLinker", "Missing temporal scope for archive action", "For which month and year should I archive these invoices?"
                
            if not self.entity_repo.check_vendor_exists(slots.VENDOR_ID):
                return False, "EntityLinker", f"Vendor {slots.VENDOR_ID} does not exist in the system.", None
                
        elif candidate.intent == "access.grant":
            if not slots.TARGET_ID:
                return False, "EntityLinker", "Missing TARGET_ID for grant action", "Who should I grant access to?"
            if not slots.ROLE:
                return False, "EntityLinker", "Missing ROLE for grant action", "What role should I assign?"
                
        return True, None, None, None

    def compile(self, actor_id: str, actor_role: str, raw_text: str, intake_result: IntakeResult, reference_dt: datetime | None = None) -> CompilerResult:
        repair_attempted = False
        if reference_dt is None:
            reference_dt = datetime.now(timezone.utc)
        
        try:
            # Stage 1: LLM Extractor
            candidate = self._extract_candidate(intake_result.normalized_text, reference_dt)

            # #22: Low-confidence guard — if the model itself says it is unsure, clarify.
            if not ConfidenceCalibrator.is_confident(candidate.confidence, candidate.intent):
                return CompilerResult(
                    contract=None,
                    error_stage="LLMExtractor",
                    error_detail=f"Extraction confidence too low: {candidate.confidence:.2f} for intent {candidate.intent}",
                    clarification_prompt=(
                        "I wasn't confident about what you meant. Could you rephrase with "
                        "the details clearly specified?"
                    ),
                    extraction_confidence=candidate.confidence,
                )

            # Stage 2: Type Checker
            ok, err_stage, err_detail = self._type_check(candidate)
            if not ok:
                # #23: Repair layer — bounded 1-shot re-extraction before failing
                try:
                    repaired = self._extract_candidate(
                        intake_result.normalized_text,
                        reference_dt,
                        repair_hint=err_detail
                    )
                    ok2, err_stage2, err_detail2 = self._type_check(repaired)
                    if ok2:
                        candidate = repaired
                        repair_attempted = True
                        ok, err_stage, err_detail = True, None, None
                    else:
                        err_stage, err_detail = err_stage2, err_detail2
                except Exception:
                    pass  # repair failed, fall through to original error

            if not ok:
                return CompilerResult(
                    contract=None,
                    error_stage=err_stage,
                    error_detail=err_detail,
                    repair_attempted=repair_attempted,
                    extraction_confidence=candidate.confidence,
                )

            # Stage 2.5: Temporal Deixis Resolution
            # If the LLM failed to extract a hard month/year (or they were relative like "last month"),
            # attempt to resolve it deterministically from the normalized text.
            if candidate.intent == "invoice.archive" and (candidate.slots.MONTH is None or candidate.slots.YEAR is None):
                from packages.nlp.temporal import TemporalDeicticsResolver
                resolver = TemporalDeicticsResolver(reference_dt=reference_dt)
                temporal_res = resolver.resolve(intake_result.normalized_text)
                if temporal_res:
                    candidate.slots.MONTH = candidate.slots.MONTH or temporal_res.month
                    candidate.slots.YEAR = candidate.slots.YEAR or temporal_res.year

            # Stage 3: Entity Linker
            ok, err_stage, err_detail, clarify_prompt = self._entity_link(candidate)
            if not ok:
                return CompilerResult(
                    contract=None,
                    error_stage=err_stage,
                    error_detail=err_detail,
                    clarification_prompt=clarify_prompt,
                    repair_attempted=repair_attempted,
                    extraction_confidence=candidate.confidence,
                )

            # Success: Build final ActionContract
            contract = ActionContract(
                actor_id=actor_id,
                actor_role=actor_role,
                intent=candidate.intent,
                intent_confidence=candidate.confidence,
                slots=candidate.slots.model_dump(exclude_none=True),
                raw_text=raw_text,
                normalized_text=intake_result.normalized_text,
                language_profile=intake_result.language_profile,
                parser_version=self.parser_version
            )
            return CompilerResult(
                contract=contract,
                repair_attempted=repair_attempted,
                extraction_confidence=candidate.confidence,
            )

        except Exception as e:
            return CompilerResult(
                contract=None,
                error_stage="LLMExtractor",
                error_detail=f"Failed to extract candidate: {e}",
            )
