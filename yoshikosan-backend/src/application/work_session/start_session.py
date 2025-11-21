"""Start Session Use Case."""

import logging
from dataclasses import dataclass
from uuid import UUID

from src.domain.sop.entities import SOP
from src.domain.sop.repositories import SOPRepository
from src.domain.work_session.entities import WorkSession
from src.domain.work_session.repositories import WorkSessionRepository

logger = logging.getLogger(__name__)


@dataclass
class StartSessionRequest:
    """Request to start a new work session."""

    sop_id: UUID
    worker_id: UUID


@dataclass
class StartSessionResponse:
    """Response from starting a session."""

    session: WorkSession
    sop: SOP
    first_step_id: UUID | None


class StartSessionUseCase:
    """Use case for starting a new work session."""

    def __init__(
        self,
        session_repository: WorkSessionRepository,
        sop_repository: SOPRepository,
    ):
        """Initialize the use case.

        Args:
            session_repository: Repository for WorkSession persistence
            sop_repository: Repository for SOP retrieval
        """
        self.session_repository = session_repository
        self.sop_repository = sop_repository

    def _get_first_step_id(self, sop: SOP) -> UUID | None:
        """Get the ID of the first step in the SOP.

        Args:
            sop: SOP entity

        Returns:
            UUID of first step, or None if SOP has no steps
        """
        if not sop.tasks:
            return None

        first_task = sop.tasks[0]
        if not first_task.steps:
            return None

        return first_task.steps[0].id

    async def execute(self, request: StartSessionRequest) -> StartSessionResponse:
        """Execute the start session use case.

        Workers can now have multiple sessions in progress simultaneously.

        Args:
            request: Start session request

        Returns:
            StartSessionResponse with session and first step

        Raises:
            ValueError: If SOP not found or not structured
        """
        # Load SOP
        sop = await self.sop_repository.get_by_id(request.sop_id)
        if not sop:
            raise ValueError(f"SOP not found: {request.sop_id}")

        # Validate SOP is structured (has tasks and steps)
        validation_errors = sop.validate()
        if validation_errors:
            raise ValueError(
                f"SOP is not properly structured: {', '.join(validation_errors)}"
            )

        # Get first step ID
        first_step_id = self._get_first_step_id(sop)
        if not first_step_id:
            raise ValueError("SOP has no steps to execute")

        # Create new work session
        session = WorkSession(
            sop_id=request.sop_id,
            worker_id=request.worker_id,
            current_step_id=first_step_id,
        )

        # Save session
        saved_session = await self.session_repository.save(session)

        logger.info(
            f"Started session {saved_session.id} for worker {request.worker_id} "
            f"on SOP {request.sop_id}"
        )

        return StartSessionResponse(
            session=saved_session, sop=sop, first_step_id=first_step_id
        )
