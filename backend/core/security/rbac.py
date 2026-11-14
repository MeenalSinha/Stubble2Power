"""
Authoritative Role-Based Access Control (RBAC) Registry & Permission Matrix.
Enforces granular, server-side permission checks across all multi-user workspaces.
"""

from typing import Dict, List, Set
from backend.core.exceptions.base import AuthorizationError

# Granular Permission Definitions
PERMISSIONS_MATRIX: Dict[str, Set[str]] = {
    "PUBLIC_VISITOR": {
        "fire:view_public",
        "agriculture:view_public",
        "report:view_public"
    },
    "FARMER": {
        "fire:view_public",
        "agriculture:view_public",
        "farm:view_own",
        "farm:edit_own",
        "farm:create_own",
        "harvest:log_own",
        "biomass:view_own",
        "consent:manage_own",
        "privacy:submit_request",
        "report:view_own"
    },
    "FIELD_OPERATOR": {
        "fire:view_public",
        "farm:view_assigned",
        "route:view_assigned",
        "collection:update",
        "biomass:view_assigned",
        "unit:view_assigned",
        "report:view_assigned"
    },
    "AGRICULTURAL_ANALYST": {
        "fire:view_public",
        "fire:view_full",
        "agriculture:view_context",
        "agriculture:view_analytics",
        "crop:view_analytics",
        "biomass:view_all",
        "report:generate_agri"
    },
    "ENVIRONMENTAL_ANALYST": {
        "fire:view_public",
        "fire:view_full",
        "seasonal:view",
        "anomaly:view",
        "agriculture:view_context",
        "lca:view_assess",
        "lca:conduct_assess",
        "report:generate_env"
    },
    "ORGANIZATION_MANAGER": {
        "fire:view_public",
        "fire:view_full",
        "seasonal:view",
        "anomaly:view",
        "agriculture:view_context",
        "agriculture:view_analytics",
        "org:manage_members",
        "farm:view_org",
        "farm:create_org",
        "farm:edit_org",
        "biomass:view_all",
        "biomass:view_org",
        "biomass:allocate_org",
        "unit:manage_org",
        "deployment:plan_org",
        "finance:view_org",
        "finance:evaluate_org",
        "lca:view_assess",
        "lca:conduct_assess",
        "report:generate_all"
    },
    "SYSTEM_ADMINISTRATOR": {
        "*",  # Universal administrative wildcard
        "fire:view_public",
        "fire:view_full",
        "seasonal:view",
        "anomaly:view",
        "agriculture:view_public",
        "agriculture:view_context",
        "agriculture:view_analytics",
        "crop:view_analytics",
        "farm:view_own",
        "farm:edit_own",
        "farm:create_own",
        "farm:view_assigned",
        "farm:view_org",
        "farm:create_org",
        "farm:edit_org",
        "harvest:log_own",
        "biomass:view_own",
        "biomass:view_assigned",
        "biomass:view_all",
        "biomass:view_org",
        "biomass:allocate_org",
        "unit:view_assigned",
        "unit:manage_org",
        "route:view_assigned",
        "collection:update",
        "deployment:plan_org",
        "finance:view_org",
        "finance:evaluate_org",
        "lca:view_assess",
        "lca:conduct_assess",
        "consent:manage_own",
        "privacy:submit_request",
        "report:view_public",
        "report:view_own",
        "report:view_assigned",
        "report:generate_agri",
        "report:generate_env",
        "report:generate_all",
        "org:manage_members",
        "system:admin",
        "audit:view",
        "config:manage",
        "user:manage_all",
        "security:view_events",
        "retention:execute",
        "backup:execute"
    }
}


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
            required_permission=required_permission
        )
