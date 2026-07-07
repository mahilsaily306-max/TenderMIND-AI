"""Bid Readiness Score calculation tests."""
import pytest
from httpx import AsyncClient

from app.core.security import create_access_token

pytestmark = pytest.mark.asyncio


def _token(user):
    return create_access_token({"sub": str(user.id), "role": user.role.value, "agency_id": user.agency_id})


class TestBidReadiness:
    async def test_calculate_score(self, client: AsyncClient, owner_user, tender):
        token = _token(owner_user)
        resp = await client.post(f"/api/v1/bid-readiness/calculate/{tender.id}",
                                 headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "overall_score" in data
        assert "compliance_score" in data
        assert "experience_score" in data
        assert "capacity_score" in data
        assert "risk_score" in data
        assert "past_performance_score" in data
        assert "weights_used" in data
        assert "breakdown" in data
        assert 0 <= data["overall_score"] <= 1

    async def test_score_persisted_on_tender(self, client: AsyncClient, owner_user, tender):
        token = _token(owner_user)
        await client.post(f"/api/v1/bid-readiness/calculate/{tender.id}",
                          headers={"Authorization": f"Bearer {token}"})
        resp = await client.get(f"/api/v1/tenders/{tender.id}",
                                headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["ai_readiness_score"] is not None
        assert resp.json()["ai_go_nogo_recommendation"] in ("go", "no_go")
        assert resp.json()["ai_go_nogo_explanation"] is not None

    async def test_get_latest_score(self, client: AsyncClient, owner_user, tender):
        token = _token(owner_user)
        await client.post(f"/api/v1/bid-readiness/calculate/{tender.id}",
                          headers={"Authorization": f"Bearer {token}"})
        resp = await client.get(f"/api/v1/bid-readiness/{tender.id}",
                                headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["overall_score"] is not None

    async def test_score_before_calculation(self, client: AsyncClient, owner_user, tender):
        token = _token(owner_user)
        resp = await client.get(f"/api/v1/bid-readiness/{tender.id}",
                                headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404
