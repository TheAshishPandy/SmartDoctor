"""Add role-aware workspace menus and CRUD entries."""
from alembic import op
import sqlalchemy as sa

revision = "0004_workspace_menu_entries"
down_revision = "0003_email_password_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspace_menu_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("key", sa.String(80), nullable=False, unique=True),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("path", sa.String(180), nullable=False),
        sa.Column("icon", sa.String(60), nullable=False, server_default="layout-dashboard"),
        sa.Column("parent_id", sa.Uuid(), sa.ForeignKey("workspace_menu_items.id"), nullable=True),
        sa.Column("roles", sa.JSON(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_workspace_menu_parent_sort", "workspace_menu_items", ["parent_id", "sort_order"])
    op.create_table(
        "workspace_entries",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id"), nullable=True),
        sa.Column("owner_sub", sa.String(255), nullable=True),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="active"),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("updated_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_workspace_entries_org_type_created", "workspace_entries", ["organization_id", "resource_type", "created_at"])
    op.create_index("ix_workspace_entries_patient_type", "workspace_entries", ["patient_id", "resource_type"])
    op.create_index("ix_workspace_entries_owner_type", "workspace_entries", ["owner_sub", "resource_type"])


def downgrade() -> None:
    op.drop_index("ix_workspace_entries_owner_type", table_name="workspace_entries")
    op.drop_index("ix_workspace_entries_patient_type", table_name="workspace_entries")
    op.drop_index("ix_workspace_entries_org_type_created", table_name="workspace_entries")
    op.drop_table("workspace_entries")
    op.drop_index("ix_workspace_menu_parent_sort", table_name="workspace_menu_items")
    op.drop_table("workspace_menu_items")
