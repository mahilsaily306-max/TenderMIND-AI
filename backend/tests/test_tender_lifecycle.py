"""Tender lifecycle state machine tests."""
import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.models.tender import TenderStatus

pytestmark = pytest.mark.asyncio


def _token(user):
    return create_access_token({"sub": str(user.id), "role": user.role.value, "agency_id": user.agency_id})


class TestTenderLifecycle:
    async def test_initial_status(self, client: AsyncClient, owner_user, workspace):
        token = _token(owner_user)
        resp = await client.post("/api/v1/tenders", json={
            "client_workspace_id": workspace.id,
            "title": "Lifecycle Test",
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "identified"

    async def test_valid_transition(self, client: AsyncClient, owner_user, tender):
        token = _token(owner_user)
        resp = await client.patch(f"/api/v1/tenders/{tender.id}", json={"status": "qualification"},
                                  headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "qualification"

    async def test_invalid_transition(self, client: AsyncClient, owner_user, tender):
        token = _token(owner_user)
        resp = await client.patch(f"/api/v1/tenders/{tender.id}", json={"status": "submitted"},
                                  headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 400

    async def test_full_lifecycle(self, client: AsyncClient, owner_user, tender):
        token = _token(owner_user)
        for status in ["qualification", "in_progress", "internal_review", "submitted", "won"]:
            resp = await client.patch(f"/api/v1/tenders/{tender.id}", json={"status": status},
                                      headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 200, f"Failed to transition to {status}: {resp.text}"
            assert resp.json()["status"] == status

    async def test_withdraw_from_any_state(self, client: AsyncClient, owner_user, tender, db_session):
        token = _token(owner_user)
        from sqlalchemy import select

        from app.models.tender import Tender
        for status in ["identified", "qualification", "in_progress", "internal_review", "submitted"]:
            async with db_session as db:
                result = await db.execute(select(Tender).where(Tender.id == tender.id))
                t = result.scalar_one()
                t.status = TenderStatus(status)
                await db.commit()
            resp = await client.patch(f"/api/v1/tenders/{tender.id}", json={"status": "withdrawn"},
                                      headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 200, f"Failed to withdraw from {status}"
