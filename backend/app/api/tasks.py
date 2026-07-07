from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_agency
from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.tender import Tender
from app.models.user import User, UserRole
from app.services.audit_service import create_audit_log
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    tender_id: int
    title: str
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_to: int | None = None
    due_date: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assigned_to: int | None = None
    due_date: str | None = None


@router.post("")
async def create_task(
    req: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner", "manager")),
    agency=Depends(get_current_agency),
):
    # Verify tender belongs to agency
    result = await db.execute(select(Tender).where(Tender.id == req.tender_id, Tender.agency_id == agency.id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender not found")

    service = TaskService(db)
    task = await service.create_task(
        tender_id=req.tender_id,
        title=req.title,
        description=req.description,
        priority=req.priority,
        assigned_to=req.assigned_to,
        assigned_by=current_user.id,
        due_date=req.due_date,
    )
    await create_audit_log(db, agency.id, current_user.id, "task.create", "task", task.id)
    return {
        "id": task.id,
        "tender_id": task.tender_id,
        "title": task.title,
        "status": task.status.value,
        "priority": task.priority.value,
        "assigned_to": task.assigned_to,
    }


@router.get("")
async def list_tasks(
    tender_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agency=Depends(get_current_agency),
):
    service = TaskService(db)
    if tender_id:
        tasks = await service.list_tasks(tender_id)
    elif current_user.role == UserRole.EMPLOYEE:
        tasks = await service.list_user_tasks(current_user.id)
    else:
        # Owner/manager — list all tasks (through tenders in their agency)
        stmt = select(Task).join(Tender, Task.tender_id == Tender.id).where(Tender.agency_id == agency.id)
        result = await db.execute(stmt.order_by(Task.created_at.desc()))
        tasks = result.scalars().all()

    return [
        {
            "id": t.id,
            "tender_id": t.tender_id,
            "title": t.title,
            "description": t.description,
            "status": t.status.value,
            "priority": t.priority.value,
            "assigned_to": t.assigned_to,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            "created_at": t.created_at.isoformat(),
        }
        for t in tasks
    ]


@router.get("/{task_id}")
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agency=Depends(get_current_agency),
):
    service = TaskService(db)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    # Verify agency scope via tender
    t_result = await db.execute(select(Tender).where(Tender.id == task.tender_id, Tender.agency_id == agency.id))
    if not t_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return {
        "id": task.id,
        "tender_id": task.tender_id,
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "priority": task.priority.value,
        "assigned_to": task.assigned_to,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "created_at": task.created_at.isoformat(),
    }


@router.patch("/{task_id}")
async def update_task(
    task_id: int,
    req: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agency=Depends(get_current_agency),
):
    # Employees can only update their own tasks
    service = TaskService(db)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    # Verify agency scope
    t_result = await db.execute(select(Tender).where(Tender.id == task.tender_id, Tender.agency_id == agency.id))
    if not t_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if current_user.role == UserRole.EMPLOYEE and task.assigned_to != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not assigned to this task")

    updated = await service.update_task(
        task_id,
        title=req.title,
        description=req.description,
        status=req.status,
        priority=req.priority,
        assigned_to=req.assigned_to,
        due_date=req.due_date,
    )
    await create_audit_log(db, agency.id, current_user.id, "task.update", "task", task_id)
    return {"id": updated.id, "status": updated.status.value, "title": updated.title}
