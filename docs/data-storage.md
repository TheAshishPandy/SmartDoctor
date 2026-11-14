# SmartDoctor polyglot data storage

## Storage ownership

| Data | System of record | Why |
|---|---|---|
| Patients, organizations, memberships, care relationships, consent, appointments, clinical transactions and audit events | PostgreSQL | ACID transactions, relational constraints, migrations and reporting |
| Chat sessions, ordered conversation messages and assistant/tool interaction metadata | MongoDB | Document-shaped, append-oriented conversation records |
| Embedded document chunks and retrieval metadata | Qdrant | Vector similarity search with payload filters |
| Original uploaded files and source documents | Encrypted object storage (S3-compatible, e.g. MinIO for local development) | Durable binary storage, versioning and lifecycle policies |
| Cache, short-lived locks and rate-limit counters | Redis | Ephemeral low-latency data; never the source of truth |

Do not duplicate patient profile, consent, billing or appointment records into MongoDB or Qdrant. PostgreSQL remains authoritative.

## Chat isolation

Every conversation is scoped by the verified identity subject and organization. The API must derive `owner_subject` and `organization_id` from the validated access token and server-side membership lookup; never accept them as trusted fields from a client. The Mongo adapter's read/update filters include organization, owner and conversation identifiers. Patient-linked chat history must additionally pass the PostgreSQL patient-access policy before it is returned.

Do not create a TTL index until the organization has approved a documented retention schedule. Chat content may contain health information and must be treated as sensitive data. Configure encrypted disks/volumes, TLS, access credentials, backups, audit logging and retention/deletion workflows before using real patient data.

## RAG and Qdrant

The Qdrant adapter stores embeddings and payload metadata for patient-specific chunks. Patient retrieval requires both `organization_id` and `patient_id` filters. The API must first authorize the principal against PostgreSQL consent and care-relationship records, then call the vector store. A vector filter is defense in depth, not authorization.

The ingestion pipeline must preserve source document ID, version, page/section, chunk ID, ingestion timestamp, content hash and provenance. Original files stay in encrypted object storage. Never index a document before upload validation, malware scanning, patient linking and access checks. Avoid copying unnecessary direct identifiers into vector payloads.

The embedding model's dimensions must match `EMBEDDING_DIMENSIONS` and the Qdrant collection. Changing embedding model or dimensions requires a new collection and controlled re-embedding/re-indexing migration.

## Local development

```bash
cp .env.example .env
docker compose up --build
```

Local Compose uses PostgreSQL, MongoDB Community Server, Qdrant and Redis. Use synthetic data only. Local development credentials and exposed ports are not production settings.

## SQL Server alternative

The current implementation uses PostgreSQL with SQLAlchemy. If an existing deployment requires SQL Server, keep the same repository/service boundary and use SQLAlchemy with the Microsoft ODBC driver and `mssql+pyodbc` URL. Do not run PostgreSQL and SQL Server as competing sources of truth for the same transactional entities.
