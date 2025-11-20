"""SOP management endpoints."""

import logging
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from src.api.dependencies.auth import get_current_user
from src.api.dependencies.repositories import get_sop_repository
from src.application.sop.structure_sop import (
    StructureSOPRequest,
    StructureSOPUseCase,
)
from src.application.sop.upload_sop import (
    UploadSOPRequest,
    UploadSOPUseCase,
)
from src.domain.sop.entities import SOP
from src.domain.user.entities import User
from src.infrastructure.database.repositories.sop_repository import (
    SQLAlchemySOPRepository,
)
from src.schemas.sop import (
    HazardSchema,
    SOPListItemSchema,
    SOPSchema,
    StepSchema,
    TaskSchema,
    UploadSOPResponse,
)

router = APIRouter(prefix="/sops", tags=["sops"])
logger = logging.getLogger(__name__)


def sop_to_schema(sop: SOP) -> SOPSchema:
    """Convert SOP domain entity to Pydantic schema.

    Args:
        sop: SOP domain entity

    Returns:
        SOPSchema
    """
    return SOPSchema(
        id=sop.id,
        title=sop.title,
        created_by=sop.created_by,
        created_at=sop.created_at,
        updated_at=sop.updated_at,
        deleted_at=sop.deleted_at,
        tasks=[
            TaskSchema(
                id=task.id,
                title=task.title,
                description=task.description,
                order_index=task.order_index,
                steps=[
                    StepSchema(
                        id=step.id,
                        description=step.description,
                        order_index=step.order_index,
                        expected_action=step.expected_action,
                        expected_result=step.expected_result,
                        hazards=[
                            HazardSchema(
                                id=hazard.id,
                                description=hazard.description,
                                severity=hazard.severity,
                                mitigation=hazard.mitigation,
                            )
                            for hazard in step.hazards
                        ],
                    )
                    for step in task.steps
                ],
            )
            for task in sop.tasks
        ],
    )


@router.post("", response_model=UploadSOPResponse, status_code=status.HTTP_201_CREATED)
async def upload_and_structure_sop(
    title: Annotated[str, Form()],
    images: list[UploadFile] = File(default=[]),
    text_content: Annotated[str | None, Form()] = None,
    current_user: User = Depends(get_current_user),
    sop_repo: SQLAlchemySOPRepository = Depends(get_sop_repository),
) -> UploadSOPResponse:
    """Upload and structure a new SOP.

    Accepts optional image files and/or text content, uses AI to structure the SOP.
    At least one of images or text_content must be provided.

    Args:
        title: SOP title
        images: Optional list of image files
        text_content: Optional text content
        current_user: Current authenticated user
        sop_repo: SOP repository

    Returns:
        UploadSOPResponse with structured SOP ID

    Raises:
        HTTPException: If upload or structuring fails, or if neither images nor text provided
    """
    # Validate that at least one of images or text_content is provided
    if not images and not text_content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one of images or text content must be provided",
        )

    # Save uploaded files to temporary directory
    temp_dir = Path("/tmp") / "sop_uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_image_paths: list[Path] = []

    try:
        # Save uploaded images
        for image in images:
            if not image.filename:
                continue

            temp_path = temp_dir / image.filename
            content = await image.read()
            temp_path.write_bytes(content)
            temp_image_paths.append(temp_path)

        # Execute upload use case
        upload_use_case = UploadSOPUseCase(sop_repo)
        upload_request = UploadSOPRequest(
            title=title,
            created_by=current_user.id,
            image_paths=temp_image_paths,
            text_content=text_content,
        )

        upload_response = await upload_use_case.execute(upload_request)

        # Execute structure use case
        structure_use_case = StructureSOPUseCase(sop_repo)
        structure_request = StructureSOPRequest(
            sop_id=upload_response.sop_id,
            image_paths=upload_response.image_paths,
            text_content=text_content,
        )

        structure_response = await structure_use_case.execute(structure_request)

        return UploadSOPResponse(
            sop_id=structure_response.sop.id,
            title=structure_response.sop.title,
            success=structure_response.success,
            error_message=structure_response.error_message,
        )

    except Exception as e:
        logger.error(f"Failed to upload and structure SOP: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process SOP: {str(e)}",
        ) from e
    finally:
        # Clean up temporary files
        for temp_path in temp_image_paths:
            if temp_path.exists():
                temp_path.unlink()


@router.get("", response_model=list[SOPListItemSchema])
async def list_sops(
    current_user: User = Depends(get_current_user),
    sop_repo: SQLAlchemySOPRepository = Depends(get_sop_repository),
) -> list[SOPListItemSchema]:
    """List all SOPs for the current user.

    Args:
        current_user: Current authenticated user
        sop_repo: SOP repository

    Returns:
        List of SOPListItemSchema
    """
    sops = await sop_repo.list_by_user(current_user.id, include_deleted=False)

    return [
        SOPListItemSchema(
            id=sop.id,
            title=sop.title,
            created_by=sop.created_by,
            created_at=sop.created_at,
            updated_at=sop.updated_at,
            task_count=len(sop.tasks),
            step_count=sum(len(task.steps) for task in sop.tasks),
        )
        for sop in sops
    ]


@router.get("/{sop_id}", response_model=SOPSchema)
async def get_sop(
    sop_id: UUID,
    current_user: User = Depends(get_current_user),
    sop_repo: SQLAlchemySOPRepository = Depends(get_sop_repository),
) -> SOPSchema:
    """Get SOP details by ID.

    Args:
        sop_id: SOP ID
        current_user: Current authenticated user
        sop_repo: SOP repository

    Returns:
        SOPSchema

    Raises:
        HTTPException: If SOP not found or user not authorized
    """
    sop = await sop_repo.get_by_id(sop_id)

    if not sop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="SOP not found"
        )

    # Authorization: only creator can view
    if sop.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this SOP",
        )

    return sop_to_schema(sop)


@router.delete("/{sop_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sop(
    sop_id: UUID,
    current_user: User = Depends(get_current_user),
    sop_repo: SQLAlchemySOPRepository = Depends(get_sop_repository),
) -> None:
    """Soft delete an SOP.

    Args:
        sop_id: SOP ID
        current_user: Current authenticated user
        sop_repo: SOP repository

    Raises:
        HTTPException: If SOP not found or user not authorized
    """
    sop = await sop_repo.get_by_id(sop_id)

    if not sop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="SOP not found"
        )

    # Authorization: only creator can delete
    if sop.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this SOP",
        )

    await sop_repo.delete(sop_id)
