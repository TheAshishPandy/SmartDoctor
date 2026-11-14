# SmartDoctor API Design

## 1. Conventions

- Base path: `/api/v1`.
- JSON request/response by default; multipart for uploads.
- OAuth 2.0 / OIDC bearer tokens; MFA for clinician and privileged roles.
- Derive actor identity from the validated token.
- Never trust patient_id, organization_id or role claims supplied only in request bodies.
- Use explicit authorization on every resource access.
- Use cursor pagination for large collections.
- Use UTC ISO-8601 timestamps.
- Return stable error codes and correlation IDs.
- Require idempotency keys for operations that may be retried.
- Version schemas and document breaking changes.

## 2. Authentication and identity

| Method | Path | Purpose |
|---|---|---|
| POST | /auth/register | Patient registration, if locally managed |
| POST | /auth/login | Login or identity-provider redirect initiation |
| POST | /auth/refresh | Refresh session where supported |
| POST | /auth/logout | Revoke session |
| POST | /auth/mfa/verify | Complete MFA challenge |
| GET | /users/me | Current principal and allowed roles |

Prefer a standards-based identity provider rather than implementing password handling from scratch.

## 3. Patient APIs

| Method | Path | Purpose |
|---|---|---|
| GET | /patients/me | Own patient profile |
| PATCH | /patients/me | Update permitted profile fields |
| GET | /patients/me/timeline | Authorized clinical timeline |
| GET | /patients/me/conditions | Conditions |
| GET | /patients/me/allergies | Allergies |
| GET | /patients/me/medications | Medication statements and requests |
| GET | /patients/me/observations | Vital signs and observations |
| GET | /patients/me/encounters | Encounters |

## 4. Conversation APIs

| Method | Path | Purpose |
|---|---|---|
| POST | /conversations | Create conversation |
| GET | /conversations | List current user's conversations |
| GET | /conversations/{conversation_id} | Read authorized conversation |
| POST | /conversations/{conversation_id}/messages | Submit message |
| GET | /conversations/{conversation_id}/messages | List messages |
| POST | /conversations/{conversation_id}/feedback | Submit feedback |

For long-running workflows, return a workflow/run ID and expose status or a server-sent event stream. Do not keep an HTTP request open for lengthy OCR or EHR synchronization.

## 5. Document and report APIs

| Method | Path | Purpose |
|---|---|---|
| POST | /documents | Upload document |
| GET | /documents | List authorized documents |
| GET | /documents/{document_id} | Document metadata |
| POST | /documents/{document_id}/analyze | Start extraction workflow |
| GET | /documents/{document_id}/analysis | Get extraction status/results |
| GET | /reports/{report_id} | Read authorized report |
| GET | /reports/{report_id}/results | Read validated result values |

Use signed, short-lived upload/download URLs where appropriate. Validate file size, type, content signature, malware scan status and patient ownership.

## 6. Clinician APIs

| Method | Path | Purpose |
|---|---|---|
| GET | /clinician/dashboard | Authorized workload |
| GET | /clinician/patients | Assigned/authorized patients |
| GET | /clinician/patients/{patient_id} | Patient overview |
| GET | /clinician/patients/{patient_id}/timeline | Clinical timeline |
| GET | /clinician/reviews | Pending AI drafts |
| GET | /clinician/reviews/{review_id} | Review details and evidence |
| POST | /clinician/reviews/{review_id}/decision | Approve, edit or reject draft |
| POST | /clinician/encounters | Create encounter |
| POST | /clinician/handoffs/{handoff_id}/assign | Assign authorized handoff |

Clinical writes require a separate permission check, clinician identity, audit event and idempotency protection.

## 7. Consent and privacy APIs

| Method | Path | Purpose |
|---|---|---|
| GET | /consents | List consent records |
| POST | /consents | Record consent |
| POST | /consents/{consent_id}/revoke | Revoke consent |
| GET | /privacy/access-history | User-visible access history where supported |
| POST | /privacy/export | Request data export |
| POST | /privacy/deletion-request | Start deletion request workflow |

Deletion and retention must account for applicable law, clinical record obligations, backups and downstream processors. Do not promise immediate deletion where retention is legally required.

## 8. Integration APIs

| Method | Path | Purpose |
|---|---|---|
| POST | /integrations | Register approved external system |
| POST | /integrations/{id}/sync | Trigger authorized sync |
| GET | /integrations/{id}/status | Sync status |
| GET | /integrations/{id}/resources | Resource mapping/sync status |
| POST | /integrations/{id}/webhooks | Validate partner event, if supported |

Do not expose partner credentials or unrestricted FHIR proxy endpoints to browsers.

## 9. Example chat request

```json
{
  "message": "I have had a headache since yesterday.",
  "language_hint": "en",
  "conversation_id": "optional-existing-id"
}
```

The server derives the authenticated patient and permitted context. A client language hint is advisory; the system can detect language from the message.

## 10. Example asynchronous response

```json
{
  "conversation_id": "conv_example",
  "run_id": "run_example",
  "status": "awaiting_patient",
  "message": {
    "role": "assistant",
    "content": "I can help you understand this. When did the headache begin, and how severe is it?"
  },
  "safety": {
    "status": "routine_path",
    "flags": []
  },
  "citations": []
}
```

Values are illustrative. A real implementation must not expose internal safety thresholds or sensitive rule details to untrusted clients.

## 11. Error response

```json
{
  "error": {
    "code": "RESOURCE_ACCESS_DENIED",
    "message": "This resource is not available to the current account.",
    "correlation_id": "req_example"
  }
}
```

Avoid revealing whether another patient's record exists.

## 12. API security checklist

- Validate JWT issuer, audience, signature, expiry and scopes.
- Enforce resource-level authorization server-side.
- Prevent insecure direct object references.
- Rate-limit authentication, chat and upload endpoints.
- Validate request schemas and payload size.
- Protect against replay and duplicate writes.
- Apply CSRF protections where cookie-based sessions are used.
- Restrict CORS to known origins.
- Validate webhook signatures and timestamps.
- Avoid PHI in URLs, query strings and logs.
