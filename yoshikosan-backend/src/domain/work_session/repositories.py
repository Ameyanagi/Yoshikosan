"""Work session repository protocol."""

from typing import Protocol
from uuid import UUID

from src.domain.work_session.entities import WorkSession


class WorkSessionRepository(Protocol):
    """Repository protocol for WorkSession persistence."""

    async def save(self, session: WorkSession) -> WorkSession:
        """Save or update a work session.

        Args:
            session: WorkSession entity to save

        Returns:
            The saved WorkSession entity
        """
        ...

    async def get_by_id(self, session_id: UUID) -> WorkSession | None:
        """Get a work session by ID.

        Args:
            session_id: WorkSession ID

        Returns:
            WorkSession entity if found, None otherwise
        """
        ...

    async def get_current_for_worker(self, worker_id: UUID) -> WorkSession | None:
        """Get the current active session for a worker.

        Args:
            worker_id: Worker user ID

        Returns:
            Active WorkSession if found, None otherwise
        """
        ...

    async def list_by_worker(self, worker_id: UUID) -> list[WorkSession]:
        """List all sessions for a worker.

        Args:
            worker_id: Worker user ID

        Returns:
            List of WorkSession entities
        """
        ...

    async def list_pending_review(self) -> list[WorkSession]:
        """List all completed sessions pending supervisor review.

        Returns:
            List of WorkSession entities with status COMPLETED
        """
        ...
