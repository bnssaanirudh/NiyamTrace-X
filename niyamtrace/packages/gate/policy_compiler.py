"""
packages/gate/policy_compiler.py — YAML-Driven Policy Bundle Compiler

Reads a YAML policy file and compiles it into a PolicyBundle instance.
Supports:
  - role_hierarchy: roles inherit permissions from parent roles
  - conditional_rules: per-tool escalation/block overrides
  - deterministic bundle_hash from YAML content SHA-256

Usage:
    from packages.gate.policy_compiler import PolicyCompiler
    bundle = PolicyCompiler.from_yaml("data/policies/default_policy.yaml")

The pipeline uses this at startup. Fallback to DEFAULT_POLICY if YAML not found.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ConditionalRule:
    """A conditional policy rule that can trigger ESCALATE or BLOCK."""
    condition: str          # Human-readable condition string (evaluated in gate)
    action: str             # "ESCALATE" or "BLOCK"
    reason: str             # Machine-readable reason code
    escalate_to_role: str = ""


@dataclass
class ToolPolicy:
    """Policy config for a single tool."""
    name: str
    allowed_roles: list[str] = field(default_factory=list)
    allowed_attributes: set[str] = field(default_factory=set)
    conditional_rules: list[ConditionalRule] = field(default_factory=list)


@dataclass
class CompiledPolicyBundle:
    """
    A fully compiled, immutable policy bundle produced by PolicyCompiler.
    Drop-in replacement for the hard-coded PolicyBundle dataclass.
    """
    version: str = "unknown"
    bundle_id: str = "unknown"
    cardinality_threshold: int = 10
    tool_policies: dict[str, ToolPolicy] = field(default_factory=dict)
    role_graph: dict[str, list[str]] = field(default_factory=dict)  # role → inherited roles
    _yaml_hash: str = ""

    def bundle_hash(self) -> str:
        return self._yaml_hash

    @property
    def bundle_version(self) -> str:
        return self.version

    def allowed_roles_for(self, tool_name: str) -> list[str]:
        """Return expanded roles (including inherited) for the given tool."""
        tp = self.tool_policies.get(tool_name)
        if not tp:
            return []
        # Expand via role hierarchy
        expanded: set[str] = set(tp.allowed_roles)
        for role in list(expanded):
            expanded.update(self._inherited_roles(role))
        return sorted(expanded)

    def _inherited_roles(self, role: str, _visited: set[str] | None = None) -> list[str]:
        """Recursively collect all roles that can inherit into the given role."""
        visited = _visited or set()
        result: list[str] = []
        for base_role, inheritors in self.role_graph.items():
            if role in inheritors and base_role not in visited:
                visited.add(base_role)
                result.append(base_role)
                result.extend(self._inherited_roles(base_role, visited))
        return result

    def allowed_attributes_for(self, tool_name: str) -> set[str]:
        tp = self.tool_policies.get(tool_name)
        return tp.allowed_attributes if tp else set()

    def conditional_rules_for(self, tool_name: str) -> list[ConditionalRule]:
        tp = self.tool_policies.get(tool_name)
        return tp.conditional_rules if tp else []

    # ---- Compatibility shims for code that reads the old PolicyBundle fields ----

    @property
    def allowed_roles_for_archive(self) -> list[str]:
        return self.allowed_roles_for("archive_invoices")

    @property
    def allowed_roles_for_block_user(self) -> list[str]:
        return self.allowed_roles_for("block_user_access")

    @property
    def allowed_roles_for_credit_limit(self) -> list[str]:
        return self.allowed_roles_for("update_credit_limit")

    @property
    def allowed_roles_for_suspend_vendor(self) -> list[str]:
        return self.allowed_roles_for("suspend_vendor")

    @property
    def allowed_attributes(self) -> dict[str, set[str]]:
        return {name: tp.allowed_attributes for name, tp in self.tool_policies.items()}


class PolicyCompiler:
    """Compiles a YAML policy file into a CompiledPolicyBundle."""

    @staticmethod
    def from_yaml(yaml_path: str | Path) -> CompiledPolicyBundle:
        """
        Load and compile a YAML policy file.
        Returns a CompiledPolicyBundle or raises FileNotFoundError/ValueError.
        """
        path = Path(yaml_path)
        if not path.exists():
            raise FileNotFoundError(f"Policy YAML not found: {path}")

        try:
            import yaml  # PyYAML — optional but recommended
        except ImportError:
            # Fallback: attempt to use a minimal YAML-subset loader
            logger.warning(
                "PolicyCompiler: PyYAML not installed. "
                "Install it with: pip install pyyaml"
            )
            raise ImportError("PyYAML is required for PolicyCompiler. Run: pip install pyyaml")

        raw_bytes = path.read_bytes()
        yaml_hash = hashlib.sha256(raw_bytes).hexdigest()[:16]
        data: dict[str, Any] = yaml.safe_load(raw_bytes)

        return PolicyCompiler._compile(data, yaml_hash)

    @staticmethod
    def _compile(data: dict[str, Any], yaml_hash: str) -> CompiledPolicyBundle:
        """Parse the YAML structure into a CompiledPolicyBundle."""
        version = data.get("version", "unknown")
        bundle_id = data.get("bundle_id", "unknown")
        cardinality_threshold = data.get("global", {}).get("cardinality_threshold", 10)

        # Build role hierarchy graph: role → list of roles it inherits
        role_graph: dict[str, list[str]] = {}
        for entry in data.get("role_hierarchy", []):
            role = entry["role"]
            role_graph[role] = entry.get("inherits", [])

        # Build tool policies
        tool_policies: dict[str, ToolPolicy] = {}
        for tool_data in data.get("tools", []):
            name = tool_data["name"]
            rules = []
            for cr in tool_data.get("conditional_rules", []):
                rules.append(ConditionalRule(
                    condition=cr.get("condition", ""),
                    action=cr.get("action", "ESCALATE"),
                    reason=cr.get("reason", ""),
                    escalate_to_role=cr.get("escalate_to_role", ""),
                ))
            tool_policies[name] = ToolPolicy(
                name=name,
                allowed_roles=tool_data.get("allowed_roles", []),
                allowed_attributes=set(tool_data.get("allowed_attributes", [])),
                conditional_rules=rules,
            )

        bundle = CompiledPolicyBundle(
            version=version,
            bundle_id=bundle_id,
            cardinality_threshold=cardinality_threshold,
            tool_policies=tool_policies,
            role_graph=role_graph,
            _yaml_hash=yaml_hash,
        )
        logger.info(
            "PolicyCompiler: compiled bundle %s v%s (hash=%s, tools=%s)",
            bundle_id, version, yaml_hash, list(tool_policies.keys()),
        )
        return bundle

    @staticmethod
    def from_yaml_or_default(yaml_path: str | Path) -> Any:
        """
        Try to load from YAML; fall back to DEFAULT_POLICY on any error.
        Safe to call at startup without crashing if YAML or PyYAML missing.
        """
        from packages.gate.policy import DEFAULT_POLICY
        try:
            return PolicyCompiler.from_yaml(yaml_path)
        except Exception as exc:
            logger.warning(
                "PolicyCompiler: falling back to DEFAULT_POLICY (%s)", exc
            )
            return DEFAULT_POLICY
