"""
packages/storage/session.py — Transaction session manager
"""
import logging
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.storage.models import NiyamIdempotency

logger = logging.getLogger(__name__)

class StateMismatchError(Exception):
    """Raised when actual execution delta does not match predicted delta."""

class IdempotencyError(Exception):
    """Raised when an idempotency key has already been executed."""

class SessionManager:
    def __init__(self, session: AsyncSession):
        self._session = session

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Provides a transactional boundary.
        Uses SQLAlchemy's async session which automatically starts a transaction.
        """
        in_transaction = True
        try:
            yield self._session
            await self._session.commit()
            in_transaction = False
        except Exception:
            if in_transaction:
                try:
                    await self._session.rollback()
                except Exception:
                    pass
            raise

    async def check_idempotency(self, idempotency_key: str) -> bool:
        """Returns True if the idempotency key was already executed."""
        if not idempotency_key:
            return False
        
        stmt = select(NiyamIdempotency).where(NiyamIdempotency.idempotency_key == idempotency_key)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def record_idempotency(self, idempotency_key: str, result_payload: str = ""):
        """Records an idempotency key after successful execution."""
        if idempotency_key:
            record = NiyamIdempotency(
                idempotency_key=idempotency_key,
                executed_at=time.time(),
                result_payload=result_payload
            )
            self._session.add(record)

    # Note: state version management was historically tied to SQLite PRAGMA user_version.
    # We stub it out here for PostgreSQL compatibility. If strict versioning is needed,
    # it should be managed via a dedicated metadata table.
    async def get_state_version(self) -> int:
        return 0

    async def increment_state_version(self) -> int:
        return 1
