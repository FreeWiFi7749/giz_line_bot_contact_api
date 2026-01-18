"""
Database configuration and session management
"""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from .config import settings

Base = declarative_base()

# Lazy initialization for engine and session maker
_engine: Optional[AsyncEngine] = None
_async_session_maker: Optional[async_sessionmaker] = None


def get_engine() -> AsyncEngine:
    """Get or create the database engine"""
    global _engine
    if _engine is None:
        # Convert postgresql:// to postgresql+asyncpg:// for async support
        database_url = settings.DATABASE_URL
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        
        _engine = create_async_engine(
            database_url,
            echo=settings.DEBUG,
            pool_pre_ping=True,
        )
    return _engine


def get_session_maker() -> async_sessionmaker:
    """Get or create the session maker"""
    global _async_session_maker
    if _async_session_maker is None:
        _async_session_maker = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_maker


async def get_db() -> AsyncSession:
    """Dependency for getting database session"""
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
