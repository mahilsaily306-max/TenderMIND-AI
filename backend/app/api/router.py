from fastapi import APIRouter

from app.api import (
    agencies,
    audit,
    auth,
    bid_readiness,
    comments,
    compliance,
    copilot,
    documents,
    extracted_fields,
    knowledge_base,
    notifications,
    reports,
    tasks,
    tenders,
    users,
    workspaces,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(agencies.router)
api_router.include_router(workspaces.router)
api_router.include_router(users.router)
api_router.include_router(tenders.router)
api_router.include_router(tasks.router)
api_router.include_router(documents.router)
api_router.include_router(comments.router)
api_router.include_router(audit.router)
api_router.include_router(compliance.router)
api_router.include_router(extracted_fields.router)
api_router.include_router(bid_readiness.router)
api_router.include_router(copilot.router)
api_router.include_router(knowledge_base.router)
api_router.include_router(notifications.router)
api_router.include_router(reports.router)
