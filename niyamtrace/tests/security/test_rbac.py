import pytest
from packages.auth.models import Principal
from packages.auth.rbac import has_permission, can_access_tenant

def test_has_permission():
    p = Principal(subject="1", tenant_id="t1", roles=frozenset(["admin", "user"]), scopes=frozenset())
    assert has_permission(p, "admin") is True
    assert has_permission(p, "user") is True
    assert has_permission(p, "auditor") is False

def test_can_access_tenant():
    p = Principal(subject="1", tenant_id="t1", roles=frozenset(), scopes=frozenset())
    assert can_access_tenant(p, "t1") is True
    assert can_access_tenant(p, "t2") is False
