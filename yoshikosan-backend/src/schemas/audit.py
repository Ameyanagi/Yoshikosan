"""Pydantic schemas for audit endpoints."""

from uuid import UUID

from pydantic import BaseModel

from src.schemas.session import WorkSessionSchema


class AuditSessionListItem(BaseModel):
    """Audit session list item."""

    session_id: UUID
    sop_title: str
    worker_id: UUID
    status: str
    completed_at: str | None
    check_count: int
    failed_check_count: int


class ApproveSessionRequest(BaseModel):
    """Request to approve a session."""

    pass  # No body needed, supervisor from auth


class ApproveSessionResponse(BaseModel):
    """Response from approving a session."""

    session: WorkSessionSchema
    approved: bool


class RejectSessionRequest(BaseModel):
    """Request to reject a session."""

    reason: str


class RejectSessionResponse(BaseModel):
    """Response from rejecting a session."""

    session: WorkSessionSchema
    rejected: bool
