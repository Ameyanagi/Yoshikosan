"""SQLAlchemy ORM models for the application."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, Boolean, Float, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all ORM models."""

    pass


class UserModel(Base):
    """User model for authentication."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<UserModel(id={self.id}, email={self.email})>"


class SOPModel(Base):
    """SOP (Standard Operating Procedure) model."""

    __tablename__ = "sops"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    # Relationships
    tasks: Mapped[list["TaskModel"]] = relationship(
        "TaskModel", back_populates="sop", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SOPModel(id={self.id}, title={self.title})>"


class TaskModel(Base):
    """Task model within an SOP."""

    __tablename__ = "tasks"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    sop_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("sops.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    sop: Mapped["SOPModel"] = relationship("SOPModel", back_populates="tasks")
    steps: Mapped[list["StepModel"]] = relationship(
        "StepModel",
        back_populates="task",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<TaskModel(id={self.id}, title={self.title}, order={self.order_index})>"
        )


class StepModel(Base):
    """Step model within a task."""

    __tablename__ = "steps"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    task_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_result: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    task: Mapped["TaskModel"] = relationship("TaskModel", back_populates="steps")
    hazards: Mapped[list["HazardModel"]] = relationship(
        "HazardModel",
        back_populates="step",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<StepModel(id={self.id}, description={self.description[:50]}, order={self.order_index})>"


class HazardModel(Base):
    """Hazard model associated with a step."""

    __tablename__ = "hazards"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    step_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("steps.id", ondelete="CASCADE"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    mitigation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    step: Mapped["StepModel"] = relationship("StepModel", back_populates="hazards")

    def __repr__(self) -> str:
        return f"<HazardModel(id={self.id}, severity={self.severity})>"


class WorkSessionModel(Base):
    """Work session model tracking worker progress through an SOP."""

    __tablename__ = "work_sessions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    sop_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("sops.id"), nullable=False
    )
    worker_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    current_step_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("steps.id"), nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    approved_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    paused_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    aborted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    abort_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    sop: Mapped["SOPModel"] = relationship("SOPModel", lazy="joined")
    checks: Mapped[list["SafetyCheckModel"]] = relationship(
        "SafetyCheckModel",
        back_populates="session",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<WorkSessionModel(id={self.id}, status={self.status}, locked={self.locked})>"


class SafetyCheckModel(Base):
    """Safety check model recording verification of a step."""

    __tablename__ = "safety_checks"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("work_sessions.id"), nullable=False
    )
    step_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("steps.id"), nullable=False
    )
    result: Mapped[str] = mapped_column(Text, nullable=False)
    feedback_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    checked_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    override_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Relationships
    session: Mapped["WorkSessionModel"] = relationship(
        "WorkSessionModel", back_populates="checks"
    )

    def __repr__(self) -> str:
        return f"<SafetyCheckModel(id={self.id}, result={self.result}, checked_at={self.checked_at})>"
