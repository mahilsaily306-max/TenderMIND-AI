from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskPriority, TaskStatus


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(
        self,
        tender_id: int,
        title: str,
        description: str | None = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        assigned_to: int | None = None,
        assigned_by: int | None = None,
        due_date: date | None = None,
    ) -> Task:
        task = Task(
            tender_id=tender_id,
            title=title,
            description=description,
            priority=priority,
            assigned_to=assigned_to,
            assigned_by=assigned_by,
            due_date=due_date,
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def get_task(self, task_id: int) -> Task | None:
        result = await self.db.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()

    async def update_task(
        self,
        task_id: int,
        title: str | None = None,
        description: str | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        assigned_to: int | None = None,
        due_date: date | None = None,
    ) -> Task | None:
        task = await self.get_task(task_id)
        if not task:
            return None
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if status is not None:
            task.status = status
            if status == TaskStatus.COMPLETED:
                task.completed_at = datetime.now(UTC)
        if priority is not None:
            task.priority = priority
        if assigned_to is not None:
            task.assigned_to = assigned_to
        if due_date is not None:
            task.due_date = due_date
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def list_tasks(self, tender_id: int) -> list[Task]:
        result = await self.db.execute(
            select(Task).where(Task.tender_id == tender_id).order_by(Task.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_user_tasks(self, user_id: int) -> list[Task]:
        result = await self.db.execute(
            select(Task).where(Task.assigned_to == user_id).order_by(Task.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_task(self, task_id: int) -> bool:
        task = await self.get_task(task_id)
        if not task:
            return False
        await self.db.delete(task)
        await self.db.commit()
        return True
