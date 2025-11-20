"""create sop tables

Revision ID: 001
Revises:
Create Date: 2025-11-21

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create sops table
    op.create_table(
        "sops",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    # Create tasks table
    op.create_table(
        "tasks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "sop_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sops.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Create steps table
    op.create_table(
        "steps",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("expected_action", sa.Text(), nullable=True),
        sa.Column("expected_result", sa.Text(), nullable=True),
    )

    # Create hazards table
    op.create_table(
        "hazards",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "step_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("steps.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("mitigation", sa.Text(), nullable=True),
    )

    # Create indexes
    op.create_index("idx_sops_created_by", "sops", ["created_by"])
    op.create_index("idx_tasks_sop_id", "tasks", ["sop_id"])
    op.create_index("idx_steps_task_id", "steps", ["task_id"])
    op.create_index("idx_hazards_step_id", "hazards", ["step_id"])


def downgrade() -> None:
    op.drop_index("idx_hazards_step_id", table_name="hazards")
    op.drop_index("idx_steps_task_id", table_name="steps")
    op.drop_index("idx_tasks_sop_id", table_name="tasks")
    op.drop_index("idx_sops_created_by", table_name="sops")

    op.drop_table("hazards")
    op.drop_table("steps")
    op.drop_table("tasks")
    op.drop_table("sops")
