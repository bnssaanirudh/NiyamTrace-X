"""
packages/nlp/llm_client.py — LLM Client Abstraction for NiyamParse

Provides a consistent interface for generating JSON from an LLM.
Includes a real OllamaClient for local execution and a MockLLMClient for tests.
"""

from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate_json(self, prompt: str) -> dict[str, Any]:
        """Generate a JSON response from the LLM based on the prompt."""
        pass


class OllamaClient(LLMClient):
    """Real client for local Ollama."""

    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def generate_json(self, prompt: str) -> dict[str, Any]:
        """Call Ollama API and return parsed JSON."""
        url = f"{self.base_url}/api/generate"
        data = {
            "model": self.model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            # Use deterministic settings for predictable slot parsing
            "options": {
                "temperature": 0.0,
                "top_p": 0.9,
            }
        }
        
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode("utf-8"), 
            headers={"Content-Type": "application/json"}
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                response_data = json.loads(response.read().decode("utf-8"))
                response_text = response_data.get("response", "{}")
                return json.loads(response_text)
        except urllib.error.URLError as e:
            logger.error(f"Ollama connection error: {e}. Is Ollama running on {self.base_url}?")
            raise RuntimeError(f"Failed to connect to Ollama: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Ollama returned invalid JSON: {e}")
            raise RuntimeError(f"Invalid JSON from LLM: {e}")


class MockLLMClient(LLMClient):
    """Mock client for testing without a real LLM."""
    
    def __init__(self):
        # We can map specific normalized text snippets to hardcoded JSON responses
        # for our canonical scenarios.
        self.canned_responses: dict[str, dict[str, Any]] = {}
        
    def add_canned_response(self, trigger_text: str, response: dict[str, Any]):
        self.canned_responses[trigger_text.lower()] = response
        
    def generate_json(self, prompt: str) -> dict[str, Any]:
        # Simple lookup: if any trigger text is in the prompt, return its response
        prompt_lower = prompt.lower()
        for trigger, response in self.canned_responses.items():
            if trigger in prompt_lower:
                return response
                
        # Default fallback (should be rare in tests if mocked correctly)
        return {
            "action": "UNKNOWN",
            "object_type": "unknown",
            "entity_ids": [],
            "allowed_attributes": [],
            "selector_predicate": "1=1",
            "temporal_scope": {"inferred": True},
            "purpose": "Mock response",
            "ambiguity": True,
            "confidence": 0.0
        }
