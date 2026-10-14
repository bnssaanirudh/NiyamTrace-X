"""
packages/auth/models.py — Authentication and Authorization Models

Principal: the verified identity extracted from a JWT.
AuthorizationContext: the stable context passed through the pipeline for
all authorization decisions. This is the single source of truth for
who the actor is — it cannot be overridden by caller-supplied request text.
"""

from __future__ import annotations

from pydantic import BaseModel


class Principal(BaseModel):
    """
    Verified principal extracted from an authenticated token (e.g., JWT).
    All fields are set from the verified token claims — never from request body.
    """

    subject: str
    tenant_id: str
    roles: frozenset[str]
    scopes: frozenset[str]

    model_config = {"frozen": True}

    @property
    def display_role(self) -> str:
        """
        A deterministic display role for logging/UI purposes ONLY.
        Do NOT use this for authorization decisions — use `roles` directly.
        Returns the lexicographically smallest role, or 'unauthenticated'.
        """
        if not self.roles:
            return "unauthenticated"
        return min(self.roles)

    def has_role(self, role: str) -> bool:
        """Check if this principal has the given role."""
        return role in self.roles

    def has_any_role(self, *roles: str) -> bool:
        """Check if this principal has at least one of the given roles."""
        return bool(self.roles.intersection(roles))

    def has_scope(self, scope: str) -> bool:
        """Check if this principal has the given scope."""
        return scope in self.scopes or "all" in self.scopes

    def is_same_tenant(self, tenant_id: str) -> bool:
        """Check if this principal belongs to the given tenant."""
        return self.tenant_id == tenant_id


class AuthorizationContext(BaseModel):
    """
    Stable, pipeline-internal authorization context derived from a verified Principal.

    This object is created once from the authenticated Principal and passed through
    the entire pipeline. It cannot be modified by downstream components or
    caller-supplied data. All authorization decisions must use this context,
    not the actor_role string in ActionContract (which is for display/audit only).

    Security invariant: this object must be created from an authenticated Principal
    and must never be reconstructed from user-supplied request fields.
    """

    subject: str
    tenant_id: str
    roles: frozenset[str]
    scopes: frozenset[str]
    # Deterministic display role for logging ONLY — not for authorization
    display_role: str

    model_config = {"frozen": True}

    @classmethod
    def from_principal(cls, principal: Principal) -> AuthorizationContext:
        """Create an AuthorizationContext from a verified Principal."""
        return cls(
            subject=principal.subject,
            tenant_id=principal.tenant_id,
            roles=principal.roles,
            scopes=principal.scopes,
            display_role=principal.display_role,
        )

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def has_any_role(self, *roles: str) -> bool:
        return bool(self.roles.intersection(roles))

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes or "all" in self.scopes

    def is_same_tenant(self, tenant_id: str) -> bool:
        return self.tenant_id == tenant_id
