"""Pydantic schemas for work session endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SafetyCheckSchema(BaseModel):
    """Safety check schema."""

    id: UUID
    step_id: UUID
    result: str  # pass, fail, override
    feedback_text: str
    confidence_score: float | None = None
    needs_review: bool = False
    checked_at: datetime
    override_reason: str | None = None
    override_by: UUID | None = None


class WorkSessionSchema(BaseModel):
    """Work session response schema."""

    id: UUID
    sop_id: UUID
    sop_title: str  # SOP title for display
    worker_id: UUID
    status: str  # in_progress, paused, completed, aborted, approved, rejected
    current_step_id: UUID | None = None
    started_at: datetime
    completed_at: datetime | None = None
    approved_at: datetime | None = None
    approved_by: UUID | None = None
    paused_at: datetime | None = None
    aborted_at: datetime | None = None
    abort_reason: str | None = None
    locked: bool
    rejection_reason: str | None = None
    checks: list[SafetyCheckSchema] = []


class StartSessionRequest(BaseModel):
    """Request to start a new work session."""

    sop_id: UUID


class StartSessionResponse(BaseModel):
    """Response from starting a session."""

    session: WorkSessionSchema
    first_step_id: UUID | None


class CompleteSessionResponse(BaseModel):
    """Response from completing a session."""

    session: WorkSessionSchema
    completed: bool


class PauseSessionResponse(BaseModel):
    """Response from pausing a session."""

    session: WorkSessionSchema


class ResumeSessionResponse(BaseModel):
    """Response from resuming a session."""

    session: WorkSessionSchema


class AbortSessionRequest(BaseModel):
    """Request to abort a session."""

    reason: str | None = None


class AbortSessionResponse(BaseModel):
    """Response from aborting a session."""

    session: WorkSessionSchema
