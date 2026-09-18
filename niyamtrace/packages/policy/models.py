from pydantic import BaseModel
from typing import Optional

class ApprovalPolicy(BaseModel):
    required_above_rows: int

class ToolRule(BaseModel):
    allowed_roles: set[str]
    allowed_attributes: set[str]
    max_rows_without_approval: int
    evidence_required: bool
    approval: Optional[ApprovalPolicy] = None

class PolicyBundle(BaseModel):
    version: str
    tenant: str
    rules: dict[str, ToolRule]
