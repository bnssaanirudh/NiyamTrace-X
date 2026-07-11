"""
packages/fuzz — NiyamFuzz: metamorphic variant generator and comparator.

Status: IMPLEMENTED (Week 6)

Modules:
  transforms.py   — deterministic multilingual variant generator (EN → Hinglish, Telugu, etc.)
  equivalence.py  — semantic-preservation checker (protected span + token Jaccard)
  comparator.py   — paired trace comparator for cross-lingual gate divergence detection
  discover.py     — minimal-failing-variant discovery via incremental substitution search
"""

from packages.fuzz.transforms import VariantTransformer, VariantRequest
from packages.fuzz.equivalence import SemanticPreservationChecker, EquivalenceResult
from packages.fuzz.comparator import TraceComparator, DivergenceReport
from packages.fuzz.discover import MinimalVariantDiscoverer, MinimalFailingVariant

__all__ = [
    "VariantTransformer",
    "VariantRequest",
    "SemanticPreservationChecker",
    "EquivalenceResult",
    "TraceComparator",
    "DivergenceReport",
    "MinimalVariantDiscoverer",
    "MinimalFailingVariant",
]

