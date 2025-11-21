"""Abort Session Use Case."""

import logging
from dataclasses import dataclass
from uuid import UUID

from src.domain.work_session.entities import WorkSession
from src.domain.work_session.repositories import WorkSessionRepository

logger = logging.getLogger(__name__)


@dataclass
class AbortSessionRequest:
    """Request to abort a work session."""

    session_id: UUID
    worker_id: UUID
    reason: str | None = None


@dataclass
class AbortSessionResponse:
    """Response from aborting a session."""

    session: WorkSession


class AbortSessionUseCase:
    """Use case for aborting a work session."""

    def __init__(self, session_repository: WorkSessionRepository):
        """Initialize the use case.

        Args:
            session_repository: Repository for WorkSession persistence
        """
        self.session_repository = session_repository

    async def execute(self, request: AbortSessionRequest) -> AbortSessionResponse:
        """Execute the abort session use case.

        Args:
            request: Abort session request

        Returns:
            AbortSessionResponse with updated session

        Raises:
            ValueError: If session not found or user not authorized
        """
        # Load session
        session = await self.session_repository.get_by_id(request.session_id)
        if not session:
            raise ValueError(f"Session not found: {request.session_id}")

        # Check authorization (owner can abort their own sessions)
        if session.worker_id != request.worker_id:
            raise ValueError("Not authorized to modify this session")

        # Abort session (domain validation happens here)
        session.abort(reason=request.reason)

        # Save updated session
        saved_session = await self.session_repository.save(session)

        logger.info(
            f"Aborted session {saved_session.id} for worker {request.worker_id}"
            + (f" with reason: {request.reason}" if request.reason else "")
        )

        return AbortSessionResponse(session=saved_session)
