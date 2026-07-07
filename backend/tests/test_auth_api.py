"""Auth API integration tests."""

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, create_refresh_token

pytestmark = pytest.mark.asyncio


class TestAuth:
    async def test_health(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    async def test_login_invalid_credentials(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/login", json={"email": "none@test.com", "password": "wrong"})
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "unauthorized"

    async def test_login_success(self, client: AsyncClient, owner_user):
        resp = await client.post("/api/v1/auth/login", json={"email": owner_user.email, "password": "password"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["role"] == "owner"

    async def test_me_endpoint(self, client: AsyncClient, owner_user):
        token = create_access_token(
            {"sub": str(owner_user.id), "role": owner_user.role.value, "agency_id": owner_user.agency_id}
        )
        resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["email"] == owner_user.email

    async def test_me_unauthenticated(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "unauthorized"

    async def test_refresh_token(self, client: AsyncClient, owner_user):
        refresh = create_refresh_token({"sub": str(owner_user.id)})
        resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
        assert resp.status_code == 200
        assert "access_token" in resp.json()
