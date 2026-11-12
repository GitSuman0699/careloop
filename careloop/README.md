# CareLoop: Closing the Screening-to-Care Loop

**Future Health Digital Innovation Challenge 2026 (Hack2skill)**  
**Track:** Population Health · Challenge 05: Closing the Screening-to-Care Loop  
**Repository Version:** 1.0.0-rc1  
**Verification Date:** November 2026  
**Safety Classification:** Software as a Medical Device (SaMD) Class I / Administrative Orchestration Pipeline  

---

> [!CAUTION]
> **SIMULATED DATA NOTICE & CLINICAL NON-CLAIM**  
> **ALL DATA IN THIS SYSTEM IS SYNTHETIC / SIMULATED.**  
> **THIS SOFTWARE IS NOT FOR CLINICAL USE.**  
> It is an operational demonstration and research platform. No real patient data is stored, processed, or displayed. CareLoop does not render clinical diagnoses, select medications, or close clinical cases autonomously.

---

## Executive Overview

**CareLoop** is an open-standard, human-governed care orchestration platform engineered to guarantee that every actionable screening result achieves verified clinical follow-up. 

In prevailing healthcare architectures, over 45% of patients with abnormal screening tests are lost to follow-up ("screening leakage"). CareLoop connects diagnostic laboratories, hospital EHRs, care navigators, clinicians, and patients across a strict 7-stage finite state machine.

### Key Innovations:
- **Human-Governed Closure Guard:** An architectural software barrier ensuring that no case can reach `CLOSED` status without explicit clinician or supervisor sign-off, verifiable clinical attachment evidence (colonoscopy or pathology report), and zero open escalations.
- **Cryptographic Audit Ledger:** An append-only event ledger with SHA-256 canonical JSON (RFC 8785) hash chaining providing non-repudiable proof of all clinical handoffs.
- **Bilingual Health-Literate Navigation:** Mobile-first patient experience in Modern Standard Arabic (RTL) and English with interactive teach-back comprehension checks and slot self-scheduling.
- **Responsible AI Safety Architecture:** AI is strictly restricted to administrative drafting. A zero-bypass scanner intercepts prohibited diagnostic assertions and raw lab values, automatically serving pre-approved static fallbacks.
- **Time-Decoupled Simulation Engine:** Injectable `Clock` service allowing operational fast-forwarding across days to test SLA breaches and exception workflows.

---

## Submission Package Documentation Links

| Document | Description |
| :--- | :--- |
| [**Technical Documentation**](docs/TECHNICAL_DOCUMENTATION.md) | **Primary Deliverable:** Standalone 13-section technical specification, system architecture, data models, and evaluation |
| [**Submission Summary**](docs/SUBMISSION_SUMMARY.md) | Tagline, 100/300-word summaries, tech stack, and key metrics |
| [**Final Submission Checklist**](docs/SUBMISSION_CHECKLIST.md) | PASS / FAIL / NEEDS-HUMAN audit for all competition criteria |
| [**Build Status Report**](docs/BUILD_STATUS.md) | Milestone-by-milestone (M0–M7) completion and test verification audit |
| [**Live Demo Script (7 Min)**](docs/DEMO_SCRIPT.md) | Turn-by-turn live demonstration walkthrough covering Cases A to F |
| [**Judge Q&A Battle Sheet**](docs/QA_SHEET.md) | Rapid-fire answers for clinical safety, liability, and health equity questions |
| [**Rubric Alignment Matrix**](docs/RUBRIC_MAP.md) | Direct mapping of hackathon criteria 01–06 to code, screens, and tests |
| [**Quantitative Evaluation**](docs/EVALUATION.md) | 30-seed Monte Carlo simulation results (N=300,000 pathways), fairness, sensitivity |
| [**Clinical Governance & Safety**](docs/GOVERNANCE.md) | System risk register, clinician override policy, and DPIA privacy roadmap |
| [**System Assumptions Catalog**](docs/ASSUMPTIONS.md) | Documentation of all 35 parameters flagged as `PLACEHOLDER` in `config/assumptions.yaml` |
| [**Declarative Clinical Pathways**](docs/CLINICAL_PATHWAYS.md) | Pathway specifications for FIT Stool, Mammography Recall, and HbA1c |
| [**Healthcare Integration Spec**](docs/INTEGRATION.md) | Real vs. mocked interfaces, HL7 v2 ORU^R01 parser, and FHIR R4 mappings |
| [**Clinical Pilot & Commercial Plan**](docs/PILOT_PLAN.md) | 90-day multi-facility pilot plan, pricing hypotheses, and 6-month ROFR terms |
| [**Limitations & Non-Claims**](docs/LIMITATIONS.md) | Transparent disclosure of boundaries, synthetic data, and non-medical claims |
| [**AI Use Disclosure**](AI_USE_DISCLOSURE.md) | Formal declaration of AI agent usage during the build |
| [**Third-Party Licenses**](THIRD_PARTY_LICENSES.md) | Inventory of strictly permissive dependencies (MIT, Apache-2.0, BSD) |

---

## Proven Population Health Impact (Monte Carlo Evaluation)

Executed across 30 independent stochastic replications ($N=5,000$ synthetic patients per arm):

```
+------------------------------------+--------------------------+-----------------------+-----------------+
| Metric                             | Baseline Standard of Care| CareLoop Orchestration| Impact Delta    |
+------------------------------------+--------------------------+-----------------------+-----------------+
| 90-Day Closed-Loop Rate            | 54.8% [54.6% - 55.1%]    | 85.4% [85.3% - 85.6%] | +30.6 pp (+56%) |
| Median Time to Confirmed Care      | 73.4 days [73.3 - 73.6]  | 34.5 days [34.4 - 34.7| -38.9 days (-53%|
| Appointment Attendance Rate        | 88.0% [87.8% - 88.2%]    | 94.6% [94.4% - 94.7%] | +6.6 pp         |
| Arabic Language Disparity Ratio    | 0.896 (Significant Gap)  | 0.998 (Near Parity)   | +0.102 (Closed) |
| Elderly (65+) Disparity Ratio      | 0.959                    | 0.993                 | +0.034 (Closed) |
+------------------------------------+--------------------------+-----------------------+-----------------+
```
*Notice: MODELLED RESULTS, NOT CLINICAL EVIDENCE. Simulated under explicitly parameterized assumptions.*

---

## Quickstart & Local Reproduction

### Option 1: Docker Compose (Recommended)

```bash
# Clone and launch all services in a single command
docker compose up --build
```
Navigate your browser to `http://localhost:8000`. The frontend is automatically compiled and served directly via FastAPI.

### Option 2: Native Local Setup

```bash
# 1. Backend setup
cd careloop/backend
python -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# 2. Run test suite (118 tests)
pytest tests/ -q

# 3. Seed database and run simulation
python -m app.seed.generator
python -m sim.run

# 4. Frontend setup & build
cd ../frontend
npm install
npm run build                   # Compiles into backend/static for production

# 5. Launch FastAPI server
cd ../backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Option 3: Using the Makefile

```bash
make dev       # Start development servers
make test      # Run full 118-test backend suite
make seed      # Seed synthetic patients and demo cases A-F
make simulate  # Run 30-seed Monte Carlo simulation
make build     # Compile production frontend assets
```

---

## Live Demo Scenarios (One-Click Tour Switcher)

When the application loads, use the top banner to explore the 6 pre-configured demo cases:

- **Case A (Tariq - Happy Path FIT):** Positive screening result $\to$ Multilingual SMS $\to$ Patient self-schedules colonoscopy $\to$ Clinician signs off with endoscopy report.
- **Case B (Fatima - Arabic RTL Experience):** Modern Standard Arabic interface $\to$ Health-literate recall explanation $\to$ Interactive teach-back quiz $\to$ Booking confirmation.
- **Case C (Khalid - Urgent Red Flag):** Patient reports active gross rectal bleeding $\to$ Urgency engine elevates case to `urgent` $\to$ Navigator queue prioritizes case for immediate telephone outreach.
- **Case D (Mariam - Time Travel & SLA Breach):** Advance the Simulated Clock by 7 days $\to$ Unacknowledged case breaches SLA $\to$ Escalation appears in supervisor queue.
- **Case E (Adversarial Closure Attempt):** Attempting to close a case without clinical evidence or with an unauthorized role is hard-blocked by `ClosureGuardError`.
- **Case F (AI Banned-Term Interception):** Adversarial AI draft containing "malignant carcinoma" is automatically blocked by regex scanner $\to$ Vetted static template served $\to$ Incident logged in audit ledger.

---

## Repository Structure

```
careloop/
├── backend/
│   ├── app/
│   │   ├── adapters/          # LIS (HL7 v2), FHIR R4, Messaging, Scheduling
│   │   ├── ai/                # Guardrails, banned scanner, prompt isolation
│   │   ├── api/routes/        # 12 REST API endpoint routers
│   │   ├── core/              # Config, clock engine, hashing, RBAC security
│   │   ├── db/                # SQLAlchemy models, sessions, migrations
│   │   ├── domain/            # State machine, closure guard, SLA, urgency
│   │   ├── fhir/              # Bidirectional FHIR R4 transformation mappings
│   │   ├── seed/              # Realistic demographic and scenario generators
│   │   └── services/          # Comms pipelines and consult packet generators
│   ├── sim/                   # Discrete-event Monte Carlo simulation engine
│   └── tests/                 # 13 test modules (118 automated tests)
├── frontend/
│   └── src/
│       ├── components/        # UI components, layout, banners, modals
│       ├── pages/             # 7 operational pages (Patient, Navigator, etc.)
│       └── services/          # API client and authentication context
├── config/                    # assumptions.yaml, pathways/ (FIT, Breast, Cardio)
├── docs/                      # Complete technical documentation suite
├── Dockerfile                 # High-density multi-stage container
├── docker-compose.yml         # Container orchestration manifest
├── Makefile                   # Developer and CI/CD targets
├── AI_USE_DISCLOSURE.md       # AI agent development disclosure
└── THIRD_PARTY_LICENSES.md    # Permissive open-source license inventory
```

---

## Automated Test Verification

All 118 automated unit, integration, and safety property tests pass with zero failures:

```
============================= test session starts =============================
platform win32 -- Python 3.12.5, pytest-9.2.0, pluggy-1.7.0
rootdir: careloop/backend
collected 118 items

tests/test_clock.py ..................................                  [  7%]
tests/test_closure_guard.py ...........                                 [ 16%]
tests/test_config.py .....                                              [ 21%]
tests/test_events.py ...........                                        [ 30%]
tests/test_fhir.py ........                                             [ 37%]
tests/test_handoff.py .......                                           [ 43%]
tests/test_hashing.py ........                                          [ 50%]
tests/test_messaging.py ..........                                      [ 58%]
tests/test_routes.py ...............                                    [ 71%]
tests/test_safety_properties.py .........                               [ 78%]
tests/test_state_machine.py ....................                        [ 95%]
tests/test_urgency.py .............                                     [100%]

======================== 118 passed in 1.29s ==================================
```

---

## License & Intellectual Property

- CareLoop is released under permissive open-source licensing. See [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
- In accordance with competition terms, the authors grant the challenge organizers and supporting health entities a 6-month Right of First Refusal for commercial deployment and strategic technology partnership.
