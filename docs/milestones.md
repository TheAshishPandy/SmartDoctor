# SmartDoctor Milestone Tracker

Milestones are marked **Complete** only after all acceptance criteria pass in CI and required environment checks are evidenced. A commit alone does not make a milestone complete.

## Milestone 1 — Platform foundation

**Status: In progress — implementation committed; full Docker and CI verification pending.**

Backend smoke tests passed locally (2 tests). Initial CI was started; consult its run history for final status. Frontend build/lint and Docker startup still require verification. See [foundation commit](https://github.com/TheAshishPandy/SmartDoctor/commit/e5e2afacd1fcd5e0eb05a8ed78bae02c3a76668a).

## Milestone 2 — Identity, authorization and audit foundation

**Status: In progress — implementation and security tests added; CI, PostgreSQL migration and live OIDC verification pending.**

### Design decisions
- A trusted OIDC provider owns credentials, MFA and identity proofing. The API validates RS256 tokens against provider JWKS, issuer and audience.
- The signed token `sub` is the external identity. Roles are read from a signed `roles` array; never accept identity or role headers from clients.
- A patient can read only their own profile.
- A clinician requires active organization membership, active patient-care relationship in the same organization, and active, unrevoked, unexpired `patient.read` consent.
- Organization membership or an administrator role alone never grants patient-record access.
- Missing/invalid credentials return 401; absent identity-provider configuration returns 503. Unknown and unauthorized patient IDs both return 404.
- Existing-patient read decisions create audit events containing actor, role, action, resource, outcome, correlation ID and timestamp, but no clinical content.
- Consent and relationships are checked on every protected read; no authorization cache is used.

### Implementation delivered
- SQLAlchemy models for organizations, memberships, patients, care relationships, consent grants and audit events.
- Alembic initial migration.
- OIDC RS256/JWKS bearer-token validation boundary.
- Protected patient profile read endpoint.
- Default-deny owner/clinician authorization policy.
- SQLite-backed tests for owner access, cross-patient denial, clinician positive access, revoked/expired consent, missing relationship, unknown role and missing bearer token.

### Acceptance criteria

| Criterion | Status | Evidence / remaining work |
|---|---|---|
| Schema and indexes | Implemented | SQLAlchemy models and Alembic revision |
| OIDC token verification | Implemented; provider not configured | RS256, JWKS, issuer, audience, required claims |
| Patient ownership | Test added | Owner can read own profile |
| Clinician access | Test added | Membership + relationship + consent |
| Cross-patient isolation | Test added | Non-owner receives 404 and denied audit |
| Consent revocation/expiry | Tests added | Both deny clinician access |
| Audit trail | Tests added | Allowed and denied reads recorded |
| Ruff and complete backend tests | Pending | Must pass CI |
| PostgreSQL migration | Pending | Requires Docker/PostgreSQL verification |
| Live OIDC integration | Pending | Requires selected provider configuration |
| Security review | Pending | Required before production |

### Run locally

```bash
cd backend
python -m pip install -e ".[dev]"
alembic upgrade head
ruff check .
pytest -q
```

Compose runs `alembic upgrade head` before starting the development API. The production deployment must run migrations as a controlled one-off deployment job, not independently from every replica.

### Implemented API

`GET /api/v1/patients/{patient_id}` requires an OIDC bearer access token. The token must be issued by the configured provider and contain a signed `sub` and `roles` array. Clinicians additionally require database-backed membership, relationship and consent. Tests override the principal dependency; do not use fabricated tokens outside tests.

### Not production-ready
The OIDC provider has not been selected/configured. User provisioning, MFA enrollment policy, consent grant/revocation endpoints, organization administration, audit retention/immutability, backup, threat modelling and independent security review remain outstanding. The audit table is not a tamper-proof compliance archive. Use synthetic data only.

## Next milestone

**Milestone 3 — Patient record ingestion and provenance:** secure upload initiation, file type/size validation, malware-scanning boundary, encrypted object storage, document metadata, extraction lifecycle, source provenance and patient-controlled record linking. Direct EHR/FHIR connectors will be separately authorized and partner-profile tested.
