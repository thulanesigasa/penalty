import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Configure async SQLite connection via aiosqlite driver
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///../data/penalty_games.db")

if DATABASE_URL.startswith("sqlite:///"):
    DATABASE_URL = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")

# Async SQLite engine
engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Async Session factory
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def create_db_and_tables():
    """
    Asynchronously initializes folders, databases, and schemas.
    """
    if "sqlite" in DATABASE_URL:
        db_parts = DATABASE_URL.split(":///")
        if len(db_parts) > 1:
            db_path = db_parts[1]
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)

    async with engine.begin() as conn:
        # Execute metadata table creation asynchronously
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session():
    """
    Asynchronous FastAPI dependency injector. Yields an active AsyncSession.
    """
    async with async_session_maker() as session:
        yield session
