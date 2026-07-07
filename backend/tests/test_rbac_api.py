"""RBAC enforcement integration tests."""

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token

pytestmark = pytest.mark.asyncio


def _token(user_id: int, role: str, agency_id: int) -> str:
    return create_access_token({"sub": str(user_id), "role": role, "agency_id": agency_id})


class TestRBAC:
    async def test_employee_cannot_create_agency(self, client: AsyncClient, employee_user):
        token = _token(employee_user.id, "employee", employee_user.agency_id)
        resp = await client.post(
            "/api/v1/agencies", json={"name": "Hacked"}, headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "forbidden"

    async def test_manager_cannot_create_agency(self, client: AsyncClient, manager_user):
        token = _token(manager_user.id, "manager", manager_user.agency_id)
        resp = await client.post(
            "/api/v1/agencies", json={"name": "Hacked"}, headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403

    async def test_owner_can_create_agency(self, client: AsyncClient, owner_user):
        token = _token(owner_user.id, "owner", owner_user.agency_id)
        resp = await client.post(
            "/api/v1/agencies", json={"name": "New Agency"}, headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200

    async def test_employee_cannot_create_workspace(self, client: AsyncClient, employee_user):
        token = _token(employee_user.id, "employee", employee_user.agency_id)
        resp = await client.post(
            "/api/v1/workspaces", json={"name": "Hacked"}, headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403

    async def test_manager_can_create_workspace(self, client: AsyncClient, manager_user):
        token = _token(manager_user.id, "manager", manager_user.agency_id)
        resp = await client.post(
            "/api/v1/workspaces", json={"name": "New Workspace"}, headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200

    async def test_employee_cannot_create_tender(self, client: AsyncClient, employee_user, workspace):
        token = _token(employee_user.id, "employee", employee_user.agency_id)
        resp = await client.post(
            "/api/v1/tenders",
            json={
                "client_workspace_id": workspace.id,
                "title": "Hacked Tender",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_manager_can_create_tender(self, client: AsyncClient, manager_user, workspace):
        token = _token(manager_user.id, "manager", manager_user.agency_id)
        resp = await client.post(
            "/api/v1/tenders",
            json={
                "client_workspace_id": workspace.id,
                "title": "Manager Tender",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    async def test_employee_can_view_tenders(self, client: AsyncClient, employee_user, tender):  # noqa: ARG002
        token = _token(employee_user.id, "employee", employee_user.agency_id)
        resp = await client.get("/api/v1/tenders", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_employee_can_update_own_task(self, client: AsyncClient, owner_user, employee_user, tender):
        owner_tok = _token(owner_user.id, "owner", owner_user.agency_id)
        emp_token = _token(employee_user.id, "employee", employee_user.agency_id)
        create_resp = await client.post(
            "/api/v1/tasks",
            json={
                "tender_id": tender.id,
                "title": "Employee Task",
                "assigned_to": employee_user.id,
            },
            headers={"Authorization": f"Bearer {owner_tok}"},
        )
        assert create_resp.status_code == 200, create_resp.text
        task_id = create_resp.json()["id"]
        resp = await client.patch(
            f"/api/v1/tasks/{task_id}", json={"status": "completed"}, headers={"Authorization": f"Bearer {emp_token}"}
        )
        assert resp.status_code == 200

    async def test_cross_agency_isolation(self, client: AsyncClient, agency, db_session):
        from app.core.security import get_password_hash
        from app.models.user import User, UserRole

        other_agency_id = agency.id + 1
        other_user = User(
            id=999,
            email="other@other.com",
            password_hash=get_password_hash("test"),
            role=UserRole.OWNER,
            agency_id=other_agency_id,
            full_name="Other",
        )
        db_session.add(other_user)
        await db_session.commit()
        other_token = _token(999, "owner", other_agency_id)
        resp = await client.get(f"/api/v1/workspaces/{agency.id}", headers={"Authorization": f"Bearer {other_token}"})
        assert resp.status_code == 404
