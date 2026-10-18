# Requirement traceability

| Assignment requirement | Evidence / status |
|---|---|
| One authorized test account; real Instagram, not emulator-only | Human-gated workflow documented; company environment absent; live work blocked. |
| Handle suggestions and availability guidance | Manual check described; no automated Instagram interaction. |
| Company email alias and controlled phone | Human-task path; real provisioning blocked pending supplied access. |
| Signup and verification human handoff with resume | Nine ordered idempotent tasks in provisioning workflow; human performs signup/verification and records redacted evidence. |
| Signup/verification task, owner/deadline/reminders/escalation/resume | Task API supports owner, deadline, status, evidence, and idempotency. Reminder/escalation integration unavailable. |
| 2FA and vault storage | Register tracks setup and references only; vault work is human-gated and blocked. |
| Profile/business conversion/Meta linking/least privilege | Human workflow documented; no live access supplied. |
| Account register fields | `GET /api/accounts`; synthetic sample in `evidence/account_register.json`; recovery contacts masked in API. |
| Weekly audit and demonstrated run | On-demand API/UI audit and sample report; scheduler not configured. |
| Audit finding types and follow-up tasks | Rule audit detects non-company recovery, missing backup codes, incomplete 2FA, stale privileged role; task API supports remediation handoffs. |
| Finding provenance | Labels are constrained to the three assignment values and inherited from record provenance; demo data is unverified. |
| Offboarding and credential rotation; temporary role | Four idempotent human tasks plus checklist/report; real role/credential operations blocked. Temporary-role guidance is in decision log. |
| Proxy vault, health, timeouts, bounded retries, consistency, rotation/failover | Policy endpoint plus deterministic bounded-retry/failover/challenge simulation; no real proxy credentials or neutral endpoint supplied, so a live check/rotation was not run. |
| Pause on security challenge | Documented as stop condition in UI/API policy and README. |
| Optional two-device neutral app fleet | Omitted; no devices/sample app supplied. Scaling considerations recorded. |
| Runnable code and README | Source and commands provided; requires Python 3.10+. |
| Docker deployment | Dockerfile and docker-compose.yml provided. |
| Golden data and evaluation metrics | Synthetic fixtures and evaluation command; fixture consistency only, not model/live accuracy. |
| Register, audit, offboarding, run log | Synthetic/redacted examples in `evidence/`. |
| 2–3 minute live walkthrough | Not produced; test account/environment unavailable. Remains required. |
| Decision log and AI tool disclosure | `DECISION_LOG.md`. |
| Six-hour focus and 48-hour submission | Prioritized a core path. Confirm receipt time and submit by email reply or task instructions. |
