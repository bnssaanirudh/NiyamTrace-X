from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from packages.auth.jwt import verify_token
from packages.auth.models import Principal
from packages.config import get_settings

security = HTTPBearer(auto_error=False)


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(security)
) -> Principal:
    """
    Dependency to get the current verified principal.
    If auth is enabled and no credentials are provided, raises 401.
    """
    settings = get_settings()
    
    if not settings.auth_enabled:
        return verify_token("")

    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return verify_token(credentials.credentials)


def require_role(role: str):
    """
    Dependency generator to require a specific role.
    """
    def _role_checker(principal: Principal = Depends(get_current_principal)):
        if role not in principal.roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return principal
    return _role_checker
