"""SOP Structuring Use Case - AI-powered SOP extraction."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from src.domain.sop.entities import SOP
from src.domain.sop.repositories import SOPRepository
from src.infrastructure.ai_services.sambanova import SambanovaClient

logger = logging.getLogger(__name__)

# AI Prompt Template
STRUCTURE_SOP_PROMPT = """
You are analyzing a Standard Operating Procedure (SOP) or Hazard Prediction (KY/危険予知) document.
Your task is to extract a structured task list with safety information.

Extract:
1. **Title**: Overall task/procedure name
2. **Tasks**: Major steps or phases (preparation → execution → cleanup)
3. **Steps**: Specific actions within each task
4. **Hazards**: For each step, identify:
   - 危険要因 (hazard factors)
   - Severity level (low, medium, high, critical)
   - 対策 (mitigation measures)

Return JSON matching this schema:
{
  "title": "string",
  "tasks": [
    {
      "title": "string",
      "description": "string (optional)",
      "steps": [
        {
          "description": "string",
          "expected_action": "string (what worker should do)",
          "expected_result": "string (what should be verified)",
          "hazards": [
            {
              "description": "string (危険要因)",
              "severity": "low|medium|high|critical",
              "mitigation": "string (対策)"
            }
          ]
        }
      ]
    }
  ]
}

Be thorough and safety-focused. Extract all hazards even if not explicitly labeled.
"""

# JSON Schema for structured response
SOP_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "expected_action": {"type": "string"},
                                "expected_result": {"type": "string"},
                                "hazards": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "description": {"type": "string"},
                                            "severity": {
                                                "type": "string",
                                                "enum": [
                                                    "low",
                                                    "medium",
                                                    "high",
                                                    "critical",
                                                ],
                                            },
                                            "mitigation": {"type": "string"},
                                        },
                                        "required": ["description", "severity"],
                                        "additionalProperties": False,
                                    },
                                },
                            },
                            "required": ["description"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["title", "steps"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "tasks"],
    "additionalProperties": False,
}


@dataclass
class StructureSOPRequest:
    """Request to structure an uploaded SOP."""

    sop_id: UUID
    image_paths: list[Path]
    text_content: str | None = None


@dataclass
class StructureSOPResponse:
    """Response from structuring an SOP."""

    sop: SOP
    success: bool
    error_message: str | None = None


class StructureSOPUseCase:
    """Use case for structuring an SOP using AI vision analysis."""

    def __init__(
        self, sop_repository: SOPRepository, ai_client: SambanovaClient | None = None
    ):
        """Initialize the use case.

        Args:
            sop_repository: Repository for SOP persistence
            ai_client: SambaNova client (if None, creates new instance)
        """
        self.sop_repository = sop_repository
        self.ai_client = ai_client or SambanovaClient()

    def _build_prompt(self, text_content: str | None) -> str:
        """Build the analysis prompt with optional user-provided text.

        Args:
            text_content: Optional user-provided text content

        Returns:
            Complete prompt string
        """
        prompt = STRUCTURE_SOP_PROMPT

        if text_content and text_content.strip():
            prompt += f"\n\n**User-provided text content:**\n{text_content}\n"

        return prompt

    def _parse_ai_response_to_sop(self, ai_response: dict[str, Any], sop: SOP) -> SOP:
        """Parse AI response JSON into SOP aggregate.

        Args:
            ai_response: Structured JSON response from AI
            sop: Existing SOP entity to populate

        Returns:
            Updated SOP entity with tasks/steps/hazards
        """
        # Update title from AI response
        sop.title = ai_response.get("title", sop.title)

        # Parse tasks
        for task_data in ai_response.get("tasks", []):
            task = sop.add_task(
                title=task_data["title"], description=task_data.get("description")
            )

            # Parse steps
            for step_data in task_data.get("steps", []):
                step = task.add_step(
                    description=step_data["description"],
                    expected_action=step_data.get("expected_action"),
                    expected_result=step_data.get("expected_result"),
                )

                # Parse hazards
                for hazard_data in step_data.get("hazards", []):
                    step.add_hazard(
                        description=hazard_data["description"],
                        severity=hazard_data["severity"],
                        mitigation=hazard_data.get("mitigation"),
                    )

        return sop

    async def execute(self, request: StructureSOPRequest) -> StructureSOPResponse:
        """Execute the SOP structuring use case.

        Args:
            request: Structure request with SOP ID, images, and optional text

        Returns:
            StructureSOPResponse with populated SOP or error

        Raises:
            ValueError: If SOP not found or has no images
        """
        # Load SOP from database
        sop = await self.sop_repository.get_by_id(request.sop_id)
        if not sop:
            raise ValueError(f"SOP not found: {request.sop_id}")

        if not request.image_paths:
            raise ValueError("At least one image is required for structuring")

        # Build prompt with optional text content
        prompt = self._build_prompt(request.text_content)

        try:
            # Call AI service with first image (vision model extracts text from image)
            logger.info(
                f"Calling SambaNova AI to structure SOP {sop.id} with {len(request.image_paths)} image(s)"
            )

            # Use the first image for analysis
            # Vision model will extract and analyze text from the image
            ai_response = await self.ai_client.analyze_image(
                image_path=str(request.image_paths[0]),
                prompt=prompt,
                response_schema=SOP_RESPONSE_SCHEMA,
            )

            logger.info(f"AI analysis complete for SOP {sop.id}")

            # Parse AI response into SOP aggregate (guaranteed dict when schema provided)
            assert isinstance(ai_response, dict), "Expected dict response with schema"
            sop = self._parse_ai_response_to_sop(ai_response, sop)

            # Validate the structured SOP
            validation_errors = sop.validate()
            if validation_errors:
                logger.warning(
                    f"SOP validation warnings for {sop.id}: {validation_errors}"
                )

            # Save structured SOP
            saved_sop = await self.sop_repository.save(sop)

            logger.info(
                f"Successfully structured SOP {sop.id}: {len(saved_sop.tasks)} tasks, "
                f"{sum(len(t.steps) for t in saved_sop.tasks)} total steps"
            )

            return StructureSOPResponse(sop=saved_sop, success=True)

        except Exception as e:
            logger.error(f"Failed to structure SOP {sop.id}: {e}", exc_info=True)
            return StructureSOPResponse(sop=sop, success=False, error_message=str(e))
