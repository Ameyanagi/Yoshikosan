"""Work session endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies.auth import get_current_user
from src.api.dependencies.repositories import get_session_repository, get_sop_repository
from src.application.work_session.start_session import (
    StartSessionRequest,
    StartSessionUseCase,
)
from src.domain.user.entities import User
from src.domain.work_session.entities import WorkSession
from src.infrastructure.database.repositories.session_repository import (
    SQLAlchemyWorkSessionRepository,
)
from src.infrastructure.database.repositories.sop_repository import (
    SQLAlchemySOPRepository,
)
from src.application.work_session.abort_session import (
    AbortSessionRequest,
    AbortSessionUseCase,
)
from src.application.work_session.pause_session import (
    PauseSessionRequest,
    PauseSessionUseCase,
)
from src.application.work_session.resume_session import (
    ResumeSessionRequest,
    ResumeSessionUseCase,
)
from src.schemas.session import (
    AbortSessionResponse,
    CompleteSessionResponse,
    PauseSessionResponse,
    ResumeSessionResponse,
    SafetyCheckSchema,
    StartSessionResponse,
    WorkSessionSchema,
)
from src.schemas.session import (
    AbortSessionRequest as AbortSessionRequestSchema,
)
from src.schemas.session import (
    StartSessionRequest as StartSessionRequestSchema,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])
logger = logging.getLogger(__name__)


def work_session_to_schema(session: WorkSession, sop_title: str) -> WorkSessionSchema:
    """Convert WorkSession domain entity to Pydantic schema.

    Args:
        session: WorkSession domain entity
        sop_title: SOP title for display

    Returns:
        WorkSessionSchema
    """
    return WorkSessionSchema(
        id=session.id,
        sop_id=session.sop_id,
        sop_title=sop_title,
        worker_id=session.worker_id,
        status=session.status.value,
        current_step_id=session.current_step_id,
        started_at=session.started_at,
        completed_at=session.completed_at,
        approved_at=session.approved_at,
        approved_by=session.approved_by,
        paused_at=session.paused_at,
        aborted_at=session.aborted_at,
        abort_reason=session.abort_reason,
        locked=session.locked,
        rejection_reason=session.rejection_reason,
        checks=[
            SafetyCheckSchema(
                id=check.id,
                step_id=check.step_id,
                result=check.result.value,
                feedback_text=check.feedback_text,
                confidence_score=check.confidence_score,
                needs_review=check.needs_review,
                checked_at=check.checked_at,
                override_reason=check.override_reason,
                override_by=check.override_by,
            )
            for check in session.checks
        ],
    )


@router.post(
    "", response_model=StartSessionResponse, status_code=status.HTTP_201_CREATED
)
async def start_session(
    request: StartSessionRequestSchema,
    current_user: User = Depends(get_current_user),
    session_repo: SQLAlchemyWorkSessionRepository = Depends(get_session_repository),
    sop_repo: SQLAlchemySOPRepository = Depends(get_sop_repository),
) -> StartSessionResponse:
    """Start a new work session.

    Args:
        request: Start session request
        current_user: Current authenticated user
        session_repo: Session repository
        sop_repo: SOP repository

    Returns:
        StartSessionResponse with session and first step

    Raises:
        HTTPException: If SOP not found, not structured, or worker has active session
    """
    try:
        use_case = StartSessionUseCase(session_repo, sop_repo)
        use_case_request = StartSessionRequest(
            sop_id=request.sop_id, worker_id=current_user.id
        )

        response = await use_case.execute(use_case_request)

        return StartSessionResponse(
            session=work_session_to_schema(response.session, response.sop.title),
            first_step_id=response.first_step_id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get("/current", response_model=WorkSessionSchema | None)
async def get_current_session(
    current_user: User = Depends(get_current_user),
    session_repo: SQLAlchemyWorkSessionRepository = Depends(get_session_repository),
    sop_repo: SQLAlchemySOPRepository = Depends(get_sop_repository),
) -> WorkSessionSchema | None:
    """Get the current active session for the authenticated user.

    Args:
        current_user: Current authenticated user
        session_repo: Session repository
        sop_repo: SOP repository

    Returns:
        WorkSessionSchema if active session exists, None otherwise
    """
    session = await session_repo.get_current_for_worker(current_user.id)

    if not session:
        return None

    # Get SOP title
    sop = await sop_repo.get_by_id(session.sop_id)
    sop_title = sop.title if sop else "Unknown SOP"

    return work_session_to_schema(session, sop_title)


@router.get("", response_model=list[WorkSessionSchema])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    session_repo: SQLAlchemyWorkSessionRepository = Depends(get_session_repository),
    sop_repo: SQLAlchemySOPRepository = Depends(get_sop_repository),
    include_aborted: bool = False,
) -> list[WorkSessionSchema]:
    """List all sessions for the current user.

    Args:
        current_user: Current authenticated user
        session_repo: Session repository
        sop_repo: SOP repository
        include_aborted: Whether to include aborted sessions

    Returns:
        List of WorkSessionSchema
    """
    sessions = await session_repo.list_by_worker(current_user.id, include_aborted)

    # Get SOP titles (efficiently loaded via repository joinedload)
    result = []
    for session in sessions:
        sop = await sop_repo.get_by_id(session.sop_id)
        sop_title = sop.title if sop else "Unknown SOP"
        result.append(work_session_to_schema(session, sop_title))

    return result


@router.get("/{session_id}", response_model=WorkSessionSchema)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_repo: SQLAlchemyWorkSessionRepository = Depends(get_session_repository),
    sop_repo: SQLAlchemySOPRepository = Depends(get_sop_repository),
) -> WorkSessionSchema:
    """Get session details by ID.

    Args:
        session_id: Session ID
        current_user: Current authenticated user
        session_repo: Session repository
        sop_repo: SOP repository

    Returns:
        WorkSessionSchema

    Raises:
        HTTPException: If session not found or user not authorized
    """
    session = await session_repo.get_by_id(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    # Authorization: only worker can view (supervisors handled in audit endpoints)
    if session.worker_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this session",
        )

    # Get SOP title
    sop = await sop_repo.get_by_id(session.sop_id)
    sop_title = sop.title if sop else "Unknown SOP"

    return work_session_to_schema(session, sop_title)


@router.post("/{session_id}/complete", response_model=CompleteSessionResponse)
async def complete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_repo: SQLAlchemyWorkSessionRepository = Depends(get_session_repository),
    sop_repo: SQLAlchemySOPRepository = Depends(get_sop_repository),
) -> CompleteSessionResponse:
    """Mark a session as complete.

    Args:
        session_id: Session ID
        current_user: Current authenticated user
        session_repo: Session repository
        sop_repo: SOP repository

    Returns:
        CompleteSessionResponse

    Raises:
        HTTPException: If session not found, not authorized, or cannot be completed
    """
    session = await session_repo.get_by_id(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    # Authorization: only worker can complete
    if session.worker_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to complete this session",
        )

    try:
        session.complete()
        saved_session = await session_repo.save(session)

        # Get SOP title
        sop = await sop_repo.get_by_id(saved_session.sop_id)
        sop_title = sop.title if sop else "Unknown SOP"

        return CompleteSessionResponse(
            session=work_session_to_schema(saved_session, sop_title), completed=True
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/{session_id}/pause", response_model=PauseSessionResponse)
async def pause_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_repo: SQLAlchemyWorkSessionRepository = Depends(get_session_repository),
    sop_repo: SQLAlchemySOPRepository = Depends(get_sop_repository),
) -> PauseSessionResponse:
    """Pause an in-progress session."""
    try:
        use_case = PauseSessionUseCase(session_repo)
        use_case_request = PauseSessionRequest(
            session_id=session_id, worker_id=current_user.id
        )
        response = await use_case.execute(use_case_request)
        sop = await sop_repo.get_by_id(response.session.sop_id)
        sop_title = sop.title if sop else "Unknown SOP"
        return PauseSessionResponse(
            session=work_session_to_schema(response.session, sop_title)
        )
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
        elif "not authorized" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/{session_id}/resume", response_model=ResumeSessionResponse)
async def resume_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_repo: SQLAlchemyWorkSessionRepository = Depends(get_session_repository),
    sop_repo: SQLAlchemySOPRepository = Depends(get_sop_repository),
) -> ResumeSessionResponse:
    """Resume a paused session."""
    try:
        use_case = ResumeSessionUseCase(session_repo)
        use_case_request = ResumeSessionRequest(
            session_id=session_id, worker_id=current_user.id
        )
        response = await use_case.execute(use_case_request)
        sop = await sop_repo.get_by_id(response.session.sop_id)
        sop_title = sop.title if sop else "Unknown SOP"
        return ResumeSessionResponse(
            session=work_session_to_schema(response.session, sop_title)
        )
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
        elif "not authorized" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/{session_id}/abort", response_model=AbortSessionResponse)
async def abort_session(
    session_id: UUID,
    request: AbortSessionRequestSchema,
    current_user: User = Depends(get_current_user),
    session_repo: SQLAlchemyWorkSessionRepository = Depends(get_session_repository),
    sop_repo: SQLAlchemySOPRepository = Depends(get_sop_repository),
) -> AbortSessionResponse:
    """Abort a session permanently."""
    try:
        use_case = AbortSessionUseCase(session_repo)
        use_case_request = AbortSessionRequest(
            session_id=session_id, worker_id=current_user.id, reason=request.reason
        )
        response = await use_case.execute(use_case_request)
        sop = await sop_repo.get_by_id(response.session.sop_id)
        sop_title = sop.title if sop else "Unknown SOP"
        return AbortSessionResponse(
            session=work_session_to_schema(response.session, sop_title)
        )
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
        elif "not authorized" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
