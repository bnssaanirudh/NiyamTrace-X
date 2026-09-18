import pytest
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from packages.auth.jwt import verify_token
from packages.config import get_settings

SECRET = "test-secret-key-12345"

@pytest.fixture(autouse=True)
def setup_auth_settings(monkeypatch):
    # Mock settings to always be auth-enabled
    settings = get_settings()
    settings.auth_enabled = True
    settings.auth_secret_key = SECRET
    return settings

def create_token(payload: dict, secret: str = SECRET, alg: str = "HS256") -> str:
    default_payload = {
        "sub": "test_user",
        "iss": "test_issuer",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15)
    }
    default_payload.update(payload)
    return jwt.encode(default_payload, secret, algorithm=alg)

def test_valid_token():
    token = create_token({"roles": ["admin"]})
    principal = verify_token(token)
    assert principal.subject == "test_user"
    assert "admin" in principal.roles

def test_expired_token():
    token = create_token({"exp": datetime.now(timezone.utc) - timedelta(minutes=1)})
    with pytest.raises(HTTPException) as exc:
        verify_token(token)
    assert exc.value.status_code == 401
    assert "expired" in exc.value.detail.lower()

def test_forged_signature():
    token = create_token({}, secret="wrong-secret")
    with pytest.raises(HTTPException) as exc:
        verify_token(token)
    assert exc.value.status_code == 401
    assert "validate" in exc.value.detail.lower()

def test_alg_none_rejected():
    # pyjwt automatically rejects 'none' if we specify allowed algorithms=["HS256", "RS256"]
    # So we bypass create_token because pyjwt might refuse to encode it or we can construct it manually
    header = 'eyJhbGciOiJub25lIn0' # {"alg":"none"}
    payload = 'eyJzdWIiOiJ0ZXN0X3VzZXIiLCJleHAiOjE5OTk5OTk5OTksImlzcyI6InRlc3RfaXNzdWVyIn0'
    token = f"{header}.{payload}."
    with pytest.raises(HTTPException) as exc:
        verify_token(token)
    assert exc.value.status_code == 401

def test_missing_claims():
    token = jwt.encode({"sub": "test"}, SECRET, algorithm="HS256")
    with pytest.raises(HTTPException) as exc:
        verify_token(token)
    assert exc.value.status_code == 401
