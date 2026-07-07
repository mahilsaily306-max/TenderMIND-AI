from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.agency import Agency
from app.models.client_workspace import ClientWorkspace
from app.models.user import User


async def get_current_agency(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Agency:
    result = await db.execute(select(Agency).where(Agency.id == current_user.agency_id))
    agency = result.scalar_one_or_none()
    if not agency or not agency.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found or inactive")
    return agency


async def verify_workspace_access(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClientWorkspace:
    result = await db.execute(
        select(ClientWorkspace).where(
            ClientWorkspace.id == workspace_id,
            ClientWorkspace.agency_id == current_user.agency_id,
        )
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if not workspace.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workspace is inactive")
    return workspace
