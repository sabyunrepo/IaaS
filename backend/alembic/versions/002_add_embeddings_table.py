"""Add embeddings table for pgvector similarity search.

Revision ID: 002_embeddings
Revises: 001_initial
Create Date: 2026-02-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "002_embeddings"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("content_key", sa.String(255), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_embeddings_job", "embeddings", ["job_id"])
    op.create_index("idx_embeddings_kind", "embeddings", ["kind"])


def downgrade() -> None:
    op.drop_table("embeddings")
