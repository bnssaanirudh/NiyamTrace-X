"""
packages/gate/tool_schemas.py — Tool JSON Schema Registry (Facade)

Forwards tool schema validation and hashing to the new central tool capability registry
(Phase 6 Intent and Tool Capability Model).
"""

from packages.tools.registry import (
    ToolSchemaValidationError,
    validate_tool_call,
)
from packages.tools.registry import (
    get_registry_hash as schema_hash,
)

__all__ = ["ToolSchemaValidationError", "schema_hash", "validate_tool_call"]
