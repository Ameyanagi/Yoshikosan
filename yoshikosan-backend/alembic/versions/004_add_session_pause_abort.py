"""add session pause and abort statuses

Revision ID: 004
Revises: 003
Create Date: 2025-11-21

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add new columns to work_sessions table
    op.add_column(
        "work_sessions",
        sa.Column("paused_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "work_sessions",
        sa.Column("aborted_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "work_sessions", sa.Column("abort_reason", sa.Text(), nullable=True)
    )

    # Drop old check constraint
    op.drop_constraint("check_session_status", "work_sessions", type_="check")

    # Create new check constraint with paused and aborted statuses
    op.create_check_constraint(
        "check_session_status",
        "work_sessions",
        "status IN ('in_progress', 'paused', 'completed', 'aborted', 'approved', 'rejected')",
    )

    # Add composite index for efficient querying by worker and status
    op.create_index(
        "idx_sessions_worker_status", "work_sessions", ["worker_id", "status"]
    )


def downgrade() -> None:
    # Drop composite index
    op.drop_index("idx_sessions_worker_status", table_name="work_sessions")

    # Drop new check constraint
    op.drop_constraint("check_session_status", "work_sessions", type_="check")

    # Restore old check constraint
    op.create_check_constraint(
        "check_session_status",
        "work_sessions",
        "status IN ('in_progress', 'completed', 'approved', 'rejected')",
    )

    # Drop new columns
    op.drop_column("work_sessions", "abort_reason")
    op.drop_column("work_sessions", "aborted_at")
    op.drop_column("work_sessions", "paused_at")
