"""Approve Session Use Case."""

import logging
from dataclasses import dataclass
from uuid import UUID

from src.domain.work_session.entities import WorkSession
from src.domain.work_session.repositories import WorkSessionRepository

logger = logging.getLogger(__name__)


@dataclass
class ApproveSessionRequest:
    """Request to approve a completed session."""

    session_id: UUID
    supervisor_id: UUID


@dataclass
class ApproveSessionResponse:
    """Response from approving a session."""

    session: WorkSession
    approved: bool


class ApproveSessionUseCase:
    """Use case for approving a completed work session."""

    def __init__(self, session_repository: WorkSessionRepository):
        """Initialize the use case.

        Args:
            session_repository: Repository for WorkSession persistence
        """
        self.session_repository = session_repository

    async def execute(self, request: ApproveSessionRequest) -> ApproveSessionResponse:
        """Execute the approve session use case.

        Args:
            request: Approve session request

        Returns:
            ApproveSessionResponse with updated session

        Raises:
            ValueError: If session not found or cannot be approved
        """
        # Load session
        session = await self.session_repository.get_by_id(request.session_id)
        if not session:
            raise ValueError(f"Session not found: {request.session_id}")

        # Approve session (domain logic validates state)
        session.approve(request.supervisor_id)

        # Save session
        saved_session = await self.session_repository.save(session)

        logger.info(
            f"Session {saved_session.id} approved by supervisor {request.supervisor_id}"
        )

        return ApproveSessionResponse(session=saved_session, approved=True)
