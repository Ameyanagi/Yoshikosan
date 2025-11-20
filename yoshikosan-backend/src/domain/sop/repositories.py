"""SOP repository protocol."""

from typing import Protocol
from uuid import UUID

from src.domain.sop.entities import SOP


class SOPRepository(Protocol):
    """Repository protocol for SOP persistence."""

    async def save(self, sop: SOP) -> SOP:
        """Save or update an SOP.

        Args:
            sop: SOP entity to save

        Returns:
            The saved SOP entity
        """
        ...

    async def get_by_id(self, sop_id: UUID) -> SOP | None:
        """Get an SOP by ID.

        Args:
            sop_id: SOP ID

        Returns:
            SOP entity if found, None otherwise
        """
        ...

    async def list_by_user(
        self, user_id: UUID, include_deleted: bool = False
    ) -> list[SOP]:
        """List all SOPs created by a user.

        Args:
            user_id: User ID
            include_deleted: Whether to include soft-deleted SOPs

        Returns:
            List of SOP entities
        """
        ...

    async def delete(self, sop_id: UUID) -> bool:
        """Soft delete an SOP by setting deleted_at timestamp.

        Args:
            sop_id: SOP ID

        Returns:
            True if SOP was deleted, False if not found
        """
        ...
