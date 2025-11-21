"""Pause Session Use Case."""

import logging
from dataclasses import dataclass
from uuid import UUID

from src.domain.work_session.entities import WorkSession
from src.domain.work_session.repositories import WorkSessionRepository

logger = logging.getLogger(__name__)


@dataclass
class PauseSessionRequest:
    """Request to pause a work session."""

    session_id: UUID
    worker_id: UUID


@dataclass
class PauseSessionResponse:
    """Response from pausing a session."""

    session: WorkSession


class PauseSessionUseCase:
    """Use case for pausing a work session."""

    def __init__(self, session_repository: WorkSessionRepository):
        """Initialize the use case.

        Args:
            session_repository: Repository for WorkSession persistence
        """
        self.session_repository = session_repository

    async def execute(self, request: PauseSessionRequest) -> PauseSessionResponse:
        """Execute the pause session use case.

        Args:
            request: Pause session request

        Returns:
            PauseSessionResponse with updated session

        Raises:
            ValueError: If session not found or user not authorized
        """
        # Load session
        session = await self.session_repository.get_by_id(request.session_id)
        if not session:
            raise ValueError(f"Session not found: {request.session_id}")

        # Check authorization
        if session.worker_id != request.worker_id:
            raise ValueError("Not authorized to modify this session")

        # Pause session (domain validation happens here)
        session.pause()

        # Save updated session
        saved_session = await self.session_repository.save(session)

        logger.info(
            f"Paused session {saved_session.id} for worker {request.worker_id}"
        )

        return PauseSessionResponse(session=saved_session)
