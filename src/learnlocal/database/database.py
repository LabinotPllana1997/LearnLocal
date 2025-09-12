"""Database configuration and session management."""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from .models import Base
from ..config.settings import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,
    },
    echo=settings.database_echo
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_database():
    """Initialize the database tables."""
    import os
    os.makedirs(settings.data_directory, exist_ok=True)
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        print("Continuing without database...")

async def get_database_session():
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def close_database():
    """Close the database connection."""
    await engine.dispose()