# CareLoop: Declarative Clinical Pathways Specification

**Challenge:** Future Health Digital Innovation Challenge 2026 (Hack2skill)  
**Track:** Population Health · Challenge 05: Closing the Screening-to-Care Loop  
**Document Status:** Release Candidate (RC-1)  
**Assumptions & Citations:** All clinical thresholds and SLA durations are parameterized in `config/assumptions.yaml` and flagged as `PLACEHOLDER`.

---

> [!NOTE]
> **ZERO-CODE DECLARATIVE PATHWAY ENGINE**  
> In CareLoop, clinical pathways are not hardcoded into procedural code. They are defined as declarative JSON schemas located in `config/pathways/` (`fit.json`, `breast.json`, `cardiometabolic.json`). The domain engine (`app/domain/state_machine.py`) parses these definitions at runtime to dynamically enforce state sequences, SLA deadlines, red-flag triggers, and mandatory evidence criteria.

---

## 1. Pathway 1: Fecal Immunochemical Test (FIT) Pathway

### 1.1 Clinical Rationale & Objective
Colorectal cancer (CRC) is one of the most preventable malignancies when adenomatous polyps and early-stage lesions are identified and excised. Asymptomatic population screening utilizes the quantitative Fecal Immunochemical Test (FIT) to detect occult human hemoglobin in stool. An abnormal FIT does not establish a diagnosis of cancer; rather, it indicates the urgent need for a confirmatory diagnostic colonoscopy. Loss to follow-up after an abnormal FIT results in advanced stage presentation, higher mortality, and elevated treatment costs.

### 1.2 Specification Summary

```yaml
Pathway ID: fit_positive_v1
Title: Positive Fecal Immunochemical Test (FIT) Follow-up
Screening Trigger:
  Test: Quantitative Stool Immunochemical Test
  Actionable Threshold: FIT >= 100 ng/mL buffer (approx. 20 ug Hb/g feces)
  Source: PLACEHOLDER (Representative national screening guidelines)
Confirmatory Target Action:
  Procedure: Diagnostic Colonoscopy with biopsy/polypectomy as indicated
Target SLA Timeline:
  Result to Patient Acknowledged: 7 days
  Result to Consult Scheduled: 20 days
  Result to Colonoscopy Completed: 30 days
  Hard Loop Closure Limit: 90 days
```

### 1.3 State Sequence & Gate Requirements
1. `RESULT_ISSUED`: Ingestion of abnormal FIT from laboratory via HL7 v2 ORU^R01 or FHIR `DiagnosticReport`.
2. `PATIENT_NOTIFIED`: Automated SMS/WhatsApp outreach delivered in patient's preferred language (Arabic/English).
3. `PATIENT_ACKNOWLEDGED`: Patient confirms receipt via portal, mobile link, or completed telephone outreach by care navigator.
4. `CONSULT_SCHEDULED`: Appointment confirmed for pre-procedure colonoscopy assessment or direct colonoscopy booking.
5. `CONSULT_COMPLETED`: Patient presents for encounter; procedural prep verified.
6. `CARE_PLAN_DOCUMENTED`: Procedural report and post-endoscopy plan filed in EHR.
7. `CLOSED`: Clinician sign-off with colonoscopy report and pathology findings (if biopsies excised).

### 1.4 Red-Flag Urgency Rules
If the patient reports any of the following during digital or navigator intake, their case is immediately elevated to `urgent` priority, shortening navigator response SLAs to 24 hours:
- Active gross rectal bleeding (hematochezia).
- Unexplained involuntary weight loss $> 5\%$ of body weight within 6 months.
- Severe, persistent lower abdominal pain or bowel obstruction symptoms.

### 1.5 Mandatory Closure Evidence
To satisfy the human-governed `ClosureGuard`, the proposal must attach at least one of the following verified artifacts:
- Diagnostic colonoscopy endoscopy procedural report (signed by endoscopist).
- Histopathology report documenting adenoma, hyperplastic polyp, or carcinoma.
- Formal clinician consultation note documenting documented patient refusal or clinical contraindication (e.g., severe cardiopulmonary comorbidity).

---

## 2. Pathway 2: Breast Cancer Recall Pathway

### 2.1 Clinical Rationale & Objective
Population breast cancer screening utilizes biennial digital mammography for asymptomatic women aged 40–69. When a screening mammogram reveals indeterminate or suspicious findings, the patient requires recall for diagnostic workup (spot compression, magnification views, diagnostic ultrasound, and image-guided core needle biopsy). Delayed diagnostic recall correlates with stage progression.

### 2.2 Specification Summary

```yaml
Pathway ID: breast_recall_v1
Title: Breast Cancer Screening Recall & Diagnostic Workup
Screening Trigger:
  Modality: Screening Bilateral Digital Mammography
  Actionable Scoring: BI-RADS 0 (Incomplete), BI-RADS 4 (Suspicious), or BI-RADS 5 (Highly Suggestive)
  Source: PLACEHOLDER (American College of Radiology / EUSOBI guidelines)
Confirmatory Target Action:
  Procedure: Diagnostic Mammography, Breast Ultrasound, and/or Core Biopsy
Target SLA Timeline:
  Result to Patient Acknowledged: 3 days
  Result to Diagnostic Encounter: 14 days
  Diagnostic Encounter to Biopsy Result: 14 days
  Hard Loop Closure Limit: 60 days
```

### 2.3 State Sequence & Gate Requirements
1. `RESULT_ISSUED`: Radiologist finalizes BI-RADS 0, 4, or 5 screening interpretation.
2. `PATIENT_NOTIFIED`: High-priority multilingual outreach emphasizing the need for standard additional imaging without causing panic.
3. `PATIENT_ACKNOWLEDGED`: Patient acknowledges recall notice and confirms attendance availability.
4. `CONSULT_SCHEDULED`: Diagnostic imaging center slot reserved with dedicated breast imaging radiologist.
5. `CONSULT_COMPLETED`: Diagnostic mammography and targeted ultrasound executed.
6. `CARE_PLAN_DOCUMENTED`: Diagnostic BI-RADS assessment finalized (BI-RADS 1–2 benign, BI-RADS 3 short-interval follow-up, or BI-RADS 4–5 biopsy ordered).
7. `CLOSED`: Clinician sign-off confirming completed diagnostic workup and documented management plan.

### 2.4 Red-Flag Urgency Rules
Cases are upgraded to `urgent` if intake identifies:
- New palpable, hard, non-tender solitary breast lump.
- Spontaneous unilateral bloody or serous nipple discharge.
- Visible skin tethering, nipple retraction, or peau d'orange edema.

### 2.5 Mandatory Closure Evidence
- Signed diagnostic breast imaging report (with definitive BI-RADS score 1, 2, or 3).
- Histopathology biopsy report (if core biopsy performed, documenting benign or malignant histology).
- Formal referral documentation to a multidisciplinary breast oncology clinic if malignancy confirmed.

---

## 3. Pathway 3: Cardiometabolic Risk Pathway

### 3.1 Clinical Rationale & Objective
Type 2 diabetes mellitus and metabolic syndrome are leading drivers of cardiovascular disease and renal failure. Routine screening identifies elevated glycated hemoglobin (HbA1c) or elevated fasting glucose before overt macrovascular or microvascular complications manifest. Follow-up requires timely lifestyle intervention, medication initiation, and baseline organ damage assessment.

### 3.2 Specification Summary

```yaml
Pathway ID: cardiometabolic_v1
Title: Cardiometabolic Screening & Diabetes Care Plan
Screening Trigger:
  Test: Venous Glycated Hemoglobin (HbA1c) or Fasting Plasma Glucose
  Actionable Threshold: HbA1c >= 6.5% (48 mmol/mol) or Fasting Glucose >= 126 mg/dL
  Source: PLACEHOLDER (ADA Standards of Medical Care in Diabetes)
Confirmatory Target Action:
  Intervention: Comprehensive Primary Care Assessment, Dietary/Lifestyle Plan, Microvascular Screening
Target SLA Timeline:
  Result to Patient Acknowledged: 7 days
  Result to Primary Care Consult: 30 days
  Care Plan Documented & Baseline Screening: 45 days
  Hard Loop Closure Limit: 90 days
```

### 3.3 State Sequence & Gate Requirements
1. `RESULT_ISSUED`: Lab reports HbA1c $\ge 6.5\%$ or venous fasting glucose $\ge 126$ mg/dL.
2. `PATIENT_NOTIFIED`: Plain-language notification highlighting the importance of a wellness and metabolic review.
3. `PATIENT_ACKNOWLEDGED`: Patient confirms receipt and accesses educational self-care module.
4. `CONSULT_SCHEDULED`: Primary care physician or diabetic educator visit booked.
5. `CONSULT_COMPLETED`: Face-to-face or telehealth clinical encounter executed.
6. `CARE_PLAN_DOCUMENTED`: Comprehensive care plan filed including glycemic target, nutrition counseling, and orders for baseline urine ACR and retinal screening.
7. `CLOSED`: Primary care physician signs off on documented care plan and scheduled 3–6 month follow-up.

### 3.4 Red-Flag Urgency Rules
Cases are upgraded to `urgent` if intake indicates:
- Acute polydipsia, polyuria, nausea, and vomiting (suspected diabetic ketoacidosis / hyperosmolar state).
- Acute visual changes or blurring.
- Active foot ulceration, skin breakdown, or peripheral numbness.

### 3.5 Mandatory Closure Evidence
- Completed Primary Care Comprehensive Diabetes Consultation note.
- Documented treatment care plan with personalized glycemic targets.
- Requisition orders for baseline microvascular screening (urine albumin-to-creatinine ratio and dilated eye examination).

---

## 4. Declarative Schema Structure (`config/pathways/*.json`)

Every pathway conforms to the following schema validated by Pydantic:

```json
{
  "id": "fit_positive_v1",
  "title": "Positive Fecal Immunochemical Test (FIT) Follow-up",
  "version": "1.0.0",
  "description": "Standard diagnostic colonoscopy pathway for abnormal FIT screening results.",
  "target_sla_days": 30,
  "steps": [
    {
      "state": "RESULT_ISSUED",
      "label": "Result Issued",
      "sla_hours": 24,
      "allowed_roles": ["system", "clinician", "navigator"],
      "next": ["PATIENT_NOTIFIED"]
    },
    {
      "state": "PATIENT_NOTIFIED",
      "label": "Patient Notified",
      "sla_hours": 168,
      "allowed_roles": ["system", "navigator"],
      "next": ["PATIENT_ACKNOWLEDGED"]
    },
    {
      "state": "PATIENT_ACKNOWLEDGED",
      "label": "Patient Acknowledged",
      "sla_hours": 240,
      "allowed_roles": ["patient", "navigator"],
      "next": ["CONSULT_SCHEDULED"]
    },
    {
      "state": "CONSULT_SCHEDULED",
      "label": "Consult Scheduled",
      "sla_hours": 360,
      "allowed_roles": ["patient", "navigator", "system"],
      "next": ["CONSULT_COMPLETED"]
    },
    {
      "state": "CONSULT_COMPLETED",
      "label": "Consult Completed",
      "sla_hours": 120,
      "allowed_roles": ["clinician", "navigator"],
      "next": ["CARE_PLAN_DOCUMENTED"]
    },
    {
      "state": "CARE_PLAN_DOCUMENTED",
      "label": "Care Plan Documented",
      "sla_hours": 72,
      "allowed_roles": ["clinician"],
      "next": []
    }
  ],
  "closure_requirements": {
    "required_evidence_types": ["procedure_report", "pathology_report", "consult_note"],
    "allowed_decider_roles": ["clinician", "supervisor"],
    "prohibit_open_escalations": true
  }
}
```

