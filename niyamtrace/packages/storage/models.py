from sqlalchemy import Column, Float, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class VendorInvoice(Base):
    __tablename__ = "vendor_invoices"

    invoice_id = Column(String, primary_key=True)
    vendor_id = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    amount_usd = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="OPEN")
    created_at = Column(String, nullable=False)


class UserAccess(Base):
    __tablename__ = "user_access"

    user_id = Column(String, primary_key=True)
    role = Column(String, nullable=False)
    status = Column(String, nullable=False, default="ACTIVE")
    blocked_until = Column(String, nullable=True)



class PendingApproval(Base):
    __tablename__ = "pending_approvals"

    approval_id = Column(String, primary_key=True)
    trace_id = Column(String, nullable=False)
    contract = Column(JSON, nullable=False)
    tool_calls = Column(JSON, nullable=False)
    requested_by = Column(String, nullable=False)
    status = Column(String, nullable=False, default="PENDING")
    created_at = Column(Float, nullable=False)
    expires_at = Column(Float, nullable=False)
    reviewed_by = Column(String, nullable=True)


class VendorCreditLimit(Base):
    __tablename__ = "vendor_credit_limits"

    vendor_id = Column(Integer, primary_key=True)
    credit_limit_inr = Column(Float, nullable=False)
    updated_at = Column(String, nullable=False)


class NiyamIdempotency(Base):
    __tablename__ = "niyam_idempotency"

    idempotency_key = Column(String, primary_key=True)
    executed_at = Column(Float, nullable=False)
    result_payload = Column(Text, nullable=True)


class ConsumedCapability(Base):
    __tablename__ = "consumed_capabilities"

    nonce = Column(String, primary_key=True)
    cert_hash = Column(String, nullable=False)
    tenant_id = Column(String, nullable=False)
    tool_name = Column(String, nullable=False)
    consumed_at = Column(Float, nullable=False)

