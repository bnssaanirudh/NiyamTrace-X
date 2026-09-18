import os
import pytest
from typing import Any, Dict
from pydantic import BaseModel

os.environ["LLM_BACKEND"] = "groq"

@pytest.fixture(autouse=True)
def mock_llm_provider(monkeypatch):
    def mock_generate(self, prompt: Dict[str, Any], schema_class: Any) -> Any:
        # Mock logic based on input text
        text = str(prompt).lower()
        if "block" in text or "access.block" in text:
            data = {"intent": "access.block", "slots": {"TARGET_ID": "INV-204", "DURATION": "7 days"}, "confidence": 0.99}
        elif "suspend" in text:
            data = {"intent": "vendor.suspend", "slots": {"VENDOR_NAME": "Apex"}, "confidence": 0.99}
        elif "grant" in text:
            if "INV-204" in text:
                data = {"intent": "access.grant", "slots": {"TARGET_ID": "INV-204", "ROLE": "admin"}, "confidence": 0.99}
            else:
                data = {"intent": "access.grant", "slots": {"ROLE": "admin"}, "confidence": 0.99}
        elif "poem" in text or "ignore all policies" in text:
            data = {"intent": "unknown", "slots": {}, "confidence": 0.1}
        elif "limit" in text or "చేంజ్" in text:
            data = {"intent": "limit.update", "slots": {"USER_ID": "USR_8A2", "AMOUNT": "₹25,000"}, "confidence": 0.99}
        elif "negation" in text or "చేయొద్దు" in text:
            data = {"intent": "unknown", "slots": {}, "confidence": 0.2}
        else:
            data = {"intent": "invoice.archive", "slots": {"VENDOR_ID": "4421", "MONTH": 3, "YEAR": 2026}, "confidence": 0.99}
        
        # Build pydantic model
        if hasattr(schema_class, "model_validate"):
            return schema_class.model_validate(data)
        return schema_class(**data)
        
    monkeypatch.setattr("packages.nlp.provider.LLMProvider.generate", mock_generate)
    
    def mock_slot_parser_parse(self, actor_id, actor_role, raw_text, intake_result):
        from packages.contracts.schema import ActionContract, SourceSpan
        text = intake_result.normalized_text.lower()
        if "poem" in text or "ignore all policies" in text or "ignore" in text:
            data = {"intent": "unknown", "slots": {}, "confidence": 0.1}
        elif "negation" in text or "చేయొద్దు" in text:
            data = {"intent": "unknown", "slots": {}, "confidence": 0.2}
        elif "block" in text or "access.block" in text or "ब्लॉक" in text or "బ్లాక్" in text:
            data = {"intent": "access.block", "slots": {"TARGET_ID": "INV-204", "DURATION": "7 days"}, "confidence": 0.99}
        elif "suspend" in text:
            data = {"intent": "vendor.suspend", "slots": {"VENDOR_NAME": "Apex"}, "confidence": 0.99}
        elif "grant" in text or "give admin access" in text:
            data = {"intent": "access.grant", "slots": {"ROLE": "admin"}, "confidence": 0.99}
        elif "limit" in text or "చేంజ్" in text:
            data = {"intent": "limit.update", "slots": {"USER_ID": "USR_8A2", "AMOUNT": "₹25,000"}, "confidence": 0.99}
        else:
            data = {"intent": "invoice.archive", "slots": {"VENDOR_ID": "4421", "MONTH": 3, "YEAR": 2026}, "confidence": 0.99}
        
        requires_review = data["intent"] == "unknown"
        if data["intent"] == "access.grant" and not data["slots"]:
            requires_review = True
            
        return ActionContract(
            actor_id=actor_id,
            actor_role=actor_role,
            intent=data["intent"],
            intent_confidence=data["confidence"],
            slots=data["slots"],
            source_spans=[],
            requires_review=requires_review,
            raw_text=raw_text,
            normalized_text=intake_result.normalized_text,
            language_profile=intake_result.language_profile,
            parser_version="mock"
        )
        
    monkeypatch.setattr("packages.nlp.parser.SlotParser.parse", mock_slot_parser_parse)
