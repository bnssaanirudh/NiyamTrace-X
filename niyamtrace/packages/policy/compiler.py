from packages.policy.loader import PolicyLoader
from packages.policy.models import ToolRule

class PolicyCompiler:
    def __init__(self, loader: PolicyLoader):
        self.loader = loader

    def get_rule(self, tool_name: str) -> ToolRule | None:
        return self.loader.bundle.rules.get(tool_name)

    def is_role_allowed(self, tool_name: str, role: str) -> bool:
        rule = self.get_rule(tool_name)
        if not rule:
            return False
        return role in rule.allowed_roles

    def is_attribute_allowed(self, tool_name: str, attribute: str) -> bool:
        rule = self.get_rule(tool_name)
        if not rule:
            return False
        return attribute in rule.allowed_attributes

    def get_max_rows_without_approval(self, tool_name: str) -> int:
        rule = self.get_rule(tool_name)
        if not rule:
            return 0
        return rule.max_rows_without_approval

    def is_evidence_required(self, tool_name: str) -> bool:
        rule = self.get_rule(tool_name)
        if not rule:
            return True # fail safe
        return rule.evidence_required

    def get_approval_threshold(self, tool_name: str) -> int | None:
        rule = self.get_rule(tool_name)
        if not rule or not rule.approval:
            return None
        return rule.approval.required_above_rows
    
    @property
    def policy_hash(self) -> str:
        return self.loader.bundle_hash
