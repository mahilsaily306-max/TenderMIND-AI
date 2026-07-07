"""Comments and @mentions API tests."""

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token

pytestmark = pytest.mark.asyncio


def _token(user):
    return create_access_token({"sub": str(user.id), "role": user.role.value, "agency_id": user.agency_id})


class TestComments:
    async def test_create_comment(self, client: AsyncClient, owner_user, tender):
        token = _token(owner_user)
        resp = await client.post(
            "/api/v1/comments",
            json={
                "tender_id": tender.id,
                "content": "Test @charlie mention",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "Test" in data["content"]
        assert data["mentions"] is not None

    async def test_list_comments(self, client: AsyncClient, owner_user, tender):
        token = _token(owner_user)
        await client.post(
            "/api/v1/comments",
            json={
                "tender_id": tender.id,
                "content": "First comment",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = await client.get(f"/api/v1/comments?tender_id={tender.id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_comment_on_nonexistent_tender(self, client: AsyncClient, owner_user):
        token = _token(owner_user)
        resp = await client.post(
            "/api/v1/comments",
            json={
                "tender_id": 99999,
                "content": "Ghost",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
