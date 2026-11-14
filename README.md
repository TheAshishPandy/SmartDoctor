# SmartDoctor — AI-Powered Healthcare Assistant

SmartDoctor is a healthcare platform in active foundation development for **patients and clinicians**. The planned system combines patient-facing health-information support, clinician workflows, patient-provided documents, authorized EHR/FHIR integrations, evidence-grounded medical information and a hybrid local/cloud AI runtime.

> **Current status:** Milestone 1 foundation code has been added. Backend smoke tests pass locally. Frontend build/lint, Docker startup and hosted CI remain pending verification. No clinical workflow or patient-data processing is implemented. Do not use real patient data.

## Current implementation

| Component | Status |
|---|---|
| FastAPI API skeleton and `/health` | Implemented; 2 smoke tests pass locally |
| Next.js/React/TypeScript shell | Implemented; build/lint pending CI |
| PostgreSQL and Redis Compose services | Configuration added; Docker startup not yet verified |
| GitHub Actions CI | Added; first hosted run pending |
| Authentication, authorization and consent | Not implemented — next milestone |
| Medical chat, agents, RAG, uploads and FHIR | Not implemented |

See [Milestone tracker](docs/milestones.md) for acceptance evidence and remaining checks.

## Product goals

- Help patients understand health information and prepare for care.
- Help clinicians review patient-authorized information and AI-generated drafts.
- Support patient uploads and consented/authorized clinical-system integrations.
- Ground medical explanations in approved, traceable sources.
- Keep structured clinical records in authoritative systems.
- Use local inference where suitable and approved cloud inference only under explicit data-governance rules.
- Make safety, privacy, provenance, auditability and clinician oversight foundational.

## Documentation

See [Architecture](docs/architecture.md), [Workflows](docs/workflows.md), [Agents](docs/agents.md), [Data model](docs/data-model.md), [API design](docs/api.md), [Security](docs/security.md), [AI governance](docs/ai-governance.md), [Roadmap](docs/roadmap.md), [Milestones](docs/milestones.md) and [Development guide](docs/development.md).

## Target technology

- Web: Next.js, React, TypeScript
- API: Python, FastAPI, Pydantic
- Workflow orchestration: LangGraph
- Primary data: PostgreSQL; retrieval: Qdrant; cache: Redis
- Documents: encrypted object storage
- Local inference: Ollama for development; managed local inference for deployment
- Cloud inference: approved provider through a model gateway
- Interoperability: HL7 FHIR R4, subject to partner profile validation

## Clinical safety boundary

SmartDoctor is scoped as a **health-information, care-navigation and clinician-support platform**, not an autonomous diagnostic or treatment system. It must not independently diagnose, prescribe, change treatment or represent generated content as a clinician's decision. Emergency pathways must not delay immediate professional help with routine questioning.

Clinical use requires appropriate clinical governance, validation, legal/regulatory review and approval for the intended jurisdiction and intended use.

## Run locally

```bash
cp .env.example .env
docker compose up --build
```

- Web: http://localhost:3000
- API health: http://localhost:8000/health
- API docs: http://localhost:8000/docs

Use synthetic data only. Compose credentials are development-only and must never be exposed publicly.

## License

See [LICENSE](LICENSE).
