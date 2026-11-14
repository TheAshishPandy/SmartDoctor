# SmartDoctor — AI-Powered Healthcare Assistant

SmartDoctor is the documentation home for a planned healthcare platform serving **patients and clinicians**. The target architecture combines patient-facing conversational support, clinician workflows, patient-provided documents, authorized EHR/FHIR integrations, evidence-grounded medical information, and a hybrid local/cloud AI runtime.

> **Project status:** Architecture and product documentation baseline. This repository currently documents the proposed system; documentation does not imply that the described services, clinical capabilities, integrations, or controls have been implemented or validated.

## Product goals

- Give patients a safe, accessible way to understand health information and prepare for care.
- Give clinicians tools to review patient-authorized information and AI-generated drafts.
- Support both patient uploads and consented/authorized clinical-system integrations.
- Ground medical explanations in approved, traceable sources.
- Keep structured clinical records in authoritative systems; use retrieval indexes only as derived search aids.
- Use local inference where suitable and approved cloud inference only under explicit data-governance rules.
- Make safety, privacy, provenance, auditability, and clinician oversight foundational.

## Documentation map

| Document | Purpose |
|---|---|
| [Architecture](docs/architecture.md) | System boundaries, components, deployment and design decisions |
| [Workflows](docs/workflows.md) | Patient, EHR, report, clinician and escalation flows |
| [Agents](docs/agents.md) | LangGraph orchestration, agent responsibilities and state |
| [Data model](docs/data-model.md) | Domain entities, relationships and FHIR mapping |
| [API design](docs/api.md) | API conventions, endpoint catalogue and examples |
| [Security and privacy](docs/security.md) | Identity, authorization, consent, data protection and audit |
| [AI governance](docs/ai-governance.md) | Model routing, RAG, prompt controls, evaluations and clinical boundaries |
| [Roadmap](docs/roadmap.md) | Delivery phases, milestones and acceptance criteria |
| [Development guide](docs/development.md) | Local setup direction, repository conventions and contribution workflow |

## Target users

- **Patient:** manages their own profile, asks health-information questions, uploads records, views authorized results and requests follow-up.
- **Clinician:** accesses assigned/authorized patients, reviews source records and AI drafts, and records clinical decisions.
- **Organization administrator:** manages organization configuration and membership without implicit access to clinical content.
- **Platform operator/security auditor:** maintains infrastructure and investigates security events under controlled, audited access.

## Target technology

- Web: Next.js, React, TypeScript
- API: Python, FastAPI, Pydantic
- Workflow orchestration: LangGraph
- Primary data: PostgreSQL
- Semantic retrieval: Qdrant
- Cache/queue: Redis plus a durable message broker as needed
- Documents: encrypted object storage
- Local inference: Ollama for development; vLLM or equivalent for managed serving
- Cloud inference: approved provider through a model gateway
- Interoperability: HL7 FHIR R4 (profile and partner requirements to be confirmed)
- Observability: OpenTelemetry, metrics, traces and centralized security-safe logs

These are proposed choices, not dependencies already present in the repository.

## Important clinical boundary

SmartDoctor is initially scoped as a **health-information, care-navigation and clinician-support platform**, not an autonomous diagnostic or treatment system. It must not independently diagnose, prescribe, change treatment, or represent generated content as a clinician's decision. Emergency pathways must provide clear, location-appropriate instructions to seek immediate professional help and must not delay that advice with routine questioning.

Clinical use requires appropriate clinical governance, validation, legal/regulatory review, and approval for the intended jurisdiction and intended use.

## Start here

Read [Architecture](docs/architecture.md), then [Workflows](docs/workflows.md), [Agents](docs/agents.md), and [Security and privacy](docs/security.md). Implementation should follow the staged plan in [Roadmap](docs/roadmap.md).

## License

See [LICENSE](LICENSE).
