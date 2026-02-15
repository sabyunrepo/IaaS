"""Add email_notification_enabled to users table.

Revision ID: 004_email_notification
Revises: 003_analysis_logs
Create Date: 2026-02-16
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004_email_notification"
down_revision: Union[str, None] = "003_analysis_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("users", sa.Column("email_notification_enabled", sa.Boolean(), nullable=True))

def downgrade() -> None:
    op.drop_column("users", "email_notification_enabled")
