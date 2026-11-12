"""Role-based access control (RBAC) utilities for CareLoop."""

from __future__ import annotations

import enum
from typing import Callable, Sequence

from fastapi import Depends, HTTPException, Request, status


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------
class Role(str, enum.Enum):
    patient = "patient"
    navigator = "navigator"
    clinician = "clinician"
    supervisor = "supervisor"
    auditor = "auditor"
    admin = "admin"


# ---------------------------------------------------------------------------
# Capabilities
# ---------------------------------------------------------------------------
CAPABILITIES = (
    "view_own_case",
    "view_assigned_cases",
    "change_case_state",
    "approve_closure",
    "view_clinical_detail",
    "advance_clock",
    "run_simulation",
    "read_audit_log",
)

# ---------------------------------------------------------------------------
# RBAC matrix — (role, capability) → bool
# ---------------------------------------------------------------------------
PERMISSIONS: dict[tuple[str, str], bool] = {
    # patient
    ("patient", "view_own_case"): True,
    ("patient", "view_assigned_cases"): False,
    ("patient", "change_case_state"): False,
    ("patient", "approve_closure"): False,
    ("patient", "view_clinical_detail"): False,
    ("patient", "advance_clock"): False,
    ("patient", "run_simulation"): False,
    ("patient", "read_audit_log"): False,
    # navigator
    ("navigator", "view_own_case"): False,
    ("navigator", "view_assigned_cases"): True,
    ("navigator", "change_case_state"): True,
    ("navigator", "approve_closure"): False,
    ("navigator", "view_clinical_detail"): False,
    ("navigator", "advance_clock"): False,
    ("navigator", "run_simulation"): False,
    ("navigator", "read_audit_log"): False,
    # clinician
    ("clinician", "view_own_case"): False,
    ("clinician", "view_assigned_cases"): True,
    ("clinician", "change_case_state"): True,
    ("clinician", "approve_closure"): True,
    ("clinician", "view_clinical_detail"): True,
    ("clinician", "advance_clock"): False,
    ("clinician", "run_simulation"): False,
    ("clinician", "read_audit_log"): False,
    # supervisor
    ("supervisor", "view_own_case"): False,
    ("supervisor", "view_assigned_cases"): True,
    ("supervisor", "change_case_state"): True,
    ("supervisor", "approve_closure"): True,
    ("supervisor", "view_clinical_detail"): True,
    ("supervisor", "advance_clock"): True,
    ("supervisor", "run_simulation"): True,
    ("supervisor", "read_audit_log"): True,
    # auditor
    ("auditor", "view_own_case"): False,
    ("auditor", "view_assigned_cases"): True,
    ("auditor", "change_case_state"): False,
    ("auditor", "approve_closure"): False,
    ("auditor", "view_clinical_detail"): True,
    ("auditor", "advance_clock"): False,
    ("auditor", "run_simulation"): False,
    ("auditor", "read_audit_log"): True,
    # admin
    ("admin", "view_own_case"): False,
    ("admin", "view_assigned_cases"): True,
    ("admin", "change_case_state"): True,
    ("admin", "approve_closure"): True,
    ("admin", "view_clinical_detail"): True,
    ("admin", "advance_clock"): True,
    ("admin", "run_simulation"): True,
    ("admin", "read_audit_log"): True,
}


def check_permission(role: str, capability: str) -> bool:
    """Return ``True`` if *role* is granted *capability*."""
    return PERMISSIONS.get((role, capability), False)


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

def _get_current_user_role(request: Request) -> str:
    """Extract the current user's role from the request state.

    The auth middleware or a test fixture must set ``request.state.user_role``.
    """
    role: str | None = getattr(request.state, "user_role", None)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return role


def require_role(*roles: str) -> Callable:
    """FastAPI dependency factory that ensures the caller has one of *roles*.

    Usage::

        @router.get("/admin/audit")
        async def audit_log(
            _: str = Depends(require_role("supervisor", "auditor", "admin")),
        ):
            ...
    """
    allowed = {r.value if isinstance(r, Role) else r for r in roles}

    def _checker(role: str = Depends(_get_current_user_role)) -> str:
        if role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' is not authorized. Required: {sorted(allowed)}",
            )
        return role

    return _checker
