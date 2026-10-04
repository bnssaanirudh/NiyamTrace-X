"""
packages/tools/__init__.py
"""

from packages.tools.archive_invoices import ArchiveInvoicesTool
from packages.tools.base import ToolCapability, ToolImplementation
from packages.tools.dummy_tools import BlockUserAccessTool, SuspendVendorTool, UpdateCreditLimitTool
from packages.tools.registry import (
    ToolSchemaValidationError,
    get_registry_hash,
    get_tool_implementation,
    register_tool,
    validate_tool_call,
)

# Bootstrap Registry
register_tool(ArchiveInvoicesTool())
register_tool(SuspendVendorTool())
register_tool(UpdateCreditLimitTool())
register_tool(BlockUserAccessTool())
