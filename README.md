# SmartDoctor

SmartDoctor is a development healthcare information workspace with patient-scoped document ingestion and evidence-grounded retrieval. It is **not** a diagnostic, prescribing or treatment system.

## Technology

- **Next.js + React + TypeScript**: patient document and chat workspace.
- **FastAPI**: upload, ingestion, retrieval and chat APIs.
- **PostgreSQL**: patient identity, organization ownership, authorization audit and document metadata.
- **MongoDB**: owner-scoped chat conversations and messages.
- **Qdrant**: patient- and organization-filtered embeddings and document chunks.
- **FastEmbed**: local CPU embeddings (384-dimensional BGE small English model).
- **Redis**: reserved for cache/short-lived coordination.
- **Local Docker volume**: original uploaded files in development.

## Run the complete local demo

Requirements: Docker Desktop with Compose and at least 6 GB available memory. First embedding model use downloads model weights.

```bash
cp .env.example .env
docker compose up --build
```

Open:
- Web workspace: http://localhost:3000
- API health: http://localhost:8000/health
- API docs: http://localhost:8000/docs

Compose enables an **opt-in development-only demo identity** so the synthetic patient workspace can be tested without configuring OIDC. It is enabled only in the local Compose service and the backend refuses demo identity unless APP_ENV=development. Do not expose this setup publicly.

## Try the end-to-end flow

1. Open the web workspace. It creates/reuses a synthetic demo patient in PostgreSQL.
2. Upload a PDF, DOCX, TXT or Markdown file (20 MB maximum).
3. The API extracts text, chunks it with overlap, generates local embeddings and indexes chunks in Qdrant.
4. Ask a question about the uploaded document.
5. The API authorizes patient access through PostgreSQL, retrieves only that patient's chunks from Qdrant, stores messages in MongoDB and returns source filename/page references.
6. If `LLM_BASE_URL` is configured, the retrieved passages are sent to that OpenAI-compatible chat endpoint. Otherwise the API returns an extractive, source-grounded fallback; it does not invent a generated clinical answer.

Example optional Ollama endpoint (run Ollama on the host and set `LLM_BASE_URL=http://host.docker.internal:11434/v1`, `LLM_API_KEY=ollama`, `LLM_MODEL=qwen2.5:3b` in `.env`, then recreate the API container).

## Data ownership

- PostgreSQL is authoritative for patients, organizations, access decisions, document ownership/status and audit events.
- MongoDB stores conversations and message history.
- Qdrant stores embeddings and chunk payloads with mandatory organization and patient filters.
- Original files are stored on a mounted local volume for this demo. Production requires private encrypted object storage, malware scanning and lifecycle controls.

## Supported documents and limitations

PDF, DOCX, TXT and Markdown are supported. Text-based PDFs are extracted directly. Scanned PDFs currently fail with an explicit OCR-needed message; add a vetted OCR worker before using scanned clinical records. The bundled embedding model is English-focused. Configure a validated multilingual embedding model and matching Qdrant dimension before multilingual use.

## Security and clinical safety

Use synthetic data only. Local credentials, demo authentication, unencrypted local services and local disk uploads are for development only. Before real patient data: deploy OIDC, disable demo auth, enforce tenant membership and consent, encrypt data in transit and at rest, add malware/OCR/PHI controls, retention/deletion workflows, backups, secrets management, monitoring and clinical validation. The assistant must not diagnose, prescribe or replace a qualified clinician.
