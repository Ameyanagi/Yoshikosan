"""Work session domain entities following DDD principles."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class SessionStatus(str, Enum):
    """Work session status."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    APPROVED = "approved"
    REJECTED = "rejected"


class CheckResult(str, Enum):
    """Safety check result."""

    PASS = "pass"
    FAIL = "fail"
    OVERRIDE = "override"


@dataclass
class SafetyCheck:
    """Safety check performed during a work session."""

    step_id: UUID
    result: CheckResult
    feedback_text: str
    id: UUID = field(default_factory=uuid4)
    feedback_audio_url: str | None = None
    confidence_score: float | None = None
    needs_review: bool = False
    checked_at: datetime = field(default_factory=datetime.now)
    override_reason: str | None = None
    override_by: UUID | None = None

    def __post_init__(self) -> None:
        """Validate safety check after initialization."""
        if not self.feedback_text.strip():
            raise ValueError("Feedback text cannot be empty")
        if self.confidence_score is not None and not (
            0.0 <= self.confidence_score <= 1.0
        ):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        if self.result == CheckResult.OVERRIDE and not self.override_reason:
            raise ValueError("Override result requires override_reason")
        if self.result == CheckResult.OVERRIDE and not self.override_by:
            raise ValueError("Override result requires override_by")


@dataclass
class WorkSession:
    """Work session aggregate root tracking worker progress through an SOP."""

    sop_id: UUID
    worker_id: UUID
    id: UUID = field(default_factory=uuid4)
    status: SessionStatus = SessionStatus.IN_PROGRESS
    current_step_id: UUID | None = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    approved_at: datetime | None = None
    approved_by: UUID | None = None
    locked: bool = False
    rejection_reason: str | None = None
    checks: list[SafetyCheck] = field(default_factory=list)

    def _ensure_not_locked(self) -> None:
        """Raise ValueError if session is locked."""
        if self.locked:
            raise ValueError("Cannot modify a locked session")

    def add_check(
        self,
        step_id: UUID,
        result: CheckResult,
        feedback_text: str,
        feedback_audio_url: str | None = None,
        confidence_score: float | None = None,
        needs_review: bool = False,
    ) -> SafetyCheck:
        """Add a safety check to this session.

        Args:
            step_id: ID of the step being checked
            result: Check result (pass/fail/override)
            feedback_text: Feedback message for the worker
            feedback_audio_url: Optional URL to audio feedback file
            confidence_score: Optional AI confidence score (0.0-1.0)
            needs_review: Whether this check needs supervisor review

        Returns:
            The created SafetyCheck instance

        Raises:
            ValueError: If session is locked or not in progress
        """
        self._ensure_not_locked()
        if self.status != SessionStatus.IN_PROGRESS:
            raise ValueError("Can only add checks to in-progress sessions")

        check = SafetyCheck(
            step_id=step_id,
            result=result,
            feedback_text=feedback_text,
            feedback_audio_url=feedback_audio_url,
            confidence_score=confidence_score,
            needs_review=needs_review,
        )
        self.checks.append(check)
        return check

    def advance_to_next_step(self, next_step_id: UUID | None) -> None:
        """Advance session to the next step.

        Args:
            next_step_id: ID of next step, or None if session is complete

        Raises:
            ValueError: If session is locked or not in progress
        """
        self._ensure_not_locked()
        if self.status != SessionStatus.IN_PROGRESS:
            raise ValueError("Can only advance in-progress sessions")

        self.current_step_id = next_step_id

        # If no next step, automatically complete the session
        if next_step_id is None:
            self.complete()

    def complete(self) -> None:
        """Mark session as completed.

        Raises:
            ValueError: If session is locked or not in progress
        """
        self._ensure_not_locked()
        if self.status != SessionStatus.IN_PROGRESS:
            raise ValueError("Can only complete in-progress sessions")

        self.status = SessionStatus.COMPLETED
        self.completed_at = datetime.now()

    def approve(self, supervisor_id: UUID) -> None:
        """Approve this session and lock it.

        Args:
            supervisor_id: ID of the approving supervisor

        Raises:
            ValueError: If session is not completed or already locked
        """
        self._ensure_not_locked()
        if self.status != SessionStatus.COMPLETED:
            raise ValueError("Can only approve completed sessions")

        self.status = SessionStatus.APPROVED
        self.approved_at = datetime.now()
        self.approved_by = supervisor_id
        self.locked = True

    def reject(self, supervisor_id: UUID, reason: str) -> None:
        """Reject this session with a reason and lock it.

        Args:
            supervisor_id: ID of the rejecting supervisor
            reason: Reason for rejection

        Raises:
            ValueError: If session is not completed, already locked, or reason is empty
        """
        self._ensure_not_locked()
        if self.status != SessionStatus.COMPLETED:
            raise ValueError("Can only reject completed sessions")
        if not reason.strip():
            raise ValueError("Rejection reason is required")

        self.status = SessionStatus.REJECTED
        self.rejection_reason = reason
        self.approved_by = supervisor_id  # Track who rejected it
        self.locked = True

    def override_check(self, check_id: UUID, reason: str, supervisor_id: UUID) -> None:
        """Override a specific safety check result.

        Args:
            check_id: ID of the check to override
            reason: Reason for the override
            supervisor_id: ID of the supervisor performing override

        Raises:
            ValueError: If session is locked, check not found, or reason is empty
        """
        self._ensure_not_locked()
        if not reason.strip():
            raise ValueError("Override reason is required")

        # Find the check by ID
        target_check = None
        for check in self.checks:
            if check.id == check_id:
                target_check = check
                break

        if not target_check:
            raise ValueError(f"Check {check_id} not found in session")

        target_check.result = CheckResult.OVERRIDE
        target_check.override_reason = reason
        target_check.override_by = supervisor_id

    def override_last_check(self, reason: str, supervisor_id: UUID) -> None:
        """Override the result of the last safety check.

        Args:
            reason: Reason for the override
            supervisor_id: ID of the supervisor performing override

        Raises:
            ValueError: If session is locked, no checks exist, or reason is empty
        """
        self._ensure_not_locked()
        if not self.checks:
            raise ValueError("No checks to override")
        if not reason.strip():
            raise ValueError("Override reason is required")

        last_check = self.checks[-1]
        last_check.result = CheckResult.OVERRIDE
        last_check.override_reason = reason
        last_check.override_by = supervisor_id

    def get_latest_audio_url(self) -> str | None:
        """Get the most recent audio feedback URL.

        Returns:
            URL to the latest audio feedback, or None if no audio available
        """
        checks_with_audio = [c for c in self.checks if c.feedback_audio_url]
        if not checks_with_audio:
            return None

        latest_check = max(checks_with_audio, key=lambda c: c.checked_at)
        return latest_check.feedback_audio_url
