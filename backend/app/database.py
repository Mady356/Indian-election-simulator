"""Database engine and session management."""

import os
from collections.abc import Generator
from pathlib import Path

from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()

# Default to SQLite so the API works locally without Postgres running.
# For Postgres: set DATABASE_URL=postgresql://localhost/election_simulator
_DEFAULT_SQLITE = (
    Path(__file__).resolve().parents[1] / "data" / "election_simulator.db"
)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{_DEFAULT_SQLITE}",
)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_checked() -> Generator[Session, None, None]:
    """Yield a DB session or raise 503 if the database is unreachable."""
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        db.close()
        raise HTTPException(
            status_code=503,
            detail={
                "error": "database_unavailable",
                "message": (
                    "Cannot connect to the database. "
                    "Run: python backend/scripts/load_csvs_to_postgres.py"
                ),
                "database_url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL,
                "hint": str(exc.orig) if getattr(exc, "orig", None) else str(exc),
            },
        ) from exc
    try:
        yield db
    finally:
        db.close()
