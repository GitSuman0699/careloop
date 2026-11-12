# CareLoop: Judging Rubric Alignment Matrix

**Challenge:** Future Health Digital Innovation Challenge 2026 (Hack2skill)  
**Track:** Population Health · Challenge 05: Closing the Screening-to-Care Loop  
**Purpose:** Direct mapping between the hackathon judging criteria (01 to 06) and the CareLoop codebase, automated tests, UI screens, and documentation.

---

```
+----------------------------------------------------------------------------------------------------------------------------------+
|                                              JUDGING CRITERIA TO CODEBASE MAPPING MATRIX                                         |
+------------------------------+---------------------------------------+----------------------------------+------------------------+
| Judging Criterion            | Primary Architectural Artifacts       | Verified Code & File Locations   | Proof & Test Cases     |
+------------------------------+---------------------------------------+----------------------------------+------------------------+
| 01. Challenge Alignment      | • Declarative screening pathways      | `config/pathways/*.json`         | `test_state_machine.py`|
| (Closing the Loop)           | • Strict 7-stage state machine        | `app/domain/state_machine.py`    | `test_handoff.py`      |
|                              | • Explicit cross-provider handoffs    | `app/domain/ownership.py`        | `test_urgency.py`      |
+------------------------------+---------------------------------------+----------------------------------+------------------------+
| 02. Impact & Population      | • Discrete-event Monte Carlo engine   | `backend/sim/engine.py`          | `test_safety_propert-  |
| Health Evidence              | • 300,000 simulated patient pathways  | `backend/sim/results/`           |  ies.py::TestE`        |
|                              | • 54.8% -> 85.4% closure (+30.6 pp)   | `docs/EVALUATION.md`             | `headline_comparison.  |
|                              | • Median time: 73.4d -> 34.5d (-53%)  | `src/pages/EvidenceView.tsx`     |  csv`                  |
+------------------------------+---------------------------------------+----------------------------------+------------------------+
| 03. Technical Excellence &   | • Immutable event ledger              | `app/core/hashing.py`            | `test_safety_propert-  |
| System Architecture          | • SHA-256 canonical JSON hash chains  | `app/core/clock.py`              |  ies.py::TestD`        |
|                              | • Injectable simulated clock engine   | `app/api/routes/*.py`            | `test_clock.py`        |
|                              | • Clean REST API + React 18 frontend  | `frontend/src/`                  | `test_hashing.py`      |
+------------------------------+---------------------------------------+----------------------------------+------------------------+
| 04. Responsible AI &         | • Multi-gate human closure guard      | `app/domain/closure_guard.py`    | `test_safety_propert-  |
| Clinical Safety              | • Zero-bypass regex banned scanner    | `app/ai/guardrails.py`           |  ies.py::TestA, B, C`  |
|                              | • Deterministic safe fallback pipeline| `app/core/rbac.py`               | `test_closure_guard.py`|
|                              | • All parameters flagged PLACEHOLDER  | `config/assumptions.yaml`        | `test_config.py`       |
+------------------------------+---------------------------------------+----------------------------------+------------------------+
| 05. Usability & Human-       | • Mobile-first Patient View (EN / AR) | `src/pages/PatientView.tsx`      | Frontend Build (Vite)  |
| Centered Design              | • Worklist-driven Navigator Queue     | `src/pages/NavigatorQueue.tsx`   | Quick Tour Switcher    |
|                              | • Structured Clinician Consult Triage | `src/pages/ClinicianView.tsx`    | (Cases A through F)    |
|                              | • Executive Ops & Funnel Dashboard   | `src/pages/OpsDashboard.tsx`     |                        |
+------------------------------+---------------------------------------+----------------------------------+------------------------+
| 06. Feasibility & Commercial | • 90-day multi-facility pilot plan    | `docs/PILOT_PLAN.md`             | Docker Compose build   |
| Viability                    | • HL7 v2 and FHIR R4 interoperability | `app/adapters/lis.py`            | `docs/INTEGRATION.md`  |
|                              | • Permissive licensing (MIT / Apache) | `app/fhir/mapping.py`            | `THIRD_PARTY_LICENSES` |
|                              | • 6-month ROFR terms disclosure       | `THIRD_PARTY_LICENSES.md`        |                        |
+------------------------------+---------------------------------------+----------------------------------+------------------------+
```

---

## Detailed Evaluation Checklist

### Criterion 01: Problem Understanding & Domain Depth
- [x] Clear articulation of the screening leakage problem across asymptomatic screening.
- [x] Three pre-configured clinical pathways: FIT Colorectal Cancer, Mammography Breast Recall, and Cardiometabolic Risk.
- [x] Red-flag symptom detection integrated into digital and phone intake.

### Criterion 02: Quantitative Evaluation & Simulation Rigor
- [x] 30-seed Monte Carlo simulation ($N=5,000$ per arm) generating reproducible 95% confidence intervals.
- [x] Health equity analysis demonstrating elimination of the Arabic language disparity gap (0.896 to 0.998).
- [x] Tornado sensitivity analysis identifying high-leverage intervention levers.
- [x] Navigator caseload capacity curves defining safe operating thresholds.

### Criterion 03: Engineering Quality & Architecture
- [x] Monotonic finite state machine prohibiting step-skipping or direct unverified closure.
- [x] Append-only audit ledger with SHA-256 canonical JSON hash chains and automated tamper detection.
- [x] Temporal decoupling with simulated clock engine enabling rapid testing of SLA breaches.
- [x] 118 automated tests passing across 13 test modules with zero failures.

### Criterion 04: Responsible AI & Patient Safety
- [x] Architectural prohibition on autonomous AI case closure.
- [x] Regex banned-term scanner blocking diagnostic assertions and raw lab units.
- [x] Deterministic fallback pipeline serving pre-approved static clinical templates.
- [x] Strict Role-Based Access Control matrix.
- [x] Every clinical and operational assumption flagged as `PLACEHOLDER` in `config/assumptions.yaml`.

### Criterion 05: User Experience & Multilingual Accessibility
- [x] Native English and Modern Standard Arabic (RTL) patient portal.
- [x] Interactive teach-back comprehension question and direct slot self-scheduling.
- [x] Priority worklist queue for care navigators with one-click call logging.
- [x] Structured consult preparation packet for clinicians.
- [x] Ops dashboard tracking population funnel, SLA breaches, and delay taxonomy.

### Criterion 06: Scalability & Commercial Viability
- [x] Containerized Docker Compose deployment (~180MB footprint).
- [x] Inbound HL7 v2 ORU^R01 parser and bidirectional FHIR R4 mappings.
- [x] Detailed 90-day clinical pilot plan with phased milestones.
- [x] Clean licensing and transparent disclosure of competition terms (6-month ROFR).
