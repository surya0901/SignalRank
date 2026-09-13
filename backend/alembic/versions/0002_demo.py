"""Isolated demo profiles and revocable hashed sessions."""

import sqlalchemy as sa

from alembic import op

revision = "0002_demo"
down_revision = "0001_catalog"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "demo_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("state", sa.JSON(), nullable=False),
    )
    op.create_index("ix_demo_sessions_token_hash", "demo_sessions", ["token_hash"], unique=True)
    op.create_index("ix_demo_sessions_expires_at", "demo_sessions", ["expires_at"])


def downgrade():
    op.drop_table("demo_sessions")
