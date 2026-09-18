from pydantic import BaseModel


class Principal(BaseModel):
    """
    Verified principal extracted from an authenticated token (e.g., JWT).
    """
    subject: str
    tenant_id: str
    roles: frozenset[str]
    scopes: frozenset[str]
