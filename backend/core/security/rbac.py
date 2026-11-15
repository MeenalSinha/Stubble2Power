"""
Authoritative Role-Based Access Control (RBAC) Registry & Permission Matrix.
Enforces granular, server-side permission checks across all multi-user workspaces.
"""

from enum import Enum
from typing import Dict, List, Set, Union
from backend.core.exceptions.base import AuthorizationError


class RoleName(str, Enum):
    """Authoritative platform user roles."""
    PUBLIC_VISITOR = "PUBLIC_VISITOR"
    FARMER = "FARMER"
    FIELD_OPERATOR = "FIELD_OPERATOR"
    AGRICULTURAL_ANALYST = "AGRICULTURAL_ANALYST"
    ENVIRONMENTAL_ANALYST = "ENVIRONMENTAL_ANALYST"
    ORGANIZATION_MANAGER = "ORGANIZATION_MANAGER"
    SYSTEM_ADMINISTRATOR = "SYSTEM_ADMINISTRATOR"


class PermissionName(str, Enum):
    """Granular action and resource permission identifiers."""
    # Universal Superuser
    WILDCARD = "*"

    # Public Permissions
    FIRE_VIEW_PUBLIC = "fire:view_public"
    AGRICULTURE_VIEW_PUBLIC = "agriculture:view_public"
    REPORT_VIEW_PUBLIC = "report:view_public"

    # Farmer Permissions
    FARM_VIEW_OWN = "farm:view_own"
    FARM_EDIT_OWN = "farm:edit_own"
    FARM_CREATE_OWN = "farm:create_own"
    HARVEST_LOG_OWN = "harvest:log_own"
    BIOMASS_VIEW_OWN = "biomass:view_own"
    CONSENT_MANAGE_OWN = "consent:manage_own"
    PRIVACY_SUBMIT_REQUEST = "privacy:submit_request"
    REPORT_VIEW_OWN = "report:view_own"

    # Field Operator Permissions
    FARM_VIEW_ASSIGNED = "farm:view_assigned"
    ROUTE_VIEW_ASSIGNED = "route:view_assigned"
    COLLECTION_UPDATE = "collection:update"
    BIOMASS_VIEW_ASSIGNED = "biomass:view_assigned"
    UNIT_VIEW_ASSIGNED = "unit:view_assigned"
    REPORT_VIEW_ASSIGNED = "report:view_assigned"

    # Agricultural Analyst Permissions
    FIRE_VIEW_FULL = "fire:view_full"
    AGRICULTURE_VIEW_CONTEXT = "agriculture:view_context"
    AGRICULTURE_VIEW_ANALYTICS = "agriculture:view_analytics"
    CROP_VIEW_ANALYTICS = "crop:view_analytics"
    BIOMASS_VIEW_ALL = "biomass:view_all"
    REPORT_GENERATE_AGRI = "report:generate_agri"

    # Environmental Analyst Permissions
    SEASONAL_VIEW = "seasonal:view"
    ANOMALY_VIEW = "anomaly:view"
    LCA_VIEW_ASSESS = "lca:view_assess"
    LCA_CONDUCT_ASSESS = "lca:conduct_assess"
    REPORT_GENERATE_ENV = "report:generate_env"

    # Organization Manager Permissions
    ORG_MANAGE_MEMBERS = "org:manage_members"
    FARM_VIEW_ORG = "farm:view_org"
    FARM_CREATE_ORG = "farm:create_org"
    FARM_EDIT_ORG = "farm:edit_org"
    BIOMASS_VIEW_ORG = "biomass:view_org"
    BIOMASS_ALLOCATE_ORG = "biomass:allocate_org"
    UNIT_MANAGE_ORG = "unit:manage_org"
    DEPLOYMENT_PLAN_ORG = "deployment:plan_org"
    FINANCE_VIEW_ORG = "finance:view_org"
    FINANCE_EVALUATE_ORG = "finance:evaluate_org"
    REPORT_GENERATE_ALL = "report:generate_all"

    # System Administrator Permissions
    SYSTEM_ADMIN = "system:admin"
    AUDIT_VIEW = "audit:view"
    CONFIG_MANAGE = "config:manage"
    USER_MANAGE_ALL = "user:manage_all"
    SECURITY_VIEW_EVENTS = "security:view_events"
    RETENTION_EXECUTE = "retention:execute"
    BACKUP_EXECUTE = "backup:execute"


# Granular Permission Definitions
ROLE_PERMISSIONS: Dict[RoleName, Set[PermissionName]] = {
    RoleName.PUBLIC_VISITOR: {
        PermissionName.FIRE_VIEW_PUBLIC,
        PermissionName.AGRICULTURE_VIEW_PUBLIC,
        PermissionName.REPORT_VIEW_PUBLIC,
    },
    RoleName.FARMER: {
        PermissionName.FIRE_VIEW_PUBLIC,
        PermissionName.AGRICULTURE_VIEW_PUBLIC,
        PermissionName.FARM_VIEW_OWN,
        PermissionName.FARM_EDIT_OWN,
        PermissionName.FARM_CREATE_OWN,
        PermissionName.HARVEST_LOG_OWN,
        PermissionName.BIOMASS_VIEW_OWN,
        PermissionName.CONSENT_MANAGE_OWN,
        PermissionName.PRIVACY_SUBMIT_REQUEST,
        PermissionName.REPORT_VIEW_OWN,
    },
    RoleName.FIELD_OPERATOR: {
        PermissionName.FIRE_VIEW_PUBLIC,
        PermissionName.FARM_VIEW_ASSIGNED,
        PermissionName.ROUTE_VIEW_ASSIGNED,
        PermissionName.COLLECTION_UPDATE,
        PermissionName.BIOMASS_VIEW_ASSIGNED,
        PermissionName.UNIT_VIEW_ASSIGNED,
        PermissionName.REPORT_VIEW_ASSIGNED,
    },
    RoleName.AGRICULTURAL_ANALYST: {
        PermissionName.FIRE_VIEW_PUBLIC,
        PermissionName.FIRE_VIEW_FULL,
        PermissionName.AGRICULTURE_VIEW_CONTEXT,
        PermissionName.AGRICULTURE_VIEW_ANALYTICS,
        PermissionName.CROP_VIEW_ANALYTICS,
        PermissionName.BIOMASS_VIEW_ALL,
        PermissionName.REPORT_GENERATE_AGRI,
    },
    RoleName.ENVIRONMENTAL_ANALYST: {
        PermissionName.FIRE_VIEW_PUBLIC,
        PermissionName.FIRE_VIEW_FULL,
        PermissionName.SEASONAL_VIEW,
        PermissionName.ANOMALY_VIEW,
        PermissionName.AGRICULTURE_VIEW_CONTEXT,
        PermissionName.LCA_VIEW_ASSESS,
        PermissionName.LCA_CONDUCT_ASSESS,
        PermissionName.REPORT_GENERATE_ENV,
    },
    RoleName.ORGANIZATION_MANAGER: {
        PermissionName.FIRE_VIEW_PUBLIC,
        PermissionName.FIRE_VIEW_FULL,
        PermissionName.SEASONAL_VIEW,
        PermissionName.ANOMALY_VIEW,
        PermissionName.AGRICULTURE_VIEW_CONTEXT,
        PermissionName.AGRICULTURE_VIEW_ANALYTICS,
        PermissionName.ORG_MANAGE_MEMBERS,
        PermissionName.FARM_VIEW_ORG,
        PermissionName.FARM_CREATE_ORG,
        PermissionName.FARM_EDIT_ORG,
        PermissionName.BIOMASS_VIEW_ALL,
        PermissionName.BIOMASS_VIEW_ORG,
        PermissionName.BIOMASS_ALLOCATE_ORG,
        PermissionName.UNIT_MANAGE_ORG,
        PermissionName.DEPLOYMENT_PLAN_ORG,
        PermissionName.FINANCE_VIEW_ORG,
        PermissionName.FINANCE_EVALUATE_ORG,
        PermissionName.LCA_VIEW_ASSESS,
        PermissionName.LCA_CONDUCT_ASSESS,
        PermissionName.REPORT_GENERATE_ALL,
    },
    RoleName.SYSTEM_ADMINISTRATOR: {
        PermissionName.WILDCARD,  # Universal administrative wildcard
        PermissionName.FIRE_VIEW_PUBLIC,
        PermissionName.FIRE_VIEW_FULL,
        PermissionName.SEASONAL_VIEW,
        PermissionName.ANOMALY_VIEW,
        PermissionName.AGRICULTURE_VIEW_PUBLIC,
        PermissionName.AGRICULTURE_VIEW_CONTEXT,
        PermissionName.AGRICULTURE_VIEW_ANALYTICS,
        PermissionName.CROP_VIEW_ANALYTICS,
        PermissionName.FARM_VIEW_OWN,
        PermissionName.FARM_EDIT_OWN,
        PermissionName.FARM_CREATE_OWN,
        PermissionName.FARM_VIEW_ASSIGNED,
        PermissionName.FARM_VIEW_ORG,
        PermissionName.FARM_CREATE_ORG,
        PermissionName.FARM_EDIT_ORG,
        PermissionName.HARVEST_LOG_OWN,
        PermissionName.BIOMASS_VIEW_OWN,
        PermissionName.BIOMASS_VIEW_ASSIGNED,
        PermissionName.BIOMASS_VIEW_ALL,
        PermissionName.BIOMASS_VIEW_ORG,
        PermissionName.BIOMASS_ALLOCATE_ORG,
        PermissionName.UNIT_VIEW_ASSIGNED,
        PermissionName.UNIT_MANAGE_ORG,
        PermissionName.ROUTE_VIEW_ASSIGNED,
        PermissionName.COLLECTION_UPDATE,
        PermissionName.DEPLOYMENT_PLAN_ORG,
        PermissionName.FINANCE_VIEW_ORG,
        PermissionName.FINANCE_EVALUATE_ORG,
        PermissionName.LCA_VIEW_ASSESS,
        PermissionName.LCA_CONDUCT_ASSESS,
        PermissionName.CONSENT_MANAGE_OWN,
        PermissionName.PRIVACY_SUBMIT_REQUEST,
        PermissionName.REPORT_VIEW_PUBLIC,
        PermissionName.REPORT_VIEW_OWN,
        PermissionName.REPORT_VIEW_ASSIGNED,
        PermissionName.REPORT_GENERATE_AGRI,
        PermissionName.REPORT_GENERATE_ENV,
        PermissionName.REPORT_GENERATE_ALL,
        PermissionName.ORG_MANAGE_MEMBERS,
        PermissionName.SYSTEM_ADMIN,
        PermissionName.AUDIT_VIEW,
        PermissionName.CONFIG_MANAGE,
        PermissionName.USER_MANAGE_ALL,
        PermissionName.SECURITY_VIEW_EVENTS,
        PermissionName.RETENTION_EXECUTE,
        PermissionName.BACKUP_EXECUTE,
    },
}

# Bidirectional alias for backwards compatibility
PERMISSIONS_MATRIX: Dict[str, Set[str]] = ROLE_PERMISSIONS


def has_permission(user_role: str, required_permission: str) -> bool:
    """Evaluates whether the given user role possesses the required granular permission."""
    role_key = (user_role or "PUBLIC_VISITOR").upper()
    role_perms = PERMISSIONS_MATRIX.get(role_key, set())

    if "*" in role_perms:
        return True
    return required_permission in role_perms


def get_role_permissions(user_role: str) -> List[str]:
    """Returns the complete list of authorized permissions for a role."""
    role_key = (user_role or "PUBLIC_VISITOR").upper()
    perms = PERMISSIONS_MATRIX.get(role_key, set())
    return sorted(list(perms))


def assert_permission(user_role: str, required_permission: str) -> None:
    """Raises AuthorizationError if the user role lacks the required permission."""
    if not has_permission(user_role, required_permission):
        raise AuthorizationError(
            message=f"Access denied: Role '{user_role}' lacks required permission '{required_permission}'.",
            role=user_role,
            required_permission=required_permission,
        )
