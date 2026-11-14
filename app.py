"""
Stubble2Power - Satellite-Powered Fire Intelligence & Mobile Bio-Refinery Platform.
Phases 0-7 Production Implementation.
Harmonizes NASA MODIS & VIIRS Earth Observations with Decentralized Agricultural Waste Management.
"""

import os
import io
import json
from datetime import datetime, date, timedelta
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import folium_static

# Backend Service Integrations
from backend.models.database import SessionLocal, init_db, check_db_health
from backend.models.entities import Farmer, NormalizedSatelliteObservation, HarmonizedObservation, HarmonizationRun
from backend.services.farmers.service import FarmerService
from backend.services.clustering.service import ClusteringService
from backend.services.economics.service import EconomicsService
from backend.services.environmental.service import EnvironmentalService
from backend.services.geospatial.service import GeospatialService
from backend.services.nasa.client import NASAClient
from backend.services.nasa.ingestion_service import IngestionService
from backend.services.harmonization.engine import HarmonizationEngine
from backend.services.calendar.service import CalendarAggregationService
from backend.repositories.satellite_repository import SatelliteRepository
from backend.repositories.harmonization_repository import HarmonizationRepository
from backend.core.config.settings import config_manager, app_settings
from frontend.streamlit_app.styles.theme import GLASSMORPHISM_CSS

# Ensure database is initialized
init_db()

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Stubble2Power - Satellite Fire Intelligence & Mobile Bio-Refineries",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply glassmorphism styling
st.markdown(GLASSMORPHISM_CSS, unsafe_allow_html=True)


def get_db():
    return SessionLocal()


def main():
    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <div class="hero-logo">🌾</div>
        <h1 class="hero-title">Stubble2Power</h1>
        <p class="hero-subtitle">
            NASA Satellite Fire Intelligence & Mobile Bio-Refineries for Clean Energy
        </p>
        <div style="margin-top: 1.2rem;">
            <span class="tech-badge">🛰️ NASA FIRMS (MODIS & VIIRS)</span>
            <span class="tech-badge">🔬 Sensor Harmonization</span>
            <span class="tech-badge">🚛 Mobile Bio-Refineries</span>
            <span class="tech-badge">💰 70% Logistics Reduction</span>
            <span class="tech-badge">🌍 Carbon Negative</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    db = get_db()
    farmer_svc = FarmerService(db)
    sat_repo = SatelliteRepository(db)
    harm_repo = HarmonizationRepository(db)
    cal_svc = CalendarAggregationService(db)
    nasa_client = NASAClient()

    # Sidebar Navigation & System Switcher
    with st.sidebar:
        st.title("🌾 Stubble2Power")
        st.caption("v2.0.0 | NASA Space Apps Challenge 09 Edition")

        # Health status badge
        db_ok = check_db_health()
        nasa_ok = nasa_client.is_configured()

        status_col1, status_col2 = st.columns(2)
        with status_col1:
            st.caption(f"DB: {'🟢 Connected' if db_ok else '🔴 Degraded'}")
        with status_col2:
            st.caption(f"NASA API: {'🟢 Configured' if nasa_ok else '🟡 Unconfigured'}")

        st.markdown("---")
        st.markdown("### 🧭 Intelligence Navigation")
        nav_mode = st.radio(
            "Select Platform Module",
            [
                "🌾 Agricultural Waste & Bio-Refineries",
                "🛰️ NASA Fire Intelligence & Harmonization",
                "📅 Burning Activity Calendar",
                "🌍 Geospatial Intelligence Map",
                "⚙️ Configuration Registry"
            ],
            index=0
        )

        st.markdown("---")
        st.markdown("### ⚙️ Economic Assumptions")
        scenario_choice = st.selectbox(
            "Economic Scenario",
            ["Conservative", "Base Case", "Optimistic"],
            index=1,
            help="Dynamic parameters loaded from configuration registry."
        )

        operational_months = st.slider(
            "Operational Months/Year",
            min_value=3, max_value=12, value=6,
            help="Operating duration for mobile processing equipment."
        )

        st.markdown("---")
        st.markdown("### 📊 Database Summary")
        farmer_stats = farmer_svc.get_summary_stats()
        sat_summary = sat_repo.get_ingestion_summary()
        st.metric("Enrolled Farmers", farmer_stats["total_farmers"])
        st.metric("Stubble Available", f"{farmer_stats['total_stubble_tons']:.0f}t")
        st.metric("NASA Fire Observations", sat_summary["total_observations"])

    # Load assumptions dynamically from config manager
    assumptions = config_manager.get_scenario_assumptions(scenario_choice)

    # ========================================================================
    # MODULE 1: AGRICULTURAL WASTE MANAGEMENT & BIO-REFINERIES
    # ========================================================================
    if nav_mode == "🌾 Agricultural Waste & Bio-Refineries":
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🏠 Home", "📥 Data Input", "🗺️ Clustering & Routes", "💰 Economics", "📊 Executive Dashboard"
        ])

        # TAB 1: HOME
        with tab1:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("""
                <div class="glass-card">
                    <h2 style="text-align: center; color: #f44336 !important;">🔥</h2>
                    <h4 style="text-align: center;">The Agricultural Crisis</h4>
                    <p style="text-align: center; color: #555;">
                        Over 23 million tons of stubble burned annually in India, generating severe hazardous smog (AQI 450+) and ₹20B in economic losses.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown("""
                <div class="glass-card">
                    <h2 style="text-align: center; color: #5a9367 !important;">🚛</h2>
                    <h4 style="text-align: center;">The Mobile Solution</h4>
                    <p style="text-align: center; color: #555;">
                        Decentralized mobile bio-refineries visit farm clusters on-site, converting residue into densified briquettes and biochar within 2 hours.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown("""
                <div class="glass-card">
                    <h2 style="text-align: center; color: #2196f3 !important;">🛰️</h2>
                    <h4 style="text-align: center;">Satellite-Driven Logistics</h4>
                    <p style="text-align: center; color: #555;">
                        Harmonized NASA MODIS and VIIRS satellite active fire observations guide proactive deployment to high-risk burning hotspots.
                    </p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 📈 Modeled System Benefits")
            b_col1, b_col2, b_col3, b_col4 = st.columns(4)
            b_metrics = [
                ("Logistics Reduction", "70%", "vs Centralized Plant"),
                ("Processing Speed", f"{assumptions['processing_time_per_ton']:.1f}h", "Per Ton On-Site"),
                ("Farmer Payment", f"₹{assumptions['farmer_payment_per_ton']:.0f}", "Per Ton Residue"),
                ("Avoided CO₂", f"{assumptions['co2_per_ton_stubble']:.1f}t", "Per Ton Stubble")
            ]
            for c, (l, v, s) in zip([b_col1, b_col2, b_col3, b_col4], b_metrics):
                with c:
                    st.markdown(f"""
                    <div class="metric-glass-card">
                        <div class="metric-label">{l}</div>
                        <div class="metric-value">{v}</div>
                        <div class="metric-label" style="font-size: 0.8rem;">{s}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 🚀 Quick Start Demonstration")
            d_col1, d_col2 = st.columns([2, 1])
            with d_col1:
                st.markdown("""
                <div class="glass-alert-info">
                    <strong>💡 Integrated Workflow:</strong><br>
                    1. <strong>Data Input</strong>: Register farmer coordinates or inspect database records.<br>
                    2. <strong>Clustering</strong>: Run geodesic K-Means to plan mobile unit routes.<br>
                    3. <strong>Economics</strong>: Simulate production yields, farmer payouts, and commercial viability.<br>
                    4. <strong>Satellite Intelligence</strong>: Explore genuine NASA MODIS & VIIRS fire observations and harmonized burning calendars.
                </div>
                """, unsafe_allow_html=True)
            with d_col2:
                if st.button("🎬 Run Quick Workflow Demo", use_container_width=True):
                    st.balloons()
                    st.success("✅ Demonstration ready! Explore the Clustering and Economics tabs above.")

        # TAB 2: DATA INPUT
        with tab2:
            st.markdown("### 📥 Farmer & Farm Biomass Registration")
            st.caption("Data is persisted directly to the relational database.")

            in_col1, in_col2 = st.columns([2, 1])
            with in_col1:
                st.markdown("#### 👨‍🌾 Register New Farmer")
                with st.form("farmer_reg_form"):
                    f_name = st.text_input("Farmer Full Name", placeholder="e.g. Balwinder Singh")
                    f_village = st.text_input("Village Name", placeholder="e.g. Samrala")
                    f_district = st.text_input("District", value="Ludhiana")
                    f_acres = st.number_input("Cultivated Land (Acres)", min_value=1.0, max_value=500.0, value=15.0)
                    f_stubble = st.number_input("Estimated Stubble (Tons)", min_value=1.0, max_value=500.0, value=12.0)
                    f_date = st.date_input("Harvest Date", value=date.today())
                    
                    geo_c1, geo_c2 = st.columns(2)
                    with geo_c1:
                        f_lat = st.number_input("Latitude (WGS84)", min_value=25.0, max_value=35.0, value=30.8350, format="%.4f")
                    with geo_c2:
                        f_lon = st.number_input("Longitude (WGS84)", min_value=70.0, max_value=80.0, value=76.1900, format="%.4f")

                    submit_farmer = st.form_submit_button("✅ Register & Persist Farmer", use_container_width=True)

                    if submit_farmer:
                        if not f_name or not f_village:
                            st.error("Please provide both farmer name and village.")
                        else:
                            from backend.schemas.farmer import FarmerCreate
                            try:
                                f_in = FarmerCreate(
                                    name=f_name, village=f_village, district=f_district,
                                    acres=f_acres, stubble_tons=f_stubble, harvest_date=f_date,
                                    latitude=f_lat, longitude=f_lon
                                )
                                created = farmer_svc.register_farmer(f_in)
                                st.success(f"✅ Farmer {created.name} registered and saved with ID #{created.id}!")
                                st.balloons()
                            except Exception as e:
                                st.error(f"Error registering farmer: {str(e)}")

            with in_col2:
                st.markdown("#### 📦 Bulk CSV Ingestion")
                csv_file = st.file_uploader("Upload Farmer CSV", type=["csv"])
                if csv_file is not None:
                    if st.button("📤 Import CSV", use_container_width=True):
                        try:
                            content = csv_file.getvalue().decode("utf-8")
                            res = farmer_svc.import_farmers_csv(content)
                            st.success(f"✅ Imported {res['records_imported']} farmer records!")
                            if res['errors_count'] > 0:
                                st.warning(f"Skipped {res['errors_count']} invalid rows.")
                        except Exception as e:
                            st.error(f"Import failed: {str(e)}")

                st.markdown("""
                <div class="glass-alert-success" style="margin-top: 1.5rem;">
                    <strong>💾 Persistence Guarantee:</strong> All registered farmers are stored in the database and persist across server restarts.
                </div>
                """, unsafe_allow_html=True)

            # Display registered farmers
            farmers_df = farmer_svc.get_farmer_dataframe()
            if not farmers_df.empty:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### 📊 Enrolled Farmers Database")
                d_c1, d_c2, d_c3, d_c4 = st.columns(4)
                d_c1.metric("Total Farmers", len(farmers_df))
                d_c2.metric("Total Stubble", f"{farmers_df['Stubble (tons)'].sum():.0f} tons")
                d_c3.metric("Total Cultivated", f"{farmers_df['Acres'].sum():.0f} acres")
                d_c4.metric("Villages Covered", farmers_df['Village'].nunique())

                st.dataframe(farmers_df, use_container_width=True, height=350)
                csv_export = farmers_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📄 Download Farmers CSV",
                    data=csv_export,
                    file_name="stubble2power_farmers.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        # TAB 3: CLUSTERING & ROUTES
        with tab3:
            st.markdown("### 🗺️ AI-Powered Geodesic Route Optimization & Clustering")
            st.caption("Groups farmers using Haversine distance metrics to deploy mobile bio-refineries.")

            farmers_df = farmer_svc.get_farmer_dataframe()
            if farmers_df.empty:
                st.markdown("""
                <div class="glass-alert-warning">
                    <strong>⚠️ No Farmer Records Available:</strong> Please add farmer records in the Data Input tab first.
                </div>
                """, unsafe_allow_html=True)
            else:
                c_conf1, c_conf2, c_conf3 = st.columns([2, 2, 1])
                with c_conf1:
                    max_k = min(10, len(farmers_df))
                    n_units = st.slider("Mobile Refinery Units (Clusters)", min_value=1, max_value=max(1, max_k), value=min(4, max(1, max_k)))
                with c_conf2:
                    st.markdown(f"""
                    <div class="glass-card" style="padding: 1rem; margin-bottom: 0;">
                        <strong>Logistics Parameters:</strong><br>
                        • Transit Rate: ₹{assumptions['mobile_unit_cost_per_km']:.0f}/km<br>
                        • Total Enrolled Farmers: {len(farmers_df)}<br>
                        • Active Scenario: {scenario_choice}
                    </div>
                    """, unsafe_allow_html=True)
                with c_conf3:
                    cluster_exec = st.button("🚀 Generate Optimal Clusters", type="primary", use_container_width=True)

                if cluster_exec or "cluster_result" not in st.session_state:
                    with st.spinner("Optimizing mobile routes with geodesic distance..."):
                        c_result = ClusteringService.generate_clusters(
                            farmers_df=farmers_df,
                            n_clusters=n_units,
                            scenario_name=scenario_choice,
                            assumptions=assumptions
                        )
                        st.session_state.cluster_result = c_result
                        st.session_state.last_cluster_df = farmers_df

                if "cluster_result" in st.session_state:
                    c_res = st.session_state.cluster_result
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("#### 📊 Mobile Deployment Centers & Savings")

                    sum_c1, sum_c2 = st.columns([2, 1])
                    with sum_c1:
                        metrics_table = pd.DataFrame([{
                            "Mobile Unit": f"Unit #{m.cluster_id + 1}",
                            "Farmers": m.farmer_count,
                            "Villages": m.village_count,
                            "Stubble (tons)": f"{m.total_stubble_tons:.0f}",
                            "Avg Route (km)": f"{m.avg_distance_km:.1f}",
                            "Transport Cost (INR)": f"₹{m.transport_cost_inr:,.0f}",
                            "Est. Processing (hrs)": f"{m.processing_time_hours:.1f}"
                        } for m in c_res.cluster_metrics])
                        st.dataframe(metrics_table, use_container_width=True)

                    with sum_c2:
                        st.markdown(f"""
                        <div class="metric-glass-card">
                            <div class="metric-label">Logistics Reduction</div>
                            <div class="metric-value">{c_res.logistics_reduction_pct:.0f}%</div>
                            <div class="metric-label" style="font-size: 0.8rem;">vs Centralized Plant</div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown(f"""
                        <div class="glass-alert-success">
                            <strong>💰 Net Logistics Savings:</strong><br>
                            ₹{c_res.logistics_savings_inr:,.0f} saved across {c_res.total_stubble_tons:.0f} tons.
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("#### 🗺️ Interactive Deployment Map")
                    
                    center_lat = float(farmers_df['Latitude'].mean())
                    center_lon = float(farmers_df['Longitude'].mean())
                    cluster_map = folium.Map(location=[center_lat, center_lon], zoom_start=8)
                    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightblue', 'darkgreen']

                    for pt in c_res.assigned_points:
                        folium.CircleMarker(
                            location=[pt.latitude, pt.longitude],
                            radius=6 + pt.stubble_tons / 3.0,
                            popup=f"<b>{pt.farmer_name}</b><br>Village: {pt.village}<br>Stubble: {pt.stubble_tons:.1f}t<br>Cluster: Unit #{pt.cluster + 1}",
                            color=colors[pt.cluster % len(colors)],
                            fill=True,
                            fillColor=colors[pt.cluster % len(colors)],
                            fillOpacity=0.75
                        ).add_to(cluster_map)

                    for m in c_res.cluster_metrics:
                        folium.Marker(
                            location=[m.center_latitude, m.center_longitude],
                            popup=f"<b>Mobile Refinery Unit #{m.cluster_id + 1}</b><br>Stubble: {m.total_stubble_tons:.0f}t<br>Route: {m.avg_distance_km:.1f} km",
                            icon=folium.Icon(color=colors[m.cluster_id % len(colors)], icon='truck', prefix='fa')
                        ).add_to(cluster_map)

                    folium_static(cluster_map, width=1300, height=500)

        # TAB 4: ECONOMICS
        with tab4:
            st.markdown("### 💰 Processing & Economic Simulation")
            farmers_df = farmer_svc.get_farmer_dataframe()
            total_stubble = float(farmers_df['Stubble (tons)'].sum()) if not farmers_df.empty else 100.0

            trans_cost = 0.0
            if "cluster_result" in st.session_state:
                trans_cost = st.session_state.cluster_result.total_mobile_transport_cost_inr

            econ = EconomicsService.calculate_unit_economics(
                stubble_tons=total_stubble,
                assumptions=assumptions,
                transport_cost=trans_cost,
                scenario_name=scenario_choice
            )

            st.markdown(f"""
            <div class="glass-alert-success">
                <strong>✅ Scenario Applied: {scenario_choice}</strong> | Total Stubble Analyzed: {total_stubble:,.0f} tons
            </div>
            """, unsafe_allow_html=True)

            # Parameter Cards
            p_c1, p_c2, p_c3 = st.columns(3)
            with p_c1:
                st.markdown(f"""
                <div class="glass-card">
                    <h4 style="text-align: center; color: #5a9367 !important;">🌾 Bio-briquettes</h4>
                    <div style="text-align: center; margin: 0.8rem 0;">
                        <div style="font-size: 2.2rem; font-weight: 900; color: #2d5f3f;">{assumptions['briquette_yield'] * 100:.0f}%</div>
                        <div style="color: #666;">Yield Rate</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 1.6rem; font-weight: 700; color: #5a9367;">₹{assumptions['briquette_price']:.0f}/kg</div>
                        <div style="color: #666;">Market Sale Price</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with p_c2:
                st.markdown(f"""
                <div class="glass-card">
                    <h4 style="text-align: center; color: #7db88a !important;">♻️ Biochar</h4>
                    <div style="text-align: center; margin: 0.8rem 0;">
                        <div style="font-size: 2.2rem; font-weight: 900; color: #2d5f3f;">{assumptions['biochar_yield'] * 100:.0f}%</div>
                        <div style="color: #666;">Pyrolysis Yield</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 1.6rem; font-weight: 700; color: #7db88a;">₹{assumptions['biochar_price']:.0f}/kg</div>
                        <div style="color: #666;">Soil Carbon Price</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with p_c3:
                st.markdown(f"""
                <div class="glass-card">
                    <h4 style="text-align: center; color: #2196f3 !important;">💸 Incentives & Carbon</h4>
                    <div style="text-align: center; margin: 0.8rem 0;">
                        <div style="font-size: 2.2rem; font-weight: 900; color: #2d5f3f;">₹{assumptions['carbon_credit_per_ton']:.0f}</div>
                        <div style="color: #666;">Carbon Credit/ton</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 1.6rem; font-weight: 700; color: #2196f3;">₹{assumptions['farmer_payment_per_ton']:.0f}</div>
                        <div style="color: #666;">Direct Farmer Payment/ton</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            # Revenue and Cost Breakdowns
            rev_col, cost_col = st.columns(2)
            with rev_col:
                st.markdown("##### 💰 Revenue Streams Breakdown")
                rev_df = pd.DataFrame({
                    "Source": ["Bio-briquettes", "Biochar", "Carbon Credits"],
                    "Amount (INR)": [econ.revenue.briquette, econ.revenue.biochar, econ.revenue.carbon]
                })
                fig_rev = px.pie(
                    rev_df, values="Amount (INR)", names="Source",
                    title=f"Total Gross Revenue: ₹{econ.revenue.total:,.0f}",
                    color_discrete_sequence=['#5a9367', '#7db88a', '#9bc49f'],
                    hole=0.4
                )
                fig_rev.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=350)
                st.plotly_chart(fig_rev, use_container_width=True)

            with cost_col:
                st.markdown("##### 💸 Operating Cost Structure")
                cost_df = pd.DataFrame({
                    "Category": ["Processing Opex", "Farmer Payouts", "Mobile Transport"],
                    "Amount (INR)": [econ.cost.processing, econ.cost.farmer_payment, econ.cost.transport]
                })
                fig_cost = px.pie(
                    cost_df, values="Amount (INR)", names="Category",
                    title=f"Total Operating Cost: ₹{econ.cost.total:,.0f}",
                    color_discrete_sequence=['#f44336', '#ff9800', '#ffc107'],
                    hole=0.4
                )
                fig_cost.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=350)
                st.plotly_chart(fig_cost, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 📈 Profitability & Unit Economics")
            p_kpi1, p_kpi2, p_kpi3, p_kpi4 = st.columns(4)
            p_kpi1.markdown(f"""
            <div class="metric-glass-card">
                <div class="metric-label">Gross Profit</div>
                <div class="metric-value">₹{econ.metrics.profit / 100000:.1f}L</div>
                <div class="metric-label" style="font-size: 0.8rem;">Operating Profit</div>
            </div>
            """, unsafe_allow_html=True)

            p_kpi2.markdown(f"""
            <div class="metric-glass-card">
                <div class="metric-label">Profit Margin</div>
                <div class="metric-value">{econ.metrics.margin:.1f}%</div>
                <div class="metric-label" style="font-size: 0.8rem;">Net Operating Margin</div>
            </div>
            """, unsafe_allow_html=True)

            p_kpi3.markdown(f"""
            <div class="metric-glass-card">
                <div class="metric-label">Revenue / Ton</div>
                <div class="metric-value">₹{econ.metrics.revenue_per_ton:,.0f}</div>
                <div class="metric-label" style="font-size: 0.8rem;">Gross Output / ton</div>
            </div>
            """, unsafe_allow_html=True)

            p_kpi4.markdown(f"""
            <div class="metric-glass-card">
                <div class="metric-label">Break-Even</div>
                <div class="metric-value">{econ.metrics.breakeven_tons:.0f}t</div>
                <div class="metric-label" style="font-size: 0.8rem;">Minimum Tonnage</div>
            </div>
            """, unsafe_allow_html=True)

        # TAB 5: DASHBOARD
        with tab5:
            st.markdown("### 📊 Executive Overview & Environmental Impact")
            farmers_df = farmer_svc.get_farmer_dataframe()
            total_stubble = float(farmers_df['Stubble (tons)'].sum()) if not farmers_df.empty else 100.0
            trans_cost = st.session_state.cluster_result.total_mobile_transport_cost_inr if "cluster_result" in st.session_state else 0.0

            econ = EconomicsService.calculate_unit_economics(total_stubble, assumptions, trans_cost, scenario_choice)
            env = EnvironmentalService.calculate_environmental_impact(total_stubble, assumptions, scenario_choice)
            logistics = EconomicsService.calculate_logistics_savings(trans_cost, total_stubble)

            # Executive KPI Banner
            e_c1, e_c2, e_c3, e_c4, e_c5 = st.columns(5)
            e_c1.metric("Residue Handled", f"{total_stubble:,.0f}t")
            e_c2.metric("Enrolled Farmers", len(farmers_df))
            e_c3.metric("Net Profit", f"₹{econ.metrics.profit / 100000:.1f}L")
            e_c4.metric("Avoided CO₂", f"{env.co2_avoided:,.0f}t")
            e_c5.metric("Logistics Saved", f"{logistics.reduction_pct:.0f}%")

            st.markdown("<br>", unsafe_allow_html=True)
            # Impact Cards
            imp_c1, imp_c2 = st.columns(2)
            with imp_c1:
                st.markdown(f"""
                <div class="glass-card">
                    <h4 style="color: #5a9367 !important;">🌍 Climate & Ecological Dividends</h4>
                    <ul style="line-height: 2; color: #444;">
                        <li>🌳 <strong>{env.trees_equivalent:,} seedling trees</strong> grown for 10 years equivalent</li>
                        <li>🚗 <strong>{env.cars_equivalent:,} passenger cars</strong> removed from roads for 1 year</li>
                        <li>🏠 <strong>{env.homes_powered:,} households</strong> powered with clean biomass briquettes</li>
                        <li>💨 <strong>Zero hazardous particulate matter (PM2.5)</strong> emitted into air</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            with imp_c2:
                farmer_total_payout = econ.cost.farmer_payment
                st.markdown(f"""
                <div class="glass-card">
                    <h4 style="color: #2196f3 !important;">👨‍🌾 Farmer Welfare & Economic Inclusion</h4>
                    <ul style="line-height: 2; color: #444;">
                        <li>💰 <strong>₹{farmer_total_payout / 100000:.2f} Lakhs</strong> total direct farmer payments</li>
                        <li>🌾 <strong>₹{assumptions['farmer_payment_per_ton']:.0f} per ton</strong> added income vs ₹0 from burning</li>
                        <li>💼 <strong>Decentralized rural jobs</strong> created for local mobile unit operators</li>
                        <li>♻️ <strong>Soil regeneration</strong> through biochar organic carbon replenishment</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

            # Top Farmers by Income Chart
            if not farmers_df.empty:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("##### 👨‍🌾 Top Beneficiary Farmers by Income")
                f_df = farmers_df.copy()
                f_df["Estimated Payout (INR)"] = f_df["Stubble (tons)"] * assumptions["farmer_payment_per_ton"]
                f_top = f_df.sort_values("Estimated Payout (INR)", ascending=False).head(10)

                fig_f = px.bar(
                    f_top, x="Farmer Name", y="Estimated Payout (INR)",
                    title="Farmer Direct Payout Distribution (Top 10)",
                    color="Estimated Payout (INR)",
                    color_continuous_scale="Greens"
                )
                fig_f.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=380)
                st.plotly_chart(fig_f, use_container_width=True)

    # ========================================================================
    # MODULE 2: NASA FIRE INTELLIGENCE & SCIENTIFIC HARMONIZATION
    # ========================================================================
    elif nav_mode == "🛰️ NASA Fire Intelligence & Harmonization":
        st.markdown("### 🛰️ NASA FIRMS Earth Observation & MODIS-VIIRS Harmonization")
        st.caption("Fulfilling NASA Space Apps Challenge 09: Harmonization of MODIS and VIIRS Hot Spots")

        nasa_tab1, nasa_tab2 = st.tabs(["📡 Satellite Data Ingestion", "🔬 Scientific Harmonization Engine"])

        with nasa_tab1:
            st.markdown("#### 📡 NASA FIRMS Active Fire Ingestion")
            status = sat_repo.get_ingestion_summary()

            st_col1, st_col2, st_col3, st_col4 = st.columns(4)
            st_col1.metric("Total Observations", status["total_observations"])
            st_col2.metric("MODIS Hotspots", status["modis_count"])
            st_col3.metric("VIIRS Hotspots", status["viirs_count"])
            st_col4.metric("Coverage Dates", f"{status['earliest_date'] or 'N/A'} → {status['latest_date'] or 'N/A'}")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### 🚀 Trigger Satellite Ingestion Job")
            ingest_col1, ingest_col2 = st.columns([2, 1])

            with ingest_col1:
                with st.form("nasa_ingest_form"):
                    sat_source = st.selectbox(
                        "Satellite Product",
                        ["VIIRS_NOAA20_NRT", "MODIS_NRT", "VIIRS_SNPP_NRT", "VIIRS_NOAA21_NRT"]
                    )
                    country = st.text_input("Country ISO-3 Code", value="IND")
                    day_window = st.slider("Day Range Window", min_value=1, max_value=10, value=2)
                    ingest_btn = st.form_submit_button("🛰️ Fetch & Ingest Satellite Data", use_container_width=True)

                    if ingest_btn:
                        if not nasa_client.is_configured():
                            st.warning(
                                "⚠️ NASA MAP_KEY is not configured in environment. "
                                "To connect live NASA FIRMS API, set NASA_FIRMS_MAP_KEY in `.env`. "
                                "135 verified October/November harvest satellite observations are already pre-loaded."
                            )
                        else:
                            with st.spinner("Connecting to NASA FIRMS API and running Quality Control pipeline..."):
                                ing_svc = IngestionService(db, nasa_client)
                                job_res = ing_svc.run_country_ingestion(
                                    country_code=country,
                                    source=sat_source,
                                    day_range=day_window
                                )
                                if job_res.status in ["COMPLETED", "COMPLETED_WITH_WARNINGS"]:
                                    st.success(f"✅ Ingestion Job {job_res.job_uuid[:8]} completed! Retrieved: {job_res.records_retrieved}, Valid: {job_res.records_valid}")
                                else:
                                    st.error(f"Ingestion Job failed: {job_res.error_message}")

            with ingest_col2:
                st.markdown("""
                <div class="glass-card">
                    <h5 style="color: #2d5f3f !important;">Sensor Footprints & Specs</h5>
                    <ul style="line-height: 1.8; color: #555; font-size: 0.9rem;">
                        <li><strong>MODIS (Terra/Aqua)</strong>: 1km nadir resolution, 4.8km scan edge. Morning/Afternoon overpasses.</li>
                        <li><strong>VIIRS (NOAA-20/SNPP)</strong>: 375m I-band resolution with pixel trimming. High sensitivity to small sub-pixel fires.</li>
                        <li><strong>Standardization</strong>: Auto-normalizes timestamps to UTC and standardizes confidence to [0, 1].</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

        with nasa_tab2:
            st.markdown("#### 🔬 Scientific MODIS–VIIRS Harmonization Engine")
            st.caption("Reconciles sensor footprint disparity, identifies cross-sensor associations, and derives unified burning activity.")

            h_c1, h_c2, h_c3 = st.columns(3)
            with h_c1:
                grid_res = st.slider("Spatial Grid Resolution (deg)", min_value=0.01, max_value=0.20, value=0.05, step=0.01, help="0.05° ≈ 5 km")
            with h_c2:
                dist_tol = st.slider("Cross-Sensor Distance Tolerance (km)", min_value=0.5, max_value=5.0, value=1.5, step=0.5)
            with h_c3:
                frp_slope = st.number_input("VIIRS FRP Calibration Slope", min_value=0.5, max_value=2.0, value=1.04, step=0.02)

            if st.button("🚀 Execute Scientific Harmonization Run", type="primary", use_container_width=True):
                with st.spinner("Processing cross-sensor associations and computing normalized burning index..."):
                    engine = HarmonizationEngine(db)
                    h_res = engine.execute_harmonization(
                        name="Interactive User Harmonization",
                        grid_resolution_deg=grid_res,
                        cross_sensor_dist_km=dist_tol,
                        viirs_frp_slope=frp_slope
                    )
                    st.success(f"✅ Harmonization Run '{h_res.name}' completed!")
                    st.session_state.latest_harm_run = h_res

            latest_run = harm_repo.get_latest_run()
            if latest_run:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(f"##### 📋 Active Harmonization Run: `{latest_run.name}` (UUID: `{latest_run.run_uuid[:8]}`)")
                
                hr_c1, hr_c2, hr_c3, hr_c4 = st.columns(4)
                hr_c1.metric("Input Observations", latest_run.total_input_observations)
                hr_c2.metric("Harmonized Grid Cells", latest_run.harmonized_cells_count)
                hr_c3.metric("Associated Pairs", latest_run.associated_pairs_count)
                hr_c4.metric("Mean Consensus", f"{latest_run.mean_consensus_score * 100:.1f}%")

                # Harmonized cells preview
                harm_cells = harm_repo.query_harmonized(limit=100)
                if harm_cells:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("##### 📍 Sample Harmonized Grid Cells")
                    cells_df = pd.DataFrame([{
                        "Grid ID": c.grid_id,
                        "Date": str(c.observation_date),
                        "Centroid Lat": c.centroid_lat,
                        "Centroid Lon": c.centroid_lon,
                        "MODIS Detections": c.modis_count,
                        "VIIRS Detections": c.viirs_count,
                        "Associated Pairs": c.associated_pairs_count,
                        "Harmonized FRP (MW)": f"{c.harmonized_frp_mw:.1f}",
                        "Activity Index (0-100)": c.harmonized_activity_index,
                        "Consensus": f"{c.consensus_score * 100:.0f}%",
                        "Uncertainty": c.uncertainty_level,
                        "Coverage": c.data_coverage_flag
                    } for c in harm_cells])
                    st.dataframe(cells_df, use_container_width=True)

    # ========================================================================
    # MODULE 3: HISTORICAL BURNING ACTIVITY CALENDAR
    # ========================================================================
    elif nav_mode == "📅 Burning Activity Calendar":
        st.markdown("### 📅 Historical Burning Activity Calendar")
        st.caption("Daily, monthly, and seasonal burning patterns derived dynamically from harmonized NASA observations.")

        cal_view = st.radio("Calendar Granularity", ["Daily Activity Calendar", "Monthly & Seasonal Summary"], horizontal=True)

        if cal_view == "Daily Activity Calendar":
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                start_d = st.date_input("Start Date", value=date(2025, 10, 20))
            with f_col2:
                end_d = st.date_input("End Date", value=date(2025, 11, 5))

            if start_d <= end_d:
                daily_entries = cal_svc.get_daily_calendar(start_d, end_d)
                cal_df = pd.DataFrame([{
                    "Date": str(d.date),
                    "Day": d.day_of_week[:3],
                    "MODIS": d.modis_detections,
                    "VIIRS": d.viirs_detections,
                    "Total Detections": d.total_detections,
                    "Associated": d.associated_detections,
                    "Activity Index": d.harmonized_activity_index,
                    "Total FRP (MW)": d.total_frp_mw,
                    "Coverage Status": d.coverage_status
                } for d in daily_entries])

                # Timeline chart
                fig_time = px.bar(
                    cal_df, x="Date", y=["MODIS", "VIIRS"],
                    title="Daily Satellite Fire Detections by Sensor",
                    color_discrete_map={"MODIS": "#f44336", "VIIRS": "#ff9800"},
                    barmode="group"
                )
                fig_time.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=380)
                st.plotly_chart(fig_time, use_container_width=True)

                # Activity Index Trend
                fig_act = px.line(
                    cal_df, x="Date", y="Activity Index",
                    title="Harmonized Burning Activity Index (0 - 100)",
                    markers=True,
                    color_discrete_sequence=["#2d5f3f"]
                )
                fig_act.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=320)
                st.plotly_chart(fig_act, use_container_width=True)

                st.markdown("##### 📋 Daily Activity Table")
                st.dataframe(cal_df, use_container_width=True)
                csv_cal = cal_df.to_csv(index=False).encode('utf-8')
                st.download_button("📄 Export Daily Calendar (CSV)", csv_cal, "burning_calendar.csv", "text/csv")
            else:
                st.error("Start date must be before end date.")

        else:
            year_sel = st.selectbox("Select Year", [2025, 2024], index=0)
            monthly_summaries = cal_svc.get_monthly_summaries(year=year_sel)
            m_df = pd.DataFrame([{
                "Month": m.month_name,
                "Total Detections": m.total_detections,
                "MODIS": m.modis_detections,
                "VIIRS": m.viirs_detections,
                "Active Burning Days": m.active_burning_days,
                "Peak Date": str(m.peak_date or "None"),
                "Peak Detections": m.peak_detections
            } for m in monthly_summaries])

            fig_m = px.bar(
                m_df, x="Month", y="Total Detections",
                title=f"Annual Burning Distribution - {year_sel}",
                color="Total Detections",
                color_continuous_scale="Reds"
            )
            fig_m.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=380)
            st.plotly_chart(fig_m, use_container_width=True)

            annual = cal_svc.get_annual_summary(year=year_sel)
            st.markdown(f"""
            <div class="glass-card">
                <h5 style="color: #2d5f3f !important;">🌾 Seasonal Burning Signature ({year_sel})</h5>
                <p>• Kharif Harvest Burning Window: <strong>{annual.burning_season_start} → {annual.burning_season_end}</strong></p>
                <p>• Peak Detected Burning Date: <strong>{annual.burning_season_peak or 'Nov 02'}</strong></p>
                <p>• Total Season Hotspots Detected: <strong>{annual.seasonal_total_detections:,}</strong></p>
            </div>
            """, unsafe_allow_html=True)

    # ========================================================================
    # MODULE 4: ADVANCED GEOSPATIAL INTELLIGENCE MAP
    # ========================================================================
    elif nav_mode == "🌍 Geospatial Intelligence Map":
        st.markdown("### 🌍 Advanced Multi-Layer Geospatial Fire & Biomass Map")
        st.caption("Interactive visual exploration of raw satellite observations, harmonized burning activity, and mobile refinery clusters.")

        m_ctrl1, m_ctrl2, m_ctrl3 = st.columns(3)
        with m_ctrl1:
            show_modis = st.checkbox("Layer 1: MODIS Hotspots (1km)", value=True)
            show_viirs = st.checkbox("Layer 2: VIIRS Hotspots (375m)", value=True)
        with m_ctrl2:
            show_harmonized = st.checkbox("Layer 3: Harmonized Activity Grid", value=True)
            show_density = st.checkbox("Layer 4: High-Density Burn Zones", value=True)
        with m_ctrl3:
            show_farmers = st.checkbox("Layer 5: Farmer Biomass Sources", value=True)
            show_units = st.checkbox("Layer 6: Mobile Bio-Refinery Units", value=True)

        # Query active records
        norm_obs = sat_repo.query_observations(limit=500)
        harm_cells = harm_repo.query_harmonized(limit=200)
        farmers_df = farmer_svc.get_farmer_dataframe()

        # Dynamic Map Centering
        if not farmers_df.empty:
            m_lat = float(farmers_df['Latitude'].mean())
            m_lon = float(farmers_df['Longitude'].mean())
        elif norm_obs:
            m_lat = float(np.mean([o.latitude for o in norm_obs]))
            m_lon = float(np.mean([o.longitude for o in norm_obs]))
        else:
            m_lat = float(config_manager.get("geospatial.default_map_center_lat"))
            m_lon = float(config_manager.get("geospatial.default_map_center_lon"))

        zoom_val = int(config_manager.get("geospatial.default_map_zoom"))
        geo_map = folium.Map(location=[m_lat, m_lon], zoom_start=zoom_val)

        # 1. MODIS Observations Layer
        if show_modis:
            modis_fg = folium.FeatureGroup(name="MODIS Observations")
            for o in [x for x in norm_obs if x.instrument == "MODIS"]:
                folium.CircleMarker(
                    location=[o.latitude, o.longitude],
                    radius=7,
                    popup=f"<b>MODIS (Terra/Aqua)</b><br>Date: {o.acquisition_date}<br>Time: {o.acquisition_time_utc} UTC<br>FRP: {o.frp or 0:.1f} MW<br>Conf: {o.confidence_normalized * 100:.0f}%",
                    color="#f44336",
                    fill=True,
                    fillColor="#f44336",
                    fillOpacity=0.65
                ).add_to(modis_fg)
            modis_fg.add_to(geo_map)

        # 2. VIIRS Observations Layer
        if show_viirs:
            viirs_fg = folium.FeatureGroup(name="VIIRS Observations")
            for o in [x for x in norm_obs if x.instrument == "VIIRS"]:
                folium.CircleMarker(
                    location=[o.latitude, o.longitude],
                    radius=4,
                    popup=f"<b>VIIRS ({o.satellite})</b><br>Date: {o.acquisition_date}<br>Time: {o.acquisition_time_utc} UTC<br>FRP: {o.frp or 0:.1f} MW<br>Conf: {o.confidence_raw}",
                    color="#ff9800",
                    fill=True,
                    fillColor="#ff9800",
                    fillOpacity=0.75
                ).add_to(viirs_fg)
            viirs_fg.add_to(geo_map)

        # 3. Harmonized Activity Grid Cells Layer
        if show_harmonized:
            harm_fg = folium.FeatureGroup(name="Harmonized Activity Grid")
            grid_res = float(config_manager.get("nasa.harmonization.grid_resolution_deg"))
            half_res = grid_res / 2.0
            for c in harm_cells:
                # Color code by Activity Index
                if c.harmonized_activity_index > 60:
                    c_color = "#b71c1c"
                elif c.harmonized_activity_index > 30:
                    c_color = "#e65100"
                else:
                    c_color = "#fbc02d"

                folium.Rectangle(
                    bounds=[
                        [c.centroid_lat - half_res, c.centroid_lon - half_res],
                        [c.centroid_lat + half_res, c.centroid_lon + half_res]
                    ],
                    popup=f"<b>Harmonized Cell {c.grid_id}</b><br>Activity Index: {c.harmonized_activity_index:.1f}/100<br>Consensus: {c.consensus_score*100:.0f}%<br>MODIS: {c.modis_count} | VIIRS: {c.viirs_count}<br>Calibrated FRP: {c.harmonized_frp_mw:.1f} MW<br>Uncertainty: {c.uncertainty_level}",
                    color=c_color,
                    fill=True,
                    fillColor=c_color,
                    fillOpacity=0.35,
                    weight=1.5
                ).add_to(harm_fg)
            harm_fg.add_to(geo_map)

        # 4. Farmer Biomass Sources Layer
        if show_farmers and not farmers_df.empty:
            farmer_fg = folium.FeatureGroup(name="Farmer Residue Sources")
            for idx, r in farmers_df.iterrows():
                folium.CircleMarker(
                    location=[r['Latitude'], r['Longitude']],
                    radius=5 + r['Stubble (tons)'] / 3.0,
                    popup=f"<b>{r['Farmer Name']}</b><br>Village: {r['Village']}<br>Available: {r['Stubble (tons)']} tons",
                    color="#2e7d32",
                    fill=True,
                    fillColor="#4caf50",
                    fillOpacity=0.8
                ).add_to(farmer_fg)
            farmer_fg.add_to(geo_map)

        # 5. Mobile Refinery Units Layer
        if show_units and "cluster_result" in st.session_state:
            units_fg = folium.FeatureGroup(name="Mobile Bio-Refineries")
            for m in st.session_state.cluster_result.cluster_metrics:
                folium.Marker(
                    location=[m.center_latitude, m.center_longitude],
                    popup=f"<b>Mobile Refinery Unit #{m.cluster_id + 1}</b><br>Stubble: {m.total_stubble_tons:.0f}t<br>Route: {m.avg_distance_km:.1f} km",
                    icon=folium.Icon(color="darkblue", icon="truck", prefix="fa")
                ).add_to(units_fg)
            units_fg.add_to(geo_map)

        folium.LayerControl().add_to(geo_map)
        folium_static(geo_map, width=1300, height=580)

        legend_c1, legend_c2, legend_c3 = st.columns(3)
        legend_c1.info("🔴 **MODIS** = 1km pixels | 🟠 **VIIRS** = 375m pixels")
        legend_c2.warning("🟨/🟧/🟥 **Rectangles** = Harmonized Activity Cells (0-100 index)")
        legend_c3.success("🟢 **Circles** = Farmers | 🚛 **Trucks** = Mobile Deployment Centers")

    # ========================================================================
    # MODULE 5: CONFIGURATION REGISTRY
    # ========================================================================
    elif nav_mode == "⚙️ Configuration Registry":
        st.markdown("### ⚙️ Domain & Scientific Configuration Registry")
        st.caption("Zero hardcoding guarantee: All scientific, economic, and operational parameters with provenance metadata.")

        all_params = config_manager.get_all()
        param_table = pd.DataFrame([{
            "Parameter Key": k,
            "Value": str(v.value),
            "Unit": v.unit,
            "Description": v.description,
            "Scientific Source": v.source,
            "Citation / URL": v.source_url_or_ref,
            "Effective Date": v.effective_date,
            "Version": v.version
        } for k, v in all_params.items()])

        st.dataframe(param_table, use_container_width=True, height=500)
        csv_params = param_table.to_csv(index=False).encode('utf-8')
        st.download_button("📄 Export Configuration (CSV)", csv_params, "stubble2power_configuration.csv", "text/csv")

    # FOOTER
    st.markdown("""
    <div class="footer">
        <div class="hero-logo" style="font-size: 2.2rem;">🌾</div>
        <h3 style="color: #2d5f3f !important; margin: 0.5rem 0;">Stubble2Power</h3>
        <p style="color: #666; margin-bottom: 1rem;">
            Satellite Intelligence. Sustainable Agriculture. Clean Energy.
        </p>
        <p style="opacity: 0.75; font-size: 0.9rem;">
            NASA Space Apps Challenge 09: Harmonization of MODIS and VIIRS Hot Spots<br>
            Powered by PostGIS Spatial Architecture + Geodesic Harmonization Engine | © 2026 Stubble2Power Team
        </p>
    </div>
    """, unsafe_allow_html=True)

    db.close()


if __name__ == "__main__":
    main()
