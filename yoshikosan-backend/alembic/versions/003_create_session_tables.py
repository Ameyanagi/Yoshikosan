"""create session tables

Revision ID: 002
Revises: 001
Create Date: 2025-11-21

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create work_sessions table
    op.create_table(
        "work_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "sop_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sops.id"),
            nullable=False,
        ),
        sa.Column(
            "worker_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column(
            "current_step_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("steps.id"),
            nullable=True,
        ),
        sa.Column(
            "started_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("approved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "approved_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column(
            "locked", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
    )

    # Create safety_checks table
    op.create_table(
        "safety_checks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("work_sessions.id"),
            nullable=False,
        ),
        sa.Column(
            "step_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("steps.id"),
            nullable=False,
        ),
        sa.Column("result", sa.Text(), nullable=False),
        sa.Column("feedback_text", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column(
            "needs_review",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "checked_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column(
            "override_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
    )

    # Create indexes
    op.create_index("idx_sessions_status", "work_sessions", ["status"])
    op.create_index("idx_sessions_worker_id", "work_sessions", ["worker_id"])
    op.create_index("idx_sessions_sop_id", "work_sessions", ["sop_id"])
    op.create_index("idx_checks_session_id", "safety_checks", ["session_id"])
    op.create_index("idx_checks_result", "safety_checks", ["result"])

    # Add CHECK constraints
    op.create_check_constraint(
        "check_session_status",
        "work_sessions",
        "status IN ('in_progress', 'completed', 'approved', 'rejected')",
    )
    op.create_check_constraint(
        "check_result_type", "safety_checks", "result IN ('pass', 'fail', 'override')"
    )


def downgrade() -> None:
    op.drop_constraint("check_result_type", "safety_checks")
    op.drop_constraint("check_session_status", "work_sessions")

    op.drop_index("idx_checks_result", table_name="safety_checks")
    op.drop_index("idx_checks_session_id", table_name="safety_checks")
    op.drop_index("idx_sessions_sop_id", table_name="work_sessions")
    op.drop_index("idx_sessions_worker_id", table_name="work_sessions")
    op.drop_index("idx_sessions_status", table_name="work_sessions")

    op.drop_table("safety_checks")
    op.drop_table("work_sessions")
