"""Tests for RBAC permission matrix."""

from __future__ import annotations

import pytest

from app.core.rbac import PERMISSIONS, Role, check_permission


class TestCheckPermission:
    # --- patient ---
    def test_patient_can_view_own_case(self):
        """Patient role can view_own_case."""
        assert check_permission("patient", "view_own_case") is True

    def test_patient_cannot_approve_closure(self):
        """Patient role cannot approve_closure."""
        assert check_permission("patient", "approve_closure") is False

    def test_patient_cannot_change_case_state(self):
        """Patient role cannot change_case_state."""
        assert check_permission("patient", "change_case_state") is False

    def test_patient_cannot_advance_clock(self):
        """Patient role cannot advance_clock."""
        assert check_permission("patient", "advance_clock") is False

    # --- navigator ---
    def test_navigator_can_change_case_state(self):
        """Navigator role can change_case_state."""
        assert check_permission("navigator", "change_case_state") is True

    def test_navigator_cannot_approve_closure(self):
        """Navigator role cannot approve_closure."""
        assert check_permission("navigator", "approve_closure") is False

    def test_navigator_cannot_advance_clock(self):
        """Navigator role cannot advance_clock (only admin can)."""
        assert check_permission("navigator", "advance_clock") is False

    # --- clinician ---
    def test_clinician_can_approve_closure(self):
        """Clinician role can approve_closure."""
        assert check_permission("clinician", "approve_closure") is True

    def test_clinician_can_change_case_state(self):
        """Clinician role can change_case_state."""
        assert check_permission("clinician", "change_case_state") is True

    def test_clinician_can_view_clinical_detail(self):
        """Clinician role can view_clinical_detail."""
        assert check_permission("clinician", "view_clinical_detail") is True

    def test_clinician_cannot_advance_clock(self):
        """Clinician role cannot advance_clock."""
        assert check_permission("clinician", "advance_clock") is False

    # --- supervisor ---
    def test_supervisor_can_approve_closure(self):
        """Supervisor role can approve_closure."""
        assert check_permission("supervisor", "approve_closure") is True

    def test_supervisor_can_run_simulation(self):
        """Supervisor role can run_simulation."""
        assert check_permission("supervisor", "run_simulation") is True

    def test_supervisor_can_advance_clock(self):
        """Supervisor role CAN advance clock per Plan Section 10.2."""
        actual = check_permission("supervisor", "advance_clock")
        assert actual is True, "supervisor.advance_clock must be True per plan Table 10.2"

    # --- auditor ---
    def test_auditor_cannot_change_case_state(self):
        """Auditor role cannot change_case_state."""
        assert check_permission("auditor", "change_case_state") is False

    def test_auditor_can_read_audit_log(self):
        """Auditor role can read_audit_log."""
        assert check_permission("auditor", "read_audit_log") is True

    def test_auditor_cannot_approve_closure(self):
        """Auditor role cannot approve_closure."""
        assert check_permission("auditor", "approve_closure") is False

    # --- admin ---
    def test_admin_can_advance_clock(self):
        """Admin role can advance_clock."""
        assert check_permission("admin", "advance_clock") is True

    def test_admin_can_approve_closure(self):
        """Admin role can approve_closure."""
        assert check_permission("admin", "approve_closure") is True

    # --- unknown ---
    def test_unknown_role_returns_false(self):
        """Unknown role with any capability returns False."""
        assert check_permission("ghost", "view_own_case") is False

    def test_unknown_capability_returns_false(self):
        """Known role with unknown capability returns False."""
        assert check_permission("admin", "teleport") is False


class TestPermissionsMatrix:
    def test_permissions_covers_all_roles(self):
        """PERMISSIONS matrix has entries for all defined roles."""
        roles = {r.value for r in Role}
        matrix_roles = {key[0] for key in PERMISSIONS}
        for role in roles:
            assert role in matrix_roles, f"Role '{role}' missing from PERMISSIONS matrix"

    def test_permissions_matrix_is_complete(self):
        """Every (role, capability) pair has an entry in the matrix."""
        from app.core.rbac import CAPABILITIES
        for role in Role:
            for cap in CAPABILITIES:
                key = (role.value, cap)
                assert key in PERMISSIONS, f"Missing PERMISSIONS entry: {key}"
