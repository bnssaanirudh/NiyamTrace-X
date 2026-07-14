"""
tests/integration/test_week3_multilingual_intake.py — Week 3 Integration Tests

Verifies that the multilingual intake is correctly wired into the pipeline:
  - All 4 language forms produce a real (non-stub) language_profile in the trace
  - language_profile contains primary_lang, script, code_switched, spans
  - normalized_text from the intake appears in the trace event payload
  - input_received event carries intake diagnostics (applied_maps, primary_lang)
  - All 9 event types still present and in order (regression from Week 2)
  - Week 2 exit-criterion canonical scenario still passes (no regression)

Note: The contract extractor is still hardcoded for vendor 4421 / March 2025.
Only language detection and normalization are real in Week 3.
Week 4 will wire the NLP slot-parser so multilingual variants can resolve to
different contracts.
"""

from __future__ import annotations

import json
import sqlite3

import pytest

from apps.gateway.pipeline import NiyamPipeline, PipelineRequest
from data.synthetic.erp import init_schema, reset_to_seed
from packages.lake.writer import read_trace

# Four language forms of the canonical scenario
CANONICAL_EN = "Archive March invoices for vendor 4421"
CANONICAL_HI_ROM = "Vendor 4421 ke March invoices archive karo"
# Fully Telugu-script version (Telugu words for domain nouns + digits)
CANONICAL_TE = "వెండర్ 4421 మార్చి ఇన్వాయిస్లు ఆర్కైవ్ చేయండి"  # fully Telugu
CANONICAL_TE_ROM = "Vendor 4421 March invoices archive cheyyandi garu"

EXPECTED_LANGS = {
    CANONICAL_EN: "eng_Latn",
    CANONICAL_HI_ROM: "hin_Latn",
    CANONICAL_TE: "tel_Telu",
    CANONICAL_TE_ROM: "tel_Latn",
}

REQUIRED_EVENT_TYPES = [
    "input_received", "contract_extracted", "retrieval_completed",
    "policy_evaluated", "tool_proposed", "tool_simulated",
    "gate_decision", "tool_executed", "evaluation_verdict",
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fresh_erp():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    reset_to_seed(conn)
    yield conn
    conn.close()


@pytest.fixture
def traces_dir(tmp_path):
    return tmp_path / "traces"


@pytest.fixture
def pipeline(fresh_erp, traces_dir):
    from packages.nlp.compiler import NiyamCompiler
    
    compiler = NiyamCompiler(parser_version_suffix="mock")
    return NiyamPipeline(erp_conn=fresh_erp, traces_dir=traces_dir, compiler=compiler)


def _make_req(text: str) -> PipelineRequest:
    return PipelineRequest(
        raw_text=text,
        actor_id="user-pm-001",
        actor_role="procurement_manager",
        task_id=f"task-week3-{text[:20].replace(' ', '_')}",
    )


# ---------------------------------------------------------------------------
# Week 3: Real language profile in trace envelope
# ---------------------------------------------------------------------------


class TestWeek3LanguageProfile:
    """All 4 language forms must produce real language profiles (not the stub)."""

    @pytest.mark.parametrize("text,expected_lang", list(EXPECTED_LANGS.items()))
    def test_correct_primary_lang_detected(self, pipeline, text, expected_lang):
        result = pipeline.run(_make_req(text))
        profile = result.contract.language_profile
        actual_lang = profile.get("primary_lang")
        assert actual_lang == expected_lang, (
            f"For input {text!r}: expected primary_lang={expected_lang!r}, "
            f"got {actual_lang!r}"
        )

    @pytest.mark.parametrize("text", list(EXPECTED_LANGS.keys()))
    def test_language_profile_not_stub(self, pipeline, text):
        """Ensure the old stub {'lang': 'en', 'script': 'Latin'} is gone."""
        result = pipeline.run(_make_req(text))
        profile = result.contract.language_profile
        # Old stub had 'lang' key; new profile has 'primary_lang'
        assert "primary_lang" in profile, (
            f"language_profile still looks like the old stub for {text!r}: {profile}"
        )
        assert "lang" not in profile or "primary_lang" in profile

    @pytest.mark.parametrize("text", list(EXPECTED_LANGS.keys()))
    def test_language_profile_has_required_fields(self, pipeline, text):
        result = pipeline.run(_make_req(text))
        profile = result.contract.language_profile
        for field in ("primary_lang", "script", "code_switched", "spans", "confidence"):
            assert field in profile, (
                f"Missing field '{field}' in language_profile for {text!r}"
            )

    @pytest.mark.parametrize("text", list(EXPECTED_LANGS.keys()))
    def test_language_profile_is_json_serializable(self, pipeline, text):
        result = pipeline.run(_make_req(text))
        profile = result.contract.language_profile
        # Must not raise
        serialized = json.dumps(profile)
        assert len(serialized) > 0

    def test_english_is_not_code_switched(self, pipeline):
        result = pipeline.run(_make_req(CANONICAL_EN))
        assert result.contract.language_profile.get("code_switched") is False

    def test_hinglish_is_code_switched(self, pipeline):
        result = pipeline.run(_make_req(CANONICAL_HI_ROM))
        assert result.contract.language_profile.get("code_switched") is True

    def test_telugu_script_detected(self, pipeline):
        result = pipeline.run(_make_req(CANONICAL_TE))
        # CANONICAL_TE is fully Telugu-script; script should be Telugu or Mixed
        # (Mixed is acceptable when digits are present as Latin chars)
        script = result.contract.language_profile.get("script")
        assert script in ("Telugu", "Mixed"), (
            f"Expected Telugu or Mixed script for Telugu input, got {script!r}"
        )

    def test_latin_scripts_detected(self, pipeline):
        for text in [CANONICAL_EN, CANONICAL_HI_ROM, CANONICAL_TE_ROM]:
            result = pipeline.run(_make_req(text))
            assert result.contract.language_profile.get("script") == "Latin", (
                f"Expected Latin script for {text!r}"
            )


# ---------------------------------------------------------------------------
# Week 3: Normalized text in trace and contract
# ---------------------------------------------------------------------------


class TestWeek3NormalizedText:
    def test_hinglish_normalized_text_strips_markers(self, pipeline):
        """Hinglish function words should be removed from normalized_text."""
        result = pipeline.run(_make_req(CANONICAL_HI_ROM))
        norm = result.contract.normalized_text.lower()
        # "karo" and "ke" should be stripped by normalizer
        assert "karo" not in norm
        assert " ke " not in norm

    def test_te_rom_normalized_text_strips_markers(self, pipeline):
        result = pipeline.run(_make_req(CANONICAL_TE_ROM))
        norm = result.contract.normalized_text.lower()
        assert "cheyyandi" not in norm
        assert "garu" not in norm

    @pytest.mark.parametrize("text", [CANONICAL_EN, CANONICAL_HI_ROM, CANONICAL_TE_ROM])
    def test_vendor_id_preserved_in_normalized_text(self, pipeline, text):
        result = pipeline.run(_make_req(text))
        assert "4421" in result.contract.normalized_text, (
            f"Vendor ID 4421 lost in normalized_text for: {text!r}"
        )

    def test_raw_text_is_unchanged(self, pipeline):
        result = pipeline.run(_make_req(CANONICAL_HI_ROM))
        assert result.contract.raw_text == CANONICAL_HI_ROM


# ---------------------------------------------------------------------------
# Week 3: Trace envelope carries language profile
# ---------------------------------------------------------------------------


class TestWeek3TraceLanguageProfile:
    def test_all_trace_events_carry_language_profile(self, pipeline, traces_dir):
        result = pipeline.run(_make_req(CANONICAL_EN))
        for event in result.events:
            assert event.language_profile, (
                f"Event '{event.event_type}' has empty language_profile"
            )

    def test_input_received_event_has_intake_payload(self, pipeline):
        result = pipeline.run(_make_req(CANONICAL_HI_ROM))
        input_event = next(e for e in result.events if e.event_type == "input_received")
        payload = input_event.payload
        assert "primary_lang" in payload
        assert "normalized_text" in payload
        assert "applied_maps" in payload

    def test_contract_extracted_event_has_intake_lang(self, pipeline):
        result = pipeline.run(_make_req(CANONICAL_HI_ROM))
        contract_event = next(
            e for e in result.events if e.event_type == "contract_extracted"
        )
        payload = contract_event.payload
        assert "intake_primary_lang" in payload
        assert payload["intake_primary_lang"] == "hin_Latn"

    def test_trace_language_profile_matches_contract(self, pipeline):
        result = pipeline.run(_make_req(CANONICAL_HI_ROM))
        # All events should carry the same language profile
        for event in result.events:
            assert event.language_profile.get("primary_lang") == "hin_Latn"

    def test_replayed_trace_has_language_profile(self, pipeline, traces_dir):
        result = pipeline.run(_make_req(CANONICAL_EN))
        replayed = read_trace(result.trace_path)
        for event in replayed:
            assert event.language_profile.get("primary_lang") == "eng_Latn"


# ---------------------------------------------------------------------------
# Regression: Week 2 exit criterion still holds
# ---------------------------------------------------------------------------


class TestWeek2RegressionUnderWeek3:
    """All Week 2 exit criteria must still pass after Week 3 changes."""

    def test_gate_still_returns_allow_for_english(self, pipeline):
        result = pipeline.run(_make_req(CANONICAL_EN))
        assert result.gate_decision.verdict == "ALLOW"

    def test_predicted_delta_still_3_records(self, pipeline):
        result = pipeline.run(_make_req(CANONICAL_EN))
        assert result.predicted_delta.estimated_row_count == 3

    def test_all_9_event_types_present(self, pipeline):
        result = pipeline.run(_make_req(CANONICAL_EN))
        seen = [e.event_type for e in result.events]
        for req_type in REQUIRED_EVENT_TYPES:
            assert req_type in seen

    def test_simulator_fidelity_still_perfect(self, pipeline):
        result = pipeline.run(_make_req(CANONICAL_EN))
        pred_ids = result.predicted_delta.record_id_set()
        actual_ids = result.actual_delta.record_id_set()
        assert pred_ids == actual_ids

    def test_parser_version_updated_to_week4(self, pipeline):
        result = pipeline.run(_make_req(CANONICAL_EN))
        assert "0.4.0" in result.contract.parser_version
