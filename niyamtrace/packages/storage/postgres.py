from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from packages.config import get_settings


def get_async_engine(db_url: str | None = None):
    settings = get_settings()
    
    if db_url is not None:
        if db_url.startswith("sqlite+aiosqlite://"):
            url = db_url
        else:
            url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    elif settings.erp_db_type == "postgres":
        # Format for asyncpg: postgresql+asyncpg://user:pass@host/dbname
        url = settings.erp_db_url.replace("postgresql://", "postgresql+asyncpg://")
        if not url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgres://", "postgresql+asyncpg://")
    else:
        # SQLite fallback for dev/test
        # Format for aiosqlite: sqlite+aiosqlite:///...
        url = settings.erp_db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
        if "sqlite+aiosqlite:///" in url and not url.startswith("sqlite+aiosqlite:////"):
            # Ensure it resolves correctly if relative
            import os
            # niyamtrace directory is root
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            # The setting defaults to sqlite:///niyamtrace/data/...
            # which is relative to the outer repo root. 
            # If we're inside niyamtrace, we want to resolve it correctly.
            db_path = url.replace("sqlite+aiosqlite:///", "")
            if db_path.startswith("niyamtrace/"):
                db_path = db_path.replace("niyamtrace/", "", 1)
            abs_path = os.path.join(root_dir, db_path).replace("\\", "/")
            url = f"sqlite+aiosqlite:///{abs_path}"
    
    engine = create_async_engine(
        url,
        echo=settings.debug_mode,
        future=True,
    )
    return engine

# Create the global engine and session maker
engine = get_async_engine()
AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_db_session() -> AsyncSession:
    """FastAPI Dependency for database sessions."""
    async with AsyncSessionLocal() as session:
        yield session
