"""Safety check endpoints."""

import base64
import logging
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, status

from src.api.dependencies.auth import get_current_user
from src.api.dependencies.repositories import get_session_repository, get_sop_repository
from src.application.safety_check.execute_check import (
    ExecuteSafetyCheckRequest,
    ExecuteSafetyCheckUseCase,
)
from src.domain.user.entities import User
from src.infrastructure.database.repositories.session_repository import (
    SQLAlchemyWorkSessionRepository,
)
from src.infrastructure.database.repositories.sop_repository import (
    SQLAlchemySOPRepository,
)
from src.schemas.check import (
    ExecuteCheckRequest,
    ExecuteCheckResponse,
    OverrideCheckRequest,
    OverrideCheckResponse,
)

router = APIRouter(prefix="/checks", tags=["checks"])
logger = logging.getLogger(__name__)


@router.post(
    "", response_model=ExecuteCheckResponse, status_code=status.HTTP_201_CREATED
)
async def execute_safety_check(
    request: ExecuteCheckRequest = Body(...),
    current_user: User = Depends(get_current_user),
    session_repo: SQLAlchemyWorkSessionRepository = Depends(get_session_repository),
    sop_repo: SQLAlchemySOPRepository = Depends(get_sop_repository),
) -> ExecuteCheckResponse:
    """Execute a safety check with image and audio verification.

    Args:
        request: Execute check request with base64-encoded image and audio
        current_user: Current authenticated user
        session_repo: Session repository
        sop_repo: SOP repository

    Returns:
        ExecuteCheckResponse with result, feedback text and audio

    Raises:
        HTTPException: If validation fails or check execution fails
    """
    # Verify session belongs to current user
    session = await session_repo.get_by_id(request.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    if session.worker_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add checks to this session",
        )

    # Create temporary files for image and audio
    temp_dir = Path("temp") / "checks"
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_image_path = (
        temp_dir / f"check_image_{request.session_id}_{request.step_id}.jpg"
    )
    temp_audio_path = (
        temp_dir / f"check_audio_{request.session_id}_{request.step_id}.mp3"
    )

    try:
        # Decode base64 data and save to temp files
        image_data = base64.b64decode(request.image_base64)
        audio_data = base64.b64decode(request.audio_base64)

        temp_image_path.write_bytes(image_data)
        temp_audio_path.write_bytes(audio_data)

        # Execute use case
        use_case = ExecuteSafetyCheckUseCase(session_repo, sop_repo)
        use_case_request = ExecuteSafetyCheckRequest(
            session_id=request.session_id,
            step_id=request.step_id,
            image_path=temp_image_path,
            audio_path=temp_audio_path,
        )

        response = await use_case.execute(use_case_request)

        # Encode feedback audio to base64
        feedback_audio_base64 = base64.b64encode(response.feedback_audio_bytes).decode(
            "utf-8"
        )

        return ExecuteCheckResponse(
            result=response.result.value,
            feedback_text=response.feedback_text,
            feedback_audio_base64=feedback_audio_base64,
            confidence_score=response.confidence_score,
            needs_review=response.needs_review,
            next_step_id=response.next_step_id,
            session_updated=response.session_updated,
        )

    except ValueError as e:
        logger.error(f"Check execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error during check execution: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute safety check",
        ) from e
    finally:
        # Clean up temporary files
        if temp_image_path.exists():
            temp_image_path.unlink()
        if temp_audio_path.exists():
            temp_audio_path.unlink()


@router.post(
    "/{check_id}/override",
    response_model=OverrideCheckResponse,
    status_code=status.HTTP_200_OK,
)
async def override_check(
    check_id: UUID,
    request: OverrideCheckRequest,
    current_user: User = Depends(get_current_user),
    session_repo: SQLAlchemyWorkSessionRepository = Depends(get_session_repository),
) -> OverrideCheckResponse:
    """Override a safety check result (supervisor only).

    Args:
        check_id: Check ID
        request: Override request with reason
        current_user: Current authenticated user (must be supervisor)
        session_repo: Session repository

    Returns:
        OverrideCheckResponse

    Raises:
        HTTPException: If check not found, not authorized, or override fails
    """
    # TODO: Implement role-based authorization for supervisors
    # For now, allow any authenticated user (will be restricted in production)

    # Find session containing this check
    # This is a simplified implementation - in production you'd have a check repository
    sessions = await session_repo.list_pending_review()

    target_session = None
    for session in sessions:
        for check in session.checks:
            if check.id == check_id:
                target_session = session
                break
        if target_session:
            break

    if not target_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Check not found"
        )

    try:
        target_session.override_last_check(request.reason, current_user.id)
        await session_repo.save(target_session)

        return OverrideCheckResponse(check_id=check_id, overridden=True)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
