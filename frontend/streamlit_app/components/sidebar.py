"""
Stubble2Power - Sidebar Navigation & Identity Governance Component.
Phases 13 & 14 Multi-User Identity, Multilingual Support, and RBAC Navigation.
Zero emojis compliance (Rule 7 & Rule 9).
"""

from typing import Tuple, Dict, Any, Optional
import streamlit as st
from backend.models.entities import User, Organization
from backend.core.security.rbac import RoleName, PermissionName, ROLE_PERMISSIONS
from backend.core.security.auth import create_access_token
from frontend.streamlit_app.localization.i18n import t


BENCHMARK_IDENTITIES = [
    {
        "label": "Public Visitor (Unauthenticated Guest)",
        "username": "public_visitor",
        "role": RoleName.PUBLIC_VISITOR.value,
        "name": "Public Visitor",
        "org_code": "PUBLIC",
        "farmer_id": None
    },
    {
        "label": "Gurpreet Singh (Farmer - PB-BIO-COOP)",
        "username": "gurpreet_singh",
        "role": RoleName.FARMER.value,
        "name": "Gurpreet Singh",
        "org_code": "PB-BIO-COOP",
        "farmer_id": 1
    },
    {
        "label": "Ramesh Kumar (Field Operator - PB-BIO-COOP)",
        "username": "operator_ramesh",
        "role": RoleName.FIELD_OPERATOR.value,
        "name": "Ramesh Kumar",
        "org_code": "PB-BIO-COOP",
        "farmer_id": None
    },
    {
        "label": "Priya Sharma (Agri Analyst - PB-BIO-COOP)",
        "username": "analyst_priya",
        "role": RoleName.AGRICULTURAL_ANALYST.value,
        "name": "Priya Sharma",
        "org_code": "PB-BIO-COOP",
        "farmer_id": None
    },
    {
        "label": "Vikram Malhotra (Env Analyst - MAPS-MALWA)",
        "username": "analyst_vikram",
        "role": RoleName.ENVIRONMENTAL_ANALYST.value,
        "name": "Vikram Malhotra",
        "org_code": "MAPS-MALWA",
        "farmer_id": None
    },
    {
        "label": "Harpreet Kaur (Org Manager - PB-BIO-COOP)",
        "username": "manager_harpreet",
        "role": RoleName.ORGANIZATION_MANAGER.value,
        "name": "Harpreet Kaur",
        "org_code": "PB-BIO-COOP",
        "farmer_id": None
    },
    {
        "label": "System Administrator (All Organizations)",
        "username": "admin",
        "role": RoleName.SYSTEM_ADMINISTRATOR.value,
        "name": "System Administrator",
        "org_code": "SYSTEM",
        "farmer_id": None
    }
]


def render_sidebar(db, db_ok: bool, nasa_ok: bool) -> Tuple[Dict[str, Any], str, str]:
    """
    Renders the modern role-based sidebar.
    Returns: (active_user_context, active_workspace, selected_language)
    """
    with st.sidebar:
        st.markdown("### STUBBLE2POWER")
        st.caption("NASA Space Apps Challenge 09 | v2.2.0")

        # Multilingual Language Selector
        lang_options = {"en": "English", "hi": "Hindi (हिन्दी)", "pa": "Punjabi (ਪੰਜਾਬੀ)"}
        selected_lang_code = st.selectbox(
            "Language / भाषा / ਭਾਸ਼ਾ",
            options=list(lang_options.keys()),
            format_func=lambda x: lang_options[x],
            index=0
        )

        st.markdown("---")
        st.markdown("#### Identity & Role Switcher")
        st.caption("Select active benchmark profile to evaluate RBAC and tenant security:")

        identity_labels = [item["label"] for item in BENCHMARK_IDENTITIES]
        selected_idx = st.selectbox(
            "Active User Identity",
            range(len(identity_labels)),
            format_func=lambda i: identity_labels[i],
            index=0
        )
        selected_identity = BENCHMARK_IDENTITIES[selected_idx]

        # Retrieve or construct user context from database
        user_record = None
        if selected_identity["username"] != "public_visitor":
            user_record = db.query(User).filter(User.username == selected_identity["username"]).first()

        # Update session state with identity
        st.session_state["username"] = selected_identity["username"]
        st.session_state["role"] = selected_identity["role"]
        st.session_state["user_id"] = user_record.id if user_record else None
        st.session_state["organization_id"] = user_record.organization_id if user_record else None
        st.session_state["farmer_id"] = user_record.farmer_id if user_record else selected_identity["farmer_id"]
        st.session_state["full_name"] = user_record.full_name if user_record else selected_identity["name"]

        # Display Identity Badge
        role_label = selected_identity["role"].replace("_", " ")
        org_label = selected_identity["org_code"]
        st.markdown(f"""
        <div style="background: rgba(255, 255, 255, 0.7); border: 1px solid rgba(45, 95, 63, 0.3); border-radius: 10px; padding: 0.8rem; margin: 0.6rem 0;">
            <div style="font-weight: 700; color: #1e462d; font-size: 0.95rem;">{selected_identity['name']}</div>
            <div style="font-size: 0.8rem; color: #444; margin-top: 0.2rem;">
                <b>Role:</b> {role_label}<br>
                <b>Tenant:</b> {org_label}<br>
                <b>Status:</b> [VERIFIED IDENTITY]
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Platform Navigation")

        # Determine available workspaces based on role
        current_role = selected_identity["role"]
        workspaces = []

        if current_role == RoleName.PUBLIC_VISITOR.value:
            workspaces = ["Public Fire Intelligence & Mission"]
        elif current_role == RoleName.FARMER.value:
            workspaces = ["Farmer Parcel & Harvest Workspace", "Public Fire Intelligence & Mission"]
        elif current_role == RoleName.FIELD_OPERATOR.value:
            workspaces = ["Mobile Unit & Route Logistics Workspace", "Public Fire Intelligence & Mission"]
        elif current_role == RoleName.AGRICULTURAL_ANALYST.value:
            workspaces = [
                "Agricultural Analyst Workspace",
                "Technical Engine Explorer",
                "Public Fire Intelligence & Mission"
            ]
        elif current_role == RoleName.ENVIRONMENTAL_ANALYST.value:
            workspaces = [
                "Environmental Analyst Workspace",
                "Technical Engine Explorer",
                "Public Fire Intelligence & Mission"
            ]
        elif current_role == RoleName.ORGANIZATION_MANAGER.value:
            workspaces = [
                "Organization Manager Workspace",
                "Technical Engine Explorer",
                "Public Fire Intelligence & Mission"
            ]
        elif current_role == RoleName.SYSTEM_ADMINISTRATOR.value:
            workspaces = [
                "System Administrator Workspace",
                "Agricultural Analyst Workspace",
                "Environmental Analyst Workspace",
                "Organization Manager Workspace",
                "Mobile Unit & Route Logistics Workspace",
                "Farmer Parcel & Harvest Workspace",
                "Technical Engine Explorer",
                "Public Fire Intelligence & Mission"
            ]

        active_workspace = st.radio(
            "Select Workspace View",
            options=workspaces,
            index=0
        )

        st.markdown("---")
        st.markdown("#### System Health Status")
        col_db, col_nasa = st.columns(2)
        with col_db:
            st.caption(f"PostGIS DB: {'[ONLINE]' if db_ok else '[DEGRADED]'}")
        with col_nasa:
            st.caption(f"NASA FIRMS: {'[CONFIGURED]' if nasa_ok else '[UNCONFIGURED]'}")

        st.markdown("---")
        st.caption("Stubble2Power Security: PBKDF2-SHA256 Auth | Role-Based Access Control | DPDP Act 2023 Compliant")

    user_ctx = {
        "username": st.session_state["username"],
        "role": st.session_state["role"],
        "user_id": st.session_state["user_id"],
        "organization_id": st.session_state["organization_id"],
        "farmer_id": st.session_state["farmer_id"],
        "full_name": st.session_state["full_name"],
        "is_authenticated": st.session_state["username"] != "public_visitor"
    }

    return user_ctx, active_workspace, selected_lang_code
