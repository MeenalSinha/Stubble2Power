"""
Stubble2Power - Farmer Workspace Component.
Farm boundaries, interactive harvest yield logging, biomass estimation, DPDP Act 2023 consent management, DSR requests, and financial statements.
Zero emojis compliance (Rule 7 & Rule 9).
"""

from datetime import date, datetime
import pandas as pd
import folium
from streamlit_folium import folium_static
import streamlit as st

from backend.models.entities import (
    Farmer, Farm, FarmCrop, HarvestRecord, BiomassEstimate,
    ConsentRecord, DataSubjectRequest, AuditLog
)
from backend.services.farms.farm_service import FarmService
from backend.services.biomass.estimation_service import BiomassEstimationService
from backend.services.privacy.privacy_service import PrivacyGovernanceService
from frontend.streamlit_app.localization.i18n import t


def render_farmer_workspace(db, user_ctx: dict, lang: str = "en"):
    """Renders the dedicated Farmer Workspace."""
    st.markdown("## Farmer Agricultural & Residue Management Workspace")
    st.caption("Registered Landholder Portal | Crop Cultivation, Biomass Monetization & Privacy Governance")

    farmer_id = user_ctx.get("farmer_id")
    farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first() if farmer_id else None

    if not farmer:
        st.warning("No farmer profile linked to this account. Demonstrating with benchmark farmer: Gurpreet Singh.")
        farmer = db.query(Farmer).first()
        farmer_id = farmer.id if farmer else None

    if not farmer:
        st.error("No registered farmers found in database.")
        return

    # Profile Summary Header
    masked_aadhaar = f"XXXX-XXXX-{farmer.aadhaar_hash[-4:]}" if farmer.aadhaar_hash else "XXXX-XXXX-1234"
    st.markdown(f"""
    <div style="background: rgba(255, 255, 255, 0.7); border-radius: 12px; padding: 1rem; border: 1px solid rgba(45, 95, 63, 0.2); margin-bottom: 1.2rem;">
        <div style="font-size: 1.15rem; font-weight: 700; color: #2d5f3f;">{farmer.name}</div>
        <div style="font-size: 0.85rem; color: #555; margin-top: 0.3rem;">
            <b>District:</b> {farmer.district} | <b>Village:</b> {farmer.village} | 
            <b>Aadhaar ID:</b> {masked_aadhaar} | <b>Total Landholding:</b> {farmer.total_acres} acres | 
            <b>Stubble Available:</b> {farmer.stubble_tonnage:.1f} tons
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_parcels, tab_harvest, tab_biomass, tab_privacy, tab_earnings = st.tabs([
        "Farm Parcels & Boundary Map",
        "Harvest Logging & Records",
        "Biomass Availability Schedule",
        "DPDP Privacy & Consent Manager",
        "Financial Earnings & Statements"
    ])

    farm_service = FarmService(db)
    biomass_service = BiomassEstimationService(db)
    privacy_service = PrivacyGovernanceService(db)

    # 1. PARCELS & EXACT MAP
    with tab_parcels:
        st.markdown("### Registered Land Parcels (Exact Spatial Boundaries)")
        st.caption("Exact coordinates are displayed to the authorized landholder.")

        farms = db.query(Farm).filter(Farm.farmer_id == farmer.id).all()
        if farms:
            col_m1, col_m2 = st.columns([2, 1])
            with col_m1:
                center_lat = sum(f.latitude for f in farms) / len(farms)
                center_lon = sum(f.longitude for f in farms) / len(farms)
                farm_map = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="OpenStreetMap")

                for f in farms:
                    folium.Marker(
                        location=[f.latitude, f.longitude],
                        popup=f"<b>{f.farm_name}</b><br>Acres: {f.total_acres}<br>Soil: {f.soil_type}",
                        tooltip=f"{f.farm_name} ({f.total_acres} ac)",
                        icon=folium.Icon(color="green", icon="info-sign")
                    ).add_to(farm_map)
                folium_static(farm_map, width=720, height=380)

            with col_m2:
                for f in farms:
                    st.markdown(f"""
                    <div style="background: white; border-radius: 8px; padding: 0.8rem; border: 1px solid #ddd; margin-bottom: 0.6rem;">
                        <div style="font-weight: 700; color: #1e462d;">{f.farm_name}</div>
                        <div style="font-size: 0.8rem; color: #666;">
                            <b>Parcel ID:</b> #{f.id}<br>
                            <b>Area:</b> {f.total_acres} acres<br>
                            <b>Soil Type:</b> {f.soil_type}<br>
                            <b>Coordinates:</b> {f.latitude:.4f}, {f.longitude:.4f}<br>
                            <b>Irrigation:</b> {getattr(f, 'irrigation_status', 'CANAL_IRRIGATED')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No farms registered under your profile.")

    # 2. HARVEST LOGGING & RECORDS
    with tab_harvest:
        st.markdown("### Interactive Harvest Yield Logger")
        st.caption("Log grain yields to trigger automated residue estimation and scheduling.")

        farms = db.query(Farm).filter(Farm.farmer_id == farmer.id).all()
        if farms:
            with st.form("harvest_logger_form"):
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    selected_farm = st.selectbox(
                        "Select Farm Parcel",
                        options=farms,
                        format_func=lambda f: f"{f.farm_name} ({f.total_acres} acres)"
                    )
                    selected_crop = st.selectbox(
                        "Crop Designation",
                        options=["PADDY", "WHEAT", "COTTON", "MAIZE"]
                    )
                with col_f2:
                    grain_tons = st.number_input(
                        "Harvested Grain (Metric Tons)",
                        min_value=0.5, max_value=500.0, value=25.0, step=0.5
                    )
                    harvest_dt = st.date_input("Harvest Completion Date", value=date.today())

                submit_harvest = st.form_submit_button("Log Harvest & Compute Residue")

                if submit_harvest and selected_farm:
                    # Resolve or create FarmCrop association
                    farm_crop = db.query(FarmCrop).filter(
                        FarmCrop.farm_id == selected_farm.id,
                        FarmCrop.crop_type == selected_crop
                    ).first()
                    if not farm_crop:
                        farm_crop = FarmCrop(
                            farm_id=selected_farm.id,
                            crop_type=selected_crop,
                            cultivated_acres=selected_farm.total_acres,
                            crop_season="Kharif",
                            crop_year=date.today().year
                        )
                        db.add(farm_crop)
                        db.commit()
                        db.refresh(farm_crop)

                    # Save HarvestRecord
                    rec = HarvestRecord(
                        farm_crop_id=farm_crop.id,
                        harvest_date=harvest_dt,
                        actual_grain_yield_tons=float(grain_tons),
                        harvest_method="COMBINE_HARVESTER_WITH_SMS",
                        notes=f"Interactive harvest entry by {user_ctx.get('full_name')}"
                    )
                    db.add(rec)
                    db.commit()
                    db.refresh(rec)

                    # Estimate Biomass
                    crop_acres = selected_farm.total_acres
                    est_result = biomass_service.estimate_from_harvest_yield(
                        farm_id=selected_farm.id,
                        crop_name=selected_crop,
                        grain_yield_tons=float(grain_tons),
                        acres=crop_acres,
                        harvest_date=harvest_dt
                    )
                    st.success(
                        f"Harvest yield logged successfully! Estimated collectable residue: "
                        f"{est_result.collectable_biomass_tons:.1f} dry tons (Confidence: {est_result.confidence_score * 100:.0f}%)."
                    )

        st.markdown("---")
        st.markdown("#### Historical Harvest Logs")
        farm_ids = [f.id for f in farms]
        harvests = db.query(HarvestRecord).filter(HarvestRecord.farm_id.in_(farm_ids)).order_by(HarvestRecord.harvest_date.desc()).all() if farm_ids else []
        if harvests:
            h_df = pd.DataFrame([{
                "Harvest ID": h.id,
                "Farm ID": h.farm_id,
                "Harvest Date": str(h.harvest_date),
                "Crop": h.crop_name,
                "Grain Yield (t)": f"{h.grain_yield_tons:.1f}",
                "Harvest Method": h.harvest_method
            } for h in harvests])
            st.dataframe(h_df, use_container_width=True, height=200)
        else:
            st.info("No harvest records logged yet.")

    # 3. BIOMASS AVAILABILITY
    with tab_biomass:
        st.markdown("### Agricultural Biomass Availability & Collection Window")
        st.caption("Residue availability calculations with PAU soil retention factors.")

        farm_ids = [f.id for f in farms]
        estimates = db.query(BiomassEstimate).filter(BiomassEstimate.farm_id.in_(farm_ids)).all() if farm_ids else []
        if estimates:
            col_b1, col_b2, col_b3 = st.columns(3)
            total_residue = sum(e.total_residue_tons for e in estimates)
            total_collectable = sum(e.collectable_biomass_tons for e in estimates)
            soil_retained = total_residue - total_collectable

            with col_b1:
                st.metric("Total Generated Residue", f"{total_residue:.1f} t")
            with col_b2:
                st.metric("Collectable Biomass", f"{total_collectable:.1f} t")
            with col_b3:
                st.metric("Soil Conservation Retained", f"{soil_retained:.1f} t")

            est_df = pd.DataFrame([{
                "Estimate ID": e.id,
                "Farm ID": e.farm_id,
                "Crop": e.crop_name,
                "Total Residue (t)": f"{e.total_residue_tons:.1f}",
                "Collectable (t)": f"{e.collectable_biomass_tons:.1f}",
                "Moisture %": f"{e.moisture_content_pct:.1f}%",
                "Collection Window": f"{e.availability_start_date} to {e.availability_end_date}",
                "Estimation Method": e.estimation_method
            } for e in estimates])
            st.dataframe(est_df, use_container_width=True, height=220)
        else:
            st.info("No biomass estimates found. Log a harvest record to generate availability estimates.")

    # 4. PRIVACY & DPDP CONSENT MANAGEMENT
    with tab_privacy:
        st.markdown("### DPDP Act 2023 Consent & Privacy Governance")
        st.caption("Manage statutory purpose-bound consents and exercise digital data rights.")

        st.markdown("#### Purpose-Bound Consents")
        consents = db.query(ConsentRecord).filter(ConsentRecord.farmer_id == farmer.id).all()
        if consents:
            for c in consents:
                status_badge = "[ACTIVE / GRANTED]" if c.is_granted else "[WITHDRAWN]"
                col_c1, col_c2 = st.columns([3, 1])
                with col_c1:
                    st.markdown(f"""
                    <div style="background: white; border-radius: 8px; padding: 0.8rem; border-left: 4px solid {'#2d5f3f' if c.is_granted else '#c0392b'}; margin-bottom: 0.5rem;">
                        <b>Purpose:</b> <code>{c.consent_purpose}</code> | <b>Status:</b> {status_badge}<br>
                        <span style="font-size: 0.8rem; color: #666;">Granted: {c.consent_timestamp.strftime('%Y-%m-%d %H:%M')} | Version: {c.consent_version}</span>
                    </div>
                    """, unsafe_allow_html=True)
                with col_c2:
                    if c.is_granted:
                        if st.button("Withdraw Consent", key=f"btn_withdraw_{c.id}"):
                            privacy_service.withdraw_consent(farmer_id=farmer.id, purpose=c.consent_purpose)
                            st.success(f"Consent for {c.consent_purpose} withdrawn.")
                            st.rerun()
                    else:
                        if st.button("Grant Consent", key=f"btn_grant_{c.id}"):
                            privacy_service.record_consent(farmer_id=farmer.id, purpose=c.consent_purpose)
                            st.success(f"Consent for {c.consent_purpose} granted.")
                            st.rerun()
        else:
            st.info("No existing consent records. You can grant standard consents below.")

        st.markdown("---")
        st.markdown("#### Submit Data Subject Request (DSR)")
        with st.form("dsr_request_form"):
            req_type = st.selectbox(
                "Request Category",
                options=["ACCESS", "CORRECTION", "ERASURE", "EXPORT"]
            )
            req_notes = st.text_area("Request Justification & Scope", placeholder="Describe your data access or erasure request...")
            submit_dsr = st.form_submit_button("Submit Statutory Data Request")

            if submit_dsr and user_ctx.get("user_id"):
                dsr = privacy_service.submit_data_subject_request(
                    user_id=user_ctx.get("user_id"),
                    request_type=req_type,
                    details={"notes": req_notes, "farmer_id": farmer.id}
                )
                st.success(f"Request #{dsr.id} submitted successfully under DPDP Act 2023. Status: SUBMITTED.")

        # Display Past DSR Requests
        if user_ctx.get("user_id"):
            dsrs = db.query(DataSubjectRequest).filter(DataSubjectRequest.user_id == user_ctx.get("user_id")).all()
            if dsrs:
                st.markdown("##### Your Prior Requests")
                dsr_df = pd.DataFrame([{
                    "Request ID": d.id,
                    "Type": d.request_type,
                    "Status": d.status,
                    "Requested Date": d.requested_at.strftime('%Y-%m-%d %H:%M')
                } for d in dsrs])
                st.dataframe(dsr_df, use_container_width=True, height=140)

    # 5. FINANCIAL EARNINGS
    with tab_earnings:
        st.markdown("### Biomass Monetization & Settlement Statements")
        st.caption("Guaranteed direct payments for residue diverted from burning.")

        rate_per_ton = 1800.0  # INR per ton
        tons_delivered = farmer.stubble_tonnage
        gross_earnings = tons_delivered * rate_per_ton

        col_e1, col_e2, col_e3 = st.columns(3)
        with col_e1:
            st.metric("Base Procurement Price", f"₹{rate_per_ton:,.0f}/t")
        with col_e2:
            st.metric("Pledged Biomass", f"{tons_delivered:.1f} t")
        with col_e3:
            st.metric("Estimated Gross Earnings", f"₹{gross_earnings:,.0f}")

        st.markdown("""
        **Payment Terms:**
        - **50% Advance:** Disbursed within 48 hours of mobile baler / refinery arrival at farm parcel.
        - **50% Final Settlement:** Disbursed upon weighbridge verification and moisture check (< 20%).
        - Payments are deposited directly to your enrolled Aadhaar-linked cooperative bank account.
        """)
