"""Add feedback_audio_url to safety_checks

Revision ID: 004
Revises: 003
Create Date: 2024-12-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add feedback_audio_url column to safety_checks table."""
    # Add feedback_audio_url column
    op.add_column(
        'safety_checks',
        sa.Column('feedback_audio_url', sa.Text(), nullable=True)
    )

    # Add index for audio URL lookups (only on non-null values)
    op.execute(
        """
        CREATE INDEX idx_checks_audio_url
        ON safety_checks(feedback_audio_url)
        WHERE feedback_audio_url IS NOT NULL
        """
    )


def downgrade() -> None:
    """Remove feedback_audio_url column from safety_checks table."""
    # Drop index
    op.drop_index('idx_checks_audio_url', table_name='safety_checks')

    # Drop column
    op.drop_column('safety_checks', 'feedback_audio_url')
