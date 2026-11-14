# SmartDoctor Delivery Roadmap

## 1. Delivery strategy

Deliver in increments. Security, privacy, safety and evaluation are cross-cutting workstreams and start in Phase 0. Do not introduce real patient data until access control, audit, retention, incident response and vendor review are ready.

## 2. Phases

### Phase 0 — Product, clinical and regulatory discovery
Deliverables:
- Intended-use statement and explicit exclusions.
- Target jurisdictions and regulatory assessment.
- Patient/clinician user journeys.
- Clinical safety owner and review process.
- Data inventory, data-flow map and threat model.
- EHR partner/FHIR version and implementation-guide discovery.
- Approved initial knowledge-source list.
Acceptance:
- Product, clinical, privacy and security stakeholders approve the scope.
- No unresolved critical safety or data-flow assumptions.

### Phase 1 — Platform foundation
Deliverables:
- Repository and modular FastAPI/Next.js structure.
- OIDC authentication and MFA integration.
- Patient, practitioner, organization and membership models.
- Resource-level authorization and consent framework.
- PostgreSQL migrations and audit events.
- Docker development environment and CI checks.
Acceptance:
- Automated tests prove patient A cannot access patient B.
- Privileged actions are audited.
- No secrets or PHI appear in logs or Git.

### Phase 2 — Safe conversational MVP
Deliverables:
- Conversation APIs and UI.
- Language detection and intent classification.
- LangGraph workflow state and persistence.
- Independent safety screening and safe fallback.
- Model gateway with local inference.
- Cloud route disabled until provider/privacy approval.
Acceptance:
- Correct workflow routing on an adjudicated test set.
- Emergency tests trigger the approved safe pathway.
- Model failure does not bypass safety or privacy controls.

### Phase 3 — Medical knowledge RAG
Deliverables:
- Approved source registry and ingestion pipeline.
- Qdrant collections and metadata filters.
- Hybrid retrieval and reranking.
- Citation rendering and evidence trace.
- Corpus review/expiry process.
Acceptance:
- Every factual citation resolves to a stored approved source.
- Unauthorized patient content is not returned.
- Stale/unapproved sources are excluded.

### Phase 4 — Patient profile and document analysis
Deliverables:
- Patient timeline and authorized record views.
- Secure upload and quarantine.
- OCR and structured extraction.
- Lab report validation and uncertainty flags.
- Patient-friendly explanations.
Acceptance:
- Original files and exact source values are preserved.
- Low-confidence or mismatched documents are blocked from automated interpretation.
- Extraction quality is measured on representative reports.

### Phase 5 — Clinician portal and review
Deliverables:
- Clinician dashboard and assigned-patient access.
- Source-linked AI summaries.
- Review, edit and reject workflow.
- Clinician identity and approval audit.
- Handoff queue.
Acceptance:
- AI drafts are never presented as signed clinical records.
- Only authorized clinicians can approve.
- Source data is visible beside generated summaries.

### Phase 6 — FHIR/EHR and laboratory integrations
Deliverables:
- Partner onboarding and capability discovery.
- Scoped authorization and patient identity mapping.
- Resource validation and synchronization.
- Idempotency, retries and reconciliation.
- Integration health and stale-data indicators.
Acceptance:
- Partner test environment passes contract tests.
- Duplicate and ambiguous patient matching is safely handled.
- Consent revocation blocks subsequent unauthorized access.

### Phase 7 — Production hardening and controlled pilot
Deliverables:
- Independent security testing and remediation.
- Clinical evaluation and governance approval.
- Load, resilience and disaster-recovery testing.
- Monitoring, alerting and incident response.
- Vendor and regulatory review.
- Controlled pilot with trained users.
Acceptance:
- All critical/high findings are resolved or formally risk-accepted.
- Clinical acceptance criteria are met.
- Recovery and incident exercises pass.
- Production approval is documented.

## 3. MVP boundary

Recommended first MVP:
1. Secure patient sign-in.
2. Patient/doctor role separation.
3. Medical-information chat with safe limitations.
4. Approved medical knowledge RAG.
5. Patient upload of PDF/image reports.
6. Basic OCR extraction with explicit uncertainty.
7. Patient history and provenance.
8. Clinician review of AI-generated summaries.

Defer direct EHR write-back, prescribing, diagnosis and autonomous triage.

## 4. Workstreams

| Workstream | Owner role |
|---|---|
| Product and UX | Product owner / designer |
| Backend and data | Backend engineer |
| AI and RAG | AI/ML engineer |
| Frontend | Frontend engineer |
| Integration | FHIR/integration engineer |
| Clinical safety | Clinical lead |
| Privacy and compliance | Privacy/legal lead |
| Security and operations | Security/platform engineer |
| Validation | QA + clinical evaluators |

A small team may cover multiple roles, but clinical, privacy and security approvals must remain explicit.

## 5. Definition of done

A feature is not complete until:
- Requirements and intended use are documented.
- API and data contracts are reviewed.
- Authorization and negative-access tests pass.
- Audit and provenance are implemented.
- Failure and safe-fallback behavior is tested.
- AI features have versioned evaluation evidence.
- Documentation and runbooks are updated.
- Privacy/security review is complete.
- Clinical review is completed when the feature may affect care.
