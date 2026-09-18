import pytest
from packages.policy.loader import PolicyLoader, PolicyLoadError

def test_tampered_policy_signature(tmp_path, monkeypatch):
    # Mock signature verification to fail
    import packages.policy.loader as loader_module
    monkeypatch.setattr(loader_module, "verify_signature", lambda content, sig: False)

    policy_file = tmp_path / "valid.yaml"
    policy_file.write_text("""
version: "1.0.0"
tenant: "acme"
rules: {}
    """)

    loader = PolicyLoader(str(policy_file))
    
    with pytest.raises(PolicyLoadError, match="Policy signature verification failed"):
        loader.load(require_signature=True, signature="bad_sig")
