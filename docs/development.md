# SmartDoctor Development Guide

## 1. Repository status

The repository now contains the first implementation skeleton: a FastAPI backend, a Next.js frontend shell, Docker Compose services, a backend smoke-test suite and GitHub Actions CI. Authentication, database persistence, clinical workflows and AI capabilities are not implemented yet. Track verified progress in [milestones.md](milestones.md).

## 2. Local prerequisites

- Docker Engine with Docker Compose v2.
- Python 3.12 or 3.13 for backend development.
- Node.js 22 and npm for frontend development.
- Git.

## 3. Start the complete development stack

```bash
cp .env.example .env
docker compose up --build
```

Endpoints:
- Web: `http://localhost:3000`
- API health: `http://localhost:8000/health`
- API OpenAPI: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

The API health endpoint currently confirms process availability only; it is not a database or dependency readiness check. PostgreSQL and Redis have Compose health checks. The frontend container installs npm dependencies on first start.

## 4. Backend development and tests

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[dev]"
ruff check .
pytest -q
```

The current smoke tests cover the health response and OpenAPI availability. Add unit and integration tests alongside each new feature.

## 5. Frontend development and checks

```bash
cd web
npm install
npm run dev
npm run lint
npm run build
```

## 6. Environment and secrets

- `.env.example` contains development-only placeholders; copy it to `.env` locally.
- `.env` and populated environment files are ignored by Git.
- Never commit API keys, credentials, access tokens or real patient documents.
- Use synthetic or properly de-identified data only.
- Production secrets must come from a managed secret store, not Compose or source files.
- Do not enable external cloud inference for sensitive data until provider, region, retention and contractual controls are approved.

## 7. Current limitations

- PostgreSQL and Redis containers are provisioned, but the API does not connect to them yet.
- There is no ORM, schema migration, identity provider, authentication, authorization or consent enforcement yet.
- `/health` is a process health check, not a full dependency readiness check.
- The UI is a static foundation page, not a patient portal or clinical tool.
- No real patient data may be used.

## 8. Quality checks

CI runs backend Ruff lint and pytest, plus frontend ESLint and Next.js production build. Add checks for database migrations, authorization, security scanning, dependency auditing and container scanning as those capabilities are introduced.

## 9. Branch and commit conventions

- `main`: releasable baseline.
- `feature/<short-name>`: feature work.
- `fix/<short-name>`: defect fixes.
- `docs/<short-name>`: documentation-only work.

Commit prefixes: `feat:`, `fix:`, `test:`, `refactor:`, `chore:`, `security:` and `docs:`. Keep changes focused and include tests and documentation.

## 10. Before production

Complete identity and access controls, consent, audit, data retention, backup/restore, key rotation, incident response, threat modelling, clinical validation, privacy/legal review and independent security testing. The current foundation is not production-ready.
