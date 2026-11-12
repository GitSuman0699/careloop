# CareLoop: Build Status & Milestone Audit

**Project:** CareLoop — Closing the Screening-to-Care Loop  
**Challenge:** Future Health Digital Innovation Challenge 2026, Population Health · Challenge 05  
**Audit Date:** 12 November 2026  
**Auditor:** Lead Engineering Agent  

---

## 1. Executive Summary

| Total Milestones | Done | Partial | Missing | Test Suite Status | Simulation Status |
|---|---|---|---|---|---|
| **8 (M0 – M7)** | **8** | **0** | **0** | **118 / 118 Passing** (0 failures) | **30 seeds / N=5,000 per arm verified** |

All components specified in the Agent Build Plan have been built, integrated, tested, and verified against the challenge rubric.

---

## 2. Milestone-by-Milestone Verification

### M0: Foundations (Scaffold, Configuration, Models, State Machine)
- **Status:** **DONE**
- **Evidence:**
  - `careloop/Makefile`, `backend/pyproject.toml`, `frontend/package.json`, `Dockerfile`, `docker-compose.yml`.
  - `config/assumptions.yaml`: 35 parameters categorized, each with `value`, `unit`, `source`, `status: PLACEHOLDER`, and `notes`.
  - 3 Declarative JSON Pathways: `fit_positive_to_colonoscopy.json`, `breast_recall.json`, `cardiometabolic_hba1c.json`.
  - 17 SQLAlchemy Models: `Patient`, `Consent`, `Provider`, `User`, `Case`, `CaseEvent`, `Referral`, `Appointment`, `Message`, `Evidence`, `ClosureProposal`, `SLATimer`, `Escalation`, `AIAction`, `AuditLog`, `SimRun`, `SimResult`.
  - `Clock` service (`SimulatedClock` + `RealClock` + singleton factory) ensuring zero hard-coded `datetime.now()` in domain logic.
  - State Machine engine (`StateMachine.can_transition`, `transition`, `get_allowed_next_states`) with `CLOSED` blocked from direct transition.
  - Tests: `test_clock.py`, `test_config.py`, `test_state_machine.py`, `test_pathway_loader.py`.

### M1: Ledger, SLA Engine, Ownership, API & RBAC
- **Status:** **DONE**
- **Evidence:**
  - Append-only event ledger with SHA-256 canonical JSON hash-chain linking (`prev_hash`, `hash`) and `/api/cases/{id}/verify-chain` endpoint.
  - `SLAEngine` (`backend/app/domain/sla_engine.py`): tracks `warn_at` (75% threshold), `due_at`, automated Tier 1 and Tier 2 escalations.
  - `OwnershipEngine` (`backend/app/domain/ownership.py`): enforces single-owner invariant, hand-off offer (`handoff_offered`) and acceptance (`handoff_accepted`).
  - FastAPI routers: `/api/cases`, `/api/queues`, `/api/clock`, `/api/auth/demo-login`.
  - Role-based Access Control (`backend/app/core/rbac.py`) enforcing matrix permissions with denied-access audit logging.
  - Synthetic Data Generator (`backend/app/seed/generator.py`): loads 4 healthcare providers, 6 role users, 5,000 synthetic patients, and 300 active cases.

### M2: Communications Pipeline & Patient Experience
- **Status:** **DONE**
- **Evidence:**
  - Multilingual template store: English (`messages.en.json`) and Arabic (`messages.ar.json`, marked `NEEDS_NATIVE_REVIEW`).
  - Rule-based `MessageValidator` (`backend/app/ai/guardrails.py`): scans for 10 banned terms, acronyms, raw numeric lab units, and explicit diagnosis disclosures.
  - AI Provider Interface: `MockAIProvider` (deterministic, offline-first) and `AnthropicAIProvider`.
  - Interception & Safe Fallback: adversarial output mentioning cancer/diagnosis is intercepted, logged to `ai_actions` (`validator_passed=False`, `fallback_used=True`), and replaced with the approved deterministic template.
  - Mobile-first Patient View (`frontend/src/pages/PatientView.tsx`): full English and Arabic (RTL) toggle, progress tracker, digital acknowledgement, red-flag symptoms check with clinical alerts, appointment slot chooser, teach-back comprehension check, and "I need help" button.

### M3: Navigator, Clinician & Human-Governed Closure
- **Status:** **DONE**
- **Evidence:**
  - Navigator Work Queue (`frontend/src/pages/NavigatorQueue.tsx`): prioritized by urgency × SLA risk, filters, phone outreach action, manual escalation, and real-time event ledger viewer.
  - Clinician View (`frontend/src/pages/ClinicianView.tsx`): urgent case triage, structured Consult Packet viewer with AI timeline summary and disclaimer badge.
  - Strict Closure Guard (`backend/app/domain/closure_guard.py` & `/api/closure-proposals/{id}/decide`): enforces 4 non-negotiable conditions:
    1. Approved closure proposal exists.
    2. Approver is human with role `clinician` or `supervisor`.
    3. Required procedure/pathology evidence is attached.
    4. Zero open unresolved escalations.

### M4: Operations Command & Discrete-Event Simulation
- **Status:** **DONE**
- **Evidence:**
  - Ops Dashboard (`frontend/src/pages/OpsDashboard.tsx`): full screening funnel progression, SLA compliance stats, exception queues (overdue, unassigned, rejected, unreachable), delay reason taxonomy, and supervisor Advance Time controls.
  - Discrete-Event Simulation Engine (`backend/sim/engine.py`):
    - Cohort: N=5,000 actionable results per arm (Baseline vs CareLoop).
    - Modeled leakage points: notification failure, unacknowledged results, confirmation stall, referral drop-off, appointment no-show, loss to follow-up.
    - Capacity constraints & alert fatigue modeled dynamically.

### M5: Evidence, Fairness, Sensitivity & Governance UI
- **Status:** **DONE**
- **Evidence:**
  - 30 Monte Carlo replicate seeds executed (`backend/sim/run.py`), outputting `simulation_results.json` and `headline_comparison.csv` with 95% Confidence Intervals.
  - Evidence Dashboard (`frontend/src/pages/EvidenceView.tsx`): before/after funnel comparison, 90-day closure gains (+30.6% absolute gain), median time-to-care reduction (73.4d to 34.5d).
  - Demographic Fairness Cuts: analyzed across Language, Age Band, Sex, Nationality Group, and Care Setting with disparity gap ratios and small-cell suppression.
  - Tornado Sensitivity Chart: ±25% parameter swings on headline metrics.
  - Navigator Caseload Capacity Curve: proves system degradation when caseload exceeds 120 cases/navigator.
  - Governance View (`frontend/src/pages/GovernanceView.tsx`): interactive SHA-256 hash-chain verification inspector, AI action audit logs, access audit logs.
  - Zero-code Pathway Viewer (`frontend/src/pages/PathwayViewer.tsx`): displays FIT, Breast Recall, and HbA1c pathways from JSON alone.
  - Read-only FHIR R4 Export endpoints (`/api/fhir/{ServiceRequest|Task|Appointment|Communication|Consent}`).

### M6: Hardening, Packaging & Accessibility
- **Status:** **DONE**
- **Evidence:**
  - Clean build: Frontend built via Vite (`dist/` copied to `backend/static/`).
  - Single Dockerfile (multi-stage Node + Python) and `docker-compose.yml`.
  - Third-Party License Audit: All dependencies verified MIT, Apache-2.0, or BSD-3. Zero GPL/AGPL dependencies.
  - `AI_USE_DISCLOSURE.md` published.
  - CORS, input sanitization, and Pydantic v2 schemas across all API endpoints.

### M7: Demo Readiness
- **Status:** **DONE**
- **Evidence:**
  - Quick Tour Page (`frontend/src/pages/QuickTour.tsx`): one-click switcher for all 6 demo cases (A to F), role switchers, and mandatory disclaimer banners.
  - Seeded Demo Scenarios (`backend/app/seed/scenarios.py`):
    - Case A ("Amira"): The Happy Path — positive result, Arabic notification, acknowledgement, colonoscopy, evidence, human sign-off.
    - Case B ("Rahul"): Unresponsive patient, channel retries, SLA breach, outreach call task.
    - Case C ("Maria"): Rejected referral, auto-returned ownership, exception queue.
    - Case D ("Omar"): Red-flag symptoms reported, urgent upgrade, clinical lead alert.
    - Case E ("Chen"): Provider transfer, hand-off offer/accept, unbroken hash chain.
    - Case F ("AI Blocked"): Banned term / diagnosis disclosure intercepted, fallback used, logged in AI actions.

---

## 3. Core Safety Properties Verification Matrix

| Property | Requirement | Implementation | Test Status |
|---|---|---|---|
| **(a) Closure Guard** | Case cannot close without human approval, evidence, clinician role, and no open escalations | `backend/app/domain/closure_guard.py` & `/api/closure-proposals/{id}/decide` | **PASS** (`test_closure_fails_without_evidence`, `test_closure_fails_with_open_escalation`, `test_closure_fails_with_non_human_or_unauthorized_role`, `test_api_closure_endpoint_enforces_guard`) |
| **(b) AI Guardrail** | AI disclosure of diagnosis or numeric result is blocked; deterministic fallback used and logged | `backend/app/ai/guardrails.py` & `backend/app/services/comms_pipeline.py` | **PASS** (`test_ai_diagnosis_disclosure_blocked_and_fallback_used`, `test_banned_numeric_lab_result_in_patient_message_blocked`) |
| **(c) RBAC Matrix** | Strict enforcement across Patient, Navigator, Clinician, Supervisor, Auditor | `backend/app/core/rbac.py` & `backend/app/api/auth.py` | **PASS** (`test_patient_cannot_advance_clock`, `test_navigator_cannot_approve_closure`, `test_auditor_cannot_change_case_state`, `test_clinician_can_approve_closure`, `test_supervisor_can_advance_clock`) |
| **(d) Hash Chain** | SHA-256 event chain detects any tampering | `backend/app/core/hashing.py` | **PASS** (`test_tamper_detection`, `test_verify_chain_valid`, `test_chain_built_by_transitions`) |
| **(e) Simulation Reproducibility** | Same random seed produces identical bit-for-bit results | `backend/sim/engine.py` | **PASS** (`test_identical_seed_produces_identical_results`) |

---

## 4. Known Gaps & Transparent Limitations

1. **Synthetic Data Only:** No real patient records or clinical databases were accessed. All patient demographics, phone numbers, and findings are synthetically generated.
2. **Modelled Rather than Empirical Clinical Outcomes:** Reported gains in 90-day closure (+30.6%) and days saved (38.9d) are derived from Monte Carlo discrete-event simulations based on parameterized assumptions.
3. **Simulated External Adapters:** LIS, hospital scheduling, and SMS gateways are mocked using high-fidelity interface adapters. Production integration requires HL7 v2 / FHIR endpoints.
4. **Language Translations:** Arabic templates are synthetically generated and marked `NEEDS_NATIVE_REVIEW` pending review by native Arabic clinical linguists.

