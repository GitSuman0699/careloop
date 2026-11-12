# CareLoop: Responsible AI & Clinical Safety Governance Framework

**Challenge:** Future Health Digital Innovation Challenge 2026 (Hack2skill)  
**Track:** Population Health · Challenge 05: Closing the Screening-to-Care Loop  
**Compliance Classification:** Software as a Medical Device (SaMD) Class I / Administrative Orchestration Pipeline  
**Standards Alignment:** UAE Health Data Law (Federal Law No. 2 of 2019), GDPR Art. 22 (Automated Decision Making), HIPAA Security & Privacy Rules, WHO Guidance on Ethics and Governance of AI for Health.

---

> [!IMPORTANT]
> **FIRST PRINCIPLE OF CARELOOP GOVERNANCE**  
> **The algorithm must never replace the clinician.** CareLoop's artificial intelligence capabilities are strictly confined to administrative drafting, plain-language translation, and operational prioritization. The platform incorporates hard architectural barriers that physically prevent autonomous clinical closures or unverified diagnostic communication.

---

## 1. System Risk Register & Safety Property Verification

CareLoop maintains a formal clinical risk register mapping potential hazards to algorithmic failure modes, operational harm, and verified software mitigations:

```
+----------------------------------------------------------------------------------------------------------------------------------+
|                                                   CARELOOP SYSTEM RISK REGISTER                                                  |
+----+----------------------+---------------------------+-----------------------------------+--------------------+-----------------+
| ID | Hazard Category      | Failure Mode              | Operational & Patient Harm        | Software Mitigation| Automated Proof |
+----+----------------------+---------------------------+-----------------------------------+--------------------+-----------------+
| R1 | Unwarranted Closure  | Case closed prematurely   | Patient with abnormal screening   | Multi-gate closure | `tests/test_    |
|    |                      | without diagnostic exam   | lesion develops metastatic cancer | guard; requires    | safety_propert  |
|    |                      |                           | due to dropped follow-up          | clinician sign-off | ies.py::TestA`  |
+----+----------------------+---------------------------+-----------------------------------+--------------------+-----------------+
| R2 | Inappropriate AI     | Generative AI declares    | Severe psychological anxiety,     | Zero-bypass regex  | `tests/test_    |
|    | Diagnostic Claims    | "You have colon cancer"   | panic, or denial causing patient  | scanner + safe     | safety_propert  |
|    |                      | or reveals raw lab values | to avoid clinical care            | fallback template  | ies.py::TestB`  |
+----+----------------------+---------------------------+-----------------------------------+--------------------+-----------------+
| R3 | Privilege Escalation | Non-clinician or automated| Unauthorized discharge or waiver  | Strict RBAC matrix | `tests/test_    |
|    | & Role Bypass        | agent signs off closure   | of mandatory clinical evaluation  | enforced at domain | safety_propert  |
|    |                      | proposal                  |                                   | and API endpoints  | ies.py::TestC`  |
+----+----------------------+---------------------------+-----------------------------------+--------------------+-----------------+
| R4 | Audit Log Tampering  | Malicious or inadvertent  | Inability to trace medical        | Append-only SHA-256| `tests/test_    |
|    |                      | deletion/modification of  | negligence or system failure      | canonical JSON     | safety_propert  |
|    |                      | historical care events    | during legal/clinical review      | hash-chain ledger  | ies.py::TestD`  |
+----+----------------------+---------------------------+-----------------------------------+--------------------+-----------------+
| R5 | Model Context Drift  | Hallucinated medical history| Specialist acts on incorrect     | Strict Pydantic    | `tests/test_    |
|    | & Hallucination      | in consult preparation    | prior history, leading to wrong   | schema validation; | messaging.py`   |
|    |                      | packet                    | clinical procedure selection      | raw lab context lock             |
+----+----------------------+---------------------------+-----------------------------------+--------------------+-----------------+
```

---

## 2. The Five Non-Bypassable Safety Properties

### Property A: Human-Governed Closure Enforcement
- **Requirement:** A case can never reach `CLOSED` status without:
  1. An approved `closure_proposal` record.
  2. A verified human decider holding the role of `clinician` or `supervisor`.
  3. At least one linked clinical `evidence_item` (e.g., procedure report, pathology findings).
  4. A documented closure reason.
  5. Zero unresolved or open escalations on the case.
- **Enforcement Layer:** `app/domain/closure_guard.py` and `app/domain/state_machine.py`. Attempting to transition to `CLOSED` via standard state transition raises `IllegalTransitionError`.

### Property B: Banned-Term Scanner & Deterministic Fallbacks
- **Requirement:** All AI-generated text destined for patient review must undergo automated inspection before transmission.
- **Forbidden Regex Patterns:**
  - Diagnostic terms: `r"\b(cancer|carcinoma|malignant|malignancy|neoplasm|tumor|you have diabetes)\b"`
  - Raw lab values with units: `r"\b\d+(\.\d+)?\s*(ug/g|ng/ml|mg/dl|%|mmol/l)\b"`
- **Fallback Action:** If a banned term is detected, the draft is immediately dropped, an audit event is logged in `ai_action_logs`, and a static, pre-approved clinical template is served.

### Property C: Role-Based Access Control (RBAC) Integrity
- **Requirement:** All operations are guarded by explicit permission checks.
- **Enforcement Layer:** `app/core/rbac.py`.
- **Key Matrix Constraints:**
  - Patients can only view their own records and self-schedule appointments.
  - Care Navigators can log calls and raise escalations, but **cannot approve closures**.
  - Clinicians can sign off closures, review clinical evidence, and resolve escalations.
  - Supervisors can reassign caseloads and advance time in simulation mode.
  - Auditors hold global read-only rights and hash-chain verification tools.

### Property D: Cryptographic Audit Trail & Tamper Detection
- **Requirement:** Event history must be permanent and non-repudiable.
- **Enforcement Layer:** `app/core/hashing.py`.
- **Implementation:** Every `case_events` row contains an `event_hash` calculated as the SHA-256 digest of its canonical JSON representation combined with the previous event's hash. Any database modification breaks the chain and triggers immediate alerting.

### Property E: Deterministic Simulation Reproducibility
- **Requirement:** Monte Carlo simulation results must be scientifically reproducible.
- **Enforcement Layer:** `backend/sim/engine.py`.
- **Implementation:** Seeded pseudo-random number generators ensure that identical initial conditions produce identical demographic cohorts, transition paths, and outcome distributions.

---

## 3. Clinician Override & Escalation Policy

CareLoop respects clinician autonomy at every phase of care:

1. **Pathway Deviations:** If a patient has a documented clinical contraindication (e.g., severe cardiovascular frailty rendering colonoscopy hazardous), the clinician can submit an exception closure proposal with reason `clinical_contraindication` and attach their consultation note as evidence.
2. **Patient Refusal:** If a patient declines follow-up despite multilingual education and navigator outreach, the case cannot be silently dropped. The clinician must conduct a final review and sign off an `informed_refusal` closure.
3. **Auditability of Overrides:** Every override or exception closure is permanently stamped in the event ledger with the clinician's user ID, timestamp, rationale, and supporting evidence.

---

## 4. Data Protection & Privacy Roadmap (DPIA Outline)

CareLoop is designed to operate within heavily regulated health information environments:

### 4.1 UAE Health Data Law & GDPR Compliance Architecture
- **Data Minimization:** CareLoop collects only the specific clinical parameters required to coordinate screening follow-up (e.g., screening date, test category, binary result indicator, contact phone). Full longitudinal medical records remain within the hospital EHR.
- **Data Residency:** In accordance with UAE Federal Law No. 2 of 2019, all production instances must be hosted on certified in-country cloud infrastructure (e.g., Microsoft Azure UAE Central / G42 Cloud).
- **Pseudonymization at Rest:** Direct patient identifiers (National ID / Emirates ID, full name, phone number) are tokenized using AES-256-GCM encryption with keys stored in a hardware security module (HSM).

### 4.2 Reconciling Right to Erasure (GDPR Art. 17) with Immutable Hash Chains
A key engineering tension exists between privacy regulations mandating the right to erasure and cryptographic ledgers designed to be immutable:
- **CareLoop Solution (Cryptographic Salt Tokenization):**
  - Personal identifiable information is never embedded in plaintext inside `case_events.payload`.
  - Payloads store pseudonymized IDs (`patient_uuid`).
  - In the event of a legally sanctioned "Right to Erasure" request, the patient's identity mapping key is permanently shredded.
  - The historical audit ledger and SHA-256 hash chain remain mathematically valid and intact, but all historical events are irreversibly anonymized.
