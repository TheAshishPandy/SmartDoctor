# SmartDoctor Milestone Tracker

Milestones are marked **Complete** only after their acceptance criteria have been tested. A commit alone does not make a milestone complete.

## Milestone 1 — Platform foundation

**Status: In progress — implementation committed; full environment verification pending.**

### Scope delivered
- FastAPI application with environment-backed settings and a non-sensitive health endpoint.
- Next.js/React/TypeScript application shell with an explicit non-clinical development notice.
- Docker Compose services for PostgreSQL, Redis, API and web development server.
- Safe `.env.example`, ignore rules and backend container definition.
- GitHub Actions CI for backend lint/tests and frontend lint/build.
- Backend health and OpenAPI smoke tests.

### Acceptance criteria

| Criterion | Status | Evidence / remaining work |
|---|---|---|
| Backend application imports and compiles | Passed locally | `python -m compileall -q app tests` |
| Backend API smoke tests | Passed locally | `python -m pytest -q` — 2 passed |
| Backend lint | Pending | Ruff is not installed in the current execution environment; CI installs it |
| Frontend lint and production build | Pending | Dependencies are not installed in the current execution environment; CI installs them |
| Docker Compose configuration and service startup | Pending | Docker is not available in the current execution environment |
| CI workflow | Pending | Must inspect the GitHub Actions run after push |
| No secrets or patient data committed | Reviewed | Only placeholder development credentials; no patient data |

### Explicitly not included in this milestone
- Authentication/OIDC, MFA, roles, patient/clinician authorization and consent.
- Database ORM, migrations, audit event persistence or patient records.
- Chat, medical agents, model gateway, RAG, document upload or FHIR integration.

These are subsequent milestones. Do not use real patient data with this foundation.

### Local start

```bash
cp .env.example .env
docker compose up --build
```

- Web: http://localhost:3000
- API health: http://localhost:8000/health
- API OpenAPI: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

The credentials in `.env.example` and Compose are development-only. Never expose these services to a public network.

### Backend checks

```bash
cd backend
python -m pip install -e ".[dev]"
ruff check .
pytest -q
```

### Frontend checks

```bash
cd web
npm install
npm run lint
npm run build
```

## Next milestone

**Milestone 2 — Identity, authorization and audit foundation:** OIDC integration design, user/organization/membership domain, patient-to-clinician relationship authorization, consent checks, PostgreSQL schema/migrations, and negative tests proving cross-patient access is denied. Use a test identity provider or deterministic test principal; do not introduce production credentials.
