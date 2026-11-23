"""platform and organization theme persistence

Revision ID: 0005_theme_studio
Revises: b0b97b958237
Create Date: 2026-11-21
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_theme_studio"
down_revision = "b0b97b958237"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("organizations", sa.Column("ui_theme", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    op.create_table(
        "platform_settings",
        sa.Column("key", sa.String(length=100), primary_key=True),
        sa.Column("value", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("platform_settings")
    op.drop_column("organizations", "ui_theme")
