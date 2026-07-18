import pytest
from packages.nlp.entity_linker import EntityLinker
from packages.contracts.schema import ActionContract

@pytest.fixture
def linker():
    return EntityLinker()

def test_vendor_id_exact_match(linker):
    contract = ActionContract(
        actor_id="U1",
        actor_role="admin",
        intent="access.block",
        intent_confidence=1.0,
        slots={"VENDOR_ID": "VEN-004"},
        raw_text="",
        normalized_text=""
    )
    res = linker.link_entities(contract)
    assert not res.requires_review
    assert res.slots["VENDOR_ID"] == "VEN-004"

def test_vendor_id_invalid(linker):
    contract = ActionContract(
        actor_id="U1",
        actor_role="admin",
        intent="access.block",
        intent_confidence=1.0,
        slots={"VENDOR_ID": "VEN-0010"},
        raw_text="",
        normalized_text=""
    )
    res = linker.link_entities(contract)
    assert res.requires_review

def test_vendor_name_ambiguous(linker):
    contract = ActionContract(
        actor_id="U1",
        actor_role="admin",
        intent="vendor.suspend",
        intent_confidence=1.0,
        slots={"VENDOR_NAME": "Apex"},
        raw_text="",
        normalized_text=""
    )
    res = linker.link_entities(contract)
    assert res.requires_review
    assert "candidate_vendors" in res.slots
    assert len(res.slots["candidate_vendors"]) > 1

def test_vendor_name_fuzzy_success(linker):
    contract = ActionContract(
        actor_id="U1",
        actor_role="admin",
        intent="vendor.update", # NOT permission changing
        intent_confidence=1.0,
        slots={"VENDOR_NAME": "Global Corpp"}, # typo, score > 95
        raw_text="",
        normalized_text=""
    )
    res = linker.link_entities(contract)
    assert not res.requires_review
    assert res.slots["VENDOR_ID"] == "VEN-100"

def test_vendor_name_fuzzy_permission_block(linker):
    contract = ActionContract(
        actor_id="U1",
        actor_role="admin",
        intent="access.grant", # Permission changing
        intent_confidence=1.0,
        slots={"VENDOR_NAME": "Global Corporation"}, # fuzzy
        raw_text="",
        normalized_text=""
    )
    res = linker.link_entities(contract)
    assert res.requires_review # Blocked due to permission changing action
    assert "candidate_vendors" in res.slots

def test_scope_validation(linker):
    contract = ActionContract(
        actor_id="U1",
        actor_role="admin",
        intent="access.grant",
        intent_confidence=1.0,
        slots={"ROLE": "super_admin"}, # invalid
        raw_text="",
        normalized_text=""
    )
    res = linker.link_entities(contract)
    assert res.requires_review
