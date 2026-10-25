"""
Centralized Role-Based Access Control (RBAC) Architecture for SOVA.
Defines system roles, persona metadata, permission catalog, and authorization checks.
"""

from typing import Dict, List, Any, Optional

# Master permission definitions
PERMISSIONS = {
    # Engineering Permissions
    "documents:engineering": "Access engineering documents",
    "documents:pid_technical": "Analyze P&ID and technical files",
    "plant:query_data": "Query plant/engineering data",
    "reports:engineering": "Generate engineering reports",
    "rag:document_analysis": "Use SOVA document analysis and RAG",
    "chat:engineering": "Engineering conversational inference",

    # Manager Permissions
    "ops:view_info": "View operational information",
    "reports:management": "Access management reports",
    "analytics:plant_performance": "Analyze plant performance",
    "ops:generate_summaries": "Generate operational summaries",
    "documents:approved_org": "View approved organizational documents",
    "chat:operational": "Operational conversational inference",

    # Admin Permissions
    "admin:manage_users": "Manage users and roles",
    "admin:system_config": "Manage system configuration",
    "admin:model_management": "Manage models",
    "admin:security_policies": "Manage security policies",
    "admin:audit_logs": "View system/audit logs",
    "admin:manage_infrastructure": "Manage SOVA infrastructure",
    "chat:admin": "Admin conversational inference",

    # Analyst Permissions
    "data:telemetry_csv": "Analyze CSV/telemetry data",
    "analytics:process_analysis": "Perform process analysis",
    "reports:analytical": "Generate analytical reports",
    "data:query_operational": "Query operational datasets",
    "analytics:visualization": "Use data visualization/analytics features",
    "chat:analytics": "Process analytics conversational inference",

    # Developer Permissions
    "dev:access_tools": "Access development tools",
    "dev:test_models": "Test SOVA models",
    "dev:view_technical_info": "View technical system information",
    "dev:api_functionality": "Access API/development functionality",
    "dev:test_pipelines": "Test document/model pipelines",
    "chat:dev_sandbox": "Developer sandbox conversational inference",
}

# Master Role Personas
ROLE_PERSONAS: Dict[str, Dict[str, Any]] = {
    "engineer": {
        "role": "engineer",
        "role_title": "ENGINEER",
        "display_name": "Er. Rajesh K. Nayak",
        "name": "Er. Rajesh K. Nayak",
        "department": "Mechanical & Plant Integrity",
        "email": "engineer@mrpl.co.in",
        "username": "engineer",
        "clearance": "Level 2 (Engineering Integrity)",
        "clearance_code": "L2",
        "badge_color": "linear-gradient(135deg, #0284C7, #0EA5E9)",
        "accent_color": "#0EA5E9",
        "description": "Mechanical & plant integrity engineering, technical analysis, P&ID and RAG document intelligence.",
        "permissions": [
            "documents:engineering",
            "documents:pid_technical",
            "plant:query_data",
            "reports:engineering",
            "rag:document_analysis",
            "chat:engineering",
        ],
    },
    "manager": {
        "role": "manager",
        "role_title": "MANAGER",
        "display_name": "V. Shenoy",
        "name": "V. Shenoy",
        "department": "Refinery Operations",
        "email": "manager@mrpl.co.in",
        "username": "manager",
        "clearance": "Level 2 (Operations Management)",
        "clearance_code": "L2",
        "badge_color": "linear-gradient(135deg, #2563EB, #1D4ED8)",
        "accent_color": "#3B82F6",
        "description": "Refinery operations oversight, operational reporting, performance analytics, and executive compliance.",
        "permissions": [
            "ops:view_info",
            "reports:management",
            "analytics:plant_performance",
            "ops:generate_summaries",
            "documents:approved_org",
            "chat:operational",
        ],
    },
    "admin": {
        "role": "admin",
        "role_title": "ADMIN",
        "display_name": "SOVA Admin",
        "name": "SOVA Admin",
        "department": "Enterprise IT & Cyber Security",
        "email": "admin@mrpl.co.in",
        "username": "admin",
        "clearance": "Level 3 (Root Sovereign Admin)",
        "clearance_code": "L3",
        "badge_color": "linear-gradient(135deg, #DC2626, #B91C1C)",
        "accent_color": "#EF4444",
        "description": "Enterprise IT security, sovereign infrastructure, role provisioning, model registries, and audit telemetry.",
        "permissions": [
            "admin:manage_users",
            "admin:system_config",
            "admin:model_management",
            "admin:security_policies",
            "admin:audit_logs",
            "admin:manage_infrastructure",
            "documents:engineering",
            "documents:approved_org",
            "reports:engineering",
            "reports:management",
            "reports:analytical",
            "chat:admin",
        ],
    },
    "analyst": {
        "role": "analyst",
        "role_title": "ANALYST",
        "display_name": "R. Mehta",
        "name": "R. Mehta",
        "department": "Process Analytics & Optimization",
        "email": "analyst@mrpl.co.in",
        "username": "analyst",
        "clearance": "Level 2 (Process Analytics)",
        "clearance_code": "L2",
        "badge_color": "linear-gradient(135deg, #059669, #10B981)",
        "accent_color": "#10B981",
        "description": "Process telemetry analytics, CSV dataset processing, ultrasonic trend analysis, and process optimization.",
        "permissions": [
            "data:telemetry_csv",
            "analytics:process_analysis",
            "reports:analytical",
            "data:query_operational",
            "analytics:visualization",
            "chat:analytics",
        ],
    },
    "developer": {
        "role": "developer",
        "role_title": "DEVELOPER",
        "display_name": "A. Krishnan",
        "name": "A. Krishnan",
        "department": "Digital & IT Systems",
        "email": "developer@mrpl.co.in",
        "username": "developer",
        "clearance": "Level 2 (Systems & Dev Engineering)",
        "clearance_code": "L2",
        "badge_color": "linear-gradient(135deg, #7C3AED, #9333EA)",
        "accent_color": "#8B5CF6",
        "description": "Digital IT systems, model testing, sandbox runtime, API development tools, and pipeline diagnostics.",
        "permissions": [
            "dev:access_tools",
            "dev:test_models",
            "dev:view_technical_info",
            "dev:api_functionality",
            "dev:test_pipelines",
            "chat:dev_sandbox",
        ],
    },
}

DEMO_DEFAULT_PASSWORD = "sova123"


def get_role_persona(role: str) -> Optional[Dict[str, Any]]:
    """Returns the persona dict for a given role key."""
    return ROLE_PERSONAS.get(role.lower().strip())


def get_role_permissions(role: str) -> List[str]:
    """Returns list of permission strings granted to a role."""
    persona = get_role_persona(role)
    if not persona:
        return []
    # Admin has all permissions implicitly or through its catalog
    return list(persona.get("permissions", []))


def has_permission(user_role: str, required_permission: str) -> bool:
    """
    Checks if a role has the required permission.
    Admin role grants all administrative and global permissions.
    """
    clean_role = user_role.lower().strip()
    if clean_role == "admin":
        return True
    perms = get_role_permissions(clean_role)
    return required_permission in perms


def get_public_roles_catalog() -> List[Dict[str, Any]]:
    """Returns sanitized role personas for the public authentication screen."""
    catalog = []
    for key, persona in ROLE_PERSONAS.items():
        catalog.append({
            "role": persona["role"],
            "role_title": persona["role_title"],
            "display_name": persona["display_name"],
            "name": persona["name"],
            "department": persona["department"],
            "email": persona["email"],
            "username": persona["username"],
            "description": persona["description"],
            "clearance": persona["clearance"],
            "clearance_code": persona["clearance_code"],
            "badge_color": persona["badge_color"],
            "accent_color": persona["accent_color"],
            "permissions": persona["permissions"],
            "permission_details": [
                {"id": p, "label": PERMISSIONS.get(p, p)} for p in persona["permissions"]
            ],
        })
    return catalog
