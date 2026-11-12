# AI Use Disclosure

**Project:** CareLoop — Closing the Screening-to-Care Loop  
**Challenge:** Future Health Digital Innovation Challenge 2026, Population Health · Challenge 05  
**Submission Date:** November 2026  

---

## 1. AI Assistance During Development (Coding Phase)
- **AI Coding Assistance:** Antigravity AI agent (powered by Gemini & Claude models) was used as an interactive programming collaborator for codebase scaffolding, test drafting, simulation model equations, and technical documentation drafting.
- **Human Oversight & Verification:** All architecture decisions, clinical pathway configurations, safety guardrail specifications, and database models were guided and reviewed by the lead developer.
- **Synthesized Data:** All patient demographic records, laboratory findings, provider rosters, and contact phone numbers were synthetically generated. No private health information (PHI) or personal data was ever ingested or exposed.

---

## 2. Runtime AI Components in the CareLoop Prototype
CareLoop deliberately limits AI to non-clinical, non-decision-making, advisory roles behind strict deterministic guardrails:

| Component | Permitted Runtime Role | Hard Guardrail & Safety Bound |
|---|---|---|
| **Message Rewrite** | Adapting reading level and language of approved templates for clear patient communication | **Strictly prohibited** from modifying urgency, changing clinical instructions, or disclosing diagnostic findings. Banned terms (`banned_terms.json`) intercept and trigger deterministic safe fallbacks. |
| **Consult Summarizer** | Compiling longitudinal event timelines for receiving clinicians | Advisory draft only. Tagged with visible `AI-DRAFTED: REQUIRES CLINICAL REVIEW` badge. Human clinician must review before transmission. |
| **Closure Proposal Assistant** | Assembling evidence checklist for human review | **Cannot close cases.** Closure is mathematically blocked by `ClosureGuard` unless signed off by an authorized human clinician or supervisor. |
| **Delay Reason Classifier** | Categorizing free-text contact notes into operational taxonomy | Analytical categorization only; zero influence on clinical routing or medical urgency. |

---

## 3. Autonomous Decision Guardrails (Non-Negotiable)
- **Zero Autonomous Clinical Closure:** An AI model cannot close a case or sign off evidence.
- **Zero Autonomous Diagnostic Disclosure:** AI is blocked from diagnosing or communicating unconfirmed disease entities to patients.
- **Auditability:** Every runtime AI invocation is logged to the `ai_actions` table with input hash, output text, validator verdict, and fallback status.
