"""Add analysis_logs table for activity execution tracking.

Revision ID: 003_analysis_logs
Revises: 002_embeddings
Create Date: 2026-02-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003_analysis_logs"
down_revision: Union[str, None] = "002_embeddings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "analysis_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("activity_name", sa.String(100), nullable=False),
        sa.Column("phase", sa.String(50), nullable=False),
        sa.Column("log_type", sa.String(20), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("data", postgresql.JSONB(), server_default="{}"),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_analysis_logs_job", "analysis_logs", ["job_id"])
    op.create_index("idx_analysis_logs_activity", "analysis_logs", ["activity_name"])
    op.create_index("idx_analysis_logs_phase", "analysis_logs", ["phase"])
    op.create_index("idx_analysis_logs_created", "analysis_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("analysis_logs")
