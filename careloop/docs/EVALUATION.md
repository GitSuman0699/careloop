# CareLoop: Simulation & Quantitative Evaluation Report

**Challenge:** Future Health Digital Innovation Challenge 2026 (Hack2skill)  
**Track:** Population Health · Challenge 05: Closing the Screening-to-Care Loop  
**Evaluation Engine:** Discrete-Event Monte Carlo Simulator (`backend/sim/`)  
**Data Artifacts:** `backend/sim/results/simulation_results.json`, `backend/sim/results/headline_comparison.csv`  
**Statistical Notice:** **MODELLED RESULTS, NOT CLINICAL EVIDENCE.** Simulated under explicitly parameterized assumptions (`config/assumptions.yaml`).

---

## 1. Executive Evaluation Summary

To evaluate whether CareLoop's operational interventions can structurally resolve screening leakage across large populations, we built and executed a discrete-event Monte Carlo simulation engine. The simulation models patient cohorts transitioning through sequential care states, incorporating stochastic attrition, language barriers, age penalties, navigator capacity constraints, and human-in-the-loop closure verification.

```
+---------------------------------------------------------------------------------------------------------+
|                                  PRIMARY OUTCOME FINDINGS AT A GLANCE                                   |
+------------------------------------+--------------------------+-----------------------+-----------------+
| Metric                             | Baseline Standard of Care| CareLoop Orchestration| Impact Delta    |
+------------------------------------+--------------------------+-----------------------+-----------------+
| 90-Day Closed-Loop Rate            | 54.8% [54.6% - 55.1%]    | 85.4% [85.3% - 85.6%] | +30.6 pp (+56%) |
| Median Time to Confirmed Care      | 73.4 days [73.3 - 73.6]  | 34.5 days [34.4 - 34.7| -38.9 days (-53%|
| Appointment Completion Rate        | 88.0% [87.8% - 88.2%]    | 94.6% [94.4% - 94.7%] | +6.6 pp         |
| Arabic Language Disparity Ratio    | 0.896 (Significant Gap)  | 0.998 (Near Parity)   | +0.102 (Closed) |
| Elderly (65+) Disparity Ratio      | 0.959                    | 0.993                 | +0.034 (Closed) |
+------------------------------------+--------------------------+-----------------------+-----------------+
```
*Confidence intervals are empirical 95% CIs calculated across 30 independent stochastic replications ($N=5,000$ per arm).*

---

## 2. Simulation Methodology & Architecture

### 2.1 Discrete-Event State Engine (`backend/sim/engine.py`)
Each synthetic patient enters the simulation at $t = 0$ upon the issuance of an actionable screening result (`RESULT_ISSUED`). The patient trajectory progresses through a state transition network governed by probability distributions and queuing delays:

```
[RESULT_ISSUED] 
       │  (Notification Delay ~ LogNormal, Ack Loss Rate)
       ▼
[PATIENT_ACKNOWLEDGED]
       │  (Referral Transmission, Referral Loss Rate)
       ▼
[CONSULT_SCHEDULED]
       │  (Clinic Wait Queue ~ Gamma, No-Show Rate)
       ▼
[CONSULT_COMPLETED]
       │  (Encounter Documentation & Diagnostic Workup)
       ▼
[CARE_PLAN_DOCUMENTED]
       │  (Closure Sign-off Delay, Unverified Completion Rate)
       ▼
[CLOSED]
```

### 2.2 Replications and Deterministic Reproducibility
- **Cohort Size:** $N = 5,000$ patients per arm ($10,000$ per seed, $300,000$ total patient pathways simulated).
- **Replications:** 30 independent runs initialized with seeds $1,000$ through $1,029$.
- **Reproducibility Test:** Verified by automated test `tests/test_safety_properties.py::test_identical_seed_produces_identical_results` guaranteeing bit-for-bit identical outputs across environments.

---

## 3. Detailed Results & Statistical Comparisons

### 3.1 Headline Metrics Comparison

```
+---------------------------------------------------------------------------------------------------------+
|                                    DETAILED SIMULATION COMPARISON (N=30 SEEDS)                          |
+-------------------------------+--------------------------+--------------------------+-------------------+
| Metric                        | Baseline Mean [95% CI]   | CareLoop Mean [95% CI]   | Difference        |
+-------------------------------+--------------------------+--------------------------+-------------------+
| closed_90d_pct                | 0.548 [0.546 - 0.551]    | 0.854 [0.853 - 0.856]    | +0.306 (+30.6 pp) |
| referral_conversion_rate      | 1.000 [1.000 - 1.000]    | 1.000 [1.000 - 1.000]    | 0.000             |
| appointment_completion_rate   | 0.880 [0.878 - 0.882]    | 0.946 [0.944 - 0.947]    | +0.066 (+6.6 pp)  |
| median_days_to_closure        | 73.433 [73.253 - 73.614] | 34.533 [34.352 - 34.715] | -38.900 days      |
+-------------------------------+--------------------------+--------------------------+-------------------+
```

### 3.2 Time-to-Care Acceleration
In the baseline standard of care, fragmented communication and lost referrals cause prolonged delays: patients take a median of **73.4 days** to reach verified loop closure, with over 45% failing to achieve closure within the 90-day population health horizon.

Under CareLoop orchestration:
- Automated multilingual SMS/WhatsApp notification delivers immediate patient outreach within 24 hours.
- Direct digital self-scheduling and navigator outreach reduce scheduling lag from a median of 22.4 days to 8.2 days.
- Structured consult preparation packets accelerate specialist sign-off.
- **Overall median days to confirmed closure is reduced by 38.9 days (a 53% acceleration in time to definitive care).**

---

## 4. Health Equity & Fairness Analysis

Screening leakage disproportionately impacts vulnerable demographic sub-populations. We evaluated model outcomes across language preference and age groups:

```
+---------------------------------------------------------------------------------------------------------+
|                                 DEMOGRAPHIC DISPARITY & HEALTH EQUITY CUTS                              |
+--------------------+---------------+---------------+---------------+------------------+----------------+
| Subgroup           | Baseline Rate | CareLoop Rate | Absolute Gain | Baseline Dispar. | CareLoop Disp. |
+--------------------+---------------+---------------+---------------+------------------+----------------+
| Language: Arabic   | 50.59%        | 85.17%        | +34.58 pp     | 0.896            | 0.998          |
| Language: English  | 56.43%        | 85.30%        | +28.87 pp     | 1.000 (Ref)      | 1.000 (Ref)    |
| Language: Other    | 54.79%        | 88.12%        | +33.33 pp     | 0.971            | 1.033          |
+--------------------+---------------+---------------+---------------+------------------+----------------+
| Age: 18 - 49       | 55.87%        | 85.50%        | +29.63 pp     | 1.000 (Ref)      | 1.000 (Ref)    |
| Age: 50 - 64       | 54.76%        | 85.71%        | +30.95 pp     | 0.980            | 1.002          |
| Age: 65+ (Elderly) | 53.60%        | 84.90%        | +31.30 pp     | 0.959            | 0.993          |
+--------------------+---------------+---------------+---------------+------------------+----------------+
```

### Key Health Equity Insights:
- **Eliminating the Language Gap:** In the baseline arm, Arabic-speaking patients experienced a 5.8 percentage point disadvantage in 90-day closure compared to English speakers (disparity ratio 0.896). CareLoop's native Arabic patient experience and bilingual navigation completely closed this gap, elevating closure to **85.17%** (disparity ratio 0.998).
- **Bridging the Digital Divide for Seniors:** Older adults ($65+$) suffer from higher drop-off when forced to navigate complex digital-only portals. CareLoop's automated telephone escalation ensures that non-digital seniors are proactively called by human navigators, lifting elderly closure from **53.60%** to **84.90%** (disparity ratio 0.993).

---

## 5. Univariate Sensitivity Analysis (Tornado Impact)

To evaluate which system parameters exert the greatest influence on population health outcomes, we varied key model parameters by $\pm 20\%$ while holding all other variables constant:

```
+---------------------------------------------------------------------------------------------------------+
|                                    UNIVARIATE SENSITIVITY RANKING                                       |
+---+---------------------------------------------------+-----------+------------+------------+-----------+
| # | Parameter Name                                    | Key       | Low Delta  | High Delta | Swing     |
+---+---------------------------------------------------+-----------+------------+------------+-----------+
| 1 | Navigator reminder & rescheduling efficacy        | nav_rem   | +22.1 pp   | +34.4 pp   | 12.3 pp   |
| 2 | Multilingual acknowledgement gain                 | multi_ack | +24.5 pp   | +32.8 pp   | 8.3 pp    |
| 3 | SLA automated escalation recovery                 | sla_esc   | +27.2 pp   | +32.3 pp   | 5.1 pp    |
| 4 | Clinician packet closure acceleration             | clin_acc  | +28.9 pp   | +31.4 pp   | 2.5 pp    |
+---+---------------------------------------------------+-----------+------------+------------+-----------+
```

### Architectural Implication:
Human navigator intervention and timely rescheduling have the single highest marginal return on loop closure (12.3 pp swing). Automated tooling must be designed to empower, rather than replace, human care navigators.

---

## 6. Navigator Caseload & Capacity Breakeven Curve

CareLoop models the operational tradeoff between navigator workload and system effectiveness. As caseload per full-time equivalent (FTE) increases, navigators experience alert fatigue, leading to delayed outreach and missed follow-ups:

```
+---------------------------------------------------------------------------------------------------------+
|                                   NAVIGATOR CASELOAD CAPACITY ANALYSIS                                  |
+-------------------+----------------------------+-----------------------+--------------------------------+
| Active Cases / FTE| Modelled 90-Day Closure    | Alert Fatigue Penalty | Operational Recommendation     |
+-------------------+----------------------------+-----------------------+--------------------------------+
| 40 cases / FTE    | 88.4%                      | 1.0%                  | High touch, underutilized      |
| 60 cases / FTE    | 87.9%                      | 2.0%                  | Optimal clinical balance       |
| 75 cases / FTE    | 86.8%                      | 3.0%                  | Recommended operational target |
| 80 cases / FTE    | 86.5%                      | 3.0%                  | Safe upper limit               |
| 100 cases / FTE   | 84.2%                      | 6.0%                  | Mild fatigue onset             |
| 120 cases / FTE   | 81.2%                      | 10.0%                 | High alert fatigue, degraded   |
| 140 cases / FTE   | 76.5%                      | 16.0%                 | Critical backlog breakdown     |
+-------------------+----------------------------+-----------------------+--------------------------------+
```

### Recommendation for Health Authorities:
To sustain loop closure rates above **85%**, health systems should size care navigator staffing to maintain active caseloads between **60 and 75 cases per navigator FTE**.
