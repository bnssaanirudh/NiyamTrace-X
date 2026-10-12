import hashlib
import json
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest

from packages.auth.models import AuthorizationContext, Principal
from packages.contracts.schema import EffectCertificate, StateDelta, ToolCall
from packages.gate.broker import (
    BrokerVerificationError,
    VerifiedExecutionBroker,
    sign_certificate_authority,
)


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = Mock()
    mock_res = Mock()
    mock_res.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_res
    return session


@pytest.fixture
def auth_context():
    principal = Principal(
        subject="user-001",
        tenant_id="acme",
        roles=frozenset(["procurement_manager"]),
        scopes=frozenset(["procurement.write"]),
    )
    return AuthorizationContext.from_principal(principal)

@pytest.fixture
def tool_call():
    return ToolCall(tool_name="archive_invoices", arguments={"vendor_id": 4421})

@pytest.fixture
def effect_certificate(tool_call):
    args_hash = hashlib.sha256(
        json.dumps(tool_call.arguments, sort_keys=True).encode()
    ).hexdigest()
    cert = EffectCertificate(
        trace_id="trace-123",
        actor="user-001",
        tenant_id="acme",
        action="archive_invoices",
        target_type="archive_invoices",
        selector={"vendor_id": 4421},
        canonical_args_hash=args_hash,
        policy_rules_used=[],
        evidence_refs=[],
        predicted_delta={
            "record_ids": ["INV-1", "INV-2"],
            "rows_changed": 2,
            "fields_changed": ["status"],
        },
        expires_at=time.time() + 3600,
    )
    cert = cert.seal()
    return sign_certificate_authority(cert)

@pytest.mark.asyncio
async def test_broker_valid_execution(auth_context, effect_certificate, tool_call, mock_session):
    broker = VerifiedExecutionBroker(mock_session)
    
    # Mock executor to return exactly what's predicted
    expected_delta = StateDelta(
        affected_record_ids=["INV-1", "INV-2"],
        record_deltas=[],
        table="vendor_invoices",
        estimated_row_count=2,
    )
    with patch.object(broker._executor, "execute", return_value=expected_delta):
        actual_delta = await broker.commit(effect_certificate, tool_call, auth_context)
    assert set(actual_delta.affected_record_ids) == {"INV-1", "INV-2"}

@pytest.mark.asyncio
async def test_broker_rejects_tampered_cert(auth_context, effect_certificate, tool_call, mock_session):
    broker = VerifiedExecutionBroker(mock_session)
    
    # Tamper the cert without resealing
    effect_certificate.actor = "user-hacker"
    
    with pytest.raises(BrokerVerificationError):
        await broker.commit(effect_certificate, tool_call, auth_context)

@pytest.mark.asyncio
async def test_broker_rejects_actor_mismatch(auth_context, effect_certificate, tool_call, mock_session):
    broker = VerifiedExecutionBroker(mock_session)
    
    # Create auth context for different user
    principal = Principal(
        subject="user-002",
        tenant_id="acme",
        roles=frozenset(["procurement_manager"]),
        scopes=frozenset(["procurement.write"]),
    )
    wrong_auth_context = AuthorizationContext.from_principal(principal)
    
    with pytest.raises(BrokerVerificationError, match="Actor identity mismatch"):
        await broker.commit(effect_certificate, tool_call, wrong_auth_context)

@pytest.mark.asyncio
async def test_broker_rejects_state_mismatch(auth_context, effect_certificate, tool_call, mock_session):
    broker = VerifiedExecutionBroker(mock_session)
    
    # Executor returns different delta
    unexpected_delta = StateDelta(
        affected_record_ids=["INV-1", "INV-3"],  # Mismatch!
        record_deltas=[],
        table="vendor_invoices",
        estimated_row_count=2,
    )
    with (
        patch.object(broker._executor, "execute", return_value=unexpected_delta),
        pytest.raises(BrokerVerificationError, match="State mismatch"),
    ):
        await broker.commit(effect_certificate, tool_call, auth_context)
