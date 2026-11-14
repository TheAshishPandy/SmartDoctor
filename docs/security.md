# SmartDoctor Security, Privacy and Compliance

## 1. Security objective

Health data is highly sensitive. Security and privacy controls must be designed, implemented, tested and monitored before real patient data is introduced. This document is a technical baseline, not legal advice or a compliance certification.

## 2. Identity and authentication

- Use a standards-based OIDC provider.
- Require MFA for clinicians, administrators and privileged operators.
- Use short-lived access tokens and secure refresh-token rotation.
- Validate issuer, audience, signature, expiry and scopes.
- Use secure, HttpOnly, SameSite cookies where applicable.
- Support session revocation and device/session management.
- Use workload identity or short-lived credentials for service-to-service calls.

## 3. Authorization

Use RBAC for broad role assignment and ABAC/resource policies for patient, organization, purpose, relationship and consent scope.

Every request must validate:
- Authenticated actor.
- Active account and role.
- Organization membership.
- Patient-to-clinician relationship or patient self-access.
- Resource ownership and sensitivity.
- Purpose of use and applicable consent.
- Operation permission (read, create, amend, sign, export).

Do not rely on frontend hiding, vector filters or a user-supplied patient ID. Platform administrators do not receive automatic clinical-record access.

## 4. Consent and purpose limitation

Record consent with patient, purpose, recipient/system, scope, status, effective period, source, version and withdrawal history. Consent must be understandable and specific enough for the intended data use. Check consent at access time, not only when a connection is first created.

Revocation should stop future processing under the revoked permission and trigger defined downstream actions. Retention, legal holds and required clinical records must follow jurisdiction-specific policy.

## 5. Data protection

| Data state | Control |
|---|---|
| In transit | TLS 1.2+ (prefer current secure TLS configuration) |
| At rest | Strong encryption with managed keys |
| Backups | Encryption, access restrictions and restore tests |
| Object storage | Private buckets, short-lived URLs, malware scanning |
| Database | Network isolation, least privilege and encrypted backups |
| Secrets | Managed secret store; no secrets in Git |
| Local development | Synthetic/de-identified data only |
| Logs | Redaction, minimal metadata and restricted access |

Classify data (public, internal, confidential, restricted/PHI) and attach handling policies to each classification.

## 6. AI and external provider privacy

- Maintain an allowlist of model providers, regions and deployments.
- Record provider retention, training, subprocessors and contractual terms.
- Block PHI from unapproved endpoints.
- Minimize or de-identify input when possible and validated.
- Apply policy checks before local and cloud model routing.
- Do not use patient conversations for model training without an appropriate legal basis, notice and consent where required.
- Prevent prompt, trace and exception logs from storing raw clinical content.
- Review provider changes and model updates before enabling them.

A local model is not automatically secure; secure the host, weights, runtime, network, logs and access controls.

## 7. Upload and document security

- Enforce extension, MIME, magic-byte, size and page-count limits.
- Quarantine files until malware scanning succeeds.
- Use isolated parsers/OCR workers with restricted network access.
- Protect against archive bombs, malformed PDFs and parser exploits.
- Treat extracted text as untrusted input.
- Prevent document instructions from altering agent behavior.
- Store original checksums and immutable versions.
- Use short-lived, authorized download links.

## 8. Audit and monitoring

Capture:
- Actor/service identity.
- Action and purpose.
- Patient/resource reference.
- Organization scope.
- Timestamp and correlation ID.
- Result and denial reason category.
- Source system and version where relevant.
- AI model, prompt and workflow version for AI runs.

Use tamper-evident or immutable audit storage where required. Restrict audit access and avoid copying clinical content into audit events.

## 9. Threat model

| Threat | Mitigation |
|---|---|
| Cross-patient data leakage | Resource authorization, tenant isolation and negative tests |
| Stolen clinician account | MFA, session controls, risk-based monitoring |
| Prompt injection in PDF/RAG | Treat retrieved text as untrusted; tool allowlists |
| Malicious upload | Quarantine, scanning and sandboxed parsers |
| Cloud model data leakage | Provider allowlist, data policy gateway and minimization |
| EHR token compromise | Scoped short-lived tokens and secret vault |
| Insecure direct object reference | Server-side authorization on every resource |
| Ransomware/data loss | Immutable backups and tested recovery |
| Insider misuse | Least privilege, audit, alerts and break-glass controls |
| Model hallucination | Evidence grounding, validation, clinician oversight and evaluation |

## 10. Break-glass access

If emergency access is required, implement a documented break-glass process with strong authentication, reason capture, limited duration/scope, prominent warnings, immediate audit and retrospective review. Do not create a hidden administrator bypass.

## 11. Compliance workstream

Before production, identify the operating jurisdictions, controller/processor roles, covered entities, data flows, hosting regions and intended clinical use. Obtain qualified legal and clinical review for applicable requirements, which may include:
- HIPAA and related rules for applicable US entities.
- Applicable Indian DPDP requirements and ABDM ecosystem requirements.
- GDPR and national health-data laws where applicable.
- Medical-device/software regulations if intended functionality falls within scope.
- Contractual, professional licensing, records-retention and breach-notification requirements.

Complete a data protection impact/risk assessment where required, vendor agreements, incident response plan, access reviews, retention schedule and evidence of control testing. Do not claim certification until independently assessed.
