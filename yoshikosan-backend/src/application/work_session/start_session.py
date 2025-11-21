"""Start Session Use Case."""

import logging
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from src.domain.sop.entities import SOP
from src.domain.sop.repositories import SOPRepository
from src.domain.work_session.entities import WorkSession
from src.domain.work_session.repositories import WorkSessionRepository
from src.infrastructure.ai_services.hume import HumeClient

logger = logging.getLogger(__name__)

# Welcome message template for first task
WELCOME_MESSAGE_TEMPLATE = """こんにちは！{task_title}を開始します。

今日の作業は{total_steps}ステップあります。
最初のステップは「{first_step_description}」です。

準備ができたら、「ヨシッ！」ボタンを押して確認を始めてください。
安全作業、よろしくお願いします！"""


@dataclass
class StartSessionRequest:
    """Request to start a new work session."""

    sop_id: UUID
    worker_id: UUID


@dataclass
class StartSessionResponse:
    """Response from starting a session."""

    session: WorkSession
    sop: SOP
    first_step_id: UUID | None
    welcome_audio_url: str | None = None


class StartSessionUseCase:
    """Use case for starting a new work session."""

    def __init__(
        self,
        session_repository: WorkSessionRepository,
        sop_repository: SOPRepository,
        tts_client: HumeClient | None = None,
    ):
        """Initialize the use case.

        Args:
            session_repository: Repository for WorkSession persistence
            sop_repository: Repository for SOP retrieval
            tts_client: Hume AI client for TTS (if None, creates new instance)
        """
        self.session_repository = session_repository
        self.sop_repository = sop_repository
        self.tts_client = tts_client or HumeClient()

    def _get_first_step_id(self, sop: SOP) -> UUID | None:
        """Get the ID of the first step in the SOP.

        Args:
            sop: SOP entity

        Returns:
            UUID of first step, or None if SOP has no steps
        """
        if not sop.tasks:
            return None

        first_task = sop.tasks[0]
        if not first_task.steps:
            return None

        return first_task.steps[0].id

    async def _generate_welcome_audio(self, session_id: UUID, sop: SOP) -> str | None:
        """Generate welcome audio for first task.

        Args:
            session_id: Session ID for file organization
            sop: SOP entity

        Returns:
            File path to saved welcome audio, or None if generation fails
        """
        first_task = sop.tasks[0]
        first_step = first_task.steps[0]
        total_steps = sum(len(t.steps) for t in sop.tasks)

        # Generate welcome message
        message = WELCOME_MESSAGE_TEMPLATE.format(
            task_title=first_task.title,
            total_steps=total_steps,
            first_step_description=first_step.description,
        )

        try:
            # Synthesize audio to temp file
            temp_audio_path = Path("/tmp") / f"welcome_{session_id}.mp3"
            await self.tts_client.synthesize_speech(
                text=message, output_path=str(temp_audio_path)
            )

            # Save to persistent location
            audio_dir = Path("/tmp/audio/feedback/welcome")
            audio_dir.mkdir(parents=True, exist_ok=True)

            audio_path = audio_dir / f"{session_id}.mp3"
            audio_path.write_bytes(temp_audio_path.read_bytes())
            temp_audio_path.unlink()  # Cleanup temp file

            # Set readable permissions
            audio_path.chmod(0o644)

            logger.info(f"Generated welcome audio at {audio_path}")
            return str(audio_path)

        except Exception as e:
            logger.error(f"Failed to generate welcome audio: {e}")
            return None

    async def execute(self, request: StartSessionRequest) -> StartSessionResponse:
        """Execute the start session use case.

        Args:
            request: Start session request

        Returns:
            StartSessionResponse with session and first step

        Raises:
            ValueError: If SOP not found, not structured, or worker has active session
        """
        # Load SOP
        sop = await self.sop_repository.get_by_id(request.sop_id)
        if not sop:
            raise ValueError(f"SOP not found: {request.sop_id}")

        # Validate SOP is structured (has tasks and steps)
        validation_errors = sop.validate()
        if validation_errors:
            raise ValueError(
                f"SOP is not properly structured: {', '.join(validation_errors)}"
            )

        # Check for existing active session
        existing_session = await self.session_repository.get_current_for_worker(
            request.worker_id
        )
        if existing_session:
            raise ValueError(
                f"Worker already has an active session: {existing_session.id}"
            )

        # Get first step ID
        first_step_id = self._get_first_step_id(sop)
        if not first_step_id:
            raise ValueError("SOP has no steps to execute")

        # Create new work session
        session = WorkSession(
            sop_id=request.sop_id,
            worker_id=request.worker_id,
            current_step_id=first_step_id,
        )

        # Save session
        saved_session = await self.session_repository.save(session)

        # Generate welcome audio for first task
        welcome_audio_path = await self._generate_welcome_audio(
            session_id=saved_session.id, sop=sop
        )
        welcome_audio_url = (
            f"/api/v1/sessions/{saved_session.id}/welcome-audio"
            if welcome_audio_path
            else None
        )

        logger.info(
            f"Started session {saved_session.id} for worker {request.worker_id} "
            f"on SOP {request.sop_id}"
        )

        return StartSessionResponse(
            session=saved_session,
            sop=sop,
            first_step_id=first_step_id,
            welcome_audio_url=welcome_audio_url,
        )
