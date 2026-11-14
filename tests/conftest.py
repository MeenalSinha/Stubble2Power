"""
Pytest Central Configuration & Test Fixtures.
Provides shared in-memory database sessions and test harnesses.
"""

from datetime import date
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.database import Base
from backend.models.entities import Farmer, AreaOfInterest


@pytest.fixture
def db_session():
    """Provides a fresh, isolated in-memory SQLite database session for each test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    # Pre-seed default AOI for Punjab to assist spatial queries
    aoi = AreaOfInterest(
        name="Punjab Central",
        country_code="IND",
        description="Central agricultural belt of Punjab",
        min_latitude=29.5,
        max_latitude=32.5,
        min_longitude=73.8,
        max_longitude=76.9,
        is_active=True
    )
    session.add(aoi)
    session.commit()

    try:
        yield session
    finally:
        session.close()
