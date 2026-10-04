# MediLink roadmap after v11

## v12 — Production data architecture
- Alembic database migrations
- PostgreSQL-first deployment
- object-storage abstraction for documents
- background task queue for document and notification jobs
- Redis cache/session services
- structured FHIR-inspired resource mapping
- expanded consent model and record-access policy

## v13 — Clinical intelligence
- larger clinically reviewed routing dataset
- calibration reports and drift checks
- medication knowledge service integration
- richer longitudinal risk models
- model registry and model cards
- clinician feedback loop for AI output quality
- retrieval evaluation for Patient and Clinical Copilots

## v14 — Connected care
- MQTT device gateway
- registered devices and provisioning
- historical vital-sign storage
- streaming anomaly pipeline
- configurable clinician alert thresholds
- TURN-backed telehealth deployment
- appointment-bound telehealth rooms

## v15 — Hospital platform
- organisations, facilities and departments as database entities
- staff rostering
- bed/capacity feeds
- referral queues
- operational SLA dashboards
- tenant-level RBAC
- governance exports and audit retention controls

## Release principle
Future versions should replace simulated integrations with real service adapters while preserving a safe local mode for portfolio use. No version should label a model clinically validated unless that validation has actually been completed and documented.
