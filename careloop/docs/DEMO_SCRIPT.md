# CareLoop: 7-Minute Live Demo Script

**Event:** Future Health Digital Innovation Challenge 2026 (Hack2skill)  
**Track:** Population Health · Challenge 05: Closing the Screening-to-Care Loop  
**Format:** 7-Minute Live Product Demonstration + 3-Minute Judge Q&A  
**Target Environment:** Local Docker Compose / Development Server (`http://localhost:8000`)

---

## 0. Demo Setup & Pre-Flight Checklist (T-Minus 5 Minutes)
1. Start application: `docker compose up` or `uvicorn app.main:app --port 8000` + `npm run dev`.
2. Open browser to `http://localhost:8000/` (or `http://localhost:5173/`).
3. Ensure simulated data banner is visible: `SIMULATED DATA: NOT FOR CLINICAL USE`.
4. Open top navigation bar with one-click **Quick Tour Switcher** (Cases A through F) and **Role Switcher** (`patient`, `navigator`, `clinician`, `supervisor`, `auditor`).

---

## 1. Minute-by-Minute Live Demo Script (0:00 - 7:00)

```
+----------------------------------------------------------------------------------------------------------+
|                                  CARELOOP 7-MINUTE LIVE DEMO TIMELINE                                    |
+---------+-------------------+------------------------------------+---------------------------------------+
| Time    | Phase             | Screen / Interface                 | Core Action & Narrative               |
+---------+-------------------+------------------------------------+---------------------------------------+
| 0:00    | Problem Context   | Slide / Overview                   | The Screening Leakage Crisis          |
| 1:00    | Case A: End-to-End| Patient Portal (Mobile)            | Multilingual Notification & Booking   |
| 2:15    | Case B & C: Triage| Patient Portal (Arabic RTL)        | Red-Flag Escalation & Navigator Queue |
| 3:30    | Case D: Governance| Ops Dashboard                      | Time Travel: Advancing Clock & SLA    |
| 4:45    | Case E: Human Gate| Clinician Triage                   | Adversarial Closure Block & Sign-off  |
| 5:45    | Case F: AI Safety | Governance & Audit View            | Adversarial Prompt Block & Hash Chain |
| 6:30    | Evidence & Impact | Modelled Evidence View             | Simulation Numbers & Wrap-up          |
+---------+-------------------+------------------------------------+---------------------------------------+
```

### [0:00 - 1:00] The Screening Leakage Crisis
- **Presenter:** *"Across screening programs, an abnormal result only saves lives if it leads to timely care. Yet in prevailing health systems, over 45% of patients drop out between screening and care. Results get stuck in doctor inboxes, patients don't understand the notice, and referrals get lost in transit. This is CareLoop: the first open-standard, human-governed care orchestration platform that guarantees verified closure for every abnormal screening result."*

### [1:00 - 2:15] Case A: The Frictionless Patient Journey
- **Action:** Click **Case A (Tariq - Happy Path FIT)** in Quick Tour. Switch to **Patient View**.
- **Presenter:** *"Meet Tariq. He completed an at-home FIT screening test. The lab issued an abnormal result. Instead of receiving clinical jargon, Tariq gets a WhatsApp message with a secure link to this mobile portal. Notice the clear, health-literate explanation: 'Your test showed microscopic blood, which requires a routine colonoscopy to check for polyps.' Tariq answers a simple teach-back question to confirm understanding, views available slots at Central Hospital, and self-schedules his appointment in two clicks. The state instantly advances to `CONSULT_SCHEDULED`."*

### [2:15 - 3:30] Case B & C: Health Equity & Red-Flag Escalation
- **Action:** Click **Case B & C (Fatima - Arabic & Red Flag)**. Toggle language to **العربية (Arabic RTL)**.
- **Presenter:** *"Now meet Fatima, an Arabic-speaking patient with an abnormal mammogram recall. CareLoop provides a native RTL Arabic experience. While checking in, Fatima reports a new red-flag symptom: active bleeding or palpable mass. Watch what happens: CareLoop immediately triggers our clinical urgency evaluator. The case is upgraded to `urgent`. Switch to the **Navigator Queue**—Fatima instantly appears at the top of the priority worklist with an urgent red-flag banner, prompting the care navigator to initiate immediate telephone outreach."*

### [3:30 - 4:45] Case D: Time-Travel & Proactive SLA Management
- **Action:** Switch to **Supervisor View** -> **Ops Dashboard**.
- **Presenter:** *"How do we prevent cases from falling through the cracks when patients don't respond? Let's look at our Ops Dashboard. We can see our live patient funnel and SLA compliance. To demonstrate CareLoop's temporal monitoring, let's use our Simulated Clock control. Let's advance time forward by 7 days. Instantly, cases with unacknowledged notifications cross their SLA threshold, automatically triggering SLA breach warnings and routing into the navigator exception queue."*

### [4:45 - 5:45] Case E: The Non-Bypassable Human Closure Gate
- **Action:** Switch to **Clinician View**. Open **Case E (Adversarial Closure)**.
- **Presenter:** *"Here is our core safety architecture: **the AI never closes a case.** Let's try to close this case without clinical evidence. Click 'Submit Closure'—the system immediately throws a hard block: `ClosureGuardError: Missing mandatory clinical evidence`. Now let's try having a non-clinician approve it—denied by our strict RBAC matrix. Only when Dr. Sarah reviews the attached colonoscopy report and histopathology findings can she sign off with her cryptographic credential, formally moving the case to `CLOSED`."*

### [5:45 - 6:30] Case F: AI Safety & Cryptographic Audit Ledger
- **Action:** Open **Governance View** -> **AI Action Logs** and **Ledger Inspector**.
- **Presenter:** *"What about Generative AI? CareLoop uses AI solely to draft patient summaries and consult packets. But look at our AI logs: when an adversarial draft attempted to state 'You have malignant carcinoma', our zero-bypass regex scanner blocked it instantly, serving a pre-approved safe fallback template and logging the violation. Furthermore, every event is chained with SHA-256 canonical JSON hashes. Click 'Verify Hash Chain'—all 12 events verified tamper-free."*

### [6:30 - 7:00] Simulation Evidence & Conclusion
- **Action:** Switch to **Evidence View**.
- **Presenter:** *"We evaluated CareLoop across 300,000 simulated patient pathways in a 30-seed Monte Carlo evaluation: CareLoop improves 90-day closure from 54.8% to 85.4%, reduces time to care from 73 days to 34 days, and completely closes the Arabic language disparity gap. CareLoop is containerized, tested with 118 automated proofs, and ready for clinical pilot. Thank you, and we welcome your questions."*
