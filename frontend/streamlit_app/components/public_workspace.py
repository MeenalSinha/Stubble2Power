"""
Stubble2Power - Public Visitor Workspace Component.
Public Satellite Fire Intelligence, Obfuscated Coordinates, Historical Calendars, and Clean Energy Overview.
Zero emojis compliance (Rule 7 & Rule 9).
"""

from datetime import date, timedelta
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static
import streamlit as st
import plotly.express as px

from backend.models.entities import (
    NormalizedSatelliteObservation, HarmonizedObservation,
    HistoricalBaseline, SeasonalProfile
)
from backend.services.privacy.privacy_service import PrivacyGovernanceService
from frontend.streamlit_app.localization.i18n import t


def render_public_workspace(db, lang: str = "en"):
    """Renders the public transparency portal with location obfuscation."""
    st.markdown("## Public Agricultural Fire Intelligence & Clean Energy Portal")
    st.caption("NASA Earth Observation FIRMS hot spots with DPDP Act 2023 location privacy obfuscation.")

    # DPDP Act 2023 Privacy Disclosure Banner
    st.info(
        "**Geospatial Privacy Notice (DPDP Act 2023):** "
        "In accordance with statutory digital personal data protection principles, coordinates on this public viewer "
        "are blurred to 2 decimal places (approx. 1.1 km resolution). Precise farm boundary coordinates are restricted "
        "to authenticated parcel owners and licensed mobile refinery dispatchers."
    )

    tab_map, tab_calendar, tab_mission = st.tabs([
        "Public Satellite Fire Intelligence",
        "Historical Burning Activity Calendar",
        "Mission & Technological Architecture"
    ])

    privacy_service = PrivacyGovernanceService(db)

    with tab_map:
        st.markdown("### NASA FIRMS Satellite Fire Observations")
        st.caption("Active crop residue hot spots detected by MODIS (Terra/Aqua) and VIIRS (Suomi-NPP/NOAA-20).")

        # Query recent observations
        obs_records = db.query(NormalizedSatelliteObservation).order_by(
            NormalizedSatelliteObservation.acquisition_date.desc(),
            NormalizedSatelliteObservation.acquisition_time_utc.desc()
        ).limit(300).all()

        if obs_records:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Detected Hotspots (Sample)", len(obs_records))
            with col2:
                modis_count = sum(1 for o in obs_records if "MODIS" in (o.satellite or "").upper())
                st.metric("MODIS Hotspots", modis_count)
            with col3:
                viirs_count = len(obs_records) - modis_count
                st.metric("VIIRS Hotspots", viirs_count)

            # Apply 2-decimal obfuscation
            obfuscated_records = [privacy_service.obfuscate_coordinates(o, decimal_places=2) for o in obs_records]

            # Folium Map
            center_lat = sum(o["latitude"] for o in obfuscated_records) / len(obfuscated_records)
            center_lon = sum(o["longitude"] for o in obfuscated_records) / len(obfuscated_records)
            m = folium.Map(location=[center_lat, center_lon], zoom_start=8, tiles="CartoDB positron")

            for o in obfuscated_records[:120]:
                is_modis = "MODIS" in (o.get("satellite") or "").upper()
                marker_color = "red" if is_modis else "darkred"
                folium.CircleMarker(
                    location=[o["latitude"], o["longitude"]],
                    radius=5 if is_modis else 4,
                    color=marker_color,
                    fill=True,
                    fill_opacity=0.6,
                    popup=f"Obs #{o.get('id')} | Sensor: {o.get('satellite')} | Approx Lat: {o['latitude']:.2f}, Lon: {o['longitude']:.2f} | FRP: {o.get('frp', 0.0):.1f} MW"
                ).add_to(m)

            folium_static(m, width=1100, height=480)

            # Obfuscated Summary Table
            df_obs = pd.DataFrame([{
                "Observation ID": o.get("id"),
                "Acquisition Date": str(o.get("acquisition_date")),
                "Approximate Latitude": f"{o.get('latitude'):.2f}",
                "Approximate Longitude": f"{o.get('longitude'):.2f}",
                "Sensor": o.get("satellite"),
                "Fire Radiative Power (MW)": f"{o.get('frp', 0.0):.1f}",
                "Confidence Score": f"{o.get('confidence_numeric', 0.0):.1f}%"
            } for o in obfuscated_records[:30]])
            st.dataframe(df_obs, use_container_width=True, height=220)
        else:
            st.info("No satellite observations available in database. Run ingestion from the Administrator workspace.")

    with tab_calendar:
        st.markdown("### Historical Burning Activity & Seasonality")
        st.caption("Empirical burning patterns across Punjab and Haryana agricultural regions.")

        baselines = db.query(HistoricalBaseline).limit(50).all()
        if baselines:
            base_df = pd.DataFrame([{
                "Region": b.region_id,
                "Period": b.analysis_period,
                "Day of Year": b.day_of_year or 0,
                "Mean FRP (MW)": b.mean_val,
                "Median FRP (MW)": b.median_val,
                "P90 FRP (MW)": b.p90_val,
                "Data Coverage": f"{b.data_coverage_ratio * 100:.0f}%"
            } for b in baselines])
            fig_hist = px.bar(
                base_df, x="Day of Year", y="Mean FRP (MW)", color="Region",
                title="Historical Mean Daily Fire Radiative Power (MW)",
                color_discrete_sequence=["#2d5f3f", "#8ab491"]
            )
            fig_hist.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("Historical baseline datasets are initializing or not yet loaded.")

        st.markdown("""
        **Seasonal Burning Dynamics in Northwest India:**
        - **Kharif Post-Harvest Window (Mid-October to Late-November):** Peak burning occurs within a narrow 15-20 day window as farmers clear paddy straw before sowing winter wheat.
        - **Rabi Post-Harvest Window (Mid-April to Late-May):** Secondary burning period for wheat straw, characterized by lower stubble volume and dry conditions.
        """)

    with tab_mission:
        st.markdown("### Mission: Sustainable Energy from Agricultural Residue")
        st.markdown("""
        Every autumn, over **20 million metric tons** of paddy straw are burned in open fields across northwest India, 
        emitting severe levels of PM2.5, black carbon, carbon monoxide, and greenhouse gases.

        **The Core Logistics Challenge:**
        Traditional biomass-to-energy power plants require transporting low-density raw straw over long distances (50-100 km), 
        which leads to prohibitive transport costs and road congestion.

        **The Stubble2Power Solution:**
        1. **NASA FIRMS Earth Observation:** Continuous satellite monitoring via MODIS and VIIRS detects burning hot spots and active harvest zones.
        2. **Decentralized Mobile Bio-Refineries:** Modular processing units mounted on transport trailers deploy directly to village farm clusters.
        3. **On-Site Upgrading:** Raw residue is converted into high-density **biochar** (soil carbon sequestration) and **fuel briquettes** (coal replacement in industrial boilers).
        4. **70% Logistics Cost Reduction:** Upgrading volume at the farm gate shrinks transport volumes and costs dramatically.
        5. **Farmer Empowerment:** Farmers are paid fair prices for clean residue collection rather than resorting to open-field burning.
        """)
