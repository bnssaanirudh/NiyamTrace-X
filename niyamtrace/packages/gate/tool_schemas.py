"""
packages/gate/tool_schemas.py — Tool JSON Schema Registry (Facade)

Forwards tool schema validation and hashing to the new central tool capability registry
(Phase 6 Intent and Tool Capability Model).
"""

from packages.tools.registry import (
    validate_tool_call,
    ToolSchemaValidationError,
    get_registry_hash as schema_hash,
)

__all__ = ["validate_tool_call", "ToolSchemaValidationError", "schema_hash"]
