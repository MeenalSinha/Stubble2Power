"""
Unit Tests for Phase 13: User Experience, Personalization, Notifications, and Reporting.
Tests multi-lingual user preferences, real notification lifecycles, auditable report generation,
and purpose-bound consent workflows.
"""

import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.entities import Base, User, Farmer
from backend.services.user_experience.user_experience_service import UserExperienceService
from backend.services.privacy.privacy_service import PrivacyService
from backend.schemas.user_experience import UserPreferenceUpdate


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed baseline user & farmer
    user = User(
        username="test_user_ux",
        email="ux@test.com",
        full_name="Test User",
        role_name="FARMER",
        is_active=True
    )
    farmer = Farmer(
        name="Harjit Singh",
        village="Raikot",
        district="Ludhiana",
        state="Punjab",
        acres=20.0,
        stubble_tons=16.0,
        harvest_date=date(2025, 10, 28),
        latitude=30.6500,
        longitude=75.6000
    )
    session.add_all([user, farmer])
    session.commit()
    session.refresh(user)
    session.refresh(farmer)
    yield session
    session.close()


def test_user_preferences_lifecycle(db_session):
    ux_svc = UserExperienceService(db_session)
    user = db_session.query(User).first()

    # Initial default preference creation
    pref = ux_svc.get_or_create_preferences(user.id)
    assert pref.preferred_language == "en"
    assert pref.theme == "light"

    # Update to Punjabi and dark theme
    updated = ux_svc.update_preferences(user.id, UserPreferenceUpdate(
        preferred_language="pa",
        theme="dark",
        default_aoi="Malwa Belt"
    ))
    assert updated.preferred_language == "pa"
    assert updated.theme == "dark"
    assert updated.default_aoi == "Malwa Belt"


def test_notification_creation_and_reading(db_session):
    ux_svc = UserExperienceService(db_session)
    user = db_session.query(User).first()

    # Create notifications
    notif1 = ux_svc.create_notification(
        user_id=user.id,
        title="Harvest Window Open",
        message="Paddy harvesting has commenced in your district.",
        category="HARVEST",
        priority="HIGH"
    )
    notif2 = ux_svc.create_notification(
        user_id=user.id,
        title="System Maintenance",
        message="Scheduled maintenance on Sunday at 02:00 AM.",
        category="SYSTEM",
        priority="LOW"
    )
    assert notif1.id is not None
    assert notif2.id is not None

    # Query unread
    unread = ux_svc.list_user_notifications(user.id, unread_only=True)
    assert len(unread) == 2

    # Mark first read
    ux_svc.mark_notification_read(notif1.id, user.id)
    unread_after = ux_svc.list_user_notifications(user.id, unread_only=True)
    assert len(unread_after) == 1
    assert unread_after[0].id == notif2.id


def test_report_generation_from_real_records(db_session):
    ux_svc = UserExperienceService(db_session)
    user = db_session.query(User).first()

    # Generate Farmer Directory report
    rep = ux_svc.generate_and_save_report(
        user_id=user.id,
        report_type="FARMER_DIRECTORY",
        title="Ludhiana Farmer Directory 2025",
        file_format="CSV"
    )
    assert rep.id is not None
    assert rep.report_type == "FARMER_DIRECTORY"
    assert rep.summary_data_json["record_count"] == 1
    assert rep.summary_data_json["total_acreage"] == 20.0
    assert "Ludhiana" in rep.summary_data_json["districts"]


def test_consent_management_and_withdrawal(db_session):
    priv_svc = PrivacyService(db_session)
    farmer = db_session.query(Farmer).first()

    # Grant purpose-specific consent
    c1 = priv_svc.record_consent(
        farmer_id=farmer.id,
        consent_purpose="BIOMASS_AGGREGATION",
        consent_version="v1.2",
        notes="Agreed to mechanical baling"
    )
    assert c1.id is not None
    assert c1.is_granted is True
    assert c1.consent_purpose == "BIOMASS_AGGREGATION"

    # Grant second distinct purpose
    c2 = priv_svc.record_consent(
        farmer_id=farmer.id,
        consent_purpose="SATELLITE_FIRE_CORRELATION",
        consent_version="v1.2"
    )
    assert c2.id is not None

    consents = priv_svc.list_consents_for_farmer(farmer.id)
    assert len(consents) == 2

    # Withdraw first consent
    withdrawn = priv_svc.withdraw_consent(c1.id)
    assert withdrawn.is_granted is False
    assert withdrawn.withdrawn_at is not None
