"""Data package for NiyamTrace.

This file makes the `data` directory a Python package so imports
like `from data.synthetic.erp import ...` work when running scripts
from the `niyamtrace` package root.
"""

__all__ = ["synthetic", "benchmark", "gold", "external"]
