"""Unit tests for WorkSession domain entity."""

from datetime import datetime
from uuid import uuid4

import pytest

from src.domain.work_session.entities import (
    CheckResult,
    SessionStatus,
    WorkSession,
)


class TestWorkSessionPause:
    """Test pause functionality."""

    def test_pause_in_progress_session(self):
        """Test pausing an in-progress session."""
        session = WorkSession(sop_id=uuid4(), worker_id=uuid4())
        assert session.status == SessionStatus.IN_PROGRESS
        assert session.paused_at is None

        session.pause()

        assert session.status == SessionStatus.PAUSED
        assert session.paused_at is not None
        assert isinstance(session.paused_at, datetime)

    def test_pause_completed_session_fails(self):
        """Test that pausing a completed session raises ValueError."""
        session = WorkSession(sop_id=uuid4(), worker_id=uuid4())
        session.complete()

        with pytest.raises(ValueError, match="Can only pause in-progress sessions"):
            session.pause()

    def test_pause_paused_session_fails(self):
        """Test that pausing an already paused session raises ValueError."""
        session = WorkSession(sop_id=uuid4(), worker_id=uuid4())
        session.pause()

        with pytest.raises(ValueError, match="Can only pause in-progress sessions"):
            session.pause()

    def test_pause_locked_session_fails(self):
        """Test that pausing a locked session raises ValueError."""
        session = WorkSession(sop_id=uuid4(), worker_id=uuid4(), locked=True)

        with pytest.raises(ValueError, match="Cannot modify a locked session"):
            session.pause()


class TestWorkSessionResume:
    """Test resume functionality."""

    def test_resume_paused_session(self):
        """Test resuming a paused session."""
        session = WorkSession(sop_id=uuid4(), worker_id=uuid4())
        session.pause()

        assert session.status == SessionStatus.PAUSED
        paused_at = session.paused_at

        session.resume()

        assert session.status == SessionStatus.IN_PROGRESS
        # paused_at should remain set for audit purposes
        assert session.paused_at == paused_at

    def test_resume_in_progress_session_fails(self):
        """Test that resuming an in-progress session raises ValueError."""
        session = WorkSession(sop_id=uuid4(), worker_id=uuid4())

        with pytest.raises(ValueError, match="Only paused sessions can be resumed"):
            session.resume()

    def test_resume_completed_session_fails(self):
        """Test that resuming a completed session raises ValueError."""
        session = WorkSession(sop_id=uuid4(), worker_id=uuid4())
        session.complete()

        with pytest.raises(ValueError, match="Only paused sessions can be resumed"):
            session.resume()

    def test_resume_aborted_session_fails(self):
        """Test that resuming an aborted session raises ValueError."""
        session = WorkSession(sop_id=uuid4(), worker_id=uuid4())
        session.abort()

        with pytest.raises(ValueError, match="Only paused sessions can be resumed"):
            session.resume()

    def test_resume_locked_session_fails(self):
        """Test that resuming a locked session raises ValueError."""
        session = WorkSession(sop_id=uuid4(), worker_id=uuid4())
        session.pause()
        session.locked = True

        with pytest.raises(ValueError, match="Cannot modify a locked session"):
            session.resume()


class TestWorkSessionAbort:
    """Test abort functionality."""

    def test_abort_in_progress_session(self):
        """Test aborting an in-progress session."""
        session = WorkSession(sop_id=uuid4(), worker_id=uuid4())
        assert session.status == SessionStatus.IN_PROGRESS
        assert session.aborted_at is None
        assert session.abort_reason is None

        session.abort()

        assert session.status == SessionStatus.ABORTED
        assert session.aborted_at is not None
        assert isinstance(session.aborted_at, datetime)
        assert session.abort_reason is None

    def test_abort_with_reason(self):
        """Test aborting a session with a reason."""
        session = WorkSession(sop_id=uuid4(), worker_id=uuid4())
        reason = "Worker reassigned to different task"

        session.abort(reason)

        assert session.status == SessionStatus.ABORTED
        assert session.aborted_at is not None
        assert session.abort_reason == reason

    def test_abort_paused_session(self):
        """Test aborting a paused session."""
        session = WorkSession(sop_id=uuid4(), worker_id=uuid4())
        session.pause()

        session.abort("No longer needed")

        assert session.status == SessionStatus.ABORTED
        assert session.aborted_at is not None
        assert session.abort_reason == "No longer needed"

    def test_abort_completed_session_fails(self):
        """Test that aborting a completed session raises ValueError."""
        session = WorkSession(sop_id=uuid4(), worker_id=uuid4())
        session.complete()

        with pytest.raises(ValueError, match="Cannot abort a completed session"):
            session.abort()

    def test_abort_approved_session_fails(self):
        """Test that aborting an approved session raises ValueError."""
        session = WorkSession(sop_id=uuid4(), worker_id=uuid4())
        session.complete()
        session.approve(supervisor_id=uuid4())

        # Approved sessions are locked, so the locked check happens first
        with pytest.raises(ValueError, match="Cannot modify a locked session"):
            session.abort()

    def test_abort_rejected_session_fails(self):
        """Test that aborting a rejected session raises ValueError."""
        session = WorkSession(sop_id=uuid4(), worker_id=uuid4())
        session.complete()
        session.reject(supervisor_id=uuid4(), reason="Incorrect")

        # Rejected sessions are locked, so the locked check happens first
        with pytest.raises(ValueError, match="Cannot modify a locked session"):
            session.abort()

    def test_abort_locked_session_fails(self):
        """Test that aborting a locked session raises ValueError."""
        session = WorkSession(sop_id=uuid4(), worker_id=uuid4(), locked=True)

        with pytest.raises(ValueError, match="Cannot modify a locked session"):
            session.abort()


class TestWorkSessionPauseResumeWorkflow:
    """Test pause/resume workflow integration."""

    def test_pause_resume_maintains_checks(self):
        """Test that pausing and resuming maintains safety checks."""
        session = WorkSession(sop_id=uuid4(), worker_id=uuid4())
        step_id = uuid4()

        # Add a check
        check = session.add_check(
            step_id=step_id,
            result=CheckResult.PASS,
            feedback_text="Step verified correctly",
            confidence_score=0.95,
        )

        assert len(session.checks) == 1
        assert session.checks[0] == check

        # Pause and resume
        session.pause()
        session.resume()

        # Checks should still be present
        assert len(session.checks) == 1
        assert session.checks[0] == check
        assert session.checks[0].result == CheckResult.PASS

    def test_cannot_add_check_to_paused_session(self):
        """Test that adding checks to paused session raises ValueError."""
        session = WorkSession(sop_id=uuid4(), worker_id=uuid4())
        session.pause()

        with pytest.raises(ValueError, match="Cannot add checks to a paused session"):
            session.add_check(
                step_id=uuid4(),
                result=CheckResult.PASS,
                feedback_text="Test",
            )

    def test_cannot_add_check_to_aborted_session(self):
        """Test that adding checks to aborted session raises ValueError."""
        session = WorkSession(sop_id=uuid4(), worker_id=uuid4())
        session.abort()

        with pytest.raises(ValueError, match="Cannot add checks to an aborted session"):
            session.add_check(
                step_id=uuid4(),
                result=CheckResult.PASS,
                feedback_text="Test",
            )

    def test_cannot_advance_paused_session(self):
        """Test that advancing a paused session raises ValueError."""
        session = WorkSession(sop_id=uuid4(), worker_id=uuid4())
        session.pause()

        with pytest.raises(ValueError, match="Cannot advance a paused session"):
            session.advance_to_next_step(uuid4())

    def test_cannot_advance_aborted_session(self):
        """Test that advancing an aborted session raises ValueError."""
        session = WorkSession(sop_id=uuid4(), worker_id=uuid4())
        session.abort()

        with pytest.raises(ValueError, match="Cannot advance an aborted session"):
            session.advance_to_next_step(uuid4())

    def test_multiple_pause_resume_cycles(self):
        """Test multiple pause/resume cycles work correctly."""
        session = WorkSession(sop_id=uuid4(), worker_id=uuid4())

        # First cycle
        session.pause()
        assert session.status == SessionStatus.PAUSED
        first_paused_at = session.paused_at

        session.resume()
        assert session.status == SessionStatus.IN_PROGRESS

        # Second cycle
        session.pause()
        assert session.status == SessionStatus.PAUSED
        second_paused_at = session.paused_at

        # Second pause should have a later timestamp
        assert second_paused_at >= first_paused_at

        session.resume()
        assert session.status == SessionStatus.IN_PROGRESS


class TestWorkSessionAbortRetainsChecks:
    """Test that aborted sessions retain audit trail."""

    def test_abort_retains_safety_checks(self):
        """Test that aborting a session retains all safety checks."""
        session = WorkSession(sop_id=uuid4(), worker_id=uuid4())
        step1_id = uuid4()
        step2_id = uuid4()

        check1 = session.add_check(
            step_id=step1_id,
            result=CheckResult.PASS,
            feedback_text="First step OK",
        )
        check2 = session.add_check(
            step_id=step2_id,
            result=CheckResult.FAIL,
            feedback_text="Second step failed",
            needs_review=True,
        )

        assert len(session.checks) == 2

        session.abort("Failed quality check")

        # Checks should still be present for audit trail
        assert len(session.checks) == 2
        assert session.checks[0] == check1
        assert session.checks[1] == check2
        assert session.checks[1].needs_review is True
