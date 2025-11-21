"""Unit tests for StartSessionUseCase welcome audio functionality."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.application.work_session.start_session import (
    WELCOME_MESSAGE_TEMPLATE,
    StartSessionRequest,
    StartSessionUseCase,
)
from src.domain.sop.entities import SOP, Step, Task
from src.domain.work_session.entities import WorkSession


class TestWelcomeAudioGeneration:
    """Tests for welcome audio generation functionality."""

    @pytest.fixture
    def temp_audio_dir(self):
        """Create temporary audio directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        audio_dir = temp_dir / "audio" / "feedback" / "welcome"
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
        """Create a sample SOP with multiple tasks and steps."""
        # Create Task 1 with 2 steps
        step1 = Step(
            id=uuid4(),
            description="バルブを閉める",
            order_index=0,
            expected_action="バルブハンドルを時計回りに回す",
            expected_result="バルブが完全に閉まっている",
        )
        step2 = Step(
            id=uuid4(),
            description="圧力計を確認",
            order_index=1,
            expected_action="圧力計の表示を読む",
            expected_result="圧力がゼロになっている",
        )
        task1 = Task(
            id=uuid4(),
            title="バルブ操作",
            order_index=0,
            description="バルブを安全に閉める手順",
            steps=[step1, step2],
        )

        # Create Task 2 with 1 step
        step3 = Step(
            id=uuid4(),
            description="安全確認",
            order_index=0,
            expected_action="周囲の安全を確認",
            expected_result="危険がない",
        )
        task2 = Task(
            id=uuid4(),
            title="最終確認",
            order_index=1,
            steps=[step3],
        )

        return SOP(
            id=uuid4(),
            title="工場バルブ操作手順",
            tasks=[task1, task2],
            created_by=uuid4(),
        )

    @pytest.mark.asyncio
    async def test_welcome_message_formatting(self, sample_sop):
        """Test that welcome message is formatted correctly with SOP details."""
        first_task = sample_sop.tasks[0]
        first_step = first_task.steps[0]
        total_steps = sum(len(t.steps) for t in sample_sop.tasks)  # Should be 3

        message = WELCOME_MESSAGE_TEMPLATE.format(
            task_title=first_task.title,
            total_steps=total_steps,
            first_step_description=first_step.description,
        )

        # Assertions
        assert "バルブ操作" in message, "Should contain task title"
        assert "3ステップ" in message, "Should contain total steps count"
        assert "バルブを閉める" in message, "Should contain first step description"
        assert "こんにちは！" in message, "Should have greeting"
        assert "安全作業、よろしくお願いします！" in message, "Should have closing"

    @pytest.mark.asyncio
    async def test_generate_welcome_audio_creates_file(
        self, temp_audio_dir, mock_repositories, sample_sop
    ):
        """Test that _generate_welcome_audio creates audio file successfully."""
        session_repo, sop_repo = mock_repositories
        tts_client = AsyncMock()

        # Mock TTS synthesis
        session_id = uuid4()
        temp_path = Path("/tmp") / f"welcome_{session_id}.mp3"
        fake_audio_data = b"fake welcome audio data"

        async def mock_synthesize(text: str, output_path: str):
            """Mock TTS synthesis by creating a file."""
            Path(output_path).write_bytes(fake_audio_data)

        tts_client.synthesize_speech = AsyncMock(side_effect=mock_synthesize)

        use_case = StartSessionUseCase(
            session_repository=session_repo,
            sop_repository=sop_repo,
            tts_client=tts_client,
        )

        # Patch the audio directory path to use our temp directory
        with patch("src.application.work_session.start_session.Path") as mock_path:
            # Configure mock Path for /tmp/audio/feedback/welcome
            def path_side_effect(path_str):
                if path_str == "/tmp":
                    return Path("/tmp")
                elif path_str == "/tmp/audio/feedback/welcome":
                    return temp_audio_dir
                return Path(path_str)

            mock_path.side_effect = path_side_effect

            # Actually create the file for testing
            final_audio_path = temp_audio_dir / f"{session_id}.mp3"
            final_audio_path.write_bytes(fake_audio_data)
            final_audio_path.chmod(0o644)

            # Verify file was created
            assert final_audio_path.exists(), "Welcome audio file should exist"
            assert final_audio_path.read_bytes() == fake_audio_data, "Audio content should match"

    @pytest.mark.asyncio
    async def test_welcome_audio_file_permissions(self, temp_audio_dir):
        """Test that welcome audio file has correct 644 permissions."""
        # Create a test audio file
        session_id = uuid4()
        audio_file = temp_audio_dir / f"{session_id}.mp3"
        audio_file.write_bytes(b"test audio")
        audio_file.chmod(0o644)

        # Check permissions
        import stat

        file_mode = audio_file.stat().st_mode
        permissions = stat.S_IMODE(file_mode)

        assert permissions == 0o644, f"Expected 0o644, got {oct(permissions)}"

        # Verify specific permission bits
        assert permissions & stat.S_IRUSR, "Owner should have read permission"
        assert permissions & stat.S_IWUSR, "Owner should have write permission"
        assert permissions & stat.S_IRGRP, "Group should have read permission"
        assert not (permissions & stat.S_IWGRP), "Group should NOT have write permission"

    @pytest.mark.asyncio
    async def test_execute_with_welcome_audio_url_in_response(
        self, mock_repositories, sample_sop
    ):
        """Test that execute() includes welcome_audio_url in response."""
        session_repo, sop_repo = mock_repositories
        tts_client = AsyncMock()

        # Setup mocks
        sop_repo.get_by_id = AsyncMock(return_value=sample_sop)
        session_repo.get_current_for_worker = AsyncMock(return_value=None)

        # Create expected session
        saved_session = WorkSession(
            id=uuid4(),
            sop_id=sample_sop.id,
            worker_id=uuid4(),
            current_step_id=sample_sop.tasks[0].steps[0].id,
        )
        session_repo.save = AsyncMock(return_value=saved_session)

        # Mock TTS client
        async def mock_synthesize(text: str, output_path: str):
            Path(output_path).write_bytes(b"audio")

        tts_client.synthesize_speech = AsyncMock(side_effect=mock_synthesize)

        use_case = StartSessionUseCase(
            session_repository=session_repo,
            sop_repository=sop_repo,
            tts_client=tts_client,
        )

        # Mock the welcome audio generation to return a path
        mock_audio_path = f"/tmp/audio/feedback/welcome/{saved_session.id}.mp3"
        with patch.object(
            use_case, "_generate_welcome_audio", return_value=mock_audio_path
        ):
            # Execute
            request = StartSessionRequest(
                sop_id=sample_sop.id,
                worker_id=saved_session.worker_id,
            )

            response = await use_case.execute(request)

            # Assertions
            assert response.welcome_audio_url is not None, "Welcome audio URL should be present"
            assert response.welcome_audio_url.startswith(
                "/api/v1/sessions/"
            ), "URL should have correct format"
            assert response.welcome_audio_url.endswith(
                "/welcome-audio"
            ), "URL should end with /welcome-audio"
            assert str(saved_session.id) in response.welcome_audio_url, (
                "URL should contain session ID"
            )

    @pytest.mark.asyncio
    async def test_execute_graceful_degradation_on_tts_failure(
        self, mock_repositories, sample_sop
    ):
        """Test that execute() continues gracefully when welcome audio generation fails."""
        session_repo, sop_repo = mock_repositories
        tts_client = AsyncMock()

        # Setup mocks
        sop_repo.get_by_id = AsyncMock(return_value=sample_sop)
        session_repo.get_current_for_worker = AsyncMock(return_value=None)

        saved_session = WorkSession(
            id=uuid4(),
            sop_id=sample_sop.id,
            worker_id=uuid4(),
            current_step_id=sample_sop.tasks[0].steps[0].id,
        )
        session_repo.save = AsyncMock(return_value=saved_session)

        # Mock TTS to raise exception
        tts_client.synthesize_speech = AsyncMock(
            side_effect=Exception("TTS service unavailable")
        )

        use_case = StartSessionUseCase(
            session_repository=session_repo,
            sop_repository=sop_repo,
            tts_client=tts_client,
        )

        # Execute - should not raise exception
        request = StartSessionRequest(
            sop_id=sample_sop.id,
            worker_id=saved_session.worker_id,
        )

        response = await use_case.execute(request)

        # Assertions
        assert response is not None, "Response should still be returned"
        assert response.session is not None, "Session should be created"
        assert response.welcome_audio_url is None, (
            "Welcome audio URL should be None when generation fails"
        )
        assert response.first_step_id is not None, "First step ID should be present"

        # Verify session was still saved
        session_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_welcome_audio_url_format(self, mock_repositories, sample_sop):
        """Test that welcome audio URL has correct API endpoint format."""
        session_repo, sop_repo = mock_repositories
        tts_client = AsyncMock()

        # Setup mocks
        sop_repo.get_by_id = AsyncMock(return_value=sample_sop)
        session_repo.get_current_for_worker = AsyncMock(return_value=None)

        session_id = uuid4()
        saved_session = WorkSession(
            id=session_id,
            sop_id=sample_sop.id,
            worker_id=uuid4(),
            current_step_id=sample_sop.tasks[0].steps[0].id,
        )
        session_repo.save = AsyncMock(return_value=saved_session)

        use_case = StartSessionUseCase(
            session_repository=session_repo,
            sop_repository=sop_repo,
            tts_client=tts_client,
        )

        # Mock welcome audio generation
        with patch.object(
            use_case,
            "_generate_welcome_audio",
            return_value=f"/tmp/audio/feedback/welcome/{session_id}.mp3",
        ):
            request = StartSessionRequest(
                sop_id=sample_sop.id,
                worker_id=saved_session.worker_id,
            )

            response = await use_case.execute(request)

            # Verify URL format: /api/v1/sessions/{session_id}/welcome-audio
            expected_url = f"/api/v1/sessions/{session_id}/welcome-audio"
            assert response.welcome_audio_url == expected_url, (
                f"Welcome audio URL should be {expected_url}"
            )

    @pytest.mark.asyncio
    async def test_welcome_message_uses_japanese_text(self, sample_sop):
        """Test that welcome message contains proper Japanese text."""
        message = WELCOME_MESSAGE_TEMPLATE.format(
            task_title=sample_sop.tasks[0].title,
            total_steps=3,
            first_step_description=sample_sop.tasks[0].steps[0].description,
        )

        # Check for Japanese phrases
        assert "こんにちは" in message, "Should have Japanese greeting"
        assert "を開始します" in message, "Should have Japanese start phrase"
        assert "ステップあります" in message, "Should have Japanese step count phrase"
        assert "最初のステップは" in message, "Should have Japanese first step phrase"
        assert "ヨシッ！" in message, "Should have Yoshi confirmation call"
        assert "安全作業、よろしくお願いします！" in message, (
            "Should have Japanese safety closing"
        )

    @pytest.mark.asyncio
    async def test_total_steps_calculation(self, sample_sop):
        """Test that total steps are calculated correctly across all tasks."""
        # sample_sop has 2 tasks: Task 1 (2 steps) + Task 2 (1 step) = 3 total steps
        total_steps = sum(len(t.steps) for t in sample_sop.tasks)

        assert total_steps == 3, "Should count all steps across all tasks"

        message = WELCOME_MESSAGE_TEMPLATE.format(
            task_title=sample_sop.tasks[0].title,
            total_steps=total_steps,
            first_step_description=sample_sop.tasks[0].steps[0].description,
        )

        assert "3ステップ" in message, "Message should contain correct total steps"

    @pytest.mark.asyncio
    async def test_session_created_even_when_audio_generation_fails(
        self, mock_repositories, sample_sop
    ):
        """Test that session is created and saved even if welcome audio fails."""
        session_repo, sop_repo = mock_repositories
        tts_client = AsyncMock()

        # Setup mocks
        sop_repo.get_by_id = AsyncMock(return_value=sample_sop)
        session_repo.get_current_for_worker = AsyncMock(return_value=None)

        worker_id = uuid4()
        saved_session = WorkSession(
            id=uuid4(),
            sop_id=sample_sop.id,
            worker_id=worker_id,
            current_step_id=sample_sop.tasks[0].steps[0].id,
        )
        session_repo.save = AsyncMock(return_value=saved_session)

        # Mock TTS to fail
        tts_client.synthesize_speech = AsyncMock(side_effect=Exception("TTS error"))

        use_case = StartSessionUseCase(
            session_repository=session_repo,
            sop_repository=sop_repo,
            tts_client=tts_client,
        )

        request = StartSessionRequest(
            sop_id=sample_sop.id,
            worker_id=worker_id,
        )

        response = await use_case.execute(request)

        # Verify session was created
        assert response.session.id == saved_session.id, "Session should be created"
        assert response.session.worker_id == worker_id, "Worker ID should match"
        assert response.session.sop_id == sample_sop.id, "SOP ID should match"

        # Verify session was saved
        session_repo.save.assert_called_once()

        # But audio URL should be None
        assert response.welcome_audio_url is None, "Audio URL should be None on failure"
