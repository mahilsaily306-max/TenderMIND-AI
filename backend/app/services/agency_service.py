import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agency import Agency


class AgencyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_agency(self, name: str, domain: str | None = None, logo_url: str | None = None) -> Agency:
        slug = re.sub(r"[^a-z0-9-]", "", name.lower().replace(" ", "-"))[:100]
        agency = Agency(name=name, slug=slug, domain=domain, logo_url=logo_url)
        self.db.add(agency)
        await self.db.commit()
        await self.db.refresh(agency)
        return agency

    async def get_agency(self, agency_id: int) -> Agency | None:
        result = await self.db.execute(select(Agency).where(Agency.id == agency_id))
        return result.scalar_one_or_none()

    async def update_agency(self, agency_id: int, **kwargs) -> Agency | None:
        agency = await self.get_agency(agency_id)
        if not agency:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(agency, key):
                setattr(agency, key, value)
        await self.db.commit()
        await self.db.refresh(agency)
        return agency

    async def list_agencies(self) -> list[Agency]:
        result = await self.db.execute(select(Agency).order_by(Agency.name))
        return list(result.scalars().all())
