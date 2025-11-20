"""SQLAlchemy implementation of SOP repository."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.domain.sop.entities import SOP
from src.infrastructure.database.mappers.sop_mapper import sop_to_domain, sop_to_model
from src.infrastructure.database.models import SOPModel, StepModel, TaskModel


class SQLAlchemySOPRepository:
    """SQLAlchemy implementation of SOPRepository."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def save(self, sop: SOP) -> SOP:
        """Save or update an SOP.

        Args:
            sop: SOP entity to save

        Returns:
            The saved SOP entity
        """
        # Check if SOP already exists
        existing = await self.session.get(SOPModel, sop.id)

        if existing:
            # Update existing SOP
            existing.title = sop.title
            existing.updated_at = sop.updated_at
            existing.deleted_at = sop.deleted_at

            # Remove existing tasks (cascade will handle steps and hazards)
            existing.tasks = []
            await self.session.flush()

            # Create new task models from domain entity
            from src.infrastructure.database.mappers.sop_mapper import task_to_model

            existing.tasks = [task_to_model(t, sop.id) for t in sop.tasks]
            await self.session.flush()
            await self.session.refresh(existing)
            # Return domain entity
            return sop_to_domain(existing)
        else:
            # Convert domain entity to model for new SOP
            model = sop_to_model(sop)
            self.session.add(model)
            await self.session.flush()
            await self.session.refresh(model)
            # Return domain entity
            return sop_to_domain(model)

    async def get_by_id(self, sop_id: UUID) -> SOP | None:
        """Get an SOP by ID with eager loading of relationships.

        Args:
            sop_id: SOP ID

        Returns:
            SOP entity if found, None otherwise
        """
        # Build query with eager loading
        stmt = (
            select(SOPModel)
            .where(SOPModel.id == sop_id)
            .options(
                joinedload(SOPModel.tasks)
                .joinedload(TaskModel.steps)
                .joinedload(StepModel.hazards)
            )
        )

        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()

        if model is None:
            return None

        return sop_to_domain(model)

    async def list_by_user(
        self, user_id: UUID, include_deleted: bool = False
    ) -> list[SOP]:
        """List all SOPs created by a user.

        Args:
            user_id: User ID
            include_deleted: Whether to include soft-deleted SOPs

        Returns:
            List of SOP entities
        """
        # Build query with eager loading
        stmt = (
            select(SOPModel)
            .where(SOPModel.created_by == user_id)
            .options(
                joinedload(SOPModel.tasks)
                .joinedload(TaskModel.steps)
                .joinedload(StepModel.hazards)
            )
        )

        # Filter out deleted SOPs unless requested
        if not include_deleted:
            stmt = stmt.where(SOPModel.deleted_at.is_(None))

        result = await self.session.execute(stmt)
        models = result.unique().scalars().all()

        return [sop_to_domain(model) for model in models]

    async def delete(self, sop_id: UUID) -> bool:
        """Soft delete an SOP by setting deleted_at timestamp.

        Args:
            sop_id: SOP ID

        Returns:
            True if SOP was deleted, False if not found
        """
        model = await self.session.get(SOPModel, sop_id)

        if model is None:
            return False

        model.deleted_at = datetime.now()
        model.updated_at = datetime.now()
        await self.session.flush()

        return True
