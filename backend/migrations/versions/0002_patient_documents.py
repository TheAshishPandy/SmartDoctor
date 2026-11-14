"""Add patient document metadata for RAG ingestion."""
from alembic import op
import sqlalchemy as sa

revision = "0002_patient_documents"
down_revision = "0001_identity_access_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "patient_documents",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("uploaded_by", sa.String(255), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(120), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False, unique=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="processing"),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_patient_documents_patient_created", "patient_documents", ["patient_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_patient_documents_patient_created", table_name="patient_documents")
    op.drop_table("patient_documents")
