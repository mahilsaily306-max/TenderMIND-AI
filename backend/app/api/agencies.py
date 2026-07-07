from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_agency
from app.core.database import get_db
from app.core.deps import require_role
from app.models.agency import Agency
from app.models.user import User
from app.services.agency_service import AgencyService

router = APIRouter(prefix="/agencies", tags=["agencies"])


class AgencyCreate(BaseModel):
    name: str
    domain: str | None = None
    logo_url: str | None = None


class AgencyUpdate(BaseModel):
    name: str | None = None
    domain: str | None = None
    logo_url: str | None = None
    settings: str | None = None


@router.post("")
async def create_agency(
    req: AgencyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner")),
):
    service = AgencyService(db)
    agency = await service.create_agency(name=req.name, domain=req.domain, logo_url=req.logo_url)
    return {"id": agency.id, "name": agency.name, "slug": agency.slug}


@router.get("")
async def list_agencies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner")),
):
    service = AgencyService(db)
    agencies = await service.list_agencies()
    return [
        {"id": a.id, "name": a.name, "slug": a.slug, "domain": a.domain, "is_active": a.is_active} for a in agencies
    ]


@router.get("/current")
async def get_current_agency_endpoint(
    agency: Agency = Depends(get_current_agency),
):
    return {
        "id": agency.id,
        "name": agency.name,
        "slug": agency.slug,
        "domain": agency.domain,
        "logo_url": agency.logo_url,
        "is_active": agency.is_active,
        "settings": agency.settings,
    }


@router.patch("/current")
async def update_current_agency(
    req: AgencyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner")),
    agency: Agency = Depends(get_current_agency),
):
    service = AgencyService(db)
    updated = await service.update_agency(
        agency.id,
        name=req.name,
        domain=req.domain,
        logo_url=req.logo_url,
        settings=req.settings,
    )
    return {"id": updated.id, "name": updated.name, "slug": updated.slug}
