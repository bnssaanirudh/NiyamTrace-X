from packages.auth.models import Principal


def has_permission(principal: Principal, required_role: str) -> bool:
    """
    Check if the principal has the required role.
    """
    return required_role in principal.roles

def can_access_tenant(principal: Principal, tenant_id: str) -> bool:
    """
    Check if the principal belongs to the specified tenant.
    """
    # Simple tenant isolation logic
    return principal.tenant_id == tenant_id
