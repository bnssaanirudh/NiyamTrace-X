"""
packages/nlp — NiyamParse multilingual NLP intake module.

Week 3 (IMPLEMENTED):
  language_id.py   — language/script detection, code-switch span detection
  normalizer.py    — romanization-aware normalization, raw-to-canonical storage
  intake.py        — MultilingualIntake orchestrator

Week 4 (STUB):
  parser.py        — NLP slot-parser (XLM-R or local LLM), entity/time/scope resolution
  entity_linker.py — entity linking for vendor IDs, document IDs, etc.
"""

from packages.nlp.intake import IntakeResult, MultilingualIntake
from packages.nlp.language_id import LanguageIdentifier
from packages.nlp.llm_client import LLMClient, MockLLMClient, OllamaClient
from packages.nlp.normalizer import TextNormalizer
from packages.nlp.parser import SlotParser

__all__ = [
    "MultilingualIntake",
    "IntakeResult",
    "LanguageIdentifier",
    "TextNormalizer",
    "LLMClient",
    "OllamaClient",
    "MockLLMClient",
    "SlotParser",
]
