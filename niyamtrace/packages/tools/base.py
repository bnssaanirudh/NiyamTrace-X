"""
packages/tools/base.py — NiyamTrace-X Core Tool Framework

Defines the ToolCapability metadata model and the abstract ToolImplementation
interface that all executable capabilities must fulfill.
"""

from abc import ABC, abstractmethod
from typing import Any, Literal

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from packages.contracts.schema import StateDelta


class ToolCapability(BaseModel):
    name: str
    schema_version: str
    risk_class: Literal["READ", "LOW_WRITE", "HIGH_WRITE"]
    required_scopes: frozenset[str]
    supports_simulation: bool
    supports_idempotency: bool

class ToolImplementation(ABC):
    """
    Abstract interface for all executable tools in the NiyamTrace-X ERP.
    Enforces that simulation (predicting changes) and execution (applying changes)
    are bound in the same class, guaranteeing parity.
    """

    @property
    @abstractmethod
    def capability(self) -> ToolCapability:
        """Return the metadata and capabilities of this tool."""

    @property
    @abstractmethod
    def schema(self) -> dict[str, Any]:
        """Return the JSON schema defining the arguments for this tool."""

    @abstractmethod
    async def simulate(self, session: AsyncSession, arguments: dict[str, Any]) -> StateDelta:
        """
        Predict the changes this tool would make to the ERP state WITHOUT actually
        mutating anything (read-only SELECTs).
        """

    @abstractmethod
    async def execute(self, session: AsyncSession, arguments: dict[str, Any]) -> StateDelta:
        """
        Execute the tool's mutation on the ERP state and return the actual StateDelta.
        This is only called by the ERPExecutor if the gate returned ALLOW.
        """

    def validate_arguments(self, arguments: dict[str, Any]) -> None:
        """
        Validate tool-specific argument logic. 
        Should raise packages.tools.registry.ToolSchemaValidationError on failure.
        """
