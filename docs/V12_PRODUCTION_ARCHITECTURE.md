# MediLink v12 — Production Data Architecture

- PostgreSQL-ready configuration while retaining SQLite fallback.
- Redis configuration and in-process fallback.
- Object-storage abstraction path.
- Background job API and job persistence.
- FHIR R4-style Patient resource endpoint.
- Docker Compose stack for PostgreSQL, Redis, MQTT and the API.
- Alembic dependency added for schema migration workflow.

The local development experience still works without PostgreSQL/Redis/MQTT.
