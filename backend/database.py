"""
database.py — SQLAlchemy + SQLite database setup for CrisisMesh.
Provides engine, SessionLocal, Base, and the get_db FastAPI dependency.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./crisismesh.db"

# connect_args is required for SQLite to allow multi-threaded access
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a database session and ensures it is
    closed after the request completes (success or failure).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
