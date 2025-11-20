"""SOP domain entities following DDD principles."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Hazard:
    """Hazard associated with a step."""

    description: str
    severity: str
    mitigation: str | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        """Validate hazard after initialization."""
        if not self.description.strip():
            raise ValueError("Hazard description cannot be empty")
        if not self.severity.strip():
            raise ValueError("Hazard severity cannot be empty")


@dataclass
class Step:
    """Step within a task."""

    description: str
    order_index: int
    expected_action: str | None = None
    expected_result: str | None = None
    id: UUID = field(default_factory=uuid4)
    hazards: list[Hazard] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate step after initialization."""
        if not self.description.strip():
            raise ValueError("Step description cannot be empty")
        if self.order_index < 0:
            raise ValueError("Step order_index must be non-negative")

    def add_hazard(
        self, description: str, severity: str, mitigation: str | None = None
    ) -> Hazard:
        """Add a hazard to this step.

        Args:
            description: Hazard description
            severity: Hazard severity level
            mitigation: Optional mitigation strategy

        Returns:
            The created Hazard instance
        """
        hazard = Hazard(
            description=description, severity=severity, mitigation=mitigation
        )
        self.hazards.append(hazard)
        return hazard


@dataclass
class Task:
    """Task within an SOP."""

    title: str
    order_index: int
    description: str | None = None
    id: UUID = field(default_factory=uuid4)
    steps: list[Step] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate task after initialization."""
        if not self.title.strip():
            raise ValueError("Task title cannot be empty")
        if self.order_index < 0:
            raise ValueError("Task order_index must be non-negative")

    def add_step(
        self,
        description: str,
        expected_action: str | None = None,
        expected_result: str | None = None,
    ) -> Step:
        """Add a step to this task.

        Args:
            description: Step description
            expected_action: Expected action to perform
            expected_result: Expected result after action

        Returns:
            The created Step instance with order_index set to len(steps)
        """
        step = Step(
            description=description,
            order_index=len(self.steps),
            expected_action=expected_action,
            expected_result=expected_result,
        )
        self.steps.append(step)
        return step


@dataclass
class SOP:
    """SOP (Standard Operating Procedure) aggregate root."""

    title: str
    created_by: UUID
    id: UUID = field(default_factory=uuid4)
    tasks: list[Task] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    deleted_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate SOP after initialization."""
        if not self.title.strip():
            raise ValueError("SOP title cannot be empty")

    def add_task(self, title: str, description: str | None = None) -> Task:
        """Add a task to this SOP.

        Args:
            title: Task title
            description: Optional task description

        Returns:
            The created Task instance with order_index set to len(tasks)
        """
        task = Task(title=title, description=description, order_index=len(self.tasks))
        self.tasks.append(task)
        self.updated_at = datetime.now()
        return task

    def validate(self) -> list[str]:
        """Validate the SOP structure and return list of validation errors.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors: list[str] = []

        if not self.title.strip():
            errors.append("SOP title is required")

        if not self.tasks:
            errors.append("SOP must have at least one task")

        for i, task in enumerate(self.tasks):
            if not task.title.strip():
                errors.append(f"Task {i + 1} title is required")

            if not task.steps:
                errors.append(f"Task '{task.title}' must have at least one step")

            for j, step in enumerate(task.steps):
                if not step.description.strip():
                    errors.append(
                        f"Step {j + 1} in task '{task.title}' must have a description"
                    )

        return errors

    def mark_deleted(self) -> None:
        """Soft delete this SOP by setting deleted_at timestamp."""
        self.deleted_at = datetime.now()
        self.updated_at = datetime.now()

    def is_deleted(self) -> bool:
        """Check if this SOP is soft deleted."""
        return self.deleted_at is not None
