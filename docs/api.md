# API Design

## Conventions
- JSON REST API under `/api/v1`.
- OIDC bearer access token on protected endpoints.
- Validate signature, issuer, audience, expiry and subject before using claims.
- Use signed token `sub`; never accept identity from request body or custom headers.
- UUID identifiers and explicit Pydantic response schemas.
- 401 for missing/invalid credentials; 503 when OIDC configuration is absent; 404 for unknown or unauthorized patient resources.
- `X-Correlation-ID` is recorded for traceability; validate it at the production gateway.
- Avoid leaking authorization details in responses.

## Implemented endpoints

| Method | Path | Authentication | Purpose |
|---|---|---|---|
| GET | `/health` | Public | Process health |
| GET | `/api/v1/patients/{patient_id}` | OIDC bearer | Read own profile or clinician-authorized profile |

A patient owner needs signed role `patient` and matching subject. A clinician needs signed role `clinician`, active organization membership, active care relationship in that organization and active `patient.read` consent. Checks are repeated on every read.

The response exposes only patient UUID, display label and creation time, not internal ownership or consent metadata.

## Planned endpoints
- Patient provisioning and identity linking.
- Consent grant and revocation workflows with audit.
- Authorized document metadata and upload initiation.
- Patient/clinician conversation APIs.
- Administrator-controlled FHIR connection setup.
- Separately privileged audit-event access.

Every new endpoint must reuse resource-level authorization, consent, explicit schemas, rate limits and audit. Never return unrestricted ORM objects.
