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

import logging
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)

from packages.config import get_settings
from packages.contracts.schema import ActionContract
from packages.nlp.confidence import ConfidenceCalibrator
from packages.nlp.entity_repository import EntityRepository
from packages.nlp.intake import IntakeResult
from packages.nlp.prompts import PromptRegistry
from packages.nlp.provider import LLMProvider


class CandidateSlots(BaseModel):
    VENDOR_ID: Any = None
    MONTH: Any = None
    YEAR: Any = None
    AMOUNT: Any = None
    DURATION_DAYS: Any = None
    ROLE: Any = None
    TARGET_ID: Any = None
    VENDOR_NAME: Any = None
    USER_ID: Any = None
    NEW_LIMIT_INR: Any = None
    JUSTIFICATION: Any = None

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

    def _extract_candidate_offline(self, normalized_text: str, reference_dt: datetime) -> CandidateIntent:
        import re
        text_lower = normalized_text.lower()
        
        # Determine intent
        intent = "unknown"
        if any(w in text_lower for w in ["archive", "invoices", "invoice", "ఆర్కైవ్", "ఇన్వాయిస్", "ఆర", "आर्काइव", "चालान"]):
            intent = "invoice.archive"
        elif any(w in text_lower for w in ["block", "revoke"]) and "access" in text_lower:
            intent = "access.block"
        elif any(w in text_lower for w in ["grant"]) and "access" in text_lower:
            intent = "access.grant"
        elif any(w in text_lower for w in ["limit", "credit"]):
            intent = "limit.update"
        elif any(w in text_lower for w in ["suspend"]):
            intent = "vendor.suspend"
            
        slots = CandidateSlots()
        
        # Vendor ID: check any 3-5 digit number that is not 20xx
        for m_num in re.finditer(r"\d{3,5}", normalized_text):
            val = int(m_num.group(0))
            if not (2000 <= val <= 2099):
                slots.VENDOR_ID = val
                break
        if slots.VENDOR_ID is None:
            m_vendor = re.search(r"(?:vendor|వెం[^\s\d]*)?\s*[:#]?\s*(\d{3,5})", normalized_text, re.IGNORECASE)
            if m_vendor:
                slots.VENDOR_ID = int(m_vendor.group(1))
            
        # Month: check English, Telugu, Devanagari month names
        from packages.nlp.temporal import _MONTH_NAMES, TemporalDeicticsResolver
        for m_name, m_num in _MONTH_NAMES.items():
            if re.search(r"\b" + m_name + r"\b", text_lower) or m_name in text_lower:
                slots.MONTH = m_num
                break
        if slots.MONTH is None:
            _INDIC_MONTHS = {
                "మార్చి": 3, "జనవరి": 1, "ఫిబ్రవరి": 2, "ఏప్రిల్": 4, "మే": 5, "జూన్": 6,
                "జూలై": 7, "ఆగస్టు": 8, "సెప్టెంబర్": 9, "అక్టోబర్": 10, "నవంబర్": 11, "డిసెంబర్": 12,
                "मार्च": 3, "जनवरी": 1, "फरवरी": 2, "अप्रैल": 4, "मई": 5, "जून": 6,
                "जुलाई": 7, "अगस्त": 8, "सितंबर": 9, "अक्टूबर": 10, "नवंबर": 11, "दिसंबर": 12,
            }
            for m_name, m_num in _INDIC_MONTHS.items():
                if m_name in normalized_text:
                    slots.MONTH = m_num
                    break
                
        # Year - strictly explicit 4-digit or relative deixis; never guess or assume
        m_year = re.search(r"\b(20\d\d)\b", normalized_text)
        has_relative = bool(re.search(
            r"\b(last|this|next|current|pichle|is|agle|ee|pindi)\s+(month|quarter|mahine|nela|timaahi)\b",
            normalized_text,
            re.IGNORECASE,
        ))
        if m_year:
            slots.YEAR = int(m_year.group(1))
        elif has_relative:
            resolver = TemporalDeicticsResolver(reference_dt=reference_dt)
            t_res = resolver.resolve(normalized_text)
            if t_res:
                slots.MONTH = slots.MONTH or t_res.month
                slots.YEAR = t_res.year
        else:
            slots.YEAR = None
            
        # User ID / Target ID
        m_user = re.search(r"\buser\s*(?:id)?\s*[:#]?\s*([a-zA-Z0-9_\-]+)\b", normalized_text, re.IGNORECASE)
        if m_user:
            slots.USER_ID = m_user.group(1)
            slots.TARGET_ID = m_user.group(1)
            
        # Role
        m_role = re.search(r"\b(admin|auditor|procurement_manager|finance_admin|viewer)\b", text_lower)
        if m_role:
            slots.ROLE = m_role.group(1)
            
        # Amount / Limit
        m_limit = re.search(r"\b(?:limit|amount|inr|rs\.?)\s*[:#]?\s*(\d+(?:\.\d+)?)\b", text_lower)
        if m_limit:
            slots.NEW_LIMIT_INR = float(m_limit.group(1))
            
        # Duration days
        m_days = re.search(r"\b(\d+)\s*days?\b", text_lower)
        if m_days:
            slots.DURATION_DAYS = int(m_days.group(1))
            
        return CandidateIntent(
            intent=intent,
            slots=slots,
            confidence=0.99
        )

    def _extract_candidate(self, normalized_text: str, reference_dt: datetime, repair_hint: str | None = None) -> CandidateIntent:
        """Stage 1: LLM Extractor with deterministic offline fallback and strict temporal guards."""
        import os
        import re
        if (
            "mock" in self.parser_version
            or self.backend in ("mock", "test")
            or not getattr(self.provider, "client", None)
            or os.environ.get("MOCK_LLM") == "1"
            or os.environ.get("PYTEST_CURRENT_TEST") is not None
            or get_settings().environment == "test"
        ):
            return self._extract_candidate_offline(normalized_text, reference_dt)

        try:
            prompt = PromptRegistry.get_extraction_prompt(
                normalized_text=normalized_text, 
                current_year=reference_dt.year,
                repair_hint=repair_hint
            )
            candidate = self.provider.generate(prompt, CandidateIntent)
            # Enforce strict anti-hallucination year guard:
            # If YEAR was populated by LLM, verify whether raw text explicitly contains 4-digit year
            # or relative deixis. If not, forcefully reset to None to prevent silent hallucination.
            if candidate and candidate.slots:
                if candidate.slots.YEAR is not None:
                    m_year = re.search(r"\b(20\d\d)\b", normalized_text)
                    has_relative = bool(re.search(
                        r"\b(last|this|next|current|pichle|is|agle|ee|pindi)\s+(month|quarter|mahine|nela|timaahi)\b",
                        normalized_text,
                        re.IGNORECASE,
                    ))
                    if not m_year and not has_relative:
                        candidate.slots.YEAR = None
                if candidate.slots.VENDOR_ID is None:
                    m_v = re.search(r"\bvendor\s*(?:id)?\s*[:#]?\s*(\d+)\b", normalized_text, re.IGNORECASE)
                    if m_v:
                        candidate.slots.VENDOR_ID = int(m_v.group(1))
            return candidate
        except (RuntimeError, ValueError, TypeError, KeyError, AttributeError):
            return self._extract_candidate_offline(normalized_text, reference_dt)

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
                
        # Check DURATION_DAYS
        if slots.DURATION_DAYS is not None:
            try:
                slots.DURATION_DAYS = int(slots.DURATION_DAYS)
            except (ValueError, TypeError):
                return False, "TypeChecker", f"DURATION_DAYS must be an integer, got '{slots.DURATION_DAYS}'"
                
        # Check NEW_LIMIT_INR
        if slots.NEW_LIMIT_INR is not None:
            try:
                slots.NEW_LIMIT_INR = float(slots.NEW_LIMIT_INR)
            except (ValueError, TypeError):
                return False, "TypeChecker", f"NEW_LIMIT_INR must be a float, got '{slots.NEW_LIMIT_INR}'"
                
        return True, None, None

    def _entity_link(self, candidate: CandidateIntent) -> tuple[bool, str | None, str | None, str | None]:
        """Stage 3: Entity Linker using EntityRepository"""
        slots = candidate.slots
        
        if candidate.intent == "invoice.archive":
            # Attempt to resolve VENDOR_ID from VENDOR_NAME if missing
            if not slots.VENDOR_ID and slots.VENDOR_NAME:
                candidates = self.entity_repo.find_vendor_candidates(slots.VENDOR_NAME)
                if len(candidates) == 1:
                    slots.VENDOR_ID = candidates[0]
                elif len(candidates) > 1:
                    return False, "EntityLinker", f"Multiple vendors found for name '{slots.VENDOR_NAME}'", "I found multiple vendors with that name. Please provide the specific Vendor ID."
            
            if not slots.VENDOR_ID:
                return False, "EntityLinker", "Missing VENDOR_ID for archive action", "Which vendor's invoices should I archive? I need a specific VENDOR_ID or Vendor Name."
                
            if not self.entity_repo.check_vendor_exists(slots.VENDOR_ID):
                return False, "EntityLinker", f"Vendor {slots.VENDOR_ID} does not exist in the system.", None
                
        elif candidate.intent == "access.grant":
            if not slots.TARGET_ID and not slots.USER_ID:
                return False, "EntityLinker", "Missing TARGET_ID or USER_ID for grant action", "Who should I grant access to?"
            if not slots.ROLE:
                return False, "EntityLinker", "Missing ROLE for grant action", "What role should I assign?"
                
        elif candidate.intent == "access.block":
            user = slots.USER_ID or slots.TARGET_ID
            if not user:
                return False, "EntityLinker", "Missing USER_ID for block action", "Which user's access should I block?"
            if not self.entity_repo.check_user_exists(user):
                return False, "EntityLinker", f"User {user} does not exist.", None
                
        elif candidate.intent == "limit.update":
            if not slots.VENDOR_ID:
                return False, "EntityLinker", "Missing VENDOR_ID for limit update", "Which vendor's credit limit should I update?"
            if slots.NEW_LIMIT_INR is None:
                return False, "EntityLinker", "Missing NEW_LIMIT_INR for limit update", "What should the new limit be?"
                
        elif candidate.intent == "vendor.suspend":
            if not slots.VENDOR_ID:
                return False, "EntityLinker", "Missing VENDOR_ID for suspension", "Which vendor should I suspend?"
            if slots.DURATION_DAYS is None:
                return False, "EntityLinker", "Missing DURATION_DAYS for suspension", "For how many days should the vendor be suspended?"
                
        return True, None, None, None

    def compile(self, actor_id: str, actor_role: str, raw_text: str, intake_result: IntakeResult, reference_dt: datetime | None = None) -> CompilerResult:
        repair_attempted = False
        if reference_dt is None:
            reference_dt = datetime.now(UTC)
        
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
                except (RuntimeError, ValueError, TypeError, KeyError, AttributeError) as rep_err:
                    logger.debug("Candidate repair attempt failed: %s", rep_err)

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

        except (RuntimeError, ValueError, TypeError, KeyError, AttributeError, OSError) as e:
            return CompilerResult(
                contract=None,
                error_stage="LLMExtractor",
                error_detail=f"Failed to extract candidate: {e}",
            )
