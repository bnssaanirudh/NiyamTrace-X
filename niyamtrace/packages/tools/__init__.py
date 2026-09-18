"""
packages/tools/__init__.py
"""

from packages.tools.base import ToolCapability, ToolImplementation
from packages.tools.registry import get_tool_implementation, register_tool, validate_tool_call, get_registry_hash, ToolSchemaValidationError
from packages.tools.archive_invoices import ArchiveInvoicesTool
from packages.tools.dummy_tools import SuspendVendorTool, UpdateCreditLimitTool, BlockUserAccessTool

# Bootstrap Registry
register_tool(ArchiveInvoicesTool())
register_tool(SuspendVendorTool())
register_tool(UpdateCreditLimitTool())
register_tool(BlockUserAccessTool())
