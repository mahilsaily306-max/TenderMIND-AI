from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_agency, verify_workspace_access
from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.client_workspace import ClientWorkspace
from app.models.user import User, UserRole
from app.services.audit_service import create_audit_log
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


class WorkspaceCreate(BaseModel):
    name: str
    description: str | None = None


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class GrantAccessRequest(BaseModel):
    user_id: int


@router.post("")
async def create_workspace(
    req: WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner", "manager")),
    agency=Depends(get_current_agency),
):
    service = WorkspaceService(db)
    workspace = await service.create_workspace(agency_id=agency.id, name=req.name, description=req.description)
    await create_audit_log(db, agency.id, current_user.id, "workspace.create", "client_workspace", workspace.id)
    return {"id": workspace.id, "name": workspace.name}


@router.get("")
async def list_workspaces(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agency=Depends(get_current_agency),
):
    service = WorkspaceService(db)
    if current_user.role == UserRole.OWNER:
        workspaces = await service.list_workspaces(agency.id)
    else:
        workspaces = await service.list_user_workspaces(current_user.id, agency.id)
    return [
        {
            "id": w.id,
            "name": w.name,
            "description": w.description,
            "is_active": w.is_active,
            "created_at": w.created_at.isoformat(),
        }
        for w in workspaces
    ]


@router.get("/{workspace_id}")
async def get_workspace(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agency=Depends(get_current_agency),
    workspace: ClientWorkspace = Depends(verify_workspace_access),
):
    return {
        "id": workspace.id,
        "name": workspace.name,
        "description": workspace.description,
        "is_active": workspace.is_active,
        "settings": workspace.settings,
        "created_at": workspace.created_at.isoformat(),
    }


@router.patch("/{workspace_id}")
async def update_workspace(
    workspace_id: int,
    req: WorkspaceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner")),
    agency=Depends(get_current_agency),
):
    service = WorkspaceService(db)
    updated = await service.update_workspace(
        workspace_id, agency.id, name=req.name, description=req.description, is_active=req.is_active
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    await create_audit_log(db, agency.id, current_user.id, "workspace.update", "client_workspace", workspace_id)
    return {"id": updated.id, "name": updated.name}


@router.post("/{workspace_id}/access")
async def grant_workspace_access(
    workspace_id: int,
    req: GrantAccessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner")),
    agency=Depends(get_current_agency),
    workspace: ClientWorkspace = Depends(verify_workspace_access),
):
    service = WorkspaceService(db)
    access = await service.grant_access(req.user_id, workspace_id)
    await create_audit_log(db, agency.id, current_user.id, "workspace.grant_access", "user_client_access", access.id)
    return {"message": "Access granted"}


@router.delete("/{workspace_id}/access/{user_id}")
async def revoke_workspace_access(
    workspace_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner")),
    agency=Depends(get_current_agency),
    workspace: ClientWorkspace = Depends(verify_workspace_access),
):
    service = WorkspaceService(db)
    success = await service.revoke_access(user_id, workspace_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Access record not found")
    await create_audit_log(db, agency.id, current_user.id, "workspace.revoke_access", "user_client_access")
    return {"message": "Access revoked"}
