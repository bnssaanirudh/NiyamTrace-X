"""
packages/gate/tool_schemas.py — Tool JSON Schema Registry

Defines the typed JSON schema for every tool available in the sandbox ERP.
Week 2 scope: one tool — archive_invoices.

Tool vocabulary is deliberately small and explicitly extended, never inferred
from free text. See docs/decisions.md §5.

Status: IMPLEMENTED (Week 2) — archive_invoices only.
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
        "tool_name": {
            "type": "string",
            "const": "archive_invoices",
        },
        "arguments": {
            "type": "object",
            "properties": {
                "vendor_id": {
                    "type": "integer",
                    "description": "Numeric vendor identifier.",
                    "minimum": 1,
                },
                "month": {
                    "type": "integer",
                    "description": "Calendar month (1–12).",
                    "minimum": 1,
                    "maximum": 12,
                },
                "year": {
                    "type": "integer",
                    "description": "Four-digit calendar year.",
                    "minimum": 2000,
                    "maximum": 2099,
                },
            },
            "required": ["vendor_id"],
            "additionalProperties": False,
        },
    },
    "required": ["tool_name", "arguments"],
    "additionalProperties": False,
}

# Map tool_name → schema dict
TOOL_REGISTRY: dict[str, dict[str, Any]] = {
    "archive_invoices": ARCHIVE_INVOICES_SCHEMA,
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

    schema_props = TOOL_REGISTRY[tool_name]["properties"]["arguments"]["properties"]
    required = TOOL_REGISTRY[tool_name]["properties"]["arguments"]["required"]
    additional_props_allowed = TOOL_REGISTRY[tool_name]["properties"]["arguments"].get(
        "additionalProperties", True
    )

    # Required fields
    for field in required:
        if field not in args:
            raise ToolSchemaValidationError(f"MISSING_REQUIRED_ARG:{field}")

    # No extra fields
    if not additional_props_allowed:
        for key in args:
            if key not in schema_props:
                raise ToolSchemaValidationError(f"EXTRA_ARG:{key}")

    # Type + range checks
    if "vendor_id" in args:
        if not isinstance(args["vendor_id"], int) or args["vendor_id"] < 1:
            raise ToolSchemaValidationError("INVALID_ARG:vendor_id:must_be_positive_int")

    if "month" in args:
        if not isinstance(args["month"], int) or not (1 <= args["month"] <= 12):
            raise ToolSchemaValidationError("INVALID_ARG:month:must_be_1_to_12")

    if "year" in args:
        if not isinstance(args["year"], int) or not (2000 <= args["year"] <= 2099):
            raise ToolSchemaValidationError("INVALID_ARG:year:must_be_2000_to_2099")
