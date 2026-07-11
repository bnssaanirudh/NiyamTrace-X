"""packages/bench/__init__.py — NiyamTrace-Bench public API."""
from packages.bench.runner import BenchmarkRunner
from packages.bench.report import BenchmarkReport

__all__ = ["BenchmarkRunner", "BenchmarkReport"]
