"""Mapper for WorkSession domain entities and database models."""

from src.domain.work_session.entities import (
    CheckResult,
    SafetyCheck,
    SessionStatus,
    WorkSession,
)
from src.infrastructure.database.models import SafetyCheckModel, WorkSessionModel


def check_to_domain(model: SafetyCheckModel) -> SafetyCheck:
    """Convert SafetyCheckModel to SafetyCheck domain entity.

    Args:
        model: SafetyCheckModel instance

    Returns:
        SafetyCheck domain entity
    """
    return SafetyCheck(
        id=model.id,
        step_id=model.step_id,
        result=CheckResult(model.result),
        feedback_text=model.feedback_text,
        feedback_audio_url=model.feedback_audio_url,
        confidence_score=model.confidence_score,
        needs_review=model.needs_review,
        checked_at=model.checked_at,
        override_reason=model.override_reason,
        override_by=model.override_by,
    )


def check_to_model(entity: SafetyCheck, session_id: object) -> SafetyCheckModel:
    """Convert SafetyCheck domain entity to SafetyCheckModel.

    Args:
        entity: SafetyCheck domain entity
        session_id: Session ID for foreign key

    Returns:
        SafetyCheckModel instance
    """
    return SafetyCheckModel(
        id=entity.id,
        session_id=session_id,
        step_id=entity.step_id,
        result=entity.result.value,
        feedback_text=entity.feedback_text,
        feedback_audio_url=entity.feedback_audio_url,
        confidence_score=entity.confidence_score,
        needs_review=entity.needs_review,
        checked_at=entity.checked_at,
        override_reason=entity.override_reason,
        override_by=entity.override_by,
    )


def session_to_domain(model: WorkSessionModel) -> WorkSession:
    """Convert WorkSessionModel to WorkSession domain entity.

    Args:
        model: WorkSessionModel instance

    Returns:
        WorkSession domain entity with safety checks
    """
    return WorkSession(
        id=model.id,
        sop_id=model.sop_id,
        worker_id=model.worker_id,
        status=SessionStatus(model.status),
        current_step_id=model.current_step_id,
        started_at=model.started_at,
        completed_at=model.completed_at,
        approved_at=model.approved_at,
        approved_by=model.approved_by,
        locked=model.locked,
        rejection_reason=model.rejection_reason,
        checks=[check_to_domain(c) for c in model.checks],
    )


def session_to_model(entity: WorkSession) -> WorkSessionModel:
    """Convert WorkSession domain entity to WorkSessionModel.

    Args:
        entity: WorkSession domain entity

    Returns:
        WorkSessionModel instance with safety checks
    """
    model = WorkSessionModel(
        id=entity.id,
        sop_id=entity.sop_id,
        worker_id=entity.worker_id,
        status=entity.status.value,
        current_step_id=entity.current_step_id,
        started_at=entity.started_at,
        completed_at=entity.completed_at,
        approved_at=entity.approved_at,
        approved_by=entity.approved_by,
        locked=entity.locked,
        rejection_reason=entity.rejection_reason,
    )
    model.checks = [check_to_model(c, entity.id) for c in entity.checks]
    return model
