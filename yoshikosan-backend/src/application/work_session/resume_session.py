"""Resume Session Use Case."""

import logging
from dataclasses import dataclass
from uuid import UUID

from src.domain.work_session.entities import WorkSession
from src.domain.work_session.repositories import WorkSessionRepository

logger = logging.getLogger(__name__)


@dataclass
class ResumeSessionRequest:
    """Request to resume a paused work session."""

    session_id: UUID
    worker_id: UUID


@dataclass
class ResumeSessionResponse:
    """Response from resuming a session."""

    session: WorkSession


class ResumeSessionUseCase:
    """Use case for resuming a paused work session."""

    def __init__(self, session_repository: WorkSessionRepository):
        """Initialize the use case.

        Args:
            session_repository: Repository for WorkSession persistence
        """
        self.session_repository = session_repository

    async def execute(self, request: ResumeSessionRequest) -> ResumeSessionResponse:
        """Execute the resume session use case.

        Args:
            request: Resume session request

        Returns:
            ResumeSessionResponse with updated session

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

        # Resume session (domain validation happens here)
        session.resume()

        # Save updated session
        saved_session = await self.session_repository.save(session)

        logger.info(
            f"Resumed session {saved_session.id} for worker {request.worker_id}"
        )

        return ResumeSessionResponse(session=saved_session)
