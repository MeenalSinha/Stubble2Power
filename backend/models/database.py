"""
Database connection, session management, and engine initialization.
Supports PostgreSQL/PostGIS in production and SQLite for local development and testing.
"""

import os
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from backend.core.config.settings import app_settings
from backend.core.logging.logger import get_logger

logger = get_logger("stubble2power.database")


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy models."""
    pass


def get_engine():
    """Builds and returns the SQLAlchemy engine."""
    db_url = app_settings.database_url
    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        # Ensure database directory exists
        db_path = db_url.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    engine = create_engine(
        db_url,
        connect_args=connect_args,
        pool_pre_ping=True
    )
    return engine


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for safe database transactions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database transaction error: {str(e)}")
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database session injection."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def check_db_health() -> bool:
    """Verifies active connectivity to the database engine."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False


def init_db():
    """Initializes schema tables if they do not exist."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")
