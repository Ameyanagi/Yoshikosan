"""Reject Session Use Case."""

import logging
from dataclasses import dataclass
from uuid import UUID

from src.domain.work_session.entities import WorkSession
from src.domain.work_session.repositories import WorkSessionRepository

logger = logging.getLogger(__name__)


@dataclass
class RejectSessionRequest:
    """Request to reject a completed session."""

    session_id: UUID
    supervisor_id: UUID
    reason: str


@dataclass
class RejectSessionResponse:
    """Response from rejecting a session."""

    session: WorkSession
    rejected: bool


class RejectSessionUseCase:
    """Use case for rejecting a completed work session."""

    def __init__(self, session_repository: WorkSessionRepository):
        """Initialize the use case.

        Args:
            session_repository: Repository for WorkSession persistence
        """
        self.session_repository = session_repository

    async def execute(self, request: RejectSessionRequest) -> RejectSessionResponse:
        """Execute the reject session use case.

        Args:
            request: Reject session request

        Returns:
            RejectSessionResponse with updated session

        Raises:
            ValueError: If session not found or cannot be rejected
        """
        # Load session
        session = await self.session_repository.get_by_id(request.session_id)
        if not session:
            raise ValueError(f"Session not found: {request.session_id}")

        # Reject session (domain logic validates state and reason)
        session.reject(request.supervisor_id, request.reason)

        # Save session
        saved_session = await self.session_repository.save(session)

        logger.info(
            f"Session {saved_session.id} rejected by supervisor {request.supervisor_id}: "
            f"{request.reason}"
        )

        return RejectSessionResponse(session=saved_session, rejected=True)
