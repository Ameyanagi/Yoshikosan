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
あなたは標準作業手順書（SOP）または危険予知（KY）文書を分析しています。
安全情報を含む構造化されたタスクリストを抽出してください。

**重要: すべての出力は日本語で記述してください。**

抽出する内容:
1. **タイトル**: 全体的な作業・手順の名称
2. **タスク**: 主要な段階やフェーズ（準備 → 実行 → 片付け）
3. **ステップ**: 各タスク内の具体的な作業
4. **危険要因**: 各ステップについて以下を特定:
   - 危険要因（hazard factors）
   - 重大度レベル（low, medium, high, critical）
   - 対策（mitigation measures）

以下のJSONスキーマに従って日本語で返してください:
{
  "title": "string（日本語）",
  "tasks": [
    {
      "title": "string（日本語）",
      "description": "string（日本語・オプション）",
      "steps": [
        {
          "description": "string（日本語・ステップの説明）",
          "expected_action": "string（日本語・作業者が行うべきこと）",
          "expected_result": "string（日本語・確認すべき結果）",
          "hazards": [
            {
              "description": "string（日本語・危険要因）",
              "severity": "low|medium|high|critical",
              "mitigation": "string（日本語・対策）"
            }
          ]
        }
      ]
    }
  ]
}

徹底的かつ安全重視で分析してください。明示的にラベル付けされていない危険要因もすべて抽出してください。
すべてのテキスト（title, description, expected_action, expected_result, hazard description, mitigation）は日本語で記述してください。
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
            request: Structure request with SOP ID, optional images, and/or text

        Returns:
            StructureSOPResponse with populated SOP or error

        Raises:
            ValueError: If SOP not found or no content provided
        """
        # Load SOP from database
        sop = await self.sop_repository.get_by_id(request.sop_id)
        if not sop:
            raise ValueError(f"SOP not found: {request.sop_id}")

        # Ensure at least one of images or text_content is provided
        if not request.image_paths and not request.text_content:
            raise ValueError("At least one of images or text content is required for structuring")

        # Build prompt with optional text content
        prompt = self._build_prompt(request.text_content)

        try:
            # Call AI service - use image if available, otherwise text-only
            if request.image_paths:
                logger.info(
                    f"Calling SambaNova AI to structure SOP {sop.id} with {len(request.image_paths)} image(s)"
                )
                # Use the first image for analysis (vision model extracts text from image)
                ai_response = await self.ai_client.analyze_image(
                    image_path=str(request.image_paths[0]),
                    prompt=prompt,
                    response_schema=SOP_RESPONSE_SCHEMA,
                )
            else:
                logger.info(
                    f"Calling SambaNova AI to structure SOP {sop.id} with text content only"
                )
                # Text-only analysis
                ai_response = await self.ai_client.chat_completion(
                    message=prompt,
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
