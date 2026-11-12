# CareLoop: System Assumptions & Parameter Catalog

**Challenge:** Future Health Digital Innovation Challenge 2026 (Hack2skill)  
**Track:** Population Health · Challenge 05: Closing the Screening-to-Care Loop  
**Configuration File:** `config/assumptions.yaml`  
**Total Documented Assumptions:** 35  
**All Assumptions Status:** `PLACEHOLDER` (Uncalibrated Synthetic Defaults)

---

> [!IMPORTANT]
> **COMPLIANCE & GOVERNANCE NOTICE**  
> In accordance with the challenge guidelines, **no clinical threshold, SLA duration, or effect size is presented as an unverified clinical fact**. Every parameter listed below resides in `config/assumptions.yaml` with explicit metadata fields: `value`, `unit`, `source`, `status: PLACEHOLDER`, and `notes`. A health authority or clinical trial sponsor must recalibrate these parameters with local epidemiological and operational data prior to clinical deployment.

---

## 1. Structural Rules vs. Calibrated Parameters

CareLoop explicitly separates **structural invariant rules** from **calibrated operational parameters**:

- **Structural Invariant Rules (Code Enforced):**
  - Case progression is monotonic (no skipping lifecycle steps).
  - The AI cannot close cases or make diagnostic claims.
  - Case closure strictly requires human sign-off with documented evidence.
  - The event ledger is append-only and cryptographically hash-chained.
  - *These rules never change regardless of healthcare network or clinical specialty.*

- **Calibrated Operational Parameters (Configuration Enforced):**
  - Lab test cutoff values (e.g., FIT $\ge 100$ ng/mL).
  - Target timelines and SLA breach warnings (e.g., 30 days to colonoscopy).
  - Caseload limits (e.g., 75 active cases per navigator FTE).
  - Baseline leakage rates and intervention effect sizes in the simulation.
  - *These parameters are managed in `config/assumptions.yaml` and can be adjusted without modifying source code.*

---

## 2. Complete Catalog of 35 System Assumptions

The table below documents all 35 operational and clinical parameters currently loaded into the system:

| # | Category | Key Name | Value | Unit | Status | Source & Justification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | `fit` | `fit_positive_threshold` | 100 | ng/mL | `PLACEHOLDER` | Standard cut-off for quantitative FIT buffer; representative of CRC screening programs. |
| **2** | `fit` | `colonoscopy_target_days` | 30 | days | `PLACEHOLDER` | Recommended interval from abnormal screening to diagnostic colonoscopy. |
| **3** | `fit` | `red_flag_weight_loss_pct` | 5.0 | % | `PLACEHOLDER` | Unexplained weight loss threshold indicating high-risk colorectal symptoms. |
| **4** | `breast` | `bi_rads_actionable_scores` | [0, 4, 5] | scores | `PLACEHOLDER` | Incomplete (0), Suspicious (4), or Highly Suggestive (5) mammographic reads. |
| **5** | `breast` | `recall_target_days` | 14 | days | `PLACEHOLDER` | Maximum target days from screening interpretation to diagnostic recall encounter. |
| **6** | `breast` | `biopsy_target_days` | 14 | days | `PLACEHOLDER` | Target timeline from suspicious imaging confirmation to core-needle biopsy. |
| **7** | `cardiometabolic` | `hba1c_actionable_threshold` | 6.5 | % | `PLACEHOLDER` | ADA diagnostic threshold for Type 2 Diabetes Mellitus ($\ge 48$ mmol/mol). |
| **8** | `cardiometabolic` | `fasting_glucose_threshold` | 126 | mg/dL | `PLACEHOLDER` | Venous plasma glucose cut-off for diabetes diagnostic criteria. |
| **9** | `cardiometabolic` | `comprehensive_assessment_target_days` | 45 | days | `PLACEHOLDER` | Target interval for primary care initial assessment and lifestyle plan establishment. |
| **10** | `sla` | `patient_ack_warning_days` | 3 | days | `PLACEHOLDER` | Days without patient acknowledgement before warning flag raised. |
| **11** | `sla` | `patient_ack_breach_days` | 7 | days | `PLACEHOLDER` | Days without patient acknowledgement before formal SLA breach and navigator escalation. |
| **12** | `sla` | `consult_scheduled_warning_days` | 10 | days | `PLACEHOLDER` | Days post-acknowledgement without confirmed appointment booking. |
| **13** | `sla` | `consult_scheduled_breach_days` | 20 | days | `PLACEHOLDER` | Days post-acknowledgement before booking SLA breach triggers supervisor alert. |
| **14** | `sla` | `consult_completed_warning_days` | 25 | days | `PLACEHOLDER` | Days without completed specialist encounter trigger preparation check. |
| **15** | `sla` | `consult_completed_breach_days` | 30 | days | `PLACEHOLDER` | Days without completed encounter marks breach of pathway timeline. |
| **16** | `sla` | `loop_closure_hard_limit_days` | 90 | days | `PLACEHOLDER` | Absolute maximum ceiling for population screening loop closure before audit flagging. |
| **17** | `navigator` | `max_active_cases_per_fte` | 75 | cases | `PLACEHOLDER` | Maximum concurrent active patient load per full-time care navigator before alert fatigue. |
| **18** | `navigator` | `phone_outreach_attempts_before_escalation` | 3 | count | `PLACEHOLDER` | Standard telephone outreach cadence before supervisor escalation. |
| **19** | `navigator` | `days_between_outreach_attempts` | 2 | days | `PLACEHOLDER` | Resting interval between sequential manual outreach telephone calls. |
| **20** | `simulation` | `default_cohort_size` | 5000 | cases | `PLACEHOLDER` | Synthetic cohort size per Monte Carlo simulation arm to ensure tight confidence intervals. |
| **21** | `simulation` | `default_replications` | 30 | runs | `PLACEHOLDER` | Number of independent random seeds executed to establish statistical variance. |
| **22** | `simulation` | `simulation_horizon_days` | 90 | days | `PLACEHOLDER` | Total temporal tracking window for synthetic cohort analysis. |
| **23** | `baseline_leakage` | `ack_loss_rate` | 0.22 | prob | `PLACEHOLDER` | Baseline probability of patient failing to acknowledge abnormal screening result. |
| **24** | `baseline_leakage` | `referral_loss_rate` | 0.18 | prob | `PLACEHOLDER` | Baseline probability of referral being lost between primary care and specialist clinic. |
| **25** | `baseline_leakage` | `scheduling_no_show_rate` | 0.15 | prob | `PLACEHOLDER` | Baseline rate of missed appointments or unrescheduled cancellations. |
| **26** | `baseline_leakage` | `unverified_completion_rate` | 0.12 | prob | `PLACEHOLDER` | Baseline proportion of cases closed without verifiable clinical documentation. |
| **27** | `intervention_effects` | `automated_multilingual_ack_boost` | 0.65 | rel.red | `PLACEHOLDER` | Relative reduction in acknowledgement failure due to plain-language Arabic/English outreach. |
| **28** | `intervention_effects` | `navigator_phone_outreach_ack_boost` | 0.50 | rel.red | `PLACEHOLDER` | Relative reduction in remaining unacknowledged cases following human phone call. |
| **29** | `intervention_effects` | `closed_loop_referral_loss_reduction`| 0.80 | rel.red | `PLACEHOLDER` | Relative reduction in lost referrals through automated tracking and handoff locks. |
| **30** | `intervention_effects` | `automated_reminder_no_show_reduction`| 0.45 | rel.red | `PLACEHOLDER` | Relative reduction in appointment no-shows via automated interactive SMS reminders. |
| **31** | `intervention_effects` | `clinician_packet_closure_acceleration_days` | 8.5 | days | `PLACEHOLDER` | Reduction in days to closure resulting from pre-populated consult preparation packets. |
| **32** | `fairness` | `language_disparity_penalty_non_english` | 1.35 | mult | `PLACEHOLDER` | Baseline multiplier on acknowledgement failure for non-English/non-majority patients. |
| **33** | `fairness` | `age_disparity_penalty_elderly` | 1.25 | mult | `PLACEHOLDER` | Baseline multiplier on digital scheduling failure for patients aged 65 and above. |
| **34** | `fairness` | `careloop_language_disparity_mitigation`| 0.85 | rel.red | `PLACEHOLDER` | CareLoop effectiveness at neutralizing language-based digital health friction. |
| **35** | `fairness` | `careloop_digital_divide_mitigation` | 0.60 | rel.red | `PLACEHOLDER` | CareLoop effectiveness at reducing elderly attrition via navigator-assisted telephone booking. |

---

## 3. Recalibration Protocol for Regional Deployment

When deploying CareLoop within an integrated regional health system (such as the Abu Dhabi Department of Health / SEHA network), parameters are recalibrated via a 3-step validation protocol:

1. **Retrospective EHR Baseline Audit:** Extract 12 months of historical screening data for FIT, Mammography, and HbA1c to establish empirical values for `baseline_leakage` parameters (`ack_loss_rate`, `referral_loss_rate`, `scheduling_no_show_rate`).
2. **Clinical Advisory Board Review:** Convene oncology and primary care clinical leads to approve SLA timeline thresholds (`colonoscopy_target_days`, `recall_target_days`) and evidence criteria.
3. **YAML Configuration Update:** Update values in `config/assumptions.yaml` and flip parameter status from `PLACEHOLDER` to `VERIFIED` with formal publication and institutional citations.
