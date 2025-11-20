"""Pydantic schemas for SOP endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class HazardSchema(BaseModel):
    """Hazard schema."""

    id: UUID
    description: str
    severity: str
    mitigation: str | None = None


class StepSchema(BaseModel):
    """Step schema."""

    id: UUID
    description: str
    order_index: int
    expected_action: str | None = None
    expected_result: str | None = None
    hazards: list[HazardSchema] = []


class TaskSchema(BaseModel):
    """Task schema."""

    id: UUID
    title: str
    description: str | None = None
    order_index: int
    steps: list[StepSchema] = []


class SOPSchema(BaseModel):
    """SOP response schema."""

    id: UUID
    title: str
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    tasks: list[TaskSchema] = []


class SOPListItemSchema(BaseModel):
    """SOP list item schema (without tasks)."""

    id: UUID
    title: str
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    task_count: int
    step_count: int


class UploadSOPRequest(BaseModel):
    """Request to upload and structure an SOP."""

    title: str = Field(..., min_length=1, max_length=500)
    text_content: str | None = None


class UploadSOPResponse(BaseModel):
    """Response from uploading an SOP."""

    sop_id: UUID
    title: str
    success: bool
    error_message: str | None = None


class UpdateSOPRequest(BaseModel):
    """Request to update an SOP."""

    title: str | None = None
    tasks: list[TaskSchema] | None = None


class UpdateSOPResponse(BaseModel):
    """Response from updating an SOP."""

    sop: SOPSchema
    updated: bool
