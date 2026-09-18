from typing import Any
from packages.tools.base import ToolCapability, ToolImplementation
from packages.contracts.schema import StateDelta

class SuspendVendorTool(ToolImplementation):
    @property
    def capability(self) -> ToolCapability:
        return ToolCapability(
            name="suspend_vendor",
            description="Suspends a vendor account.",
            required_roles=["admin", "security_officer"],
            schema_version="1.0",
            risk_class="HIGH_WRITE",
            required_scopes=["vendor.write"],
            supports_simulation=True,
            supports_idempotency=True
        )
    @property
    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "tool_name": {"const": "suspend_vendor"},
                "arguments": {
                    "type": "object",
                    "properties": {
                        "vendor_id": {"type": "integer"},
                        "justification": {"type": "string", "minLength": 10}
                    },
                    "required": ["vendor_id", "justification"],
                    "additionalProperties": False
                }
            }
        }
    def validate_arguments(self, args: dict[str, Any]) -> None:
        from packages.tools.registry import ToolSchemaValidationError
        if "justification" in args and len(args["justification"]) < 10:
            raise ToolSchemaValidationError("justification length < 10")
            
    def simulate(self, args: dict[str, Any], erp_conn: Any) -> StateDelta:
        return StateDelta(affected_record_ids=[], record_deltas=[], table="vendors", estimated_row_count=0)
    def execute(self, args: dict[str, Any], erp_conn: Any) -> StateDelta:
        return self.simulate(args, erp_conn)

class UpdateCreditLimitTool(ToolImplementation):
    @property
    def capability(self) -> ToolCapability:
        return ToolCapability(
            name="update_credit_limit",
            description="Updates vendor credit limit.",
            required_roles=["finance_admin", "credit_officer"],
            schema_version="1.0",
            risk_class="HIGH_WRITE",
            required_scopes=["vendor.write"],
            supports_simulation=True,
            supports_idempotency=True
        )
    @property
    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "tool_name": {"const": "update_credit_limit"},
                "arguments": {
                    "type": "object",
                    "properties": {
                        "vendor_id": {"type": "integer"},
                        "new_limit_inr": {"type": "number"}
                    },
                    "required": ["vendor_id", "new_limit_inr"],
                    "additionalProperties": False
                }
            }
        }
    def simulate(self, args: dict[str, Any], erp_conn: Any) -> StateDelta:
        return StateDelta(affected_record_ids=[], record_deltas=[], table="vendor_credit_limits", estimated_row_count=0)
    def execute(self, args: dict[str, Any], erp_conn: Any) -> StateDelta:
        return self.simulate(args, erp_conn)

class BlockUserAccessTool(ToolImplementation):
    @property
    def capability(self) -> ToolCapability:
        return ToolCapability(
            name="block_user_access",
            description="Blocks a user account.",
            required_roles=["it_admin", "security_officer"],
            schema_version="1.0",
            risk_class="HIGH_WRITE",
            required_scopes=["user.write"],
            supports_simulation=True,
            supports_idempotency=True
        )
    @property
    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "tool_name": {"const": "block_user_access"},
                "arguments": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "duration_days": {"type": "integer"}
                    },
                    "required": ["user_id", "duration_days"],
                    "additionalProperties": False
                }
            }
        }
    def simulate(self, args: dict[str, Any], erp_conn: Any) -> StateDelta:
        return StateDelta(affected_record_ids=[], record_deltas=[], table="users", estimated_row_count=0)
    def execute(self, args: dict[str, Any], erp_conn: Any) -> StateDelta:
        return self.simulate(args, erp_conn)
