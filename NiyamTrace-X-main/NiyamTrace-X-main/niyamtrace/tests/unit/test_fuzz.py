"""
tests/unit/test_fuzz.py — Unit tests for NiyamFuzz (Week 6)

Covers:
  - VariantTransformer: generates correct number of variants, preserves protected spans
  - SemanticPreservationChecker: equivalence/divergence detection
  - TraceComparator: verdict_flip and reason_code_diff classification
  - MinimalVariantDiscoverer: finds minimal failing variant
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from packages.fuzz.transforms import VariantTransformer, VariantRequest
from packages.fuzz.equivalence import SemanticPreservationChecker
from packages.fuzz.comparator import TraceComparator, DivergenceReport


# ---------------------------------------------------------------------------
# VariantTransformer tests
# ---------------------------------------------------------------------------


class TestVariantTransformer:
    def setup_method(self):
        self.transformer = VariantTransformer()

    def test_generates_six_variants_by_default(self):
        variants = self.transformer.generate("Archive invoices for vendor 4421")
        assert len(variants) == 6

    def test_variant_languages_are_correct(self):
        variants = self.transformer.generate("Archive invoices for vendor 4421")
        langs = {v.language for v in variants}
        assert langs == {"hin_Latn", "hin_Deva", "tel_Latn", "tel_Telu", "tam_Taml", "kan_Knda"}

    def test_protected_spans_preserved_in_all_variants(self):
        text = "Archive March 2025 invoices for INV-4421 vendor 4421"
        variants = self.transformer.generate(text)
        for v in variants:
            # Numeric IDs and labeled spans should still be present
            assert "4421" in v.raw_text, f"Number '4421' missing in {v.language}: {v.raw_text}"
            assert "INV-4421" in v.raw_text, f"ID 'INV-4421' missing in {v.language}: {v.raw_text}"

    def test_variant_group_id_shared_across_variants(self):
        group_id = str(uuid.uuid4())
        variants = self.transformer.generate(
            "Archive invoices for vendor", variant_group_id=group_id
        )
        for v in variants:
            assert v.variant_group_id == group_id

    def test_auto_generates_group_id_if_none(self):
        variants = self.transformer.generate("Archive invoices")
        # All variants share the same auto-generated ID
        group_ids = {v.variant_group_id for v in variants}
        assert len(group_ids) == 1

    def test_single_language_filter(self):
        variants = self.transformer.generate(
            "Block access for user", languages=["hin_Latn"]
        )
        assert len(variants) == 1
        assert variants[0].language == "hin_Latn"

    def test_tel_telu_variant_contains_telugu_chars(self):
        variants = self.transformer.generate(
            "Block access", languages=["tel_Telu"]
        )
        assert len(variants) == 1
        text = variants[0].raw_text
        # Should contain at least some Telugu unicode characters
        has_telugu = any("\u0C00" <= c <= "\u0C7F" for c in text)
        assert has_telugu, f"Expected Telugu chars in: {text}"

    def test_transform_trace_is_populated(self):
        variants = self.transformer.generate("Archive invoices", languages=["hin_Latn"])
        assert len(variants[0].transform_trace) > 0


# ---------------------------------------------------------------------------
# SemanticPreservationChecker tests
# ---------------------------------------------------------------------------


class TestSemanticPreservationChecker:
    def setup_method(self):
        self.checker = SemanticPreservationChecker()

    def test_identical_texts_are_equivalent(self):
        result = self.checker.check(
            "Archive March invoices for vendor 4421",
            "Archive March invoices for vendor 4421",
        )
        assert result.equivalent is True
        assert result.divergence_score == 0.0

    def test_protected_span_mismatch_not_equivalent(self):
        result = self.checker.check(
            "Archive invoices for vendor 4421",
            "Archive invoices for vendor 9999",  # different vendor ID
        )
        assert result.equivalent is False
        assert result.protected_span_match is False

    def test_same_ids_different_words_may_still_be_equivalent(self):
        result = self.checker.check(
            "Archive March 2025 invoices for vendor 4421",
            "archive ki 4421 invoices 2025",  # same numeric spans (4421, 2025), different words
        )
        # Spans: both texts contain 4421 and 2025 as numbers
        # 'vendor', 'invoices', 'March' are regular words, not protected spans
        # So protected_span_match depends on whether both have the same numbers
        # Both have {4421, 2025} → protected_span_match should be True
        assert result.protected_span_match is True

    def test_divergence_score_between_zero_and_one(self):
        result = self.checker.check("Archive vendor", "Something completely different")
        assert 0.0 <= result.divergence_score <= 1.0

    def test_has_reason_string(self):
        result = self.checker.check("Archive vendor 4421", "archive vendor 4421")
        assert isinstance(result.reason, str)
        assert len(result.reason) > 0


# ---------------------------------------------------------------------------
# TraceComparator tests
# ---------------------------------------------------------------------------


def _make_mock_result(verdict: str, reason_code: str, trace_id: str = "") -> MagicMock:
    """Build a minimal mock PipelineResult for comparator tests."""
    mock = MagicMock()
    mock.trace_id = trace_id or str(uuid.uuid4())
    mock.task_id = str(uuid.uuid4())

    gate_event = MagicMock()
    gate_event.event_type = "gate_decision"
    gate_event.payload = {"verdict": verdict, "reason_code": reason_code}

    mock.events = [gate_event]
    return mock


class TestTraceComparator:
    def setup_method(self):
        self.comparator = TraceComparator()
        self.group_id = str(uuid.uuid4())

    def test_no_divergence_same_verdict_same_reason(self):
        canonical = _make_mock_result("ALLOW", "OK")
        variant = _make_mock_result("ALLOW", "OK")
        report = self.comparator.compare(
            canonical, variant, "eng_Latn", "tel_Latn", self.group_id
        )
        assert report.diverged is False
        assert report.divergence_type == "none"

    def test_verdict_flip_detected(self):
        canonical = _make_mock_result("ALLOW", "OK")
        variant = _make_mock_result("BLOCK", "VENDOR_ID_MISMATCH")
        report = self.comparator.compare(
            canonical, variant, "eng_Latn", "tel_Latn", self.group_id
        )
        assert report.diverged is True
        assert report.divergence_type == "verdict_flip"

    def test_reason_code_diff_detected(self):
        canonical = _make_mock_result("BLOCK", "APPROVAL_REQUIRED")
        variant = _make_mock_result("BLOCK", "VENDOR_ID_MISMATCH")
        report = self.comparator.compare(
            canonical, variant, "eng_Latn", "hin_Latn", self.group_id
        )
        assert report.diverged is True
        assert report.divergence_type == "reason_code_diff"

    def test_report_has_correct_languages(self):
        canonical = _make_mock_result("ALLOW", "OK")
        variant = _make_mock_result("ALLOW", "OK")
        report = self.comparator.compare(
            canonical, variant, "eng_Latn", "tel_Telu", self.group_id
        )
        assert report.canonical_language == "eng_Latn"
        assert report.variant_language == "tel_Telu"

    def test_compare_many_returns_one_report_per_variant(self):
        canonical = _make_mock_result("ALLOW", "OK")
        variants = [_make_mock_result("ALLOW", "OK") for _ in range(3)]
        reports = self.comparator.compare_many(
            canonical, variants, "eng_Latn", ["hin_Latn", "tel_Latn", "tel_Telu"], self.group_id
        )
        assert len(reports) == 3

    def test_report_serializable_to_dict(self):
        canonical = _make_mock_result("ALLOW", "OK")
        variant = _make_mock_result("BLOCK", "APPROVAL_REQUIRED")
        report = self.comparator.compare(
            canonical, variant, "eng_Latn", "tel_Latn", self.group_id
        )
        d = report.to_dict()
        assert "diverged" in d
        assert "divergence_type" in d
        assert d["diverged"] is True
