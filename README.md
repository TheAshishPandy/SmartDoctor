# SmartDoctor — AI-Powered Healthcare Assistant

SmartDoctor is an early-stage healthcare platform for patients and clinicians. It is designed for patient-provided records, authorized EHR/FHIR integrations, evidence-grounded health information and clinician-reviewed assistance.

## Milestone status
- **Milestone 1 — Platform foundation:** implementation committed; Docker and CI verification pending.
- **Milestone 2 — Identity, authorization and audit:** implementation and security tests added; CI, PostgreSQL migration and live OIDC verification pending.
- **Milestone 3 — Patient record ingestion and provenance:** planned.

Track acceptance evidence in [docs/milestones.md](docs/milestones.md).

## Implemented foundation
- FastAPI and Next.js/React/TypeScript application shells.
- PostgreSQL/SQLAlchemy transactional schema and Alembic migrations.
- OIDC RS256/JWKS token validation boundary and patient access policy.
- MongoDB chat-history adapter with organization/owner scoped operations.
- Qdrant patient-RAG adapter with organization + patient filtered retrieval.
- Docker Compose development services for PostgreSQL, MongoDB, Qdrant, Redis, API and web.
- Automated authorization and storage-contract tests.

## Data ownership
- **PostgreSQL:** patient, organization, consent, care relationship, appointment, transaction and audit records.
- **MongoDB:** chat conversations, messages and assistant interaction history.
- **Qdrant:** embeddings, document chunks and retrieval metadata only.
- **Encrypted object storage:** original uploaded files and source documents.
- **Redis:** cache and short-lived coordination only.

See [the storage architecture](docs/data-storage.md) for isolation, security and operational requirements.

## Run locally
```bash
cp .env.example .env
docker compose up --build
```

Configure a trusted OIDC provider before authenticated requests. Use synthetic data only. Development credentials are not suitable for shared or public environments.

## Clinical safety
SmartDoctor is scoped for health information, care navigation and clinician support, not autonomous diagnosis, prescribing or treatment changes. Clinical deployment requires governance, validation and jurisdiction-specific legal/regulatory approval.

## Documentation
Architecture, workflows, agents, data model, [API](docs/api.md), [security](docs/security.md), AI governance, roadmap, [milestones](docs/milestones.md) and development guide are in `docs/`.
