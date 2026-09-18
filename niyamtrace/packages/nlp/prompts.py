import hashlib
from typing import Dict, Any

class PromptRegistry:
    @staticmethod
    def get_extraction_prompt(normalized_text: str, current_year: int, repair_hint: str = None) -> Dict[str, Any]:
        repair_instruction = f"""
        IMPORTANT CORRECTION: A previous extraction attempt failed with this error: "{repair_hint}".
        Please re-read the text carefully and fix this specific issue.
        """ if repair_hint else ""

        prompt_text = f"""Analyze the following text and extract the user's intent and key slots.
        Map month names to their integer value (1-12). All numeric IDs must be integers.
        Set confidence to reflect how certain you are (0.0 = not sure, 1.0 = completely certain).
        If a slot is missing or ambiguous, leave it as null — do NOT guess (except for the year, assume {current_year} if missing).

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
        
        system_instruction = f"You are a precise data extraction system. Assume the current year is {current_year} unless explicitly specified."

        # Generate a version hash for tracing
        prompt_hash = hashlib.sha256((system_instruction + prompt_text).encode('utf-8')).hexdigest()[:8]

        return {
            "system": system_instruction,
            "user": prompt_text,
            "version_hash": prompt_hash
        }
