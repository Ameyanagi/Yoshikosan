"""Mapper for SOP domain entities and database models."""

from src.domain.sop.entities import SOP, Hazard, Step, Task
from src.infrastructure.database.models import (
    HazardModel,
    SOPModel,
    StepModel,
    TaskModel,
)


def hazard_to_domain(model: HazardModel) -> Hazard:
    """Convert HazardModel to Hazard domain entity.

    Args:
        model: HazardModel instance

    Returns:
        Hazard domain entity
    """
    return Hazard(
        id=model.id,
        description=model.description,
        severity=model.severity,
        mitigation=model.mitigation,
    )


def hazard_to_model(entity: Hazard, step_id: object) -> HazardModel:
    """Convert Hazard domain entity to HazardModel.

    Args:
        entity: Hazard domain entity
        step_id: Step ID for foreign key

    Returns:
        HazardModel instance
    """
    return HazardModel(
        id=entity.id,
        step_id=step_id,
        description=entity.description,
        severity=entity.severity,
        mitigation=entity.mitigation,
    )


def step_to_domain(model: StepModel) -> Step:
    """Convert StepModel to Step domain entity.

    Args:
        model: StepModel instance

    Returns:
        Step domain entity with hazards
    """
    return Step(
        id=model.id,
        description=model.description,
        order_index=model.order_index,
        expected_action=model.expected_action,
        expected_result=model.expected_result,
        hazards=[hazard_to_domain(h) for h in model.hazards],
    )


def step_to_model(entity: Step, task_id: object) -> StepModel:
    """Convert Step domain entity to StepModel.

    Args:
        entity: Step domain entity
        task_id: Task ID for foreign key

    Returns:
        StepModel instance with hazards
    """
    model = StepModel(
        id=entity.id,
        task_id=task_id,
        description=entity.description,
        order_index=entity.order_index,
        expected_action=entity.expected_action,
        expected_result=entity.expected_result,
    )
    model.hazards = [hazard_to_model(h, entity.id) for h in entity.hazards]
    return model


def task_to_domain(model: TaskModel) -> Task:
    """Convert TaskModel to Task domain entity.

    Args:
        model: TaskModel instance

    Returns:
        Task domain entity with steps
    """
    return Task(
        id=model.id,
        title=model.title,
        description=model.description,
        order_index=model.order_index,
        steps=[step_to_domain(s) for s in model.steps],
    )


def task_to_model(entity: Task, sop_id: object) -> TaskModel:
    """Convert Task domain entity to TaskModel.

    Args:
        entity: Task domain entity
        sop_id: SOP ID for foreign key

    Returns:
        TaskModel instance with steps
    """
    model = TaskModel(
        id=entity.id,
        sop_id=sop_id,
        title=entity.title,
        description=entity.description,
        order_index=entity.order_index,
    )
    model.steps = [step_to_model(s, entity.id) for s in entity.steps]
    return model


def sop_to_domain(model: SOPModel) -> SOP:
    """Convert SOPModel to SOP domain entity.

    Args:
        model: SOPModel instance

    Returns:
        SOP domain entity with full task/step/hazard hierarchy
    """
    return SOP(
        id=model.id,
        title=model.title,
        created_by=model.created_by,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
        tasks=[task_to_domain(t) for t in model.tasks],
    )


def sop_to_model(entity: SOP) -> SOPModel:
    """Convert SOP domain entity to SOPModel.

    Args:
        entity: SOP domain entity

    Returns:
        SOPModel instance with full task/step/hazard hierarchy
    """
    model = SOPModel(
        id=entity.id,
        title=entity.title,
        created_by=entity.created_by,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        deleted_at=entity.deleted_at,
    )
    model.tasks = [task_to_model(t, entity.id) for t in entity.tasks]
    return model
