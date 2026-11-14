"""
Integration tests for NASA FIRMS client and ingestion workflow.
"""

import pytest
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.database import Base
from backend.services.nasa.client import NASAClient
from backend.services.nasa.ingestion_service import IngestionService
from backend.core.exceptions.base import ConfigurationError


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


class TestNASAIngestion:
    def test_unconfigured_map_key_fails_safely(self):
        client = NASAClient(map_key="")
        assert client.is_configured() is False
        with pytest.raises(ConfigurationError):
            client.fetch_country_fires("IND")

    def test_ingestion_with_mocked_nasa_response(self, test_db):
        mock_csv = """latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,confidence,version,bright_ti5,frp,daynight
30.850,75.400,340.5,0.4,0.35,2025-10-25,0830,NOAA-20,nominal,2.0NRT,298.5,15.2,D
30.860,75.410,345.0,0.4,0.35,2025-10-25,0830,NOAA-20,high,2.0NRT,301.0,22.4,D
"""
        client = NASAClient(map_key="valid_test_mock_key_12345")
        client._execute_request = MagicMock(return_value=mock_csv)

        service = IngestionService(test_db, client)
        job = service.run_country_ingestion(country_code="IND", source="VIIRS_NOAA20_NRT")

        assert job.status == "COMPLETED"
        assert job.records_retrieved == 2
        assert job.records_valid == 2
        assert job.records_quarantined == 0
