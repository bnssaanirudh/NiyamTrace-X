"""
packages/gate/tool_schemas.py — Tool JSON Schema Registry

Defines the typed JSON schema for every tool available in the sandbox ERP.
Tool vocabulary is deliberately small and explicitly extended, never inferred
from free text. See docs/decisions.md §5.

Tools:
  - archive_invoices        (Week 2) — set OPEN invoices → ARCHIVED
  - block_user_access       (Week 9) — set user_access.status → BLOCKED
  - update_credit_limit     (Week 9) — update vendor_credit_limits.credit_limit_inr
  - suspend_vendor          (Week 9) — set vendor_invoices (vendor) → SUSPENDED status

Status: IMPLEMENTED (Week 9) — 4 tools.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

# ---------------------------------------------------------------------------
# Tool schema definitions
# ---------------------------------------------------------------------------

ARCHIVE_INVOICES_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "archive_invoices",
    "description": (
        "Archive (set status=ARCHIVED) all OPEN invoices for a given vendor "
        "within a specific calendar month and year. "
        "This is a bounded write — it must not match records outside the "
        "specified vendor_id × month × year combination."
    ),
    "type": "object",
    "properties": {
        "tool_name": {"type": "string", "const": "archive_invoices"},
        "arguments": {
            "type": "object",
            "properties": {
                "vendor_id": {"type": "integer", "description": "Numeric vendor identifier.", "minimum": 1},
                "month": {"type": "integer", "description": "Calendar month (1–12).", "minimum": 1, "maximum": 12},
                "year": {"type": "integer", "description": "Four-digit calendar year.", "minimum": 2000, "maximum": 2099},
            },
            "required": ["vendor_id"],
            "additionalProperties": False,
        },
    },
    "required": ["tool_name", "arguments"],
    "additionalProperties": False,
}

BLOCK_USER_ACCESS_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "block_user_access",
    "description": (
        "Block access for a target user for a specified duration in days. "
        "Sets user_access.status = BLOCKED and records blocked_until date. "
        "Allowed roles: it_admin, security_officer."
    ),
    "type": "object",
    "properties": {
        "tool_name": {"type": "string", "const": "block_user_access"},
        "arguments": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Target user identifier (e.g. USR-IT-001)."},
                "duration_days": {
                    "type": "integer",
                    "description": "Number of days to block access (1–365).",
                    "minimum": 1,
                    "maximum": 365,
                },
            },
            "required": ["user_id", "duration_days"],
            "additionalProperties": False,
        },
    },
    "required": ["tool_name", "arguments"],
    "additionalProperties": False,
}

UPDATE_CREDIT_LIMIT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "update_credit_limit",
    "description": (
        "Update the credit limit for a vendor (vendor_credit_limits table). "
        "Allowed roles: finance_admin, credit_officer. "
        "Increases above ₹50,000 require co-approval."
    ),
    "type": "object",
    "properties": {
        "tool_name": {"type": "string", "const": "update_credit_limit"},
        "arguments": {
            "type": "object",
            "properties": {
                "vendor_id": {"type": "integer", "description": "Numeric vendor identifier.", "minimum": 1},
                "new_limit_inr": {
                    "type": "number",
                    "description": "New credit limit in INR (must be positive).",
                    "exclusiveMinimum": 0,
                },
            },
            "required": ["vendor_id", "new_limit_inr"],
            "additionalProperties": False,
        },
    },
    "required": ["tool_name", "arguments"],
    "additionalProperties": False,
}

SUSPEND_VENDOR_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "suspend_vendor",
    "description": (
        "Suspend a vendor account. Sets vendor status to SUSPENDED, halting "
        "new PO and invoice submissions. Requires a justification string. "
        "Allowed roles: procurement_manager, compliance_officer."
    ),
    "type": "object",
    "properties": {
        "tool_name": {"type": "string", "const": "suspend_vendor"},
        "arguments": {
            "type": "object",
            "properties": {
                "vendor_id": {"type": "integer", "description": "Numeric vendor identifier.", "minimum": 1},
                "justification": {
                    "type": "string",
                    "description": "Written justification for the suspension (min 10 chars).",
                    "minLength": 10,
                },
            },
            "required": ["vendor_id", "justification"],
            "additionalProperties": False,
        },
    },
    "required": ["tool_name", "arguments"],
    "additionalProperties": False,
}

# Map tool_name → schema dict
TOOL_REGISTRY: dict[str, dict[str, Any]] = {
    "archive_invoices": ARCHIVE_INVOICES_SCHEMA,
    "block_user_access": BLOCK_USER_ACCESS_SCHEMA,
    "update_credit_limit": UPDATE_CREDIT_LIMIT_SCHEMA,
    "suspend_vendor": SUSPEND_VENDOR_SCHEMA,
}


def schema_hash(tool_name: str) -> str:
    """Return a short content hash of a tool schema (for trace envelope)."""
    schema = TOOL_REGISTRY.get(tool_name, {})
    return hashlib.sha256(json.dumps(schema, sort_keys=True).encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# JSON Schema validator (no external jsonschema dep — manual for MVP)
# ---------------------------------------------------------------------------


class ToolSchemaValidationError(ValueError):
    """Raised when a ToolCall does not conform to its registered schema."""


def validate_tool_call(tool_call_dict: dict[str, Any]) -> None:
    """
    Validate a raw tool call dict against the registered schema.

    Raises ToolSchemaValidationError with a machine-readable reason on failure.
    Uses manual validation (no jsonschema library) to keep dependencies minimal.
    """
    tool_name = tool_call_dict.get("tool_name")
    if tool_name is None:
        raise ToolSchemaValidationError("MISSING_FIELD:tool_name")

    if tool_name not in TOOL_REGISTRY:
        raise ToolSchemaValidationError(f"UNKNOWN_TOOL:{tool_name}")

    args = tool_call_dict.get("arguments")
    if not isinstance(args, dict):
        raise ToolSchemaValidationError("MISSING_FIELD:arguments")

    schema_args = TOOL_REGISTRY[tool_name]["properties"]["arguments"]
    required = schema_args.get("required", [])
    additional_props_allowed = schema_args.get("additionalProperties", True)
    schema_props = schema_args.get("properties", {})

    # Required fields
    for field in required:
        if field not in args:
            raise ToolSchemaValidationError(f"MISSING_REQUIRED_ARG:{field}")

    # No extra fields
    if not additional_props_allowed:
        for key in args:
            if key not in schema_props:
                raise ToolSchemaValidationError(f"EXTRA_ARG:{key}")

    # --- archive_invoices ---
    if tool_name == "archive_invoices":
        if "vendor_id" in args:
            if not isinstance(args["vendor_id"], int) or args["vendor_id"] < 1:
                raise ToolSchemaValidationError("INVALID_ARG:vendor_id:must_be_positive_int")
        if "month" in args:
            if not isinstance(args["month"], int) or not (1 <= args["month"] <= 12):
                raise ToolSchemaValidationError("INVALID_ARG:month:must_be_1_to_12")
        if "year" in args:
            if not isinstance(args["year"], int) or not (2000 <= args["year"] <= 2099):
                raise ToolSchemaValidationError("INVALID_ARG:year:must_be_2000_to_2099")

    # --- block_user_access ---
    elif tool_name == "block_user_access":
        if "user_id" in args and not isinstance(args["user_id"], str):
            raise ToolSchemaValidationError("INVALID_ARG:user_id:must_be_string")
        if "duration_days" in args:
            if not isinstance(args["duration_days"], int) or not (1 <= args["duration_days"] <= 365):
                raise ToolSchemaValidationError("INVALID_ARG:duration_days:must_be_1_to_365")

    # --- update_credit_limit ---
    elif tool_name == "update_credit_limit":
        if "vendor_id" in args:
            if not isinstance(args["vendor_id"], int) or args["vendor_id"] < 1:
                raise ToolSchemaValidationError("INVALID_ARG:vendor_id:must_be_positive_int")
        if "new_limit_inr" in args:
            val = args["new_limit_inr"]
            if not isinstance(val, (int, float)) or val <= 0:
                raise ToolSchemaValidationError("INVALID_ARG:new_limit_inr:must_be_positive_number")

    # --- suspend_vendor ---
    elif tool_name == "suspend_vendor":
        if "vendor_id" in args:
            if not isinstance(args["vendor_id"], int) or args["vendor_id"] < 1:
                raise ToolSchemaValidationError("INVALID_ARG:vendor_id:must_be_positive_int")
        if "justification" in args:
            j = args["justification"]
            if not isinstance(j, str) or len(j) < 10:
                raise ToolSchemaValidationError("INVALID_ARG:justification:must_be_string_min_10_chars")
