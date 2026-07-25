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
from dotenv import load_dotenv

from packages.contracts.schema import ActionContract, SourceSpan
from packages.nlp.intake import IntakeResult

load_dotenv()

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
    def __init__(self, parser_version_suffix: str = "compiler-x"):
        self.backend = os.environ.get("LLM_BACKEND", "gemini").lower()
        self.parser_version = f"2.0.0-{parser_version_suffix}"
        
        if self.backend == "gemini":
            from google import genai
            from packages.secrets.manager import get_secrets_manager
            api_key = get_secrets_manager().get_optional("GEMINI_API_KEY")
            if not api_key:
                raise RuntimeError("GEMINI_API_KEY not found in secrets manager")
            self.client_gemini = genai.Client(api_key=api_key)
        elif self.backend == "groq":
            from groq import Groq
            from packages.secrets.manager import get_secrets_manager
            api_key = get_secrets_manager().get_optional("GROQ_API_KEY")
            if not api_key:
                raise RuntimeError("GROQ_API_KEY not found in secrets manager")
            self.client_groq = Groq(api_key=api_key)
            self.model_name = os.environ.get("GROQ_MODEL", "llama3-8b-8192")
        elif self.backend == "groq_instructor":
            # #2: Constrained-decoding baseline using instructor + Groq
            # This is the non-strawman "structured output" comparison baseline.
            # instructor wraps the Groq client and retries until Pydantic validates.
            import instructor
            from groq import Groq
            from packages.secrets.manager import get_secrets_manager
            api_key = get_secrets_manager().get_optional("GROQ_API_KEY")
            if not api_key:
                raise RuntimeError("GROQ_API_KEY not found in secrets manager")
            self.client_instructor = instructor.from_groq(
                Groq(api_key=api_key), mode=instructor.Mode.JSON
            )
            self.model_name = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        else:
            from openai import OpenAI
            self.model_name = os.environ.get("LOCAL_LLM_MODEL", "qwen2.5:7b")
            # Point to Ollama default endpoint
            self.client_openai = OpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama"
            )

    def _extract_candidate(self, normalized_text: str, repair_hint: str | None = None) -> CandidateIntent:
        """Stage 1: LLM Extractor. If repair_hint is provided, it is a bounded repair pass (#23)."""
        if "mock" in self.parser_version:
            return CandidateIntent(
                intent="invoice.archive",
                slots=CandidateSlots(VENDOR_ID=4421, MONTH=3, YEAR=2025),
                confidence=0.99
            )

        repair_instruction = f"""

        IMPORTANT CORRECTION: A previous extraction attempt failed with this error: "{repair_hint}".
        Please re-read the text carefully and fix this specific issue.
        """ if repair_hint else ""

        prompt = f"""Analyze the following text and extract the user's intent and key slots.
        Map month names to their integer value (1-12). All numeric IDs must be integers.
        Set confidence to reflect how certain you are (0.0 = not sure, 1.0 = completely certain).
        If a slot is missing or ambiguous, leave it as null — do NOT guess (except for the year, assume 2025 if missing).

        Text: {normalized_text}
        {repair_instruction}
        Available intents:
        - invoice.archive
        - access.grant
        - access.block
        - limit.update
        - vendor.suspend
        - unknown
        """
        if self.backend == "gemini":
            from google.genai import types
            response = self.client_gemini.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=CandidateIntent,
                    temperature=0.0
                ),
            )
            return response.parsed
        elif self.backend == "groq":
            import json
            schema_str = CandidateIntent.model_json_schema()
            completion = self.client_groq.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system", 
                        "content": f"You are a precise data extraction system. You must output valid JSON matching the following schema EXACTLY. Do not wrap it in markdown.\n{json.dumps(schema_str)}"
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            raw_json = completion.choices[0].message.content
            return CandidateIntent.model_validate_json(raw_json)
        elif self.backend == "groq_instructor":
            # #2: instructor constrains the Groq model with automatic Pydantic retry
            return self.client_instructor.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a precise data extraction system. Assume the current year is 2025 unless explicitly specified."},
                    {"role": "user", "content": prompt},
                ],
                response_model=CandidateIntent,
                temperature=0.0,
                max_retries=3,
            )
        else:
            completion = self.client_openai.beta.chat.completions.parse(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a precise data extraction system."},
                    {"role": "user", "content": prompt}
                ],
                response_format=CandidateIntent,
                temperature=0.0
            )
            return completion.choices[0].message.parsed

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
        """Stage 3: Entity Linker (Mock resolution) & Reverse Clarification trigger"""
        slots = candidate.slots
        
        if candidate.intent == "invoice.archive":
            if not slots.VENDOR_ID:
                return False, "EntityLinker", "Missing VENDOR_ID for archive action", "Which vendor's invoices should I archive? I need a specific VENDOR_ID."
            if not slots.MONTH or not slots.YEAR:
                return False, "EntityLinker", "Missing temporal scope for archive action", "For which month and year should I archive these invoices?"
                
            # Mock DB check
            if str(slots.VENDOR_ID) == "9999":
                return False, "EntityLinker", f"Vendor {slots.VENDOR_ID} does not exist in the system.", None
                
        elif candidate.intent == "access.grant":
            if not slots.TARGET_ID:
                return False, "EntityLinker", "Missing TARGET_ID for grant action", "Who should I grant access to?"
            if not slots.ROLE:
                return False, "EntityLinker", "Missing ROLE for grant action", "What role should I assign?"
                
        return True, None, None, None

    # -----------------------------------------------------------------------
    # #22: Low-confidence slot check
    # -----------------------------------------------------------------------
    _CONFIDENCE_THRESHOLD = 0.5  # slots extracted below this trigger CLARIFY

    def compile(self, actor_id: str, actor_role: str, raw_text: str, intake_result: IntakeResult) -> CompilerResult:
        repair_attempted = False
        try:
            # Stage 1: LLM Extractor
            candidate = self._extract_candidate(intake_result.normalized_text)

            # #22: Low-confidence guard — if the model itself says it is unsure, clarify.
            if candidate.confidence < self._CONFIDENCE_THRESHOLD:
                return CompilerResult(
                    contract=None,
                    error_stage="LLMExtractor",
                    error_detail=f"Extraction confidence too low: {candidate.confidence:.2f}",
                    clarification_prompt=(
                        "I wasn't confident about what you meant. Could you rephrase with "
                        "the vendor ID, the month, and the year clearly specified?"
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
                resolver = TemporalDeicticsResolver()
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
