# CareLoop — Open Questions

Questions and decisions that need resolution before or during implementation.

## Clinical / Domain

1. **Assumption validation** — All ~35 parameters in `config/assumptions.yaml` are PLACEHOLDER. Each needs validation by a domain expert. Who is the designated reviewer?

2. **Pathway completeness** — Are the three pathways (FIT, Breast Recall, Cardiometabolic HbA1c) the correct initial scope, or should others be added?

3. **Red flag rules** — The current red flag rules are illustrative. Are there additional clinical criteria that should trigger urgency upgrades?

4. **Closure types** — Are the allowed closure types per pathway correct and complete?

## Technical

5. **Database** — SQLite is used for development. What is the production database target (PostgreSQL assumed)?

6. **Authentication** — `python-jose` is included but no auth flow is implemented. What identity provider / auth scheme should be used?

7. **FHIR version** — Which FHIR version (R4 / R5) should the FHIR adapter target?

8. **AI integration** — What AI/ML capabilities are planned for the AI layer? (e.g., risk prediction, NLP, recommendation)

## Internationalisation

9. **Arabic translations** — All Arabic message templates have `review_status: NEEDS_NATIVE_REVIEW`. A native Arabic speaker must review before any user-facing use.

10. **Additional languages** — Are languages beyond English and Arabic needed?

## Governance & Ethics

11. **Fairness thresholds** — The `disparity_alert_threshold` is set to 0.10 (10% absolute difference). Is this the right threshold for equity alerts?

12. **Simulated data disclaimer** — The current banner and README warnings are text-based. Should there be additional technical safeguards to prevent confusion with real clinical data?
