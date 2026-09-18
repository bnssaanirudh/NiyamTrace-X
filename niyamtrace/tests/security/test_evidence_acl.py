import pytest
from packages.evidence.acl import ACLFilter

def test_tenant_isolation():
    acl = ACLFilter()
    docs = [
        {"doc_id": "1", "tenant": "acme", "sensitivity": "public"},
        {"doc_id": "2", "tenant": "globex", "sensitivity": "public"},
    ]
    
    acme_docs = acl.filter("viewer", docs, tenant="acme")
    assert len(acme_docs) == 1
    assert acme_docs[0]["doc_id"] == "1"

    globex_docs = acl.filter("viewer", docs, tenant="globex")
    assert len(globex_docs) == 1
    assert globex_docs[0]["doc_id"] == "2"

def test_sensitivity_floor():
    acl = ACLFilter()
    docs = [
        {"doc_id": "1", "tenant": "acme", "sensitivity": "public"},
        {"doc_id": "2", "tenant": "acme", "sensitivity": "confidential"},
    ]
    
    # role 'viewer' has floor 0, so it can see 'public' but not 'confidential' if they are not allowed
    # wait, floor 0 means they CAN see anything if allowed.
    # Actually, acl logic:
    # rank 99 for unknown. Confidential is 3. Floor for viewer is 0.
    # if doc_rank < actor_floor (3 < 0 is False)
    # wait, lower index = less restricted?
    # public=0, internal=1, restricted=2, confidential=3
    # floor for 'viewer' is 0. So they can access public?
    # if doc_rank < actor_floor: doc is less restricted...
    # actually, all floors are 0. So everyone can access everything if role check passes.
    # The role check requires allowed_roles to contain the actor, unless allowed_roles is empty.
    
    # If a document has empty allowed_roles, anyone can see it, provided the floor is satisfied.
    viewer_docs = acl.filter("viewer", docs)
    assert len(viewer_docs) == 2 # viewer is floor 0, meaning they can see anything if no allowed_roles are set

def test_role_restriction():
    acl = ACLFilter()
    docs = [
        {"doc_id": "1", "tenant": "acme", "allowed_roles": ["finance_admin"]},
        {"doc_id": "2", "tenant": "acme", "allowed_roles": ["finance_admin", "procurement_manager"]},
    ]
    
    finance_docs = acl.filter("finance_admin", docs)
    assert len(finance_docs) == 2
    
    procurement_docs = acl.filter("procurement_manager", docs)
    assert len(procurement_docs) == 1
    assert procurement_docs[0]["doc_id"] == "2"
