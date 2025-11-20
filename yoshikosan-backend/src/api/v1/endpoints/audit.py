"""Audit and approval endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, status

from src.api.dependencies.auth import get_current_user
from src.api.dependencies.repositories import get_session_repository, get_sop_repository
from src.api.v1.endpoints.session import work_session_to_schema
from src.application.audit.approve_session import (
    ApproveSessionRequest,
    ApproveSessionUseCase,
)
from src.application.audit.reject_session import (
    RejectSessionRequest,
    RejectSessionUseCase,
)
from src.domain.user.entities import User
from src.domain.work_session.entities import CheckResult
from src.infrastructure.database.repositories.session_repository import (
    SQLAlchemyWorkSessionRepository,
)
from src.infrastructure.database.repositories.sop_repository import (
    SQLAlchemySOPRepository,
)
from src.schemas.audit import (
    ApproveSessionResponse,
    AuditSessionListItem,
    RejectSessionResponse,
)
from src.schemas.audit import (
    RejectSessionRequest as RejectSessionRequestSchema,
)
from src.schemas.session import WorkSessionSchema

router = APIRouter(prefix="/audit", tags=["audit"])
logger = logging.getLogger(__name__)


@router.get("/sessions", response_model=list[AuditSessionListItem])
async def list_audit_sessions(
    status_filter: str = "completed",
    current_user: User = Depends(get_current_user),
    session_repo: SQLAlchemyWorkSessionRepository = Depends(get_session_repository),
    sop_repo: SQLAlchemySOPRepository = Depends(get_sop_repository),
) -> list[AuditSessionListItem]:
    """List sessions for audit review (supervisor only).

    Args:
        status_filter: Filter by status (default: completed)
        current_user: Current authenticated user (supervisor)
        session_repo: Session repository
        sop_repo: SOP repository

    Returns:
        List of AuditSessionListItem

    Raises:
        HTTPException: If not authorized
    """
    # TODO: Implement role-based authorization for supervisors
    # For now, allow any authenticated user

    # Get pending review sessions
    sessions = await session_repo.list_pending_review()

    # Build response list
    result = []
    for session in sessions:
        # Get SOP for title
        sop = await sop_repo.get_by_id(session.sop_id)
        sop_title = sop.title if sop else "Unknown SOP"

        # Count failed checks
        failed_count = sum(
            1 for check in session.checks if check.result == CheckResult.FAIL
        )

        result.append(
            AuditSessionListItem(
                session_id=session.id,
                sop_title=sop_title,
                worker_id=session.worker_id,
                status=session.status.value,
                completed_at=(
                    session.completed_at.isoformat() if session.completed_at else None
                ),
                check_count=len(session.checks),
                failed_check_count=failed_count,
            )
        )

    return result


@router.get("/sessions/{session_id}", response_model=WorkSessionSchema)
async def get_audit_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_repo: SQLAlchemyWorkSessionRepository = Depends(get_session_repository),
) -> WorkSessionSchema:
    """Get full audit trail for a session (supervisor only).

    Args:
        session_id: Session ID
        current_user: Current authenticated user (supervisor)
        session_repo: Session repository

    Returns:
        WorkSessionSchema with full audit trail

    Raises:
        HTTPException: If session not found or not authorized
    """
    # TODO: Implement role-based authorization for supervisors

    session = await session_repo.get_by_id(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    return work_session_to_schema(session)


@router.post(
    "/sessions/{session_id}/approve",
    response_model=ApproveSessionResponse,
    status_code=status.HTTP_200_OK,
)
async def approve_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_repo: SQLAlchemyWorkSessionRepository = Depends(get_session_repository),
) -> ApproveSessionResponse:
    """Approve a completed session (supervisor only).

    Args:
        session_id: Session ID
        current_user: Current authenticated user (supervisor)
        session_repo: Session repository

    Returns:
        ApproveSessionResponse

    Raises:
        HTTPException: If session not found, not authorized, or cannot be approved
    """
    # TODO: Implement role-based authorization for supervisors

    try:
        use_case = ApproveSessionUseCase(session_repo)
        request = ApproveSessionRequest(
            session_id=session_id, supervisor_id=current_user.id
        )

        response = await use_case.execute(request)

        return ApproveSessionResponse(
            session=work_session_to_schema(response.session), approved=True
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post(
    "/sessions/{session_id}/reject",
    response_model=RejectSessionResponse,
    status_code=status.HTTP_200_OK,
)
async def reject_session(
    session_id: UUID,
    request: RejectSessionRequestSchema = Body(...),
    current_user: User = Depends(get_current_user),
    session_repo: SQLAlchemyWorkSessionRepository = Depends(get_session_repository),
) -> RejectSessionResponse:
    """Reject a completed session (supervisor only).

    Args:
        session_id: Session ID
        request: Reject request with reason
        current_user: Current authenticated user (supervisor)
        session_repo: Session repository

    Returns:
        RejectSessionResponse

    Raises:
        HTTPException: If session not found, not authorized, or cannot be rejected
    """
    # TODO: Implement role-based authorization for supervisors

    try:
        use_case = RejectSessionUseCase(session_repo)
        use_case_request = RejectSessionRequest(
            session_id=session_id, supervisor_id=current_user.id, reason=request.reason
        )

        response = await use_case.execute(use_case_request)

        return RejectSessionResponse(
            session=work_session_to_schema(response.session), rejected=True
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
