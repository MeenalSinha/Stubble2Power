"""
Stubble2Power - Satellite Fire Intelligence & Mobile Bio-Refinery Platform.
Phases 0-14 Enterprise Implementation.
Harmonizes NASA MODIS & VIIRS Earth Observations with Decentralized Agricultural Waste Management.
Professional Multi-User Role-Based Access Control, Tenant Isolation & DPDP Act 2023 Compliance.
Zero emojis compliance (Rule 7 & Rule 9).
"""

import streamlit as st

# Backend Database & Initialization
from backend.models.database import SessionLocal, init_db, check_db_health
from backend.services.farmers.service import FarmerService
from backend.services.nasa.client import NASAClient
from backend.repositories.satellite_repository import SatelliteRepository
from backend.repositories.harmonization_repository import HarmonizationRepository
from backend.services.calendar.service import CalendarAggregationService

# Modern UI Components & Workspaces
from frontend.streamlit_app.styles.theme import GLASSMORPHISM_CSS
from frontend.streamlit_app.components.sidebar import render_sidebar
from frontend.streamlit_app.components.public_workspace import render_public_workspace
from frontend.streamlit_app.components.farmer_workspace import render_farmer_workspace
from frontend.streamlit_app.components.operator_workspace import render_operator_workspace
from frontend.streamlit_app.components.agri_analyst_workspace import render_agri_analyst_workspace
from frontend.streamlit_app.components.env_analyst_workspace import render_env_analyst_workspace
from frontend.streamlit_app.components.org_manager_workspace import render_org_manager_workspace
from frontend.streamlit_app.components.admin_workspace import render_admin_workspace
from frontend.streamlit_app.components.technical_explorer import render_technical_engine_explorer

# Ensure database schema is initialized
init_db()

# ============================================================================
# PAGE CONFIGURATION (Strict zero-emoji compliance)
# ============================================================================
st.set_page_config(
    page_title="Stubble2Power - Satellite Fire Intelligence & Mobile Bio-Refineries",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply global styling
st.markdown(GLASSMORPHISM_CSS, unsafe_allow_html=True)


def get_db():
    return SessionLocal()


def main():
    db = get_db()
    farmer_svc = FarmerService(db)
    sat_repo = SatelliteRepository(db)
    harm_repo = HarmonizationRepository(db)
    cal_svc = CalendarAggregationService(db)
    nasa_client = NASAClient()

    # Health status check
    db_ok = check_db_health()
    nasa_ok = nasa_client.is_configured()

    # Sidebar: identity switcher, role navigation, language selection
    user_ctx, active_workspace, selected_lang = render_sidebar(db, db_ok, nasa_ok)

    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">Stubble2Power</h1>
        <p class="hero-subtitle">
            NASA Satellite Fire Intelligence & Mobile Bio-Refineries for Clean Energy
        </p>
        <div style="margin-top: 1.2rem;">
            <span class="tech-badge">NASA FIRMS (MODIS & VIIRS)</span>
            <span class="tech-badge">Sensor Harmonization</span>
            <span class="tech-badge">Mobile Bio-Refineries</span>
            <span class="tech-badge">70% Logistics Cost Reduction</span>
            <span class="tech-badge">Carbon Negative</span>
            <span class="tech-badge">DPDP Act 2023 Compliant</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Workspace Dispatcher
    if active_workspace == "Public Fire Intelligence & Mission":
        render_public_workspace(db, lang=selected_lang)
    elif active_workspace == "Farmer Parcel & Harvest Workspace":
        render_farmer_workspace(db, user_ctx, lang=selected_lang)
    elif active_workspace == "Mobile Unit & Route Logistics Workspace":
        render_operator_workspace(db, user_ctx, lang=selected_lang)
    elif active_workspace == "Agricultural Analyst Workspace":
        render_agri_analyst_workspace(db, user_ctx, lang=selected_lang)
    elif active_workspace == "Environmental Analyst Workspace":
        render_env_analyst_workspace(db, user_ctx, lang=selected_lang)
    elif active_workspace == "Organization Manager Workspace":
        render_org_manager_workspace(db, user_ctx, lang=selected_lang)
    elif active_workspace == "System Administrator Workspace":
        render_admin_workspace(db, user_ctx, lang=selected_lang)
    elif active_workspace == "Technical Engine Explorer":
        render_technical_engine_explorer(db, farmer_svc, sat_repo, harm_repo, cal_svc, nasa_client)
    else:
        st.info("Please select a workspace from the sidebar.")

    # Footer
    st.markdown("""
    <div class="footer">
        <h3 style="color: #2d5f3f !important; margin: 0.5rem 0;">Stubble2Power</h3>
        <p style="color: #666; margin-bottom: 1rem;">
            Satellite Intelligence. Sustainable Agriculture. Clean Energy.
        </p>
        <p style="opacity: 0.75; font-size: 0.9rem;">
            NASA Space Apps Challenge 09: Harmonization of MODIS and VIIRS Hot Spots<br>
            Powered by PostGIS Spatial Architecture + Geodesic Harmonization Engine | Copyright 2026 Stubble2Power Team
        </p>
    </div>
    """, unsafe_allow_html=True)

    db.close()


if __name__ == "__main__":
    main()
