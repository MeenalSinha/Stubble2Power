"""
Unit Tests for Phase 10: Farmer, Farm & Biomass Intelligence.
Tests farm parcel registrations, crop cultivation records, empirical harvest logging,
mathematical residue calculations, and inventory lifecycle / double-allocation guards.
"""

import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.entities import Base, Farmer
from backend.services.farms.farm_service import FarmService
from backend.services.biomass.estimation_service import BiomassEstimationService
from backend.services.biomass.inventory_service import BiomassInventoryService
from backend.schemas.farm import FarmCreate, FarmCropCreate, HarvestRecordCreate
from backend.schemas.biomass import BiomassInventoryTransactionCreate
from backend.core.exceptions.base import ValidationError


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed baseline farmer
    farmer = Farmer(
        name="Gurdev Singh",
        phone_masked="XXXXX43210",
        district="Ludhiana",
        village="Raikot",
        latitude=30.6512,
        longitude=75.5984,
        acres=15.0,
        stubble_tons=50.0,
        harvest_date=date(2024, 10, 25),
        consent_given=True
    )
    session.add(farmer)
    session.commit()
    session.refresh(farmer)

    yield session
    session.close()


def test_create_farm_valid(db_session):
    service = FarmService(db_session)
    payload = FarmCreate(
        farmer_id=1,
        farm_name="Gurdev North Parcel",
        total_acres=15.0,
        latitude=30.6550,
        longitude=75.6010,
        state="Punjab",
        district="Ludhiana",
        tehsil="Raikot",
        village="Raikot",
        soil_type="Alluvial Loam"
    )
    farm = service.create_farm(payload)
    assert farm.id is not None
    assert farm.farmer_id == 1
    assert farm.farm_name == "Gurdev North Parcel"
    assert farm.total_acres == 15.0


def test_create_farm_invalid_coords(db_session):
    service = FarmService(db_session)
    # Latitude out of bounds via Pydantic schema validation
    with pytest.raises(Exception):
        FarmCreate(
            farmer_id=1,
            farm_name="Invalid Farm",
            total_acres=10.0,
            latitude=95.0,
            longitude=75.6010,
            district="Ludhiana",
            village="Raikot"
        )


def test_farm_crop_cultivation_lifecycle(db_session):
    farm_svc = FarmService(db_session)
    farm = farm_svc.create_farm(FarmCreate(
        farmer_id=1,
        farm_name="Gurdev Main Field",
        total_acres=10.0,
        latitude=30.6512,
        longitude=75.5984,
        state="Punjab",
        district="Ludhiana",
        village="Raikot"
    ))

    # Add crop cultivation
    crop_payload = FarmCropCreate(
        crop_type="PADDY",
        cultivated_acres=8.0,
        crop_season="Kharif",
        crop_year=2024,
        sowing_date=date(2024, 6, 20),
        expected_harvest_date=date(2024, 10, 25),
        expected_yield_tons_per_acre=2.70
    )
    crop = farm_svc.add_crop_cultivation(farm.id, crop_payload)
    assert crop.id is not None
    assert crop.crop_type == "PADDY"
    assert crop.cultivation_status == "ACTIVE"

    # Log harvest record
    harvest_payload = HarvestRecordCreate(
        harvest_date=date(2024, 10, 26),
        actual_grain_yield_tons=22.0,
        grain_moisture_pct=14.5,
        harvest_method="COMBINE_HARVESTER_WITH_SUPER_SMS",
        is_measured=True
    )
    harvest = farm_svc.record_harvest(crop.id, harvest_payload)
    assert harvest.id is not None
    assert harvest.actual_grain_yield_tons == 22.0

    # Verify crop status transitioned to HARVESTED
    db_session.refresh(crop)
    assert crop.cultivation_status == "HARVESTED"
    assert crop.actual_harvest_date == date(2024, 10, 26)


def test_biomass_estimation_paddy_math(db_session):
    farm_svc = FarmService(db_session)
    farm = farm_svc.create_farm(FarmCreate(
        farmer_id=1,
        farm_name="Paddy Calibration Field",
        total_acres=20.0,
        latitude=30.6512,
        longitude=75.5984,
        district="Ludhiana",
        village="Raikot"
    ))
    crop = farm_svc.add_crop_cultivation(farm.id, FarmCropCreate(
        crop_type="PADDY",
        cultivated_acres=20.0,
        crop_season="Kharif",
        crop_year=2024,
        sowing_date=date(2024, 6, 15),
        expected_harvest_date=date(2024, 10, 20)
    ))

    # Log measured grain yield of 50.0 tons
    farm_svc.record_harvest(crop.id, HarvestRecordCreate(
        harvest_date=date(2024, 10, 20),
        actual_grain_yield_tons=50.0,
        grain_moisture_pct=14.0
    ))

    biomass_svc = BiomassEstimationService(db_session)
    estimate = biomass_svc.estimate_crop_biomass(farm_crop_id=crop.id)

    # Mathematical assertions:
    # Gross residue = 50.0 * 1.50 = 75.0 tons
    assert estimate.gross_residue_tons == pytest.approx(75.0, 0.1)
    # Collectable fraction = 0.75 -> retained = 25% (18.75 tons)
    assert estimate.retained_residue_tons == pytest.approx(18.75, 0.1)
    assert estimate.collectable_residue_tons == pytest.approx(56.25, 0.1)
    # Handling losses = 8% of collectable (4.50 tons)
    assert estimate.handling_loss_tons == pytest.approx(4.50, 0.1)
    # Net usable = 56.25 - 4.50 = 51.75 tons
    assert estimate.net_usable_biomass_tons == pytest.approx(51.75, 0.1)
    assert estimate.estimation_source == "MEASURED"
    assert estimate.confidence_score >= 0.95


def test_biomass_inventory_lifecycle_and_double_allocation_prevention(db_session):
    farm_svc = FarmService(db_session)
    farm = farm_svc.create_farm(FarmCreate(
        farmer_id=1,
        farm_name="Inventory Test Parcel",
        total_acres=10.0,
        latitude=30.6512,
        longitude=75.5984,
        district="Ludhiana",
        village="Raikot"
    ))
    crop = farm_svc.add_crop_cultivation(farm.id, FarmCropCreate(
        crop_type="WHEAT",
        cultivated_acres=10.0,
        crop_season="Rabi",
        crop_year=2024,
        expected_yield_tons_per_acre=2.0
    ))

    # Generate estimate directly without measured harvest (scientific model fallback)
    biomass_svc = BiomassEstimationService(db_session)
    estimate = biomass_svc.estimate_crop_biomass(farm_crop_id=crop.id)
    assert estimate.net_usable_biomass_tons > 0.0

    net_usable = estimate.net_usable_biomass_tons
    inv_svc = BiomassInventoryService(db_session)

    # 1. Valid allocation within capacity
    half_qty = round(net_usable / 2.0, 2)
    tx1 = inv_svc.record_transaction(BiomassInventoryTransactionCreate(
        biomass_estimate_id=estimate.id,
        farm_id=farm.id,
        quantity_tons=half_qty,
        stage="ALLOCATED",
        allocated_unit_id=1
    ))
    assert tx1.id is not None
    assert tx1.stage == "ALLOCATED"

    # 2. Exceeding allocation must trigger ValidationError
    overflow_qty = round(net_usable, 2)  # half + full > net_usable
    with pytest.raises(ValidationError):
        inv_svc.record_transaction(BiomassInventoryTransactionCreate(
            biomass_estimate_id=estimate.id,
            farm_id=farm.id,
            quantity_tons=overflow_qty,
            stage="ALLOCATED",
            allocated_unit_id=2
        ))
