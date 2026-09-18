import yaml
import json
import hashlib
from pathlib import Path
from packages.policy.models import PolicyBundle
from packages.policy.signature import verify_signature

class PolicyLoadError(Exception):
    pass

class PolicyLoader:
    def __init__(self, policy_path: str):
        self.policy_path = Path(policy_path)
        self._bundle: PolicyBundle | None = None
        self._hash: str | None = None

    def load(self, require_signature: bool = False, signature: str | None = None) -> PolicyBundle:
        """
        Loads, validates, and hashes the policy bundle.
        """
        if not self.policy_path.exists():
            raise PolicyLoadError(f"Policy file not found: {self.policy_path}")

        try:
            content_bytes = self.policy_path.read_bytes()
            if require_signature and not verify_signature(content_bytes, signature):
                raise PolicyLoadError("Policy signature verification failed")

            data = yaml.safe_load(content_bytes)
            self._bundle = PolicyBundle(**data)
            
            # Deterministic hash of the validated model (ignoring formatting)
            normalized_json = json.dumps(self._bundle.model_dump(mode="json"), sort_keys=True)
            self._hash = hashlib.sha256(normalized_json.encode()).hexdigest()[:16]
            
            return self._bundle
        except Exception as e:
            raise PolicyLoadError(f"Failed to load policy: {str(e)}")

    @property
    def bundle(self) -> PolicyBundle:
        if not self._bundle:
            self.load()
        return self._bundle

    @property
    def bundle_hash(self) -> str:
        if not self._hash:
            self.load()
        return self._hash
