import jwt
from fastapi import HTTPException
from packages.auth.models import Principal
from packages.config import get_settings


def verify_token(token: str) -> Principal:
    """
    Verify the JWT token and extract the Principal.
    For Phase 3, we use a shared secret. Future phases may use JWKS.
    """
    settings = get_settings()
    if not settings.auth_enabled:
        # If auth is disabled (e.g. in development), return a dummy principal
        return Principal(
            subject="dev_user",
            tenant_id="dev_tenant",
            roles=frozenset(["admin", "auditor", "user"]),
            scopes=frozenset(["all"])
        )
    
    if not settings.auth_secret_key:
        raise HTTPException(status_code=500, detail="Server misconfigured: missing auth_secret_key")

    try:
        payload = jwt.decode(
            token,
            settings.auth_secret_key,
            algorithms=["HS256", "RS256"],
            options={"require": ["exp", "iss", "sub"]}
        )
        
        # In a real OIDC setup, we might extract tenant and roles from custom claims.
        # Here we map standard claims or custom namespaced claims.
        return Principal(
            subject=payload.get("sub"),
            tenant_id=payload.get("tenant_id", "default"),
            roles=frozenset(payload.get("roles", [])),
            scopes=frozenset(payload.get("scopes", []))
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidAudienceError:
        raise HTTPException(status_code=401, detail="Invalid audience")
    except jwt.InvalidIssuerError:
        raise HTTPException(status_code=401, detail="Invalid issuer")
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
