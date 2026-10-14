import re
from typing import Any, ClassVar


class PIIRedactor:
    """
    Scans trace payloads and redacts sensitive PII information before saving.
    """
    
    # Simple regex for email and phone. For production, more robust patterns
    # or NLP-based NER would be used.
    EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
    PHONE_REGEX = re.compile(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b')
    
    # Fields that should just be completely redacted if they appear in payload
    SENSITIVE_FIELDS: ClassVar[set[str]] = {"ssn", "social_security", "credit_card", "password", "secret"}
    
    @classmethod
    def redact_text(cls, text: str) -> str:
        """Redacts emails and phone numbers from a string."""
        if not isinstance(text, str):
            return text
        text = cls.EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
        text = cls.PHONE_REGEX.sub("[REDACTED_PHONE]", text)
        return text

    @classmethod
    def redact_payload(cls, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Recursively scans a payload dictionary and redacts sensitive information.
        """
        redacted_payload = {}
        for k, v in payload.items():
            if any(sensitive in k.lower() for sensitive in cls.SENSITIVE_FIELDS):
                redacted_payload[k] = "[REDACTED_FIELD]"
            elif isinstance(v, str):
                redacted_payload[k] = cls.redact_text(v)
            elif isinstance(v, dict):
                redacted_payload[k] = cls.redact_payload(v)
            elif isinstance(v, list):
                redacted_payload[k] = [
                    cls.redact_payload(item) if isinstance(item, dict) else (cls.redact_text(item) if isinstance(item, str) else item)
                    for item in v
                ]
            else:
                redacted_payload[k] = v
                
        return redacted_payload
