"""
packages/fuzz — NiyamFuzz: metamorphic variant generator and comparator.

Status: IMPLEMENTED (Week 6)

Modules:
  transforms.py   — deterministic multilingual variant generator (EN → Hinglish, Telugu, etc.)
  equivalence.py  — semantic-preservation checker (protected span + token Jaccard)
  comparator.py   — paired trace comparator for cross-lingual gate divergence detection
  discover.py     — minimal-failing-variant discovery via incremental substitution search
"""

from packages.fuzz.comparator import DivergenceReport, TraceComparator
from packages.fuzz.discover import MinimalFailingVariant, MinimalVariantDiscoverer
from packages.fuzz.equivalence import EquivalenceResult, SemanticPreservationChecker
from packages.fuzz.transforms import VariantRequest, VariantTransformer

__all__ = [
    "DivergenceReport",
    "EquivalenceResult",
    "MinimalFailingVariant",
    "MinimalVariantDiscoverer",
    "SemanticPreservationChecker",
    "TraceComparator",
    "VariantRequest",
    "VariantTransformer",
]

