"""organization chatbot and doctor scheduling

Revision ID: b0b97b958237
Revises: 0004_workspace_menu_entries
Create Date: 2026-11-20 21:35:23.463396
"""
from alembic import op
import sqlalchemy as sa

revision = "b0b97b958237"
down_revision = "0004_workspace_menu_entries"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("organizations", sa.Column("chatbot_config", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    op.add_column("memberships", sa.Column("specialties", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))
    op.add_column("memberships", sa.Column("availability", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))


def downgrade() -> None:
    op.drop_column("memberships", "availability")
    op.drop_column("memberships", "specialties")
    op.drop_column("organizations", "chatbot_config")
