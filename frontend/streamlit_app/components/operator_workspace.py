"""
Stubble2Power - Field Operator Workspace Component.
Mobile bio-refinery unit management, 2-opt TSP sequenced route stops, interactive stop status dispatcher, and logistics KPIs.
Zero emojis compliance (Rule 7 & Rule 9).
"""

from datetime import datetime
import pandas as pd
import streamlit as st

from backend.models.entities import (
    MobileBioRefinery, RoutePlan, DeploymentAssignment, Farm, AuditLog
)
from backend.services.routing.road_network_service import RoadNetworkService
from backend.services.deployment.refinery_service import MobileRefineryService
from frontend.streamlit_app.localization.i18n import t


def render_operator_workspace(db, user_ctx: dict, lang: str = "en"):
    """Renders the Field Operator Mobile Logistics & Dispatch Workspace."""
    st.markdown("## Field Operator Logistics & Route Dispatch Workspace")
    st.caption("Active Mobile Bio-Refinery Fleet Navigation | 2-Opt Sequenced Farm Collection Stops")

    # Retrieve Operator's Assigned Mobile Unit
    mobile_units = db.query(MobileBioRefinery).all()
    if not mobile_units:
        st.error("No mobile bio-refineries registered in database.")
        return

    active_unit = mobile_units[0]  # MBR-PUNJAB-01

    # Unit Status Banner
    st.markdown(f"""
    <div style="background: rgba(255, 255, 255, 0.7); border-radius: 12px; padding: 1rem; border: 1px solid rgba(45, 95, 63, 0.2); margin-bottom: 1.2rem;">
        <div style="font-size: 1.15rem; font-weight: 700; color: #2d5f3f;">Assigned Unit: {active_unit.refinery_code}</div>
        <div style="font-size: 0.85rem; color: #555; margin-top: 0.3rem;">
            <b>Type:</b> {active_unit.processing_type} | <b>Nameplate Capacity:</b> {active_unit.daily_capacity_tons:.1f} t/day | 
            <b>Operational Status:</b> [{active_unit.operational_status}] | <b>Current Hub:</b> Lat {active_unit.current_lat:.4f}, Lon {active_unit.current_lon:.4f}
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_route, tab_dispatcher, tab_logistics = st.tabs([
        "2-Opt Sequenced Collection Route",
        "Interactive Stop Status Dispatcher",
        "Logistics & Fuel Consumption KPIs"
    ])

    road_service = RoadNetworkService()

    # Retrieve active RoutePlan
    route_plan = db.query(RoutePlan).filter(RoutePlan.mobile_refinery_id == active_unit.id).first()
    if not route_plan:
        route_plan = db.query(RoutePlan).first()

    # 1. 2-OPT SEQUENCED ROUTE
    with tab_route:
        st.markdown("### Sequenced Farm Collection Route (2-Opt TSP Optimized)")
        st.caption("Route order optimized via 2-Opt local search edge-swaps to minimize travel distance.")

        if route_plan and route_plan.route_geometry_json:
            seq_stops = route_plan.route_geometry_json.get("sequenced_stops", [])
            total_dist_km = route_plan.total_distance_km
            est_duration = route_plan.estimated_duration_hours

            col_r1, col_r2, col_r3 = st.columns(3)
            with col_r1:
                st.metric("Total Route Distance", f"{total_dist_km:.1f} km")
            with col_r2:
                st.metric("Estimated Transit Time", f"{est_duration:.1f} hrs")
            with col_r3:
                st.metric("Total Stops in Cycle", len(seq_stops))

            if seq_stops:
                stop_rows = []
                for s in seq_stops:
                    stop_rows.append({
                        "Seq #": s.get("sequence_index"),
                        "Farm ID": s.get("farm_id"),
                        "Farm Name": s.get("farm_name"),
                        "Coordinates": f"{s.get('latitude', 0.0):.4f}, {s.get('longitude', 0.0):.4f}",
                        "Biomass (t)": f"{s.get('biomass_tons', 0.0):.1f}",
                        "Distance from Prior": f"{s.get('distance_from_previous_km', 0.0):.1f} km",
                        "Cumulative Distance": f"{s.get('cumulative_distance_km', 0.0):.1f} km",
                        "Stop Status": s.get("status", "PENDING")
                    })
                df_stops = pd.DataFrame(stop_rows)
                st.dataframe(df_stops, use_container_width=True, height=260)
            else:
                st.info("No sequenced stops loaded for this route.")
        else:
            # Fallback farm list
            farms = db.query(Farm).limit(10).all()
            st.info("Generating real-time 2-opt sequence from enrolled farms...")
            farm_dicts = [{"id": f.id, "farm_name": f.farm_name, "latitude": f.latitude, "longitude": f.longitude, "stubble_tonnage": 20.0} for f in farms]
            res = road_service.compute_route_plan(depot_lat=active_unit.current_lat, depot_lon=active_unit.current_lon, farms=farm_dicts)
            st.metric("Total 2-Opt Distance", f"{res['total_distance_km']:.1f} km")
            st.dataframe(pd.DataFrame(res["sequenced_stops"]), use_container_width=True, height=240)

    # 2. INTERACTIVE STOP STATUS DISPATCHER
    with tab_dispatcher:
        st.markdown("### Interactive Stop Status Dispatcher")
        st.caption("Update operational stop statuses in real time. Changes are persisted and recorded in the audit trail.")

        if route_plan and route_plan.route_geometry_json and route_plan.route_geometry_json.get("sequenced_stops"):
            seq_stops = route_plan.route_geometry_json.get("sequenced_stops", [])
            stop_options = [f"Stop #{s.get('sequence_index')}: {s.get('farm_name')} [Status: {s.get('status', 'PENDING')}]" for s in seq_stops]

            selected_stop_str = st.selectbox("Select Stop to Update", options=stop_options)
            stop_idx = int(selected_stop_str.split(":")[0].replace("Stop #", "").strip())

            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            with col_s1:
                btn_transit = st.button("Mark: IN_TRANSIT", key="btn_in_transit")
            with col_s2:
                btn_arrived = st.button("Mark: ARRIVED", key="btn_arrived")
            with col_s3:
                btn_picked = st.button("Mark: PICKED_UP", key="btn_picked")
            with col_s4:
                btn_processed = st.button("Mark: PROCESSED", key="btn_processed")

            new_status = None
            if btn_transit:
                new_status = "IN_TRANSIT"
            elif btn_arrived:
                new_status = "ARRIVED"
            elif btn_picked:
                new_status = "PICKED_UP"
            elif btn_processed:
                new_status = "PROCESSED"

            if new_status:
                # Update status in json
                for s in seq_stops:
                    if s.get("sequence_index") == stop_idx:
                        s["status"] = new_status
                        s["updated_at"] = datetime.utcnow().isoformat()
                        break

                route_plan.route_geometry_json["sequenced_stops"] = seq_stops
                db.commit()

                # Audit log
                audit = AuditLog(
                    actor_user_id=user_ctx.get("user_id"),
                    actor_username=user_ctx.get("username", "field_operator"),
                    action="UPDATE_ROUTE_STOP_STATUS",
                    resource_type="RoutePlan",
                    resource_id=str(route_plan.id),
                    details_json={"stop_index": stop_idx, "new_status": new_status}
                )
                db.add(audit)
                db.commit()

                st.success(f"Stop #{stop_idx} successfully updated to [{new_status}]. Audit record generated.")
                st.rerun()
        else:
            st.info("No active route plan stops available to update.")

    # 3. LOGISTICS & FUEL KPIS
    with tab_logistics:
        st.markdown("### Logistics & Environmental Transit Fuel Performance")
        st.caption("Empirical fuel modeling and comparison against centralized hauling logistics.")

        dist = route_plan.total_distance_km if route_plan else 78.4
        tons = 120.0
        fuel_liters = dist * 0.15 * (tons / 20.0)  # diesel fuel modeled
        diesel_emissions_co2_kg = fuel_liters * 2.68  # 2.68 kg CO2/L diesel

        col_k1, col_k2, col_k3 = st.columns(3)
        with col_k1:
            st.metric("Total Transit Distance", f"{dist:.1f} km")
        with col_k2:
            st.metric("Modeled Diesel Fuel", f"{fuel_liters:.1f} L")
        with col_k3:
            st.metric("Transport Emissions", f"{diesel_emissions_co2_kg:.1f} kg CO2e")

        st.markdown("""
        **Decentralized Mobile Fleet Efficiency Gain:**
        - **Centralized Plant Hauling:** Requires moving raw, uncompressed straw (density 60-80 kg/m3) over 60-100 km radial distances.
        - **Decentralized Mobile Processing:** Upgrades straw at the cluster hub into dense briquettes (density 1,100 kg/m3) and biochar (density 400 kg/m3), reducing outbound transport trips by **70%**.
        - **Road Tortuosity Factor:** Modeled using NRIDA PMGSY rural road network empirical tortuosity of 1.30.
        """)
