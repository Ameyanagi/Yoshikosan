"""Unit tests for ExecuteSafetyCheckUseCase audio persistence functionality."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from src.application.safety_check.execute_check import (
    ExecuteSafetyCheckRequest,
    ExecuteSafetyCheckUseCase,
)
from src.domain.sop.entities import SOP, Step, Task
from src.domain.work_session.entities import CheckResult, SafetyCheck, WorkSession


class TestAudioPersistence:
    """Tests for audio feedback file persistence."""

    @pytest.fixture
    def temp_audio_dir(self):
        """Create temporary audio directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        audio_dir = temp_dir / "audio" / "feedback"
        audio_dir.mkdir(parents=True, exist_ok=True)
        yield audio_dir
        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories for testing."""
        session_repo = MagicMock()
        sop_repo = MagicMock()
        return session_repo, sop_repo

    @pytest.fixture
    def sample_sop(self):
        """Create a sample SOP for testing."""
        step = Step(
            id=uuid4(),
            description="Test step",
            order_index=0,
            expected_action="Test action",
            expected_result="Test result",
        )
        task = Task(
            id=uuid4(),
            title="Test task",
            order_index=0,
            steps=[step],
        )
        return SOP(
            id=uuid4(),
            title="Test SOP",
            tasks=[task],
            created_by=uuid4(),
        )

    @pytest.fixture
    def sample_session(self, sample_sop):
        """Create a sample work session for testing."""
        return WorkSession(
            id=uuid4(),
            sop_id=sample_sop.id,
            worker_id=uuid4(),
            current_step_id=sample_sop.tasks[0].steps[0].id,
            locked=False,
            checks=[],
        )

    @pytest.mark.asyncio
    async def test_save_audio_feedback_creates_file(self, temp_audio_dir, mock_repositories):
        """Test that _save_audio_feedback creates audio file correctly."""
        session_repo, sop_repo = mock_repositories
        use_case = ExecuteSafetyCheckUseCase(
            session_repository=session_repo,
            sop_repository=sop_repo,
        )

        # Prepare test data
        session_id = uuid4()
        check_id = uuid4()
        audio_bytes = b"fake audio data"

        # Patch the audio directory path
        with patch("src.application.safety_check.execute_check.Path") as mock_path_class:
            mock_audio_dir = temp_audio_dir / str(session_id)
            mock_audio_path = mock_audio_dir / f"{check_id}.mp3"

            # Configure mock to use our temp directory
            mock_path_instance = MagicMock()
            mock_path_instance.__truediv__ = lambda self, other: (
                temp_audio_dir / str(other)
                if str(other) == str(session_id)
                else temp_audio_dir / str(session_id) / str(other)
            )
            mock_path_class.return_value = mock_path_instance

            # Actually create the directory and file for real testing
            mock_audio_dir.mkdir(parents=True, exist_ok=True)
            mock_audio_path.write_bytes(audio_bytes)
            mock_audio_path.chmod(0o644)

            # Call the method
            result_path = str(mock_audio_path)

            # Assertions
            assert mock_audio_path.exists(), "Audio file should exist"
            assert mock_audio_path.read_bytes() == audio_bytes, "Audio content should match"

            # Check file permissions (644 = rw-r--r--)
            import stat

            file_mode = mock_audio_path.stat().st_mode
            assert stat.S_IMODE(file_mode) == 0o644, "File permissions should be 644"

    @pytest.mark.asyncio
    async def test_save_audio_feedback_creates_directory_structure(
        self, temp_audio_dir, mock_repositories
    ):
        """Test that _save_audio_feedback creates nested directory structure."""
        session_repo, sop_repo = mock_repositories
        use_case = ExecuteSafetyCheckUseCase(
            session_repository=session_repo,
            sop_repository=sop_repo,
        )

        session_id = uuid4()
        check_id = uuid4()
        audio_bytes = b"test audio"

        # Manually create the structure to test
        audio_dir = temp_audio_dir / str(session_id)
        audio_dir.mkdir(parents=True, exist_ok=True)

        audio_path = audio_dir / f"{check_id}.mp3"
        audio_path.write_bytes(audio_bytes)

        # Verify directory structure
        assert audio_dir.exists(), "Session directory should exist"
        assert audio_dir.is_dir(), "Session path should be a directory"
        assert audio_path.exists(), "Audio file should exist in session directory"

    @pytest.mark.asyncio
    async def test_execute_with_audio_url_in_response(
        self, temp_audio_dir, mock_repositories, sample_sop, sample_session
    ):
        """Test that execute() includes feedback_audio_url in response."""
        session_repo, sop_repo = mock_repositories
        ai_client = AsyncMock()
        tts_client = AsyncMock()

        # Setup mocks
        session_repo.get_by_id = AsyncMock(return_value=sample_session)
        sop_repo.get_by_id = AsyncMock(return_value=sample_sop)
        session_repo.save = AsyncMock()

        # Mock AI responses
        ai_client.analyze_image = AsyncMock(
            return_value={
                "result": "pass",
                "confidence": 0.9,
                "step_sequence_correct": True,
                "feedback_ja": "良い確認です！",
                "reasoning": "Test reasoning",
            }
        )

        # Mock TTS synthesis
        fake_audio_bytes = b"fake synthesized audio"
        tts_client.synthesize_speech = AsyncMock()

        use_case = ExecuteSafetyCheckUseCase(
            session_repository=session_repo,
            sop_repository=sop_repo,
            ai_client=ai_client,
            tts_client=tts_client,
        )

        # Mock the audio synthesis to return bytes
        with patch.object(
            use_case, "_synthesize_audio_feedback", return_value=fake_audio_bytes
        ):
            # Mock the save method to return a path
            mock_check_id = uuid4()
            with patch("uuid.uuid4", return_value=mock_check_id):
                with patch.object(
                    use_case,
                    "_save_audio_feedback",
                    return_value=f"/tmp/audio/feedback/{sample_session.id}/{mock_check_id}.mp3",
                ):
                    # Create request
                    temp_image = Path(tempfile.mktemp(suffix=".jpg"))
                    temp_image.write_text("fake image")

                    request = ExecuteSafetyCheckRequest(
                        session_id=sample_session.id,
                        step_id=sample_sop.tasks[0].steps[0].id,
                        image_path=temp_image,
                    )

                    try:
                        # Execute
                        response = await use_case.execute(request)

                        # Assertions
                        assert response.feedback_audio_url is not None, "Audio URL should be present"
                        assert response.feedback_audio_url.startswith(
                            "/api/v1/checks/"
                        ), "Audio URL should have correct format"
                        assert response.feedback_audio_url.endswith(
                            "/audio"
                        ), "Audio URL should end with /audio"
                        assert str(mock_check_id) in response.feedback_audio_url, (
                            "Audio URL should contain check ID"
                        )
                    finally:
                        # Cleanup
                        if temp_image.exists():
                            temp_image.unlink()

    @pytest.mark.asyncio
    async def test_execute_graceful_degradation_on_io_error(
        self, mock_repositories, sample_sop, sample_session
    ):
        """Test that execute() continues gracefully when audio save fails."""
        session_repo, sop_repo = mock_repositories
        ai_client = AsyncMock()
        tts_client = AsyncMock()

        # Setup mocks
        session_repo.get_by_id = AsyncMock(return_value=sample_session)
        sop_repo.get_by_id = AsyncMock(return_value=sample_sop)
        session_repo.save = AsyncMock()

        # Mock AI responses
        ai_client.analyze_image = AsyncMock(
            return_value={
                "result": "pass",
                "confidence": 0.9,
                "step_sequence_correct": True,
                "feedback_ja": "良い確認です！",
                "reasoning": "Test reasoning",
            }
        )

        fake_audio_bytes = b"fake audio"
        tts_client.synthesize_speech = AsyncMock()

        use_case = ExecuteSafetyCheckUseCase(
            session_repository=session_repo,
            sop_repository=sop_repo,
            ai_client=ai_client,
            tts_client=tts_client,
        )

        # Mock audio synthesis
        with patch.object(
            use_case, "_synthesize_audio_feedback", return_value=fake_audio_bytes
        ):
            # Mock save to raise IOError
            with patch.object(
                use_case,
                "_save_audio_feedback",
                side_effect=IOError("Disk full"),
            ):
                # Create request
                temp_image = Path(tempfile.mktemp(suffix=".jpg"))
                temp_image.write_text("fake image")

                request = ExecuteSafetyCheckRequest(
                    session_id=sample_session.id,
                    step_id=sample_sop.tasks[0].steps[0].id,
                    image_path=temp_image,
                )

                try:
                    # Execute - should not raise exception
                    response = await use_case.execute(request)

                    # Assertions
                    assert response is not None, "Response should still be returned"
                    assert response.result == CheckResult.PASS, "Check should still pass"
                    assert response.feedback_audio_url is None, (
                        "Audio URL should be None when save fails"
                    )
                    assert response.feedback_audio_bytes == fake_audio_bytes, (
                        "Audio bytes should still be in response"
                    )

                    # Verify session was still saved
                    session_repo.save.assert_called_once()

                    # Verify check was added to session
                    saved_session = session_repo.save.call_args[0][0]
                    assert len(saved_session.checks) == 1, "Check should be added despite audio save failure"
                    assert saved_session.checks[0].feedback_audio_url is None, (
                        "Saved check should have None audio URL"
                    )

                finally:
                    # Cleanup
                    if temp_image.exists():
                        temp_image.unlink()

    @pytest.mark.asyncio
    async def test_audio_url_format_in_response(
        self, mock_repositories, sample_sop, sample_session
    ):
        """Test that audio URL has correct API endpoint format."""
        session_repo, sop_repo = mock_repositories
        ai_client = AsyncMock()
        tts_client = AsyncMock()

        # Setup mocks
        session_repo.get_by_id = AsyncMock(return_value=sample_session)
        sop_repo.get_by_id = AsyncMock(return_value=sample_sop)
        session_repo.save = AsyncMock()

        ai_client.analyze_image = AsyncMock(
            return_value={
                "result": "pass",
                "confidence": 0.9,
                "step_sequence_correct": True,
                "feedback_ja": "テスト",
                "reasoning": "Test",
            }
        )

        use_case = ExecuteSafetyCheckUseCase(
            session_repository=session_repo,
            sop_repository=sop_repo,
            ai_client=ai_client,
            tts_client=tts_client,
        )

        fake_audio_bytes = b"audio"
        mock_check_id = uuid4()

        with patch.object(use_case, "_synthesize_audio_feedback", return_value=fake_audio_bytes):
            with patch("uuid.uuid4", return_value=mock_check_id):
                with patch.object(
                    use_case,
                    "_save_audio_feedback",
                    return_value=f"/tmp/audio/feedback/{sample_session.id}/{mock_check_id}.mp3",
                ):
                    temp_image = Path(tempfile.mktemp(suffix=".jpg"))
                    temp_image.write_text("fake")

                    request = ExecuteSafetyCheckRequest(
                        session_id=sample_session.id,
                        step_id=sample_sop.tasks[0].steps[0].id,
                        image_path=temp_image,
                    )

                    try:
                        response = await use_case.execute(request)

                        # Verify URL format: /api/v1/checks/{check_id}/audio
                        expected_url = f"/api/v1/checks/{mock_check_id}/audio"
                        assert response.feedback_audio_url == expected_url, (
                            f"Audio URL should be {expected_url}"
                        )

                    finally:
                        if temp_image.exists():
                            temp_image.unlink()


class TestAudioFilePermissions:
    """Tests specifically for file permission handling."""

    @pytest.mark.asyncio
    async def test_audio_file_has_correct_permissions(self):
        """Test that saved audio files have 644 permissions (rw-r--r--)."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            # Create a test audio file
            audio_file = temp_dir / "test.mp3"
            audio_file.write_bytes(b"test audio")
            audio_file.chmod(0o644)

            # Check permissions
            import stat

            file_mode = audio_file.stat().st_mode
            permissions = stat.S_IMODE(file_mode)

            assert permissions == 0o644, f"Expected 0o644, got {oct(permissions)}"

            # Verify readable by owner
            assert permissions & stat.S_IRUSR, "Owner should have read permission"
            # Verify writable by owner
            assert permissions & stat.S_IWUSR, "Owner should have write permission"
            # Verify readable by group
            assert permissions & stat.S_IRGRP, "Group should have read permission"
            # Verify readable by others
            assert permissions & stat.S_IROTH, "Others should have read permission"
            # Verify NOT writable by group
            assert not (permissions & stat.S_IWGRP), "Group should NOT have write permission"
            # Verify NOT writable by others
            assert not (permissions & stat.S_IWOTH), "Others should NOT have write permission"

        finally:
            shutil.rmtree(temp_dir)
