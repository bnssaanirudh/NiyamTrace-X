"""
packages/tools/registry.py — NiyamTrace-X Tool Capability Registry
"""

import hashlib
import json
from typing import Any

from packages.tools.base import ToolImplementation

_TOOL_REGISTRY: dict[str, ToolImplementation] = {}

class ToolSchemaValidationError(ValueError):
    """Raised when a ToolCall does not conform to its registered schema."""

def register_tool(impl: ToolImplementation) -> None:
    """Register a ToolImplementation."""
    name = impl.capability.name
    if name in _TOOL_REGISTRY:
        raise ValueError(f"Tool {name} is already registered.")
    _TOOL_REGISTRY[name] = impl

def get_tool_implementation(tool_name: str) -> ToolImplementation | None:
    """Get a ToolImplementation by name."""
    return _TOOL_REGISTRY.get(tool_name)

def get_registry_hash() -> str:
    """Return a short content hash of all registered tool capabilities (for trace envelope)."""
    # Sort tools by name for deterministic hashing
    registry_state = {}
    for name in sorted(_TOOL_REGISTRY.keys()):
        impl = _TOOL_REGISTRY[name]
        registry_state[name] = {
            "capability": impl.capability.model_dump(mode="json"),
            "schema": impl.schema
        }
    return hashlib.sha256(json.dumps(registry_state, sort_keys=True).encode()).hexdigest()[:16]

def validate_tool_call(tool_call_dict: dict[str, Any]) -> None:
    """
    Validate a raw tool call dict against the registered schema.
    Raises ToolSchemaValidationError with a machine-readable reason on failure.
    Uses manual validation (no jsonschema library) to keep dependencies minimal.
    """
    tool_name = tool_call_dict.get("tool_name")
    if tool_name is None:
        raise ToolSchemaValidationError("MISSING_FIELD:tool_name")

    impl = get_tool_implementation(tool_name)
    if impl is None:
        raise ToolSchemaValidationError(f"UNKNOWN_TOOL:{tool_name}")

    args = tool_call_dict.get("arguments")
    if not isinstance(args, dict):
        raise ToolSchemaValidationError("MISSING_FIELD:arguments")

    schema_args = impl.schema["properties"]["arguments"]
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

    # --- archive_invoices validation logic directly moved to the tool? ---
    # For now, we can rely on the base manual validation, but wait, the original logic had manual rules:
    # "vendor_id", "month", "year" limits. 
    # Let's dynamically enforce some common constraints if we can, or let the tool implement a `validate()` method?
    # Actually, keeping the basic type validation inside validate_tool_call based on the schema might be better, or we can just ask the tool to validate its args.
    # To avoid rewriting a full JSON schema validator, let's keep the manual checks inside validate_tool_call or delegate to the tool.
    # Let's add a `validate_arguments` method to `ToolImplementation`. No, the original implementation did everything in `validate_tool_call`.
    # Let's delegate specific argument validation to the `ToolImplementation`.
    
    if hasattr(impl, "validate_arguments"):
        impl.validate_arguments(args)
