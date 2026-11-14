# SmartDoctor — AI-Powered Healthcare Assistant

SmartDoctor is an early-stage healthcare platform for patients and clinicians. It is designed for patient-provided records, authorized EHR/FHIR integrations, evidence-grounded health information and clinician-reviewed assistance.

## Milestone status
- **Milestone 1 — Platform foundation:** implementation committed; Docker and CI verification pending.
- **Milestone 2 — Identity, authorization and audit:** implementation and security tests added; CI, PostgreSQL migration and live OIDC verification pending.
- **Milestone 3 — Patient record ingestion and provenance:** planned.

Track acceptance evidence in [docs/milestones.md](docs/milestones.md).

## Implemented
- FastAPI and Next.js/React/TypeScript application shells.
- Docker Compose for PostgreSQL, Redis, API and web.
- OIDC RS256/JWKS token validation boundary.
- Patient profile access policy: patient ownership or clinician with active membership, care relationship and consent.
- SQLAlchemy identity/access/audit schema and Alembic initial migration.
- Automated authorization tests, including cross-patient denial and revoked/expired consent.

## Target technology
Next.js, React, TypeScript, FastAPI, PostgreSQL, Alembic, LangGraph, Qdrant, Redis, encrypted object storage, local Ollama development inference, approved cloud model gateway and HL7 FHIR R4 integrations subject to partner profiles.

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
