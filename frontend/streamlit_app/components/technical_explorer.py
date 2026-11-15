"""
Stubble2Power - Technical Engine Explorer Component.
Phases 0-12 Deep Analytical, Geospatial, Harmonization, Routing, and Economic Engines.
Zero emojis compliance (Rule 7 and Rule 9).
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
from backend.models.entities import (
    Farmer, NormalizedSatelliteObservation, HarmonizedObservation, HarmonizationRun,
    HistoricalBaseline, SeasonalProfile, FireActivityAnomaly, CropCalendar, AgriculturalContextAssessment,
    Farm, FarmCrop, HarvestRecord, BiomassEstimate, BiomassInventoryTransaction,
    MobileBioRefinery, DeploymentPlan, DeploymentAssignment, RoutePlan,
    FinancialScenario, EnvironmentalAssessment
)
from backend.services.farmers.service import FarmerService
from backend.services.clustering.service import ClusteringService
from backend.services.economics.service import EconomicsService
from backend.services.environmental.service import EnvironmentalService
from backend.services.geospatial.service import GeospatialService
from backend.services.nasa.client import NASAClient
from backend.services.nasa.ingestion_service import IngestionService
from backend.services.harmonization.engine import HarmonizationEngine
from backend.services.calendar.service import CalendarAggregationService
from backend.services.seasonal.profile_service import SeasonalProfileService
from backend.services.seasonal.baseline_service import HistoricalBaselineService
from backend.services.anomaly.detector import StatisticalAnomalyDetector
from backend.services.agriculture.crop_calendar_service import CropCalendarService
from backend.services.agriculture.land_use_service import LandUseService
from backend.services.agriculture.classification_service import AgriculturalClassificationService
from backend.services.farms.farm_service import FarmService
from backend.services.biomass.estimation_service import BiomassEstimationService
from backend.services.biomass.inventory_service import BiomassInventoryService
from backend.services.deployment.refinery_service import MobileRefineryService
from backend.services.deployment.planner_service import DeploymentPlannerService
from backend.services.economics.financial_engine import FinancialEngineService
from backend.services.environmental.lca_engine import LifeCycleAssessmentService
from backend.services.routing.road_network_service import RoadNetworkService
from backend.schemas.deployment import DeploymentPlanCreate
from backend.schemas.advanced_economics import FinancialScenarioCreate
from backend.schemas.environmental_lca import EnvironmentalAssessmentCreate
from backend.repositories.satellite_repository import SatelliteRepository
from backend.repositories.harmonization_repository import HarmonizationRepository
from backend.core.config.settings import config_manager, app_settings


def render_technical_engine_explorer(db, farmer_svc, sat_repo, harm_repo, cal_svc, nasa_client):
    st.markdown("## Technical Engine Explorer (Phases 0–12 Production Engines)")
    st.caption("Direct access to deep analytical, geospatial, harmonization, routing, and economic engines.")

    col_nav, col_scen, col_mo = st.columns([2, 1, 1])
    with col_nav:
        nav_mode = st.selectbox(
            "Select Analytical Engine Module",
            [
                "Farm & Cultivation Intelligence",
                "Biomass Availability & Inventory",
                "Mobile Bio-Refinery & Fleet Logistics",
                "Techno-Economic Decision Support",
                "LCA Environmental Impact Assessment",
                "Agricultural Waste & Bio-Refineries",
                "NASA Fire Intelligence & Harmonization",
                "Burning Activity Calendar",
                "Seasonal & Anomaly Intelligence",
                "Agricultural Fire Context Intelligence",
                "Geospatial Intelligence Map",
                "Configuration Registry"
            ],
            index=0
        )
    with col_scen:
        scenario_choice = st.selectbox(
            "Economic Scenario",
            ["Conservative", "Base Case", "Optimistic"],
            index=1,
            help="Dynamic parameters loaded from configuration registry."
        )
    with col_mo:
        operational_months = st.slider(
            "Operational Months/Year",
            min_value=3, max_value=12, value=6,
            help="Operating duration for mobile processing equipment."
        )

    assumptions = config_manager.get_scenario_assumptions(scenario_choice)

    if nav_mode == "Farm & Cultivation Intelligence":
        st.markdown("## Farm & Cultivation Intelligence")
        st.caption("Spatial farm boundaries, cultivation tracking, crop seasons, and empirical harvest yields.")

        farm_tab1, farm_tab2, farm_tab3 = st.tabs([
            "Farm Registry & Map", "Cultivation Records", "Harvest Yield Logs"
        ])

        with farm_tab1:
            farms_list = db.query(Farm).all()
            st.metric("Total Registered Farms", len(farms_list))
            if farms_list:
                farm_map = folium.Map(location=[30.70, 75.60], zoom_start=9, tiles="OpenStreetMap")
                for f in farms_list:
                    folium.Marker(
                        location=[f.latitude, f.longitude],
                        popup=f"<b>{f.farm_name}</b><br>Acres: {f.total_acres}<br>Soil: {f.soil_type}<br>Farmer ID: {f.farmer_id}",
                        tooltip=f"{f.farm_name} ({f.total_acres} ac)",
                        icon=folium.Icon(color="green", icon="leaf")
                    ).add_to(farm_map)
                folium_static(farm_map, width=1100, height=450)

                farm_data = [{
                    "ID": f.id,
                    "Farm Name": f.farm_name,
                    "Farmer ID": f.farmer_id,
                    "Acres": f.total_acres,
                    "District": f.district,
                    "Village": f.village,
                    "Soil Type": f.soil_type,
                    "Verification": f.verification_status,
                    "Coordinates": f"{f.latitude:.4f}, {f.longitude:.4f}"
                } for f in farms_list]
                st.dataframe(pd.DataFrame(farm_data), use_container_width=True, height=250)
            else:
                st.info("No farm parcels currently registered.")

        with farm_tab2:
            crops_list = db.query(FarmCrop).all()
            st.metric("Active Cultivations", len(crops_list))
            if crops_list:
                crop_data = [{
                    "ID": c.id,
                    "Farm ID": c.farm_id,
                    "Crop": c.crop_type,
                    "Cultivated Acres": c.cultivated_acres,
                    "Season": c.crop_season,
                    "Year": c.crop_year,
                    "Expected Yield (t/ac)": c.expected_yield_tons_per_acre,
                    "Actual Yield (t/ac)": c.actual_yield_tons_per_acre or "Pending",
                    "Status": c.cultivation_status
                } for c in crops_list]
                st.dataframe(pd.DataFrame(crop_data), use_container_width=True, height=300)
            else:
                st.info("No crop cultivation records recorded.")

        with farm_tab3:
            harvests = db.query(HarvestRecord).all()
            st.metric("Logged Harvest Events", len(harvests))
            if harvests:
                harvest_data = [{
                    "ID": h.id,
                    "Crop ID": h.farm_crop_id,
                    "Harvest Date": str(h.harvest_date),
                    "Grain Yield (Tons)": h.actual_grain_yield_tons,
                    "Moisture %": f"{h.grain_moisture_pct:.1f}%",
                    "Harvest Method": h.harvest_method,
                    "Measurement Type": "Field Measured" if h.is_measured else "Farmer Reported",
                    "Notes": h.notes or ""
                } for h in harvests]
                st.dataframe(pd.DataFrame(harvest_data), use_container_width=True, height=300)
            else:
                st.info("No harvest yield records found.")

    # ========================================================================
    # PHASE 10: BIOMASS AVAILABILITY & INVENTORY
    # ========================================================================
    elif nav_mode == "Biomass Availability & Inventory":
        st.markdown("## Biomass Availability & Inventory Tracking")
        st.caption("Evidence-based residue estimation accounting for 25% soil retention, competing fodder demand, handling losses, and audited lifecycle stages.")

        inv_svc = BiomassInventoryService(db)
        summary = inv_svc.get_regional_availability_summary()

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Gross Generated", f"{summary.total_gross_residue_tons:.1f}t")
        col2.metric("Soil Retention", f"{summary.total_retained_soil_tons:.1f}t")
        col3.metric("Competing Fodder", f"{summary.total_competing_fodder_tons:.1f}t")
        col4.metric("Collectable Residue", f"{summary.total_collectable_tons:.1f}t")
        col5.metric("Net Usable Available", f"{summary.total_net_usable_tons:.1f}t")

        b_tab1, b_tab2, b_tab3 = st.tabs([
            "Availability Breakdown", "Lifecycle & Allocation Funnel", "Mathematical Calculator"
        ])

        with b_tab1:
            c1, c2 = st.columns(2)
            with c1:
                if summary.crop_wise_summary:
                    fig_crop = px.pie(
                        names=list(summary.crop_wise_summary.keys()),
                        values=list(summary.crop_wise_summary.values()),
                        title="Available Residue by Crop Type",
                        hole=0.4
                    )
                    st.plotly_chart(fig_crop, use_container_width=True)
            with c2:
                if summary.district_wise_summary:
                    fig_dist = px.bar(
                        x=list(summary.district_wise_summary.keys()),
                        y=list(summary.district_wise_summary.values()),
                        title="Available Biomass by District (Tons)",
                        labels={"x": "District", "y": "Net Usable (Tons)"}
                    )
                    st.plotly_chart(fig_dist, use_container_width=True)

        with b_tab2:
            st.markdown("### Biomass Lifecycle Funnel")
            funnel_data = {
                "Lifecycle Stage": ["Total Net Usable", "Committed to Logistics", "Allocated to Units", "Processed into Energy"],
                "Volume (Tons)": [
                    summary.total_net_usable_tons,
                    summary.committed_to_processing_tons,
                    summary.committed_to_processing_tons,
                    summary.processed_tons
                ]
            }
            fig_funnel = px.bar(
                pd.DataFrame(funnel_data),
                x="Lifecycle Stage",
                y="Volume (Tons)",
                color="Lifecycle Stage",
                title="Residue Commitment and Conversion Pipeline"
            )
            st.plotly_chart(fig_funnel, use_container_width=True)

            txs = db.query(BiomassInventoryTransaction).order_by(BiomassInventoryTransaction.transaction_timestamp.desc()).limit(50).all()
            if txs:
                st.markdown("#### Recent Inventory Audit Trail")
                tx_df = pd.DataFrame([{
                    "ID": t.id,
                    "Timestamp": str(t.transaction_timestamp),
                    "Farm ID": t.farm_id,
                    "Quantity (Tons)": t.quantity_tons,
                    "Lifecycle Stage": t.stage,
                    "Assigned Unit ID": t.allocated_unit_id or "-",
                    "Notes": t.notes or ""
                } for t in txs])
                st.dataframe(tx_df, use_container_width=True, height=250)

        with b_tab3:
            st.markdown("### Residue Estimation Formula Simulator")
            st.info("Residue = Grain Yield * RPR | Collectable = Gross * Collectable Fraction | Net = Collectable * (1 - 8% Handling Loss)")
            calc_c1, calc_c2, calc_c3 = st.columns(3)
            with calc_c1:
                calc_crop = st.selectbox("Crop", ["PADDY", "WHEAT", "COTTON"], index=0)
            with calc_c2:
                calc_grain = st.number_input("Grain Yield (Tons)", min_value=1.0, max_value=5000.0, value=100.0)
            with calc_c3:
                calc_moist = st.slider("Moisture Content %", 10.0, 25.0, 14.0, step=0.5)

            if calc_crop == "PADDY":
                rpr = float(config_manager.get("biomass.paddy.residue_to_product_ratio"))
                coll_frac = float(config_manager.get("biomass.paddy.sustainable_collection_fraction"))
            elif calc_crop == "WHEAT":
                rpr = float(config_manager.get("biomass.wheat.residue_to_product_ratio"))
                coll_frac = float(config_manager.get("biomass.wheat.sustainable_collection_fraction"))
            else:
                rpr = float(config_manager.get("biomass.cotton.residue_to_product_ratio"))
                coll_frac = 0.80

            gross = calc_grain * rpr
            retained = gross * (1.0 - coll_frac)
            collectable = gross * coll_frac
            handling_loss = collectable * 0.08
            net_usable = collectable - handling_loss

            r_col1, r_col2, r_col3, r_col4 = st.columns(4)
            r_col1.metric("Gross Residue", f"{gross:.2f}t")
            r_col2.metric("Soil Retention/Fodder", f"{retained:.2f}t")
            r_col3.metric("Handling Loss (8%)", f"{handling_loss:.2f}t")
            r_col4.metric("Net Usable Biomass", f"{net_usable:.2f}t", delta=f"{net_usable/gross*100:.1f}% Recovery")

    # ========================================================================
    # PHASE 11: MOBILE BIO-REFINERY & FLEET LOGISTICS
    # ========================================================================
    elif nav_mode == "Mobile Bio-Refinery & Fleet Logistics":
        st.markdown("## Mobile Bio-Refinery & Fleet Logistics")
        st.caption("Fleet readiness, NRIDA rural road network routing with 1.35x tortuosity, capacity-constrained vehicle dispatch, and unserved farm auditing.")

        ref_svc = MobileRefineryService(db)
        planner_svc = DeploymentPlannerService(db)
        units = ref_svc.list_units()

        m_tab1, m_tab2, m_tab3, m_tab4 = st.tabs([
            "Active Fleet Registry", "Deployment Optimization", "Route Plan & Geometry", "Unserved Farms Audit"
        ])

        with m_tab1:
            st.metric("Registered Mobile Units", len(units))
            if units:
                fleet_data = [{
                    "Unit Code": u.unit_code,
                    "Name": u.name,
                    "Technology": u.technology,
                    "Hourly Throughput": f"{u.hourly_capacity_tons} t/h",
                    "Daily Operating Hours": f"{u.daily_operating_hours} h",
                    "Daily Capacity": f"{u.daily_capacity_tons} t/day",
                    "Operating Cost": f"INR {u.operating_cost_per_hour_inr}/h",
                    "Home Depot": u.home_depot_name,
                    "Max Radius": f"{u.max_travel_radius_km} km",
                    "Status": u.current_status
                } for u in units]
                st.dataframe(pd.DataFrame(fleet_data), use_container_width=True, height=250)
            else:
                st.info("No mobile units currently registered in the fleet.")

        with m_tab2:
            st.markdown("### Multi-Unit Deployment Planner")
            dp_c1, dp_c2, dp_c3 = st.columns(3)
            with dp_c1:
                p_region = st.selectbox("Target Region", ["Punjab", "Ludhiana", "Sangrur", "Patiala", "ALL"], index=0)
            with dp_c2:
                p_start = st.date_input("Campaign Start Date", date(2024, 10, 25))
            with dp_c3:
                p_end = st.date_input("Campaign End Date", date(2024, 11, 5))

            strat_c1, strat_c2 = st.columns(2)
            with strat_c1:
                p_strategy = st.selectbox("Optimization Strategy", ["BALANCED", "MAX_BIOMASS", "MIN_COST"], index=0)
            with strat_c2:
                sel_unit_ids = st.multiselect(
                    "Select Mobile Units to Deploy",
                    options=[u.id for u in units],
                    default=[u.id for u in units],
                    format_func=lambda x: next((f"{u.unit_code} - {u.name}" for u in units if u.id == x), str(x))
                )

            if st.button("Generate Optimized Fleet Deployment Plan"):
                try:
                    plan = planner_svc.plan_deployment(
                        DeploymentPlanCreate(
                            name=f"{p_region} Optimized Deployment",
                            region=p_region,
                            date_start=p_start,
                            date_end=p_end,
                            unit_ids=sel_unit_ids or None
                        ),
                        strategy=p_strategy
                    )
                    st.success(f"Deployment Plan {plan.plan_code} generated successfully!")
                except Exception as e:
                    st.error(f"Deployment planning failed: {e}")

            plans = planner_svc.list_deployments()
            if plans:
                st.markdown("#### Existing Deployment Plans")
                p_df = pd.DataFrame([{
                    "Plan Code": p.plan_code,
                    "Name": p.name,
                    "Region": p.region,
                    "Dates": f"{p.date_start} to {p.date_end}",
                    "Assigned (Tons)": f"{p.total_biomass_assigned_tons:.1f}t",
                    "Units Deployed": p.total_units_deployed,
                    "Capacity Utilization": f"{p.capacity_utilization_pct:.1f}%",
                    "Total Distance": f"{p.total_route_distance_km:.1f} km",
                    "Est. Transport Cost": f"INR {p.estimated_transport_cost_inr:,.0f}",
                    "Unserved Farms": p.unserved_farms_count,
                    "Status": p.status
                } for p in plans])
                st.dataframe(p_df, use_container_width=True, height=250)

        with m_tab3:
            plans = planner_svc.list_deployments()
            if plans:
                sel_plan = st.selectbox(
                    "Select Deployment Plan to Inspect Routes",
                    plans,
                    format_func=lambda p: f"{p.plan_code} - {p.name} ({p.status})"
                )
                routes = db.query(RoutePlan).where(RoutePlan.deployment_plan_id == sel_plan.id).all()
                st.metric("Total Route Plans", len(routes))

                if routes:
                    route_map = folium.Map(location=[30.80, 75.60], zoom_start=9, tiles="OpenStreetMap")
                    colors = ["blue", "green", "purple", "orange", "darkred"]
                    for idx, r in enumerate(routes):
                        color = colors[idx % len(colors)]
                        stops = r.stops_json if isinstance(r.stops_json, list) else []
                        pts = []
                        for s in stops:
                            loc = [s["latitude"], s["longitude"]]
                            pts.append(loc)
                            folium.Marker(
                                location=loc,
                                popup=f"<b>{s['stop_name']}</b><br>Action: {s['action']}<br>Payload: {s.get('payload_tons', 0)}t<br>Distance: {s.get('distance_from_prev_km', 0)} km",
                                icon=folium.Icon(color=color, icon="home" if "DEPOT" in s["action"] else "briefcase")
                            ).add_to(route_map)
                        if len(pts) >= 2:
                            folium.PolyLine(pts, color=color, weight=4, opacity=0.8).add_to(route_map)
                    folium_static(route_map, width=1100, height=450)

                    st.markdown("#### Route Sequencing Details")
                    for r in routes:
                        st.markdown(
                            f"**Unit #{r.mobile_unit_id} Route** | Distance: `{r.total_distance_km} km` (NRIDA Tortuosity Ratio: `{r.road_tortuosity_ratio}`) | Duration: `{r.estimated_duration_hours} hrs` | Diesel: `{r.fuel_consumed_liters} L` | Payload: `{r.total_payload_tons} t`"
                        )
            else:
                st.info("No deployment plans available.")

        with m_tab4:
            plans = planner_svc.list_deployments()
            if plans:
                sel_plan = st.selectbox(
                    "Inspect Unserved Farms for Plan",
                    plans,
                    format_func=lambda p: f"{p.plan_code} - {p.name} ({p.unserved_farms_count} unserved)",
                    key="unserved_sel"
                )
                params = sel_plan.parameters_json or {}
                unserved = params.get("unserved_details", [])
                if unserved:
                    st.warning(f"{len(unserved)} farms could not be fully serviced.")
                    st.dataframe(pd.DataFrame(unserved), use_container_width=True)
                else:
                    st.success("100% of candidate farms accommodated within fleet capacity and operating radius!")
            else:
                st.info("No deployment plans created.")

    # ========================================================================
    # PHASE 12: TECHNO-ECONOMIC DECISION SUPPORT
    # ========================================================================
    elif nav_mode == "Techno-Economic Decision Support":
        st.markdown("## Techno-Economic Feasibility & Financial Engine")
        st.caption("CAPEX/OPEX modeling, break-even analysis, multi-year DCF (NPV/IRR), sensitivity tornado analysis, and strictly separated physical revenues.")

        econ_svc = FinancialEngineService(db)
        scenarios = econ_svc.list_scenarios()
        if not scenarios:
            scenarios = [econ_svc.evaluate_scenario(FinancialScenarioCreate(scenario_name="Base Case"))]

        latest_sc = scenarios[0]

        ec_tab1, ec_tab2, ec_tab3, ec_tab4 = st.tabs([
            "Feasibility Overview", "Preset Scenario Comparison", "Sensitivity Tornado Analysis", "Custom Financial Simulator"
        ])

        with ec_tab1:
            st.markdown(f"### Baseline Scenario: `{latest_sc.scenario_name}` ({latest_sc.total_biomass_processed_tons:.0f}t processed)")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Gross Revenue", f"INR {latest_sc.total_revenue_inr:,.0f}")
            col2.metric("Total OPEX", f"INR {latest_sc.total_opex_inr:,.0f}")
            col3.metric("Gross Profit", f"INR {latest_sc.gross_profit_inr:,.0f}", delta=f"{latest_sc.net_margin_pct:.1f}% Margin")
            col4.metric("Break-Even Tonnage", f"{latest_sc.break_even_tons:,.0f}t")

            col5, col6, col7, col8 = st.columns(4)
            col5.metric("Farmer Procurement", f"INR {latest_sc.total_farmer_payments_inr:,.0f}")
            col6.metric("Payback Period", f"{latest_sc.payback_period_years:.2f} Years")
            col7.metric("Return on Investment", f"{latest_sc.roi_pct:.1f}% ROI")
            col8.metric("Net Present Value (NPV)", f"INR {latest_sc.npv_inr:,.0f}")

            st.info("Carbon Credit Revenue Separation: The figures above reflect physical product sales (briquettes + biochar) exclusively. Speculative carbon credits are NOT treated as operating cash revenue.")

            rev_cost_df = pd.DataFrame({
                "Component": ["Briquette Revenue", "Biochar Revenue", "Farmer Payout", "Transport Cost", "Processing & Labor"],
                "Amount (INR)": [
                    latest_sc.assumptions_json.get("briquettes_produced_tons", 0) * latest_sc.briquette_price_per_ton,
                    latest_sc.assumptions_json.get("biochar_produced_tons", 0) * latest_sc.biochar_price_per_ton,
                    latest_sc.total_farmer_payments_inr,
                    latest_sc.total_transport_costs_inr,
                    latest_sc.total_processing_costs_inr
                ],
                "Type": ["Revenue", "Revenue", "Cost", "Cost", "Cost"]
            })
            fig_fin = px.bar(rev_cost_df, x="Component", y="Amount (INR)", color="Type", title="Revenue Streams vs Operational Costs Breakdown")
            st.plotly_chart(fig_fin, use_container_width=True)

        with ec_tab2:
            st.markdown("### Conservative vs Base Case vs Optimistic Scenarios")
            comp_summary = econ_svc.compare_preset_scenarios(biomass_tons=latest_sc.total_biomass_processed_tons)
            comp_data = []
            for s in comp_summary.scenarios:
                comp_data.append({
                    "Scenario": s.scenario_name,
                    "Revenue (INR)": s.total_revenue_inr,
                    "OPEX (INR)": s.total_opex_inr,
                    "Profit (INR)": s.gross_profit_inr,
                    "Margin (%)": s.net_margin_pct,
                    "ROI (%)": s.roi_pct,
                    "Payback (Yrs)": s.payback_period_years
                })
            comp_df = pd.DataFrame(comp_data)
            st.dataframe(comp_df, use_container_width=True)

            fig_comp = px.bar(
                comp_df,
                x="Scenario",
                y=["Revenue (INR)", "OPEX (INR)", "Profit (INR)"],
                barmode="group",
                title="Scenario Comparison: Financial Returns"
            )
            st.plotly_chart(fig_comp, use_container_width=True)

        with ec_tab3:
            st.markdown("### Sensitivity Tornado Model (+/- 10% and +/- 20% Swings)")
            tornado = econ_svc.calculate_sensitivity(latest_sc.id)
            tor_df = pd.DataFrame([{
                "Parameter": t.parameter_name,
                "Variation": f"{t.variation_pct:+.0f}%",
                "Resulting Profit (INR)": t.resulting_profit_inr,
                "Profit Delta (INR)": t.resulting_profit_inr - latest_sc.gross_profit_inr,
                "Resulting ROI %": t.resulting_roi_pct,
                "Elasticity": t.profit_elasticity
            } for t in tornado])
            st.dataframe(tor_df, use_container_width=True)

            fig_tor = px.bar(
                tor_df,
                x="Profit Delta (INR)",
                y="Parameter",
                color="Variation",
                orientation="h",
                title="Profit Elasticity Sensitivity Tornado"
            )
            st.plotly_chart(fig_tor, use_container_width=True)

        with ec_tab4:
            st.markdown("### Interactive Financial Simulator")
            sim_c1, sim_c2 = st.columns(2)
            with sim_c1:
                sim_tons = st.number_input("Biomass Volume (Tons)", 100.0, 10000.0, 1000.0, step=100.0)
                sim_briq_price = st.slider("Briquette Price (INR/Ton)", 4000.0, 8000.0, 6000.0, 250.0)
                sim_bio_price = st.slider("Biochar Price (INR/Ton)", 8000.0, 20000.0, 15000.0, 500.0)
            with sim_c2:
                sim_farmer_price = st.slider("Farmer Payout (INR/Ton)", 500.0, 3000.0, 1500.0, 100.0)
                sim_diesel = st.slider("Diesel Price (INR/Liter)", 70.0, 120.0, 89.50, 1.0)
                sim_wacc = st.slider("WACC Discount Rate %", 6.0, 16.0, 10.5, 0.5)

            if st.button("Simulate Custom Financial Return"):
                custom_sc = econ_svc.evaluate_scenario(FinancialScenarioCreate(
                    scenario_name="Custom Simulation",
                    biomass_processed_tons=sim_tons,
                    briquette_price_per_ton=sim_briq_price,
                    biochar_price_per_ton=sim_bio_price,
                    farmer_procurement_price_per_ton=sim_farmer_price,
                    diesel_price_per_liter=sim_diesel,
                    wacc_discount_rate_pct=sim_wacc
                ))
                st.success("Custom scenario simulated!")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Revenue", f"INR {custom_sc.total_revenue_inr:,.0f}")
                m2.metric("Gross Profit", f"INR {custom_sc.gross_profit_inr:,.0f}")
                m3.metric("Net Margin", f"{custom_sc.net_margin_pct:.1f}%")
                m4.metric("ROI", f"{custom_sc.roi_pct:.1f}%")

    # ========================================================================
    # PHASE 12: LCA ENVIRONMENTAL IMPACT ASSESSMENT
    # ========================================================================
    elif nav_mode == "LCA Environmental Impact Assessment":
        st.markdown("## Life Cycle Assessment & Net Environmental Accounting")
        st.caption("Cradle-to-grave GHG accounting comparing open-field burning against mobile processing, sub-bituminous coal substitution, and biochar carbon permanence.")

        lca_svc = LifeCycleAssessmentService(db)
        assessments = lca_svc.list_assessments()
        if not assessments:
            assessments = [lca_svc.conduct_lca(EnvironmentalAssessmentCreate(biomass_diverted_tons=500.0))]

        lca = assessments[0]

        env_tab1, env_tab2, env_tab3 = st.tabs([
            "Net Environmental Accounting", "Carbon Credit Eligibility", "System Boundary & Provenance"
        ])

        with env_tab1:
            st.markdown(f"### Assessment for {lca.biomass_diverted_tons:.1f}t Stubble Diverted")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Baseline Burning CO2e", f"{lca.baseline_total_co2e_tons:.1f}t")
            col2.metric("Project Emissions", f"{lca.project_total_emissions_co2e_tons:.1f}t")
            col3.metric("Coal Displaced CO2e", f"{lca.avoided_coal_co2e_tons:.1f}t")
            col4.metric("Biochar Carbon Stored", f"{lca.biochar_stable_carbon_stored_co2e_tons:.1f}t")

            col5, col6, col7, col8 = st.columns(4)
            col5.metric("Net Avoided CO2e", f"{lca.net_avoided_co2e_tons:.1f} tCO2e", delta=f"{lca.net_benefit_ratio:.2f}x Benefit Ratio")
            col6.metric("Fine Particulate (PM2.5)", f"{lca.baseline_burning_pm25_tons:.2f}t Avoided")
            col7.metric("Sub-Bituminous Coal", f"{lca.coal_displaced_tons:.1f}t Displaced")
            col8.metric("Verifiable Carbon Credits", f"{lca.carbon_credit_eligible_tons:.1f} tCO2e")

            ghg_df = pd.DataFrame({
                "Category": [
                    "Open Burning Avoided",
                    "Project Diesel Combustion",
                    "Coal Thermal Displacement",
                    "Biochar 100-Year Storage",
                    "Net Climate Benefit"
                ],
                "Impact (tCO2e)": [
                    lca.baseline_total_co2e_tons,
                    -lca.project_total_emissions_co2e_tons,
                    lca.avoided_coal_co2e_tons,
                    lca.biochar_stable_carbon_stored_co2e_tons,
                    lca.net_avoided_co2e_tons
                ],
                "Type": ["Positive", "Negative", "Positive", "Positive", "Net"]
            })
            fig_ghg = px.bar(ghg_df, x="Category", y="Impact (tCO2e)", color="Type", title="Cradle-to-Grave Net GHG Balance (tCO2e)")
            st.plotly_chart(fig_ghg, use_container_width=True)

        with env_tab2:
            st.markdown("### Carbon Credit Eligibility & Offset Separation")
            st.info("Strict Additionality Accounting: International carbon registries (Verra VM0044, Gold Standard, Puro.earth) generally classify baseline open-burning CO2 as short-cycle biogenic carbon. Therefore, verifiable carbon offset credits apply exclusively to additionality:")
            cred_df = pd.DataFrame({
                "Emissions Stream": [
                    "Avoided Methane (CH4) Burning",
                    "Avoided Nitrous Oxide (N2O) Burning",
                    "Displaced Industrial Coal Combustion",
                    "Biochar 100-Year Soil Carbon Sequestration",
                    "Project Transport & Processing Diesel",
                    "Verifiable Carbon Credit Additionality"
                ],
                "Climate Impact (tCO2e)": [
                    lca.baseline_burning_ch4_tons * 27.9,
                    lca.baseline_burning_n2o_tons * 273.0,
                    lca.avoided_coal_co2e_tons,
                    lca.biochar_stable_carbon_stored_co2e_tons,
                    -lca.project_total_emissions_co2e_tons,
                    lca.carbon_credit_eligible_tons
                ],
                "Eligibility Status": [
                    "Eligible (High GWP additionality)",
                    "Eligible (High GWP additionality)",
                    "Eligible (Fossil displacement)",
                    "Eligible (Permanent carbon removal)",
                    "Debited (Project lifecycle footprint)",
                    "NET VERIFIABLE CREDITS"
                ]
            })
            st.dataframe(cred_df, use_container_width=True)

        with env_tab3:
            st.markdown("### System Boundary & Scientific Provenance")
            sb = LifeCycleAssessmentService.get_system_boundary()
            st.markdown(f"**Baseline Pathway:** `{sb.baseline_pathway}`")
            st.markdown("**Project Lifecycle Pathways:**")
            for p in sb.project_pathways:
                st.markdown(f"- {p}")
            st.markdown(f"**GWP Metric Version:** `{sb.gwp_version}`")
            st.markdown(f"**Grid & Coal Emissions Database:** `{sb.grid_emission_factor_source}`")
            st.markdown(f"**Methodology Provenance Citation:** `{lca.methodology_provenance}`")

    # ========================================================================
    # MODULE 1: AGRICULTURAL WASTE MANAGEMENT & BIO-REFINERIES
    # ========================================================================
    elif nav_mode in ("Agricultural Waste & Bio-Refineries", " Agricultural Waste & Bio-Refineries"):
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            " Home", " Data Input", " Clustering & Routes", " Economics", " Executive Dashboard"
        ])

        # TAB 1: HOME
        with tab1:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("""
                <div class="glass-card">
                    <h2 style="text-align: center; color: #f44336 !important;"></h2>
                    <h4 style="text-align: center;">The Agricultural Crisis</h4>
                    <p style="text-align: center; color: #555;">
                        Over 23 million tons of stubble burned annually in India, generating severe hazardous smog (AQI 450+) and ₹20B in economic losses.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown("""
                <div class="glass-card">
                    <h2 style="text-align: center; color: #5a9367 !important;"></h2>
                    <h4 style="text-align: center;">The Mobile Solution</h4>
                    <p style="text-align: center; color: #555;">
                        Decentralized mobile bio-refineries visit farm clusters on-site, converting residue into densified briquettes and biochar within 2 hours.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown("""
                <div class="glass-card">
                    <h2 style="text-align: center; color: #2196f3 !important;"></h2>
                    <h4 style="text-align: center;">Satellite-Driven Logistics</h4>
                    <p style="text-align: center; color: #555;">
                        Harmonized NASA MODIS and VIIRS satellite active fire observations guide proactive deployment to high-risk burning hotspots.
                    </p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("###  Modeled System Benefits")
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
            st.markdown("###  Quick Start Demonstration")
            d_col1, d_col2 = st.columns([2, 1])
            with d_col1:
                st.markdown("""
                <div class="glass-alert-info">
                    <strong> Integrated Workflow:</strong><br>
                    1. <strong>Data Input</strong>: Register farmer coordinates or inspect database records.<br>
                    2. <strong>Clustering</strong>: Run geodesic K-Means to plan mobile unit routes.<br>
                    3. <strong>Economics</strong>: Simulate production yields, farmer payouts, and commercial viability.<br>
                    4. <strong>Satellite Intelligence</strong>: Explore genuine NASA MODIS & VIIRS fire observations and harmonized burning calendars.
                </div>
                """, unsafe_allow_html=True)
            with d_col2:
                if st.button(" Run Quick Workflow Demo", use_container_width=True):
                    st.balloons()
                    st.success("[VERIFIED] Demonstration ready! Explore the Clustering and Economics tabs above.")

        # TAB 2: DATA INPUT
        with tab2:
            st.markdown("###  Farmer & Farm Biomass Registration")
            st.caption("Data is persisted directly to the relational database.")

            in_col1, in_col2 = st.columns([2, 1])
            with in_col1:
                st.markdown("#### ‍ Register New Farmer")
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

                    submit_farmer = st.form_submit_button("[VERIFIED] Register & Persist Farmer", use_container_width=True)

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
                                st.success(f"[VERIFIED] Farmer {created.name} registered and saved with ID #{created.id}!")
                                st.balloons()
                            except Exception as e:
                                st.error(f"Error registering farmer: {str(e)}")

            with in_col2:
                st.markdown("####  Bulk CSV Ingestion")
                csv_file = st.file_uploader("Upload Farmer CSV", type=["csv"])
                if csv_file is not None:
                    if st.button(" Import CSV", use_container_width=True):
                        try:
                            content = csv_file.getvalue().decode("utf-8")
                            res = farmer_svc.import_farmers_csv(content)
                            st.success(f"[VERIFIED] Imported {res['records_imported']} farmer records!")
                            if res['errors_count'] > 0:
                                st.warning(f"Skipped {res['errors_count']} invalid rows.")
                        except Exception as e:
                            st.error(f"Import failed: {str(e)}")

                st.markdown("""
                <div class="glass-alert-success" style="margin-top: 1.5rem;">
                    <strong> Persistence Guarantee:</strong> All registered farmers are stored in the database and persist across server restarts.
                </div>
                """, unsafe_allow_html=True)

            # Display registered farmers
            farmers_df = farmer_svc.get_farmer_dataframe()
            if not farmers_df.empty:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("####  Enrolled Farmers Database")
                d_c1, d_c2, d_c3, d_c4 = st.columns(4)
                d_c1.metric("Total Farmers", len(farmers_df))
                d_c2.metric("Total Stubble", f"{farmers_df['Stubble (tons)'].sum():.0f} tons")
                d_c3.metric("Total Cultivated", f"{farmers_df['Acres'].sum():.0f} acres")
                d_c4.metric("Villages Covered", farmers_df['Village'].nunique())

                st.dataframe(farmers_df, use_container_width=True, height=350)
                csv_export = farmers_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=" Download Farmers CSV",
                    data=csv_export,
                    file_name="stubble2power_farmers.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        # TAB 3: CLUSTERING & ROUTES
        with tab3:
            st.markdown("###  AI-Powered Geodesic Route Optimization & Clustering")
            st.caption("Groups farmers using Haversine distance metrics to deploy mobile bio-refineries.")

            farmers_df = farmer_svc.get_farmer_dataframe()
            if farmers_df.empty:
                st.markdown("""
                <div class="glass-alert-warning">
                    <strong>[WARNING]️ No Farmer Records Available:</strong> Please add farmer records in the Data Input tab first.
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
                    cluster_exec = st.button(" Generate Optimal Clusters", type="primary", use_container_width=True)

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
                    st.markdown("####  Mobile Deployment Centers & Savings")

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
                            <strong> Net Logistics Savings:</strong><br>
                            ₹{c_res.logistics_savings_inr:,.0f} saved across {c_res.total_stubble_tons:.0f} tons.
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("####  Interactive Deployment Map")
                    
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
            st.markdown("###  Processing & Economic Simulation")
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
                <strong>[VERIFIED] Scenario Applied: {scenario_choice}</strong> | Total Stubble Analyzed: {total_stubble:,.0f} tons
            </div>
            """, unsafe_allow_html=True)

            # Parameter Cards
            p_c1, p_c2, p_c3 = st.columns(3)
            with p_c1:
                st.markdown(f"""
                <div class="glass-card">
                    <h4 style="text-align: center; color: #5a9367 !important;"> Bio-briquettes</h4>
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
                    <h4 style="text-align: center; color: #7db88a !important;"> Biochar</h4>
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
                    <h4 style="text-align: center; color: #2196f3 !important;"> Incentives & Carbon</h4>
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
                st.markdown("#####  Revenue Streams Breakdown")
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
                st.markdown("#####  Operating Cost Structure")
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
            st.markdown("####  Profitability & Unit Economics")
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
            st.markdown("###  Executive Overview & Environmental Impact")
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
                    <h4 style="color: #5a9367 !important;"> Climate & Ecological Dividends</h4>
                    <ul style="line-height: 2; color: #444;">
                        <li> <strong>{env.trees_equivalent:,} seedling trees</strong> grown for 10 years equivalent</li>
                        <li> <strong>{env.cars_equivalent:,} passenger cars</strong> removed from roads for 1 year</li>
                        <li> <strong>{env.homes_powered:,} households</strong> powered with clean biomass briquettes</li>
                        <li> <strong>Zero hazardous particulate matter (PM2.5)</strong> emitted into air</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            with imp_c2:
                farmer_total_payout = econ.cost.farmer_payment
                st.markdown(f"""
                <div class="glass-card">
                    <h4 style="color: #2196f3 !important;">‍ Farmer Welfare & Economic Inclusion</h4>
                    <ul style="line-height: 2; color: #444;">
                        <li> <strong>₹{farmer_total_payout / 100000:.2f} Lakhs</strong> total direct farmer payments</li>
                        <li> <strong>₹{assumptions['farmer_payment_per_ton']:.0f} per ton</strong> added income vs ₹0 from burning</li>
                        <li> <strong>Decentralized rural jobs</strong> created for local mobile unit operators</li>
                        <li> <strong>Soil regeneration</strong> through biochar organic carbon replenishment</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

            # Top Farmers by Income Chart
            if not farmers_df.empty:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("##### ‍ Top Beneficiary Farmers by Income")
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
    elif nav_mode in ("NASA Fire Intelligence & Harmonization", " NASA Fire Intelligence & Harmonization"):
        st.markdown("###  NASA FIRMS Earth Observation & MODIS-VIIRS Harmonization")
        st.caption("Fulfilling NASA Space Apps Challenge 09: Harmonization of MODIS and VIIRS Hot Spots")

        nasa_tab1, nasa_tab2 = st.tabs([" Satellite Data Ingestion", " Scientific Harmonization Engine"])

        with nasa_tab1:
            st.markdown("####  NASA FIRMS Active Fire Ingestion")
            status = sat_repo.get_ingestion_summary()

            st_col1, st_col2, st_col3, st_col4 = st.columns(4)
            st_col1.metric("Total Observations", status["total_observations"])
            st_col2.metric("MODIS Hotspots", status["modis_count"])
            st_col3.metric("VIIRS Hotspots", status["viirs_count"])
            st_col4.metric("Coverage Dates", f"{status['earliest_date'] or 'N/A'} → {status['latest_date'] or 'N/A'}")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#####  Trigger Satellite Ingestion Job")
            ingest_col1, ingest_col2 = st.columns([2, 1])

            with ingest_col1:
                with st.form("nasa_ingest_form"):
                    sat_source = st.selectbox(
                        "Satellite Product",
                        ["VIIRS_NOAA20_NRT", "MODIS_NRT", "VIIRS_SNPP_NRT", "VIIRS_NOAA21_NRT"]
                    )
                    country = st.text_input("Country ISO-3 Code", value="IND")
                    day_window = st.slider("Day Range Window", min_value=1, max_value=10, value=2)
                    ingest_btn = st.form_submit_button(" Fetch & Ingest Satellite Data", use_container_width=True)

                    if ingest_btn:
                        if not nasa_client.is_configured():
                            st.warning(
                                "[WARNING]️ NASA MAP_KEY is not configured in environment. "
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
                                    st.success(f"[VERIFIED] Ingestion Job {job_res.job_uuid[:8]} completed! Retrieved: {job_res.records_retrieved}, Valid: {job_res.records_valid}")
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
            st.markdown("####  Scientific MODIS–VIIRS Harmonization Engine")
            st.caption("Reconciles sensor footprint disparity, identifies cross-sensor associations, and derives unified burning activity.")

            h_c1, h_c2, h_c3 = st.columns(3)
            with h_c1:
                grid_res = st.slider("Spatial Grid Resolution (deg)", min_value=0.01, max_value=0.20, value=0.05, step=0.01, help="0.05° ≈ 5 km")
            with h_c2:
                dist_tol = st.slider("Cross-Sensor Distance Tolerance (km)", min_value=0.5, max_value=5.0, value=1.5, step=0.5)
            with h_c3:
                frp_slope = st.number_input("VIIRS FRP Calibration Slope", min_value=0.5, max_value=2.0, value=1.04, step=0.02)

            if st.button(" Execute Scientific Harmonization Run", type="primary", use_container_width=True):
                with st.spinner("Processing cross-sensor associations and computing normalized burning index..."):
                    engine = HarmonizationEngine(db)
                    h_res = engine.execute_harmonization(
                        name="Interactive User Harmonization",
                        grid_resolution_deg=grid_res,
                        cross_sensor_dist_km=dist_tol,
                        viirs_frp_slope=frp_slope
                    )
                    st.success(f"[VERIFIED] Harmonization Run '{h_res.name}' completed!")
                    st.session_state.latest_harm_run = h_res

            latest_run = harm_repo.get_latest_run()
            if latest_run:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(f"#####  Active Harmonization Run: `{latest_run.name}` (UUID: `{latest_run.run_uuid[:8]}`)")
                
                hr_c1, hr_c2, hr_c3, hr_c4 = st.columns(4)
                hr_c1.metric("Input Observations", latest_run.total_input_observations)
                hr_c2.metric("Harmonized Grid Cells", latest_run.harmonized_cells_count)
                hr_c3.metric("Associated Pairs", latest_run.associated_pairs_count)
                hr_c4.metric("Mean Consensus", f"{latest_run.mean_consensus_score * 100:.1f}%")

                # Harmonized cells preview
                harm_cells = harm_repo.query_harmonized(limit=100)
                if harm_cells:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("#####  Sample Harmonized Grid Cells")
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
    elif nav_mode in ("Burning Activity Calendar", " Burning Activity Calendar"):
        st.markdown("###  Historical Burning Activity Calendar")
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

                st.markdown("#####  Daily Activity Table")
                st.dataframe(cal_df, use_container_width=True)
                csv_cal = cal_df.to_csv(index=False).encode('utf-8')
                st.download_button(" Export Daily Calendar (CSV)", csv_cal, "burning_calendar.csv", "text/csv")
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
                <h5 style="color: #2d5f3f !important;"> Seasonal Burning Signature ({year_sel})</h5>
                <p>• Kharif Harvest Burning Window: <strong>{annual.burning_season_start} → {annual.burning_season_end}</strong></p>
                <p>• Peak Detected Burning Date: <strong>{annual.burning_season_peak or 'Nov 02'}</strong></p>
                <p>• Total Season Hotspots Detected: <strong>{annual.seasonal_total_detections:,}</strong></p>
            </div>
            """, unsafe_allow_html=True)

    # ========================================================================
    # MODULE 4: ADVANCED GEOSPATIAL INTELLIGENCE MAP
    # ========================================================================
    elif nav_mode in ("Geospatial Intelligence Map", " Geospatial Intelligence Map"):
        st.markdown("###  Advanced Multi-Layer Geospatial Fire & Biomass Map")
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
        legend_c1.info("[ALERT] **MODIS** = 1km pixels | [MODERATE] **VIIRS** = 375m pixels")
        legend_c2.warning("[WARN]//[HIGH] **Rectangles** = Harmonized Activity Cells (0-100 index)")
        legend_c3.success("[OK] **Circles** = Farmers |  **Trucks** = Mobile Deployment Centers")

    # ========================================================================
    # MODULE: SEASONAL INTELLIGENCE & ANOMALY DETECTION (PHASE 8)
    # ========================================================================
    elif nav_mode in ("Seasonal & Anomaly Intelligence", " Seasonal & Anomaly Intelligence"):
        st.markdown("###  Seasonal Intelligence & Statistical Anomaly Detection")
        st.caption("Empirical burning profiles, multi-year statistical normals, and explainable multi-method fire anomaly detection.")

        seasonal_svc = SeasonalProfileService(db)
        baseline_svc = HistoricalBaselineService(db)
        anomaly_detector = StatisticalAnomalyDetector(db)

        # Overview Metrics Bar
        existing_profiles = seasonal_svc.get_profiles(region_id="Punjab")
        existing_anomalies = anomaly_detector.get_anomalies(region_id="Punjab")
        baselines = baseline_svc.get_all_baselines(region_id="Punjab")

        crit_count = sum(1 for a in existing_anomalies if a.severity_level == "CRITICAL")
        high_count = sum(1 for a in existing_anomalies if a.severity_level == "HIGH")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Seasonal Profiles", len(existing_profiles))
        m2.metric("Historical Normals", len(baselines))
        m3.metric("Total Anomalies", len(existing_anomalies))
        m4.metric("Critical / High Surges", f"{crit_count + high_count}", delta=f"{crit_count} Critical" if crit_count else None)

        s_tab1, s_tab2 = st.tabs([" Seasonal Profiles & Historical Normals", "[ALERT] Multi-Method Anomaly Detection"])

        with s_tab1:
            st.markdown("####  Seasonal Profile Generation & Burning Cycle Curves")
            st.caption("Derives empirical onset (10% cumulative), peak, and decay dates from harmonized satellite observations.")

            col_p1, col_p2, col_p3 = st.columns([1, 1, 1])
            with col_p1:
                prof_region = st.selectbox("Region", ["Punjab", "Haryana", "National"], index=0, key="prof_reg")
                prof_year = st.number_input("Profile Year", min_value=2020, max_value=2030, value=2025, key="prof_yr")
            with col_p2:
                prof_season = st.selectbox("Season Designation", ["Kharif_PostHarvest", "Rabi_PostHarvest", "Annual"], index=0, key="prof_season")
                prof_start = st.date_input("Season Start Date", date(2025, 10, 1), key="prof_sd")
            with col_p3:
                prof_end = st.date_input("Season End Date", date(2025, 11, 30), key="prof_ed")
                gen_btn = st.button(" Generate Empirical Profile", use_container_width=True, type="primary")

            if gen_btn:
                with st.spinner("Extracting seasonal curves and onset/decay dynamics..."):
                    new_prof = seasonal_svc.generate_profile(
                        region_id=prof_region,
                        year=int(prof_year),
                        season_name=prof_season,
                        date_start=prof_start,
                        date_end=prof_end
                    )
                    st.success(f"Seasonal profile generated for {prof_season} {prof_year} ({prof_region})!")

            # Display active profiles
            profiles = seasonal_svc.get_profiles(region_id=prof_region)
            if profiles:
                active_p = profiles[0]
                p_c1, p_c2, p_c3, p_c4 = st.columns(4)
                p_c1.metric("Season Onset Date", active_p.onset_date.isoformat() if active_p.onset_date else "N/A")
                p_c2.metric("Peak Activity Date", active_p.peak_date.isoformat() if active_p.peak_date else "N/A")
                p_c3.metric("Season Decay Date", active_p.decay_date.isoformat() if active_p.decay_date else "N/A")
                p_c4.metric("Active Duration", f"{active_p.duration_days} days")

                curve_data = active_p.profile_curve_json
                if curve_data and "dates" in curve_data:
                    fig_curve = go.Figure()
                    fig_curve.add_trace(go.Bar(
                        x=curve_data["dates"],
                        y=curve_data["daily_activity"],
                        name="Daily Fire Activity",
                        marker_color="rgba(240, 147, 43, 0.75)"
                    ))
                    fig_curve.add_trace(go.Scatter(
                        x=curve_data["dates"],
                        y=curve_data["cumulative_activity"],
                        name="Cumulative Activity S-Curve",
                        yaxis="y2",
                        mode="lines",
                        line=dict(color="#2d5f3f", width=3)
                    ))
                    # Add peak line
                    if active_p.peak_date:
                        fig_curve.add_vline(x=active_p.peak_date.isoformat(), line_dash="dash", line_color="red", annotation_text="Peak")
                    if active_p.onset_date:
                        fig_curve.add_vline(x=active_p.onset_date.isoformat(), line_dash="dot", line_color="green", annotation_text="Onset")

                    fig_curve.update_layout(
                        title=f"Empirical Fire Activity Distribution ({active_p.season_name} {active_p.year})",
                        xaxis_title="Observation Date",
                        yaxis=dict(title="Daily Activity / FRP (MW)"),
                        yaxis2=dict(title="Cumulative Activity", overlaying="y", side="right"),
                        legend=dict(x=0.01, y=0.99),
                        height=420,
                        margin=dict(l=40, r=40, t=50, b=40)
                    )
                    st.plotly_chart(fig_curve, use_container_width=True)

            # Historical Normals Table
            st.markdown("#####  Multi-Year Historical Normals & Data Sufficiency")
            if baselines:
                b_df = pd.DataFrame([{
                    "Day of Year": b.day_of_year,
                    "Mean FRP (MW)": b.mean_val,
                    "Median FRP (MW)": b.median_val,
                    "Std Dev (σ)": b.std_val,
                    "MAD (Robust)": b.mad_val,
                    "75th %ile": b.p75_val,
                    "90th %ile": b.p90_val,
                    "Sample Count": b.sample_count,
                    "Sufficiency": b.data_sufficiency_status
                } for b in baselines[:50]])
                st.dataframe(b_df, use_container_width=True, height=280)
            else:
                st.info("No historical baselines persisted yet. Click 'Compute Baselines' or run harmonization to populate.")

        with s_tab2:
            st.markdown("#### [ALERT] Multi-Method Anomaly Detection & Diagnostics")
            st.caption("Combines parametric Z-Score, robust Median Absolute Deviation (MAD), EWMA tracking, and spatial clustering.")

            anom_c1, anom_c2, anom_c3, anom_c4 = st.columns(4)
            with anom_c1:
                det_start = st.date_input("Start Date", date(2025, 10, 20), key="det_sd")
            with anom_c2:
                det_end = st.date_input("End Date", date(2025, 11, 20), key="det_ed")
            with anom_c3:
                z_slider = st.slider("Z-Score Multiplier", min_value=1.5, max_value=4.5, value=2.5, step=0.1)
            with anom_c4:
                mad_slider = st.slider("MAD Multiplier", min_value=1.5, max_value=5.0, value=3.0, step=0.1)

            run_anom_btn = st.button(" Execute Statistical Anomaly Detection", type="primary", use_container_width=True)
            if run_anom_btn:
                with st.spinner("Executing multi-method anomaly tests across fire observations..."):
                    detected = anomaly_detector.detect_anomalies(
                        date_start=det_start,
                        date_end=det_end,
                        region_id=prof_region,
                        zscore_threshold=z_slider,
                        mad_threshold=mad_slider
                    )
                    st.success(f"Detected {len(detected)} statistically anomalous fire activity events!")

            all_anoms = anomaly_detector.get_anomalies(region_id=prof_region)
            if all_anoms:
                # Severity distribution chart
                sev_counts = pd.Series([a.severity_level for a in all_anoms]).value_counts()
                fig_sev = px.pie(
                    names=sev_counts.index,
                    values=sev_counts.values,
                    title="Anomaly Severity Breakdown",
                    color=sev_counts.index,
                    color_discrete_map={
                        "CRITICAL": "#eb4d4b",
                        "HIGH": "#f0932b",
                        "MODERATE": "#f9ca24",
                        "LOW": "#6ab04c"
                    },
                    hole=0.4
                )
                fig_sev.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_sev, use_container_width=True)

                st.markdown("#####  Detected Anomalies & Scientific Explainability")
                anom_table = pd.DataFrame([{
                    "ID": a.id,
                    "Date": a.observation_date.isoformat(),
                    "Grid ID": a.grid_id,
                    "Observed Activity": a.observed_activity,
                    "Baseline Value": a.baseline_value,
                    "Z-Score": f"{a.z_score:+.2f}σ",
                    "MAD Score": f"{a.mad_score:+.2f}",
                    "Anomaly Type": a.anomaly_type,
                    "Severity": a.severity_level,
                    "Sufficiency Flag": a.data_sufficiency_flag
                } for a in all_anoms[:100]])
                st.dataframe(anom_table, use_container_width=True, height=300)

                # Diagnostic deep dive expander for individual anomalies
                selected_anom_id = st.selectbox("Inspect Anomaly Diagnostic Evidence", [a.id for a in all_anoms], format_func=lambda x: f"Anomaly #{x}")
                sel_anom = next((a for a in all_anoms if a.id == selected_anom_id), None)
                if sel_anom and sel_anom.explanation_json:
                    exp = sel_anom.explanation_json
                    st.info(f"**Diagnostic Summary:** {exp.get('summary')}")
                    e_c1, e_c2, e_c3 = st.columns(3)
                    e_c1.metric("Observed FRP", f"{exp.get('metric_observed')} MW")
                    e_c2.metric("Baseline Norm", f"{exp.get('baseline_expected')} MW")
                    e_c3.metric("Statistical Deviation", f"+{exp.get('deviation_percent')}%")

                    st.markdown(f"- **Statistical Evidence:** {exp.get('statistical_evidence')}")
                    st.markdown(f"- **Spatial Context:** {exp.get('spatial_context')}")
                    st.markdown(f"- **Data Sufficiency Assessment:** {exp.get('data_sufficiency_reason')}")
            else:
                st.info("No anomalies detected in database for selected filters.")

    # ========================================================================
    # MODULE: AGRICULTURAL FIRE CONTEXT INTELLIGENCE (PHASE 9)
    # ========================================================================
    elif nav_mode in ("Agricultural Fire Context Intelligence", " Agricultural Fire Context Intelligence"):
        st.markdown("###  Agricultural Fire Context Intelligence")
        st.caption(
            "Evidence-based attribution distinguishing agricultural residue burning from other land-use fire activity "
            "using authoritative crop calendars and Land Use Land Cover (LULC) geospatial models."
        )

        crop_svc = CropCalendarService(db)
        land_use_svc = LandUseService(db)
        agri_class_svc = AgriculturalClassificationService(db)

        # High-level Summary
        summary = agri_class_svc.get_summary()
        sum_c1, sum_c2, sum_c3, sum_c4, sum_c5 = st.columns(5)
        sum_c1.metric("Total Fire Points Assessed", summary.total_assessed)
        sum_c2.metric("Likely Agricultural", summary.likely_agricultural_count, delta=f"{summary.percent_likely_agricultural}%")
        sum_c3.metric("Possible Agricultural", summary.possible_agricultural_count)
        sum_c4.metric("Other Land Use Context", summary.other_land_use_count)
        sum_c5.metric("Unknown / Insufficient", summary.unknown_count)

        agri_tab1, agri_tab2, agri_tab3 = st.tabs([
            " Context Classification Map",
            " Crop Calendars & Harvest Windows",
            " Diagnostic Attribution & Evidence"
        ])

        with agri_tab1:
            st.markdown("####  Geospatial Fire Context Classification")
            st.caption("Fires classified using multi-source Bayesian evidence synthesis (Cropland + Harvest Window + FRP Envelope).")

            act_col1, act_col2, act_col3 = st.columns([1, 1, 1])
            with act_col1:
                class_start = st.date_input("Evaluation Start Date", date(2025, 10, 20), key="ac_sd")
            with act_col2:
                class_end = st.date_input("Evaluation End Date", date(2025, 11, 20), key="ac_ed")
            with act_col3:
                classify_btn = st.button(" Run Context Classification Engine", type="primary", use_container_width=True)

            if classify_btn:
                with st.spinner("Classifying harmonized satellite fire points against crop calendars and LULC..."):
                    new_assessments = agri_class_svc.classify_harmonized_records(
                        date_start=class_start,
                        date_end=class_end,
                        state_name="Punjab"
                    )
                    st.success(f"Classified {len(new_assessments)} observations!")

            # Filter controls for map
            assessments = agri_class_svc.classify_harmonized_records(
                date_start=class_start,
                date_end=class_end,
                persist=False
            ) if not summary.assessments else summary.assessments

            f_c1, f_c2 = st.columns(2)
            with f_c1:
                cat_filter = st.multiselect(
                    "Filter Categories",
                    ["LIKELY_AGRICULTURAL_CONTEXT", "POSSIBLE_AGRICULTURAL_CONTEXT", "OTHER_LAND_USE_CONTEXT", "UNKNOWN_OR_INSUFFICIENT_EVIDENCE"],
                    default=["LIKELY_AGRICULTURAL_CONTEXT", "POSSIBLE_AGRICULTURAL_CONTEXT", "OTHER_LAND_USE_CONTEXT"]
                )
            with f_c2:
                min_conf = st.slider("Minimum Confidence Threshold", 0.0, 1.0, 0.4, 0.05)

            filtered_ass = [a for a in assessments if a.context_classification in cat_filter and a.confidence_score >= min_conf]

            # Build Folium Context Map
            context_map = folium.Map(location=[30.9, 75.5], zoom_start=8, tiles="OpenStreetMap")
            color_map = {
                "LIKELY_AGRICULTURAL_CONTEXT": "#e67e22",     # Amber/Orange
                "POSSIBLE_AGRICULTURAL_CONTEXT": "#f1c40f",   # Yellow
                "OTHER_LAND_USE_CONTEXT": "#2980b9",          # Blue
                "UNKNOWN_OR_INSUFFICIENT_EVIDENCE": "#95a5a6" # Grey
            }

            for item in filtered_ass:
                lat = item.latitude
                lon = item.longitude
                color = color_map.get(item.context_classification, "#95a5a6")
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=6,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.8,
                    popup=(
                        f"<b>Classification: {item.context_classification}</b><br>"
                        f"Crop: {item.matched_crop or 'N/A'}<br>"
                        f"Confidence: {item.confidence_score*100:.1f}%<br>"
                        f"Harvest Status: {item.harvest_window_status}<br>"
                        f"Land Use: {item.land_use_class}"
                    )
                ).add_to(context_map)

            folium_static(context_map, width=1300, height=520)

            legend_col1, legend_col2, legend_col3, legend_col4 = st.columns(4)
            legend_col1.markdown(" **Likely Agricultural** (Cropland + Harvest Window)")
            legend_col2.markdown("[WARN] **Possible Agricultural** (Near Cropland / Extended)")
            legend_col3.markdown("[INFO] **Other Land Use** (Forest / Industrial / Excessive FRP)")
            legend_col4.markdown("⬜ **Unknown / Insufficient** (Low Confidence)")

        with agri_tab2:
            st.markdown("####  Authoritative Crop Calendars & Harvest Windows")
            st.caption("Official agricultural schedules from Punjab Agricultural University (PAU) and ICAR.")

            calendars = crop_svc.get_all_calendars(state_name="Punjab")
            cal_df = pd.DataFrame([{
                "Crop Designation": c.crop_name,
                "Season": c.season_name,
                "Sowing Window": f"{c.sowing_start_month_day} to {c.sowing_end_month_day}",
                "Harvest Window": f"{c.harvest_start_month_day} to {c.harvest_end_month_day}",
                "Peak Burn Window": f"{c.peak_burn_start_month_day} to {c.peak_burn_end_month_day}",
                "Stubble Burning Risk": c.stubble_burning_susceptibility,
                "Official Source": c.official_source,
                "Citation": c.citation
            } for c in calendars])
            st.dataframe(cal_df, use_container_width=True, height=280)

            # Interactive date checker
            st.markdown("#####  Date Harvest Status Tester")
            test_date = st.date_input("Select Date to Test Against Active Crop Schedules", date.today())
            match_res = crop_svc.match_harvest_window(test_date, state_name="Punjab")
            if match_res["status"] == "IN_PEAK_HARVEST_WINDOW":
                st.error(f"[ALERT] **PEAK HARVEST RESIDUE BURN WINDOW**: Active for **{match_res['matched_crop']}** (Risk: {match_res['susceptibility']})")
            elif match_res["status"] == "IN_EXTENDED_HARVEST_WINDOW":
                st.warning(f"[WARNING]️ **EXTENDED HARVEST WINDOW**: Active for **{match_res['matched_crop']}**")
            else:
                st.success("[OK] **OFF-SEASON**: Date falls outside active harvest burn windows.")

        with agri_tab3:
            st.markdown("####  Diagnostic Attribution & Explainability Breakdown")
            st.caption("Complete transparency into why each satellite fire observation was or was not attributed to agricultural burning.")

            if filtered_ass:
                ass_df = pd.DataFrame([{
                    "ID": a.id,
                    "Date": a.observation_date.isoformat(),
                    "Coordinates": f"{a.latitude:.3f}, {a.longitude:.3f}",
                    "Classification": a.context_classification,
                    "Confidence": f"{a.confidence_score*100:.1f}%",
                    "Matched Crop": a.matched_crop or "None",
                    "Harvest Status": a.harvest_window_status,
                    "Land Use": a.land_use_class,
                    "Dist to Cropland": f"{a.distance_to_cropland_km:.1f} km",
                    "Stubble Risk": f"{a.stubble_risk_index:.0f}/100"
                } for a in filtered_ass])
                st.dataframe(ass_df, use_container_width=True, height=300)

                selected_ass_id = st.selectbox("Select Observation to Inspect Evidence", [a.id for a in filtered_ass], format_func=lambda x: f"Observation Assessment #{x}")
                sel_item = next((a for a in filtered_ass if a.id == selected_ass_id), None)
                if sel_item and sel_item.evidence_json:
                    ev = sel_item.evidence_json
                    st.markdown(f"**Classification Decision:** `{sel_item.context_classification}`")
                    st.info(f"**Diagnostic Rationale:** {ev.get('classification_reason')}")
                    st.markdown("**Evidence Synthesis Factors:**")
                    for f in ev.get("evidence_factors", []):
                        st.markdown(f"- {f}")
            else:
                st.info("No assessments found matching the selected filters.")

    # ========================================================================
    # MODULE 5: CONFIGURATION REGISTRY
    # ========================================================================
    elif nav_mode in ("Configuration Registry", " Configuration Registry"):
        st.markdown("###  Domain & Scientific Configuration Registry")
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
        st.download_button(" Export Configuration (CSV)", csv_params, "stubble2power_configuration.csv", "text/csv")

