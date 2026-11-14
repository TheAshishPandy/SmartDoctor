# Security and Privacy

SmartDoctor processes highly sensitive health information. The current repository is a development foundation, not a production-ready or certified medical system. Use synthetic data only.

## Identity
- Delegate credential lifecycle, MFA, recovery and identity proofing to a selected OIDC provider.
- Validate access-token signature with RS256 and provider JWKS; require issuer, audience, expiry, issued-at and subject.
- Use signed token `sub` as stable external identity. Never trust client-supplied identity headers.
- Configure `OIDC_ISSUER`, `OIDC_AUDIENCE` and `OIDC_JWKS_URL`.
- Current code reads a signed `roles` array and optional `organization_id`; map claims to the provider's actual access-token contract before deployment.

## Authorization
Patient profile reads are default-deny:
1. Patients may read only profiles where `owner_sub` matches their verified token subject.
2. Clinicians require active membership in the patient's organization.
3. Clinicians require an active care relationship with that patient in the same organization.
4. Clinicians require active, unrevoked, unexpired `patient.read` consent granted to their subject.
5. Organization membership or administrator/support roles alone never grant access.

Checks run on each read. Unknown and unauthorized patient IDs both return 404. Apply equivalent resource-level policies to every future document, conversation, export and integration endpoint.

## Consent
Consent is scoped to patient, grantee and permission. Revocation and expiry are checked at request time. Grant/revocation APIs, identity verification for consent, legal basis, purpose-of-use, retention and jurisdiction-specific consent language remain to be implemented and reviewed.

## Audit
Patient read authorization decisions create events containing actor, role, action, resource, outcome, correlation ID and timestamp. Do not log clinical text, tokens, documents or credentials. The current audit table is not tamper-proof; production needs restricted access, retention policy, monitoring, protected immutable export and incident response.

## Data protection
- TLS in transit and managed encryption at rest.
- Managed secret store; no credentials in source control.
- Least-privilege database roles and network segmentation.
- Data minimization, retention/deletion and backup/restore controls.
- No patient data to AI providers until data residency, retention, training use, contract and security are approved.
- Uploads need size/type validation, malware scanning and isolated storage before parsing.

## Required before production
Threat model, privacy impact assessment, jurisdiction-specific legal/regulatory review, clinical governance, provider configuration, MFA policy, security testing, vulnerability management, incident response, disaster recovery and independent penetration testing. Do not claim HIPAA, GDPR or other compliance based only on these controls.
