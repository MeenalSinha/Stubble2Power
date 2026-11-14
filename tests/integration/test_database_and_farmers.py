"""
Integration tests for database initialization, transactions, and FarmerService operations.
"""

import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.database import Base
from backend.services.farmers.service import FarmerService
from backend.schemas.farmer import FarmerCreate


@pytest.fixture
def test_db_session():
    """In-memory SQLite database session fixture."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


class TestDatabaseAndFarmerService:
    def test_farmer_crud_lifecycle(self, test_db_session):
        svc = FarmerService(test_db_session)

        # 1. Register farmer
        farmer_in = FarmerCreate(
            name="Sukhbir Singh",
            village="Khanna",
            district="Ludhiana",
            state="Punjab",
            country="IND",
            acres=25.0,
            stubble_tons=18.5,
            harvest_date=date(2025, 10, 28),
            latitude=30.7056,
            longitude=76.2222
        )
        created = svc.register_farmer(farmer_in)
        assert created.id is not None
        assert created.name == "Sukhbir Singh"

        # 2. Query farmer
        farmers = svc.list_farmers(village="Khanna")
        assert len(farmers) == 1
        assert farmers[0].id == created.id

        # 3. Summary stats
        stats = svc.get_summary_stats()
        assert stats["total_farmers"] == 1
        assert stats["total_stubble_tons"] == 18.5
        assert stats["total_villages"] == 1

        # 4. DataFrame export
        df = svc.get_farmer_dataframe()
        assert len(df) == 1
        assert "Farmer Name" in df.columns
        assert df.iloc[0]["Farmer Name"] == "Sukhbir Singh"

    def test_csv_import(self, test_db_session):
        svc = FarmerService(test_db_session)
        csv_data = """Farmer Name,Village,District,Latitude,Longitude,Stubble (tons),Acres
Gurpreet Singh,Moga,Moga,30.8158,75.1711,15.0,20.0
Harinder Kaur,Bathinda,Bathinda,30.2110,74.9455,22.0,30.0
"""
        result = svc.import_farmers_csv(csv_data)
        assert result["records_imported"] == 2
        assert result["errors_count"] == 0

        stats = svc.get_summary_stats()
        assert stats["total_farmers"] == 2
        assert stats["total_stubble_tons"] == 37.0
