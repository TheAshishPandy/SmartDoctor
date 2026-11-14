# SmartDoctor Development Guide

## 1. Current repository status

This repository currently contains the project license and architecture documentation. Application code, dependency manifests, migrations, tests and deployment files have not yet been added. The stack described in these documents is the proposed target.

## 2. Suggested implementation sequence

1. Create backend and frontend application skeletons.
2. Add configuration and secret management.
3. Add database migrations and identity integration.
4. Implement authorization policies and audit events.
5. Add patient/clinician domain modules.
6. Add conversation persistence and workflow orchestration.
7. Add model gateway and evaluation harness.
8. Add approved RAG ingestion and retrieval.
9. Add secure document pipeline.
10. Add clinician review and FHIR adapters.

## 3. Local development principles

- Use synthetic or properly de-identified data only.
- Keep local environment files out of version control.
- Never commit API keys, credentials, access tokens or real patient documents.
- Use pinned, reviewed dependencies and automated vulnerability scanning.
- Run database migrations explicitly.
- Keep model/provider configuration external to source code.
- Make local/cloud model routes explicit in configuration.
- Do not enable external cloud inference by default for sensitive data.

## 4. Proposed environment variables

Names only; values must be supplied through a secret manager or ignored local environment file.

```dotenv
APP_ENV=development
API_BASE_URL=http://localhost:8000
DATABASE_URL=
REDIS_URL=
QDRANT_URL=
OBJECT_STORAGE_ENDPOINT=
OBJECT_STORAGE_BUCKET=
OIDC_ISSUER_URL=
OIDC_CLIENT_ID=
OIDC_CLIENT_SECRET=
LOCAL_MODEL_BASE_URL=
LOCAL_MODEL_NAME=
CLOUD_MODEL_PROVIDER=
CLOUD_MODEL_ENDPOINT=
CLOUD_MODEL_API_KEY=
FHIR_BASE_URL=
FHIR_CLIENT_ID=
FHIR_CLIENT_SECRET=
```

Do not commit a populated `.env` file. Use a checked-in `.env.example` with empty or safe placeholder values only when implementation begins.

## 5. Proposed quality checks

- Formatting and linting.
- Static type checks.
- Unit tests for domain rules.
- Integration tests for database and API.
- Authorization tests including cross-patient denial.
- Workflow tests with deterministic model stubs.
- Prompt-injection and unsafe-output tests.
- FHIR contract tests against a sandbox.
- Dependency and container scanning.
- Secret scanning.
- Migration validation.

## 6. Branch and commit conventions

Suggested branches:
- `main`: protected, releasable baseline.
- `feature/<short-name>`: feature work.
- `fix/<short-name>`: defect fixes.
- `docs/<short-name>`: documentation-only work.

Suggested commit prefixes:
- `docs:` documentation
- `feat:` feature
- `fix:` bug fix
- `test:` tests
- `refactor:` internal refactor
- `chore:` tooling/dependencies
- `security:` security hardening

Keep changes focused and include tests and docs with implementation changes.

## 7. Pull request checklist

- [ ] Scope and intended use are clear.
- [ ] No secrets, PHI or real patient files are included.
- [ ] Authorization is enforced server-side.
- [ ] Audit and provenance are covered.
- [ ] Failure paths and safe fallbacks are tested.
- [ ] AI prompt/model/corpus versions are recorded.
- [ ] Clinical review is obtained where required.
- [ ] Tests, lint and security checks pass.
- [ ] Documentation is updated.

## 8. Operational runbooks to add before production

- Database backup and restore.
- Key/secret rotation.
- Patient data access incident.
- Suspected PHI disclosure.
- Model/provider outage.
- EHR/FHIR synchronization failure.
- Unsafe AI output or emergency escalation incident.
- Document malware or parser exploit.
- Data export/deletion request.
- Disaster recovery and business continuity.
