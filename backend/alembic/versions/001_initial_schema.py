"""Initial schema baseline - matches existing init-db.sql tables.

Revision ID: 001_initial
Revises:
Create Date: 2026-02-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column("image", sa.String(2048)),
        sa.Column("plan", sa.String(50), nullable=False, server_default="free"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # OAuth Accounts
    op.create_table(
        "oauth_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("provider_account_id", sa.String(255), nullable=False),
        sa.Column("access_token", sa.Text()),
        sa.Column("refresh_token", sa.Text()),
        sa.Column("expires_at", sa.BigInteger()),
        sa.Column("token_type", sa.String(50)),
        sa.Column("scope", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_oauth_provider", "oauth_accounts", ["provider", "provider_account_id"])
    op.create_index("idx_oauth_user", "oauth_accounts", ["user_id"])

    # API Keys
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key_hash", sa.String(255), unique=True, nullable=False),
        sa.Column("key_prefix", sa.String(10), nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_api_keys_user", "api_keys", ["user_id"])
    op.create_index("idx_api_keys_hash", "api_keys", ["key_hash"])

    # Jobs
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("temporal_workflow_id", sa.String(255), unique=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("input_data", postgresql.JSONB(), nullable=False),
        sa.Column("final_output", postgresql.JSONB()),
        sa.Column("callback_url", sa.String(2048)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_jobs_user", "jobs", ["user_id"])
    op.create_index("idx_jobs_status", "jobs", ["status"])
    op.create_index("idx_jobs_temporal", "jobs", ["temporal_workflow_id"])

    # Checkpoints
    op.create_table(
        "checkpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("phase", sa.String(50), nullable=False),
        sa.Column("data", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("job_id", "phase", name="uq_checkpoints_job_phase"),
    )
    op.create_index("idx_checkpoints_job", "checkpoints", ["job_id"])


def downgrade() -> None:
    op.drop_table("checkpoints")
    op.drop_table("jobs")
    op.drop_table("api_keys")
    op.drop_table("oauth_accounts")
    op.drop_table("users")
