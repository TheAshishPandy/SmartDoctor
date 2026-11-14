# SmartDoctor System Architecture

## 1. Purpose and scope

This document defines the proposed architecture for a multi-user healthcare platform with patient and clinician experiences. It is a target design, not a statement that the system is already implemented.

### In scope
- Patient and clinician portals.
- Secure identity, role and organization management.
- Patient-reported information and document uploads.
- Authorized hospital/EHR integration through FHIR or partner APIs.
- Medical-information chat with evidence retrieval.
- Structured report extraction and patient-friendly explanation.
- Clinician review and approval of AI-generated drafts.
- Hybrid local/cloud model execution with data-classification controls.
- Auditing, consent, provenance and evaluation.

### Out of scope for the initial release
- Autonomous diagnosis or treatment decisions.
- Autonomous prescribing or prescription modification.
- Unsupervised clinical triage as a substitute for emergency services.
- Replacing an EHR or a clinician's signed record.
- Unreviewed write-back of AI-generated content to a clinical system.

## 2. Architecture principles

1. **Safety before completion:** emergency screening and safe fallback must not depend on successful LLM execution.
2. **Human clinical authority:** AI outputs are drafts or educational explanations; clinicians retain responsibility for clinical decisions.
3. **Source of truth:** the EHR or validated structured clinical store is authoritative. Vector indexes are derived and rebuildable.
4. **Least privilege:** every patient resource read/write is checked against actor, patient, organization, purpose and consent.
5. **Provenance:** preserve who supplied a fact, where it came from, when it was recorded, verification status and source identifier.
6. **Privacy by design:** minimize PHI, isolate tenants, encrypt data, and prevent unapproved model providers from receiving sensitive data.
7. **Modular delivery:** begin with a modular monolith and workers; split services only when operational boundaries justify it.
8. **Observable and testable:** model, prompt, retrieval, rules and data versions must be traceable.
9. **Interoperability:** map to a defined FHIR version/profile and partner contracts.
10. **Accessible and multilingual:** support clear language, accessibility and language-aware clinical terminology.

## 3. Logical components

```text
Patient Web / Mobile              Clinician Web
        |                               |
        +---------------+---------------+
                        |
                Edge / API Gateway
                        |
          OIDC Authentication + MFA
                        |
                 FastAPI Application
                        |
       +----------------+-------------------+
       |                |                   |
 Identity & Access   Patient Domain     Clinical Domain
       |                |                   |
       +----------------+-------------------+
                        |
                 Workflow Service
                    LangGraph
                        |
       +----------------+-------------------+
       |                |                   |
 Safety / Rules     Agent Workflows      Human Review
       |                |                   |
       +----------------+-------------------+
                        |
                  Model Gateway
                  /           \
          Local Inference   Approved Cloud
                        |
       +----------------+-------------------+
       |                |                   |
   PostgreSQL         Qdrant          Object Storage
       |                |                   |
       +----------------+-------------------+
                        |
               Integration Adapters
                        |
           EHR / FHIR / Labs / Scheduling
```

### Component responsibilities

| Component | Responsibility |
|---|---|
| Web applications | Patient and clinician user experiences |
| API gateway | TLS termination, routing, request limits and edge protection |
| Identity provider | OIDC login, MFA, session and token lifecycle |
| FastAPI modules | Domain APIs, validation and authorization enforcement |
| Workflow service | Durable conversation and document workflows |
| Safety service | Deterministic emergency checks, policy checks and safe fallbacks |
| Model gateway | Model registry, policy-based routing, privacy checks and telemetry |
| RAG service | Approved knowledge ingestion, retrieval, reranking and citations |
| PostgreSQL | Structured transactional data and audit metadata |
| Qdrant | Derived embeddings for approved knowledge/document search |
| Object storage | Encrypted original uploads and generated artifacts |
| Integration adapters | FHIR and partner-specific system connectivity |
| Worker processes | OCR, ingestion, synchronization, notifications and scheduled jobs |

## 4. Recommended deployment topology

### Initial development
Use Docker Compose for API, worker, PostgreSQL, Redis, Qdrant, local model runtime and object-storage emulator. Keep secrets in local environment files excluded from Git.

### Production
Use private networking, managed or hardened PostgreSQL, encrypted object storage, managed secrets, workload identity, controlled inference endpoints, queue workers, centralized monitoring and tested backups. Kubernetes is optional; do not introduce it until availability, scale or team operations require it.

## 5. Data boundaries

- PostgreSQL stores normalized patient, consent, encounter, observation, document metadata, conversation and audit records.
- Object storage stores original files and approved derived artifacts.
- Qdrant stores only approved, access-scoped derived chunks with source IDs and metadata.
- Redis stores ephemeral cache/session/queue data only; do not treat it as a medical source of truth.
- Model providers receive only the minimum data needed for an authorized task.
- Logs and traces must not contain raw PHI, full prompts with patient data, tokens or uploaded document content.

## 6. Trust boundaries

1. Browser/mobile to edge gateway.
2. API to identity provider.
3. Application to database and object storage.
4. Application to local model runtime.
5. Application to external cloud model provider.
6. Integration adapter to hospital/EHR/lab systems.
7. Ingestion pipeline to untrusted uploaded files and retrieved content.
8. AI workflow to clinician approval and any external write-back.

Treat uploaded documents, retrieved web pages, OCR text and FHIR narrative fields as untrusted data. They may contain malicious instructions; never interpret their contents as agent instructions.

## 7. Proposed repository/service boundaries

Start as a modular monolith with these internal modules:
- identity, organizations, patients, clinicians, consent
- records, encounters, observations, medications, allergies
- documents, reports, extraction
- conversations, workflows, AI runs, evidence
- FHIR integration, external systems, synchronization
- safety, audit, notifications

Run long-running or CPU/GPU-intensive work in separate workers. Preserve explicit module interfaces so components can be extracted later.

## 8. Key architecture decisions

| Decision | Initial choice | Rationale |
|---|---|---|
| Backend style | Modular monolith | Faster MVP and simpler transactions |
| API | FastAPI | Typed Python API and async integration |
| Orchestration | LangGraph | Stateful, inspectable workflow routing |
| Primary database | PostgreSQL | Transactional source of truth |
| Vector store | Qdrant | Derived semantic retrieval |
| File storage | Encrypted object storage | Separate large binary content from records |
| Model runtime | Hybrid gateway | Route by task, privacy and approved capability |
| Interoperability | FHIR adapter | Standard resource exchange with partner profiles |
| Clinical write-back | Disabled by default | Requires explicit clinician approval and partner authorization |

## 9. Quality attributes

Define measurable service-level objectives before production. Candidate dimensions include availability, p95 API latency, workflow completion time, document processing throughput, recovery point/time objectives, emergency-screening sensitivity, extraction accuracy, unauthorized-access rate and evidence citation correctness. Clinical thresholds must be approved by clinical governance; do not invent universal thresholds.
