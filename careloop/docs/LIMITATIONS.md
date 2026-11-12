# CareLoop: System Limitations & Explicit Non-Claims

**Challenge:** Future Health Digital Innovation Challenge 2026 (Hack2skill)  
**Track:** Population Health · Challenge 05: Closing the Screening-to-Care Loop  
**Document Status:** Release Candidate (RC-1)  

---

> [!CAUTION]
> **TRANSPARENCY STATEMENT**  
> Responsible engineering mandates honest and unambiguous disclosure of system boundaries. This document outlines the technological limitations, operational assumptions, and explicit non-claims of the CareLoop prototype.

---

## 1. Explicit Clinical Non-Claims

1. **Not a Clinical Diagnostic Tool:** CareLoop is an administrative and operational orchestration platform. It **does NOT diagnose disease, interpret laboratory assays, analyze radiologic imagery, or recommend therapeutic medical interventions**.
2. **No Autonomous Care Closure:** The system is architecturally incapable of closing a clinical case autonomously. Algorithmic recommendations or drafting must be verified and cryptographically signed by an authorized human clinician or supervisor.
3. **No Direct Clinical Advice to Patients:** The patient messaging pipeline does not provide medical consultations or personalized clinical advice. It communicates operational logistics (appointment scheduling, encounter preparation, red-flag triage questions) and connects patients to human healthcare professionals.

---

## 2. Technical & Data Limitations

### 2.1 Synthetic Data Exclusivity
- **Boundary:** 100% of the patient records, clinical identifiers, telephone numbers, laboratory test values, and provider directories used to develop, test, and demonstrate CareLoop are synthetic.
- **Implication:** While synthetic data generation scripts (`backend/app/seed/`) replicate realistic demographic distributions, clinical nuances (such as complex comorbidity interactions or atypical disease presentations) are not modeled.

### 2.2 Discrete-Event Simulation Boundaries
- **Boundary:** The quantitative simulation engine (`backend/sim/`) utilizes parameterized statistical distributions (LogNormal, Gamma, and Bernoulli trials) to estimate cohort transitions.
- **Implication:** The simulation does not model dynamic hospital bed management, specialist physician on-call scheduling, operating room strikes, or supply chain shortages. Simulation outcomes represent expected population-level trajectories under stated parameter assumptions (`config/assumptions.yaml`).

### 2.3 Mocked External Network Adapters
- **Boundary:** External health information systems (Laboratory Information Systems, Hospital Electronic Health Records, and SMS Telephony Gateways) are connected via high-fidelity mock adapters conforming to HL7 v2, FHIR R4, and REST specifications.
- **Implication:** Production deployment will require integration testing against live MLLP VPN endpoints, proprietary hospital EHR APIs (e.g., Epic, Cerner, Malaffi), and telecom SMS delivery queues.

### 2.4 Translation & Dialectical Validation
- **Boundary:** Patient communication templates are provided in Modern Standard Arabic and English.
- **Implication:** Formal regional deployment across diverse Middle Eastern populations requires dialectical adaptation (e.g., Emirati, Levantine, Egyptian, and Maghrebi colloquial variations) and multi-center health-literacy validation before live patient transmission.

---

## 3. Future Roadmap to Address Limitations

| Limitation | Current State in Prototype | Phase 2 Production Solution |
| :--- | :--- | :--- |
| **Synthetic Records** | Seeded procedurally generated data | De-identified retrospective validation with health authority data |
| **Mocked Interfaces** | In-memory mock adapters | Certified SMART-on-FHIR and MLLP enterprise connectors |
| **Simulation Simplification**| Stochastic discrete-event engine | Live observational pilot measuring real clinical throughput |
| **Arabic Dialects** | Modern Standard Arabic | Localized dialect models with clinical linguistic sign-off |

