"""Create organization, membership, patient, care, consent and audit tables."""
from alembic import op
import sqlalchemy as sa

revision = "0001_identity_access_audit"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("organizations", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("name", sa.String(200), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("memberships", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("user_sub", sa.String(255), nullable=False), sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False), sa.Column("role", sa.String(40), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_memberships_user_org_status", "memberships", ["user_sub", "organization_id", "status"])
    op.create_table("patients", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("owner_sub", sa.String(255), nullable=False), sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=True), sa.Column("display_label", sa.String(120), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_patients_owner_sub", "patients", ["owner_sub"])
    op.create_table("care_relationships", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id"), nullable=False), sa.Column("clinician_sub", sa.String(255), nullable=False), sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False), sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_care_relationships_patient_clinician", "care_relationships", ["patient_id", "clinician_sub", "status"])
    op.create_table("consent_grants", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id"), nullable=False), sa.Column("grantee_sub", sa.String(255), nullable=False), sa.Column("scope", sa.String(80), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True), sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_consent_patient_grantee_scope", "consent_grants", ["patient_id", "grantee_sub", "scope"])
    op.create_table("audit_events", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("actor_sub", sa.String(255), nullable=False), sa.Column("actor_role", sa.String(100), nullable=False), sa.Column("action", sa.String(80), nullable=False), sa.Column("resource_type", sa.String(80), nullable=False), sa.Column("resource_id", sa.String(80), nullable=False), sa.Column("outcome", sa.String(20), nullable=False), sa.Column("correlation_id", sa.String(100), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_audit_resource_created", "audit_events", ["resource_type", "resource_id", "created_at"])
    op.create_index("ix_audit_actor_created", "audit_events", ["actor_sub", "created_at"])

def downgrade() -> None:
    op.drop_index("ix_audit_actor_created", table_name="audit_events")
    op.drop_index("ix_audit_resource_created", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_consent_patient_grantee_scope", table_name="consent_grants")
    op.drop_table("consent_grants")
    op.drop_index("ix_care_relationships_patient_clinician", table_name="care_relationships")
    op.drop_table("care_relationships")
    op.drop_index("ix_patients_owner_sub", table_name="patients")
    op.drop_table("patients")
    op.drop_index("ix_memberships_user_org_status", table_name="memberships")
    op.drop_table("memberships")
    op.drop_table("organizations")
