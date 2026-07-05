import os
from sqlmodel import SQLModel, create_engine, Session

# Set target SQLite database location. Default to data/penalty_games.db
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///../data/penalty_games.db")

# SQLite specific argument connect_args={"check_same_thread": False} allows multiple worker threads
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

def create_db_and_tables():
    """
    Creates SQLite database file and initial schemas if they do not exist.
    """
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if "sqlite:" in DATABASE_URL:
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    SQLModel.metadata.create_all(engine)

def get_session():
    """
    FastAPI dependency injection utility. Yields a new database session
    and closes it when the HTTP request has finished.
    """
    with Session(engine) as session:
        yield session
