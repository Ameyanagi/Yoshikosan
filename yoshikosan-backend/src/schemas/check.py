"""Pydantic schemas for safety check endpoints."""

from uuid import UUID

from pydantic import BaseModel


class ExecuteCheckRequest(BaseModel):
    """Request to execute a safety check."""

    session_id: UUID
    step_id: UUID
    image_base64: str
    audio_base64: str


class ExecuteCheckResponse(BaseModel):
    """Response from executing a safety check."""

    result: str  # pass, fail
    feedback_text: str
    feedback_audio_base64: str
    confidence_score: float
    needs_review: bool
    next_step_id: UUID | None
    session_updated: bool


class OverrideCheckRequest(BaseModel):
    """Request to override a safety check."""

    reason: str


class OverrideCheckResponse(BaseModel):
    """Response from overriding a check."""

    check_id: UUID
    overridden: bool
