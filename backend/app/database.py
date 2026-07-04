import os
from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///../data/penalty_games.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

def create_db_and_tables():
    # Ensure the target directory for SQLite exists
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if "sqlite:" in DATABASE_URL:
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
