"""
packages/secrets/manager.py — NiyamTrace Secrets Manager

Provides a unified abstraction for secret retrieval across backends:
  - env  (default): reads from environment variables / .env file via python-dotenv
  - aws  (optional): reads from AWS Secrets Manager via boto3
  - vault(optional): reads from HashiCorp Vault via hvac

Backend is selected via NIYAMTRACE_SECRETS_BACKEND env var (default: "env").

Usage:
    from packages.secrets.manager import SecretsManager
    sm = SecretsManager()
    api_key = sm.get("GEMINI_API_KEY")

The manager caches resolved secrets in-process to avoid repeated API calls.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)


class SecretNotFoundError(KeyError):
    """Raised when a required secret cannot be resolved."""


class SecretsManager:
    """
    Pluggable secrets resolver.

    Constructor args:
        backend:  "env" | "aws" | "vault" — overrides NIYAMTRACE_SECRETS_BACKEND
        region:   AWS region name (only used for aws backend)
        vault_url: HashiCorp Vault base URL (only used for vault backend)
    """

    def __init__(
        self,
        backend: str | None = None,
        region: str = "ap-south-1",
        vault_url: str | None = None,
    ) -> None:
        self._backend = (
            backend
            or os.environ.get("NIYAMTRACE_SECRETS_BACKEND", "env")
        ).lower()
        self._region = region
        self._vault_url = vault_url or os.environ.get("VAULT_ADDR", "http://127.0.0.1:8200")
        self._cache: dict[str, str] = {}

        # Load .env file for the env backend (no-op if dotenv not installed)
        if self._backend == "env":
            self._load_dotenv()

        logger.debug("SecretsManager: using backend=%s", self._backend)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str, default: str | None = None) -> str:
        """
        Retrieve a secret by key.
        Returns default if provided and key is not found.
        Raises SecretNotFoundError if default is None and key not found.
        """
        if key in self._cache:
            return self._cache[key]

        try:
            value = self._resolve(key)
            self._cache[key] = value
            return value
        except SecretNotFoundError:
            if default is not None:
                return default
            raise

    def get_optional(self, key: str) -> str | None:
        """Retrieve a secret or None if not found (never raises)."""
        try:
            return self.get(key)
        except SecretNotFoundError:
            return None

    # ------------------------------------------------------------------
    # Backend dispatch
    # ------------------------------------------------------------------

    def _resolve(self, key: str) -> str:
        if self._backend == "env":
            return self._resolve_env(key)
        elif self._backend == "aws":
            return self._resolve_aws(key)
        elif self._backend == "vault":
            return self._resolve_vault(key)
        else:
            raise ValueError(f"Unknown secrets backend: {self._backend!r}")

    # ------------------------------------------------------------------
    # env backend
    # ------------------------------------------------------------------

    def _load_dotenv(self) -> None:
        """Load .env file if python-dotenv is available."""
        try:
            from dotenv import load_dotenv
            # Look for .env relative to CWD or two levels up
            for path in [".env", "../.env", "../../.env"]:
                if os.path.exists(path):
                    load_dotenv(path, override=False)
                    logger.debug("SecretsManager: loaded .env from %s", path)
                    return
        except ImportError:
            pass

    def _resolve_env(self, key: str) -> str:
        value = os.environ.get(key)
        if value is None:
            raise SecretNotFoundError(f"Secret not found in environment: {key!r}")
        return value

    # ------------------------------------------------------------------
    # AWS Secrets Manager backend
    # ------------------------------------------------------------------

    def _resolve_aws(self, key: str) -> str:
        """
        Resolve a secret from AWS Secrets Manager.

        The secret name is read from:
          AWS_SECRET_NAME env var (if set), or the key name itself.

        The secret value must be a JSON object where each key maps to a secret value,
        OR a plain string for single-value secrets.
        """
        try:
            import boto3  # type: ignore[import]
            import json as _json

            secret_name = os.environ.get("AWS_SECRET_NAME", "niyamtrace/secrets")
            client = boto3.client("secretsmanager", region_name=self._region)
            response = client.get_secret_value(SecretId=secret_name)
            secret_str = response.get("SecretString", "{}")
            try:
                secret_dict = _json.loads(secret_str)
                value = secret_dict.get(key)
            except (_json.JSONDecodeError, AttributeError):
                # Plain string secret
                value = secret_str if key == secret_name else None

            if value is None:
                raise SecretNotFoundError(
                    f"Key {key!r} not found in AWS secret {secret_name!r}"
                )
            return str(value)

        except ImportError:
            logger.warning(
                "SecretsManager: boto3 not installed. Falling back to env backend."
            )
            return self._resolve_env(key)

    # ------------------------------------------------------------------
    # HashiCorp Vault backend
    # ------------------------------------------------------------------

    def _resolve_vault(self, key: str) -> str:
        """
        Resolve a secret from HashiCorp Vault KV v2.

        The secret path is read from VAULT_SECRET_PATH env var
        (default: "secret/niyamtrace"). The Vault token is read from
        VAULT_TOKEN env var.
        """
        try:
            import hvac  # type: ignore[import]

            token = os.environ.get("VAULT_TOKEN")
            secret_path = os.environ.get("VAULT_SECRET_PATH", "secret/niyamtrace")
            client = hvac.Client(url=self._vault_url, token=token)

            # KV v2 — mount and path
            mount, path = secret_path.split("/", 1)
            response = client.secrets.kv.v2.read_secret_version(
                path=path, mount_point=mount
            )
            secret_dict = response["data"]["data"]
            value = secret_dict.get(key)
            if value is None:
                raise SecretNotFoundError(
                    f"Key {key!r} not found at Vault path {secret_path!r}"
                )
            return str(value)

        except ImportError:
            logger.warning(
                "SecretsManager: hvac not installed. Falling back to env backend."
            )
            return self._resolve_env(key)


# ---------------------------------------------------------------------------
# Module-level singleton for convenience import
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_secrets_manager() -> SecretsManager:
    """Return the shared singleton SecretsManager for the current process."""
    return SecretsManager()
