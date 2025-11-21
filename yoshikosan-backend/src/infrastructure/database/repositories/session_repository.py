"""SQLAlchemy implementation of WorkSession repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.domain.work_session.entities import SessionStatus, WorkSession
from src.infrastructure.database.mappers.session_mapper import (
    session_to_domain,
    session_to_model,
)
from src.infrastructure.database.models import WorkSessionModel


class SQLAlchemyWorkSessionRepository:
    """SQLAlchemy implementation of WorkSessionRepository."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def save(self, work_session: WorkSession) -> WorkSession:
        """Save or update a work session.

        Args:
            work_session: WorkSession entity to save

        Returns:
            The saved WorkSession entity
        """
        # Check if session already exists
        existing = await self.session.get(WorkSessionModel, work_session.id)

        if existing:
            # Update existing session
            existing.status = work_session.status.value
            existing.current_step_id = work_session.current_step_id
            existing.completed_at = work_session.completed_at
            existing.approved_at = work_session.approved_at
            existing.approved_by = work_session.approved_by
            existing.locked = work_session.locked
            existing.rejection_reason = work_session.rejection_reason

            # Remove existing checks and add new ones
            existing.checks = []
            await self.session.flush()
            
            # Import check_to_model from mapper
            from src.infrastructure.database.mappers.session_mapper import check_to_model
            
            # Add updated checks
            for check in work_session.checks:
                check_model = check_to_model(check, work_session.id)
                existing.checks.append(check_model)
            
            model = existing
        else:
            # Convert domain entity to model and add new session
            model = session_to_model(work_session)
            self.session.add(model)

        await self.session.flush()
        await self.session.refresh(model)

        # Return domain entity
        return session_to_domain(model)

    async def get_by_id(self, session_id: UUID) -> WorkSession | None:
        """Get a work session by ID with eager loading of checks.

        Args:
            session_id: WorkSession ID

        Returns:
            WorkSession entity if found, None otherwise
        """
        # Build query with eager loading
        stmt = (
            select(WorkSessionModel)
            .where(WorkSessionModel.id == session_id)
            .options(joinedload(WorkSessionModel.checks))
        )

        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()

        if model is None:
            return None

        return session_to_domain(model)

    async def get_current_for_worker(self, worker_id: UUID) -> WorkSession | None:
        """Get the current active session for a worker.

        Args:
            worker_id: Worker user ID

        Returns:
            Active WorkSession if found, None otherwise
        """
        # Build query for in-progress session
        stmt = (
            select(WorkSessionModel)
            .where(WorkSessionModel.worker_id == worker_id)
            .where(WorkSessionModel.status == SessionStatus.IN_PROGRESS.value)
            .options(joinedload(WorkSessionModel.checks))
            .order_by(WorkSessionModel.started_at.desc())
        )

        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()

        if model is None:
            return None

        return session_to_domain(model)

    async def list_by_worker(self, worker_id: UUID) -> list[WorkSession]:
        """List all sessions for a worker.

        Args:
            worker_id: Worker user ID

        Returns:
            List of WorkSession entities ordered by started_at desc
        """
        # Build query with eager loading
        stmt = (
            select(WorkSessionModel)
            .where(WorkSessionModel.worker_id == worker_id)
            .options(joinedload(WorkSessionModel.checks))
            .order_by(WorkSessionModel.started_at.desc())
        )

        result = await self.session.execute(stmt)
        models = result.unique().scalars().all()

        return [session_to_domain(model) for model in models]

    async def list_pending_review(self) -> list[WorkSession]:
        """List all completed sessions pending supervisor review.

        Returns:
            List of WorkSession entities with status COMPLETED ordered by completed_at
        """
        # Build query for completed sessions
        stmt = (
            select(WorkSessionModel)
            .where(WorkSessionModel.status == SessionStatus.COMPLETED.value)
            .options(joinedload(WorkSessionModel.checks))
            .order_by(WorkSessionModel.completed_at.asc())
        )

        result = await self.session.execute(stmt)
        models = result.unique().scalars().all()

        return [session_to_domain(model) for model in models]
