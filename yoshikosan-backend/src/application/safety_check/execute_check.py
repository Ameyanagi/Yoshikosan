"""Execute Safety Check Use Case."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from src.domain.sop.entities import SOP
from src.domain.sop.repositories import SOPRepository
from src.domain.work_session.entities import CheckResult
from src.domain.work_session.repositories import WorkSessionRepository
from src.infrastructure.ai_services.hume import HumeClient
from src.infrastructure.ai_services.sambanova import SambanovaClient

logger = logging.getLogger(__name__)

# Safety Verification Prompt Template
VERIFY_SAFETY_CHECK_PROMPT_TEMPLATE = """
You are verifying that a worker correctly performed a safety step.

**Complete SOP Workflow:**
{full_sop_structure}

**Current Expected Step (Task {task_number}, Step {step_number}):**
{step_description}
Expected action: {expected_action}
Expected result: {expected_result}
Known hazards: {hazards}

**Worker Evidence:**
- Audio transcript: "{audio_transcript}"
- Image: [provided]
- Timestamp: {timestamp}

**Analysis Required:**
1. Did the worker perform the correct action for THIS step?
2. Does the image show the expected result for THIS step?
3. Did the worker verbally confirm the check? (e.g., "バルブ閉ヨシッ!")
4. Are there any visible safety concerns in the image?
5. Based on the complete workflow, is the worker on the correct step? (Or did they skip/repeat steps?)

Return JSON:
{{
  "result": "pass" | "fail",
  "confidence": 0.0-1.0,
  "step_sequence_correct": true | false,
  "feedback_ja": "Japanese feedback (褒める if pass, 是正指示 if fail)",
  "reasoning": "Why you made this determination",
  "next_step_hint": "What to do next (if pass)" | null
}}

**Guidelines:**
- Be strict with safety-critical steps
- Use the full SOP context to detect if worker is ahead/behind in the sequence
- If worker appears to be on wrong step, set step_sequence_correct=false and explain in feedback
- Praise good practices (e.g., "しっかり確認できました！")
- Give specific corrections for failures (e.g., "バルブがまだ開いています。もう一度確認してください")
- If out of sequence: "この確認は早すぎます。まず〇〇を完了してください" or "この確認は既に完了しています。次は〇〇です"
- Consider both visual and audio evidence
- The full workflow context helps you understand what should have been done before and what comes after
"""

# JSON Schema for safety check response
SAFETY_CHECK_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "result": {"type": "string", "enum": ["pass", "fail"]},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "step_sequence_correct": {"type": "boolean"},
        "feedback_ja": {"type": "string"},
        "reasoning": {"type": "string"},
        "next_step_hint": {"type": "string"},
    },
    "required": [
        "result",
        "confidence",
        "step_sequence_correct",
        "feedback_ja",
        "reasoning",
    ],
    "additionalProperties": False,
}


@dataclass
class ExecuteSafetyCheckRequest:
    """Request to execute a safety check."""

    session_id: UUID
    step_id: UUID
    image_path: Path  # Temporary image file
    audio_path: Path  # Temporary audio file


@dataclass
class ExecuteSafetyCheckResponse:
    """Response from executing a safety check."""

    result: CheckResult
    feedback_text: str
    feedback_audio_bytes: bytes
    confidence_score: float
    needs_review: bool
    next_step_id: UUID | None
    session_updated: bool


class ExecuteSafetyCheckUseCase:
    """Use case for executing a safety check with AI verification."""

    def __init__(
        self,
        session_repository: WorkSessionRepository,
        sop_repository: SOPRepository,
        ai_client: SambanovaClient | None = None,
        tts_client: HumeClient | None = None,
    ):
        """Initialize the use case.

        Args:
            session_repository: Repository for WorkSession persistence
            sop_repository: Repository for SOP retrieval
            ai_client: SambaNova client (if None, creates new instance)
            tts_client: Hume AI client (if None, creates new instance)
        """
        self.session_repository = session_repository
        self.sop_repository = sop_repository
        self.ai_client = ai_client or SambanovaClient()
        self.tts_client = tts_client or HumeClient()

    def _format_sop_structure(self, sop: SOP) -> str:
        """Format complete SOP structure for prompt.

        Args:
            sop: SOP entity

        Returns:
            Formatted SOP structure string
        """
        lines = [f"SOP Title: {sop.title}\n"]

        for task_idx, task in enumerate(sop.tasks, 1):
            lines.append(f"\nTask {task_idx}: {task.title}")
            if task.description:
                lines.append(f"  Description: {task.description}")

            for step_idx, step in enumerate(task.steps, 1):
                lines.append(f"  Step {task_idx}.{step_idx}: {step.description}")
                if step.expected_action:
                    lines.append(f"    Action: {step.expected_action}")
                if step.expected_result:
                    lines.append(f"    Result: {step.expected_result}")

                if step.hazards:
                    lines.append("    Hazards:")
                    for hazard in step.hazards:
                        lines.append(
                            f"      - [{hazard.severity}] {hazard.description}"
                        )

        return "\n".join(lines)

    def _find_step_in_sop(self, sop: SOP, step_id: UUID) -> tuple[int, int, Any]:
        """Find step in SOP and return task/step numbers.

        Args:
            sop: SOP entity
            step_id: Step ID to find

        Returns:
            Tuple of (task_number, step_number, step)

        Raises:
            ValueError: If step not found
        """
        for task_idx, task in enumerate(sop.tasks, 1):
            for step_idx, step in enumerate(task.steps, 1):
                if step.id == step_id:
                    return task_idx, step_idx, step

        raise ValueError(f"Step {step_id} not found in SOP")

    def _find_next_step_id(self, sop: SOP, current_step_id: UUID) -> UUID | None:
        """Find the next step ID after the current step.

        Args:
            sop: SOP entity
            current_step_id: Current step ID

        Returns:
            Next step ID, or None if this is the last step
        """
        found_current = False

        for task in sop.tasks:
            for step in task.steps:
                if found_current:
                    return step.id
                if step.id == current_step_id:
                    found_current = True

        return None  # Last step

    async def _synthesize_audio_feedback(self, feedback_text: str) -> bytes:
        """Synthesize audio feedback using Hume AI.

        Args:
            feedback_text: Japanese feedback text

        Returns:
            Audio bytes (MP3)
        """
        # Use Hume AI to generate empathic TTS
        # For MVP, we'll save to temp file then read bytes
        temp_audio_path = Path("temp_feedback.mp3")

        try:
            await self.tts_client.synthesize_speech(
                text=feedback_text, output_path=str(temp_audio_path)
            )

            # Read audio bytes
            audio_bytes = temp_audio_path.read_bytes()

            return audio_bytes
        finally:
            # Clean up temp file
            if temp_audio_path.exists():
                temp_audio_path.unlink()

    async def execute(
        self, request: ExecuteSafetyCheckRequest
    ) -> ExecuteSafetyCheckResponse:
        """Execute the safety check use case.

        Args:
            request: Execute check request

        Returns:
            ExecuteSafetyCheckResponse with result and feedback

        Raises:
            ValueError: If session/SOP not found, session locked, etc.
        """
        # Load session
        session = await self.session_repository.get_by_id(request.session_id)
        if not session:
            raise ValueError(f"Session not found: {request.session_id}")

        # Verify session is not locked
        if session.locked:
            raise ValueError("Cannot add checks to locked session")

        # Load SOP with full structure
        sop = await self.sop_repository.get_by_id(session.sop_id)
        if not sop:
            raise ValueError(f"SOP not found: {session.sop_id}")

        # Find the step being checked
        task_num, step_num, step = self._find_step_in_sop(sop, request.step_id)

        # Transcribe audio
        logger.info(f"Transcribing audio for session {session.id}")
        audio_transcript = await self.ai_client.transcribe_audio(
            audio_path=str(request.audio_path), language="ja"
        )

        # Build verification prompt with full SOP context
        full_sop_structure = self._format_sop_structure(sop)
        hazards_text = ", ".join(
            [f"{h.severity}: {h.description}" for h in step.hazards]
        )

        prompt = VERIFY_SAFETY_CHECK_PROMPT_TEMPLATE.format(
            full_sop_structure=full_sop_structure,
            task_number=task_num,
            step_number=step_num,
            step_description=step.description,
            expected_action=step.expected_action or "N/A",
            expected_result=step.expected_result or "N/A",
            hazards=hazards_text or "None specified",
            audio_transcript=audio_transcript,
            timestamp="now",  # Could use actual timestamp
        )

        # Call AI for verification
        logger.info(f"Verifying safety check for session {session.id}, step {step_num}")
        ai_response = await self.ai_client.analyze_image(
            image_path=str(request.image_path),
            prompt=prompt,
            response_schema=SAFETY_CHECK_RESPONSE_SCHEMA,
        )

        # Parse AI response (guaranteed dict when schema provided)
        assert isinstance(ai_response, dict), "Expected dict response with schema"
        result = (
            CheckResult.PASS if ai_response["result"] == "pass" else CheckResult.FAIL
        )
        confidence = float(ai_response["confidence"])
        feedback_text = str(ai_response["feedback_ja"])
        needs_review = confidence < 0.7 or not bool(ai_response["step_sequence_correct"])

        # Generate voice feedback
        logger.info("Generating voice feedback with Hume AI")
        feedback_audio_bytes = await self._synthesize_audio_feedback(feedback_text)

        # Add safety check to session
        session.add_check(
            step_id=request.step_id,
            result=result,
            feedback_text=feedback_text,
            confidence_score=confidence,
            needs_review=needs_review,
        )

        # Advance session if check passed and sequence is correct
        next_step_id = None
        session_updated = False

        if result == CheckResult.PASS and ai_response["step_sequence_correct"]:
            next_step_id = self._find_next_step_id(sop, request.step_id)
            session.advance_to_next_step(next_step_id)
            session_updated = True
            logger.info(f"Session advanced to next step: {next_step_id}")

        # Save session
        await self.session_repository.save(session)

        logger.info(
            f"Safety check complete for session {session.id}: "
            f"result={result.value}, next_step={next_step_id}"
        )

        return ExecuteSafetyCheckResponse(
            result=result,
            feedback_text=feedback_text,
            feedback_audio_bytes=feedback_audio_bytes,
            confidence_score=confidence,
            needs_review=needs_review,
            next_step_id=next_step_id,
            session_updated=session_updated,
        )
