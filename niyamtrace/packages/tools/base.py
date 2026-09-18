"""
packages/tools/base.py — NiyamTrace-X Core Tool Framework

Defines the ToolCapability metadata model and the abstract ToolImplementation
interface that all executable capabilities must fulfill.
"""

from abc import ABC, abstractmethod
from typing import Any, Literal
import sqlite3
from pydantic import BaseModel

from packages.contracts.schema import StateDelta, ToolCall

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
        pass

    @property
    @abstractmethod
    def schema(self) -> dict[str, Any]:
        """Return the JSON schema defining the arguments for this tool."""
        pass

    @abstractmethod
    def simulate(self, conn: sqlite3.Connection, arguments: dict[str, Any]) -> StateDelta:
        """
        Predict the changes this tool would make to the ERP state WITHOUT actually
        mutating anything (read-only SELECTs).
        """
        pass

    @abstractmethod
    def execute(self, conn: sqlite3.Connection, arguments: dict[str, Any]) -> StateDelta:
        """
        Execute the tool's mutation on the ERP state and return the actual StateDelta.
        This is only called by the ERPExecutor if the gate returned ALLOW.
        """
        pass

    def validate_arguments(self, arguments: dict[str, Any]) -> None:
        """
        Validate tool-specific argument logic. 
        Should raise packages.tools.registry.ToolSchemaValidationError on failure.
        """
        pass
