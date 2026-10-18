# Decision log

## Built

FastAPI service, Streamlit operator console, SQLite workflow persistence, idempotent human-task creation, nine ordered provisioning tasks, masked register fields, rule-based audit, idempotent offboarding tasks, proxy safety policy and a credential-free synthetic failover simulation, Docker setup, synthetic evidence, and fixture evaluation. The design prioritizes an observable safe path and avoids unsupported account automation.

## Skipped or blocked

- Live provisioning, verification, 2FA, profile changes, and Meta linking: company test environment and authorization were not supplied.
- Vault integration and real secret rotation: no vault connector/access was supplied; only synthetic references are present.
- Reminders and overdue escalation: no approved scheduler or notification channel was supplied.
- Real proxy health/rotation/failover: approved proxy reference and neutral endpoint were not supplied. A deterministic local simulation demonstrates control flow only; the application does not connect to Instagram or any proxy.
- Android sample fleet: no devices or neutral sample app were supplied; omitted after prioritizing the core path.
- Live screen recording: no live account/environment was available.

## Failure points and next-day improvements

The main gap is that operational actions depend on human steps and evidence until authorized company integrations exist. Obtain written test-scope confirmation and access, integrate the approved vault and supported Meta interfaces, add authenticated roles and scheduler/notifications, then conduct a supervised live walkthrough. Independently validate idempotency and interruption recovery under controlled failure injection, add migrations/backups/monitoring, and request security review before production use.

## Device fleet at 20–50 devices

Use managed Android hardware with standardized images, dedicated power/ventilation, staged updates, device enrollment, remote access behind SSO/VPN with audit logs, centralized health monitoring, and spare-device planning. Monthly cost depends on region, hardware, hosting, connectivity, and support; no unsupported estimate is asserted.

## AI tool disclosure

OpenAI Codex was used to analyze the supplied assignment and create/organize this prototype and documentation. The application does not call an AI service. No live account actions were performed.
