from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client_workspace import ClientWorkspace
from app.models.user_client_access import UserClientAccess


class WorkspaceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_workspace(self, agency_id: int, name: str, description: str | None = None) -> ClientWorkspace:
        workspace = ClientWorkspace(agency_id=agency_id, name=name, description=description)
        self.db.add(workspace)
        await self.db.commit()
        await self.db.refresh(workspace)
        return workspace

    async def get_workspace(self, workspace_id: int, agency_id: int) -> ClientWorkspace | None:
        result = await self.db.execute(
            select(ClientWorkspace).where(
                ClientWorkspace.id == workspace_id,
                ClientWorkspace.agency_id == agency_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_workspace(self, workspace_id: int, agency_id: int, **kwargs) -> ClientWorkspace | None:
        workspace = await self.get_workspace(workspace_id, agency_id)
        if not workspace:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(workspace, key):
                setattr(workspace, key, value)
        await self.db.commit()
        await self.db.refresh(workspace)
        return workspace

    async def list_workspaces(self, agency_id: int) -> list[ClientWorkspace]:
        result = await self.db.execute(
            select(ClientWorkspace)
            .where(ClientWorkspace.agency_id == agency_id)
            .order_by(ClientWorkspace.name)
        )
        return list(result.scalars().all())

    async def list_user_workspaces(self, user_id: int, agency_id: int) -> list[ClientWorkspace]:
        result = await self.db.execute(
            select(ClientWorkspace)
            .join(UserClientAccess, UserClientAccess.client_workspace_id == ClientWorkspace.id)
            .where(
                UserClientAccess.user_id == user_id,
                ClientWorkspace.agency_id == agency_id,
            )
            .order_by(ClientWorkspace.name)
        )
        return list(result.scalars().all())

    async def grant_access(self, user_id: int, workspace_id: int) -> UserClientAccess:
        access = UserClientAccess(user_id=user_id, client_workspace_id=workspace_id)
        self.db.add(access)
        await self.db.commit()
        await self.db.refresh(access)
        return access

    async def revoke_access(self, user_id: int, workspace_id: int) -> bool:
        result = await self.db.execute(
            select(UserClientAccess).where(
                UserClientAccess.user_id == user_id,
                UserClientAccess.client_workspace_id == workspace_id,
            )
        )
        access = result.scalar_one_or_none()
        if not access:
            return False
        await self.db.delete(access)
        await self.db.commit()
        return True
