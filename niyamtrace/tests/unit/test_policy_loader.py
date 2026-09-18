import pytest
from pathlib import Path
from packages.policy.loader import PolicyLoader, PolicyLoadError
from packages.policy.compiler import PolicyCompiler

def test_load_valid_policy(tmp_path):
    policy_file = tmp_path / "valid.yaml"
    policy_file.write_text("""
version: "1.0.0"
tenant: "test_tenant"
rules:
  archive_invoices:
    allowed_roles: ["admin"]
    allowed_attributes: ["status"]
    max_rows_without_approval: 5
    evidence_required: true
    """)

    loader = PolicyLoader(str(policy_file))
    compiler = PolicyCompiler(loader)

    assert compiler.is_role_allowed("archive_invoices", "admin")
    assert not compiler.is_role_allowed("archive_invoices", "user")
    assert compiler.is_attribute_allowed("archive_invoices", "status")
    assert compiler.get_max_rows_without_approval("archive_invoices") == 5
    assert compiler.is_evidence_required("archive_invoices")
    assert len(compiler.policy_hash) == 16

def test_load_invalid_policy(tmp_path):
    policy_file = tmp_path / "invalid.yaml"
    policy_file.write_text("""
version: "1.0.0"
tenant: "test_tenant"
# missing rules
    """)

    loader = PolicyLoader(str(policy_file))
    with pytest.raises(PolicyLoadError):
        loader.load()
