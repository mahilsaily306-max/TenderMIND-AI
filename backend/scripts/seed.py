"""Seed the database with test data for development."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, timedelta

from sqlalchemy import select

from app.core.database import async_session, init_db
from app.core.security import get_password_hash
from app.models.agency import Agency
from app.models.client_workspace import ClientWorkspace
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.tender import Tender, TenderStatus
from app.models.user import User, UserRole
from app.models.user_client_access import UserClientAccess


async def seed():
    await init_db()
    async with async_session() as db:
        # Check if already seeded
        result = await db.execute(select(Agency).where(Agency.slug == "demo-agency"))
        if result.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        # Agency
        agency = Agency(name="Demo Agency", slug="demo-agency", domain="demo.tenderpilot.ai")
        db.add(agency)
        await db.flush()

        # Users
        users_data = [
            ("owner@demo.com", "owner123", "Alice Admin", UserRole.OWNER),
            ("manager@demo.com", "manager123", "Bob Manager", UserRole.MANAGER),
            ("employee@demo.com", "employee123", "Charlie Employee", UserRole.EMPLOYEE),
        ]
        users = []
        for email, pw, name, role in users_data:
            u = User(agency_id=agency.id, email=email, password_hash=get_password_hash(pw), full_name=name, role=role)
            db.add(u)
            await db.flush()
            users.append(u)

        # Workspaces
        ws = ClientWorkspace(agency_id=agency.id, name="Healthcare Tenders", description="Healthcare sector bids")
        db.add(ws)
        ws2 = ClientWorkspace(agency_id=agency.id, name="Infrastructure Projects", description="Infrastructure and construction")
        db.add(ws2)
        await db.flush()

        # Grant access
        db.add(UserClientAccess(user_id=users[1].id, client_workspace_id=ws.id))
        db.add(UserClientAccess(user_id=users[1].id, client_workspace_id=ws2.id))
        db.add(UserClientAccess(user_id=users[2].id, client_workspace_id=ws.id))

        # Tenders
        tenders_data = [
            ("Regional Hospital IT System Upgrade", "RFP-2024-001", TenderStatus.IN_PROGRESS, date.today() + timedelta(days=30), 2500000.0, users[0].id, ws.id),
            ("City Bridge Maintenance Contract", "RFP-2024-002", TenderStatus.QUALIFICATION, date.today() + timedelta(days=45), 5000000.0, users[0].id, ws2.id),
            ("School District Network Infrastructure", "RFP-2024-003", TenderStatus.IDENTIFIED, date.today() + timedelta(days=60), 1200000.0, users[0].id, ws.id),
            ("Water Treatment Plant Expansion", "RFP-2024-004", TenderStatus.INTERNAL_REVIEW, date.today() + timedelta(days=15), 8000000.0, users[0].id, ws2.id),
            ("County Health Records Digitization", "RFP-2024-005", TenderStatus.SUBMITTED, date.today() - timedelta(days=5), 3500000.0, users[0].id, ws.id),
        ]
        tenders = []
        for title, ref, status, deadline, value, creator_id, workspace_id in tenders_data:
            t = Tender(
                agency_id=agency.id,
                client_workspace_id=workspace_id,
                title=title,
                reference_number=ref,
                status=status,
                bid_deadline=deadline,
                estimated_value=value,
                created_by=creator_id,
            )
            db.add(t)
            await db.flush()
            tenders.append(t)

        # Tasks
        for _, t in enumerate(tenders[:3]):
            task = Task(
                tender_id=t.id,
                title=f"Review tender documents - {t.title[:30]}",
                status=TaskStatus.PENDING,
                priority=TaskPriority.HIGH,
                assigned_to=users[2].id,
                assigned_by=users[0].id,
                due_date=t.bid_deadline,
            )
            db.add(task)

        await db.commit()
        print("Seed data inserted successfully!")
        print(f"  Agency: {agency.name}")
        print(f"  Users: {', '.join(u.email for u in users)}")
        print(f"  Workspaces: {ws.name}, {ws2.name}")
        print(f"  Tenders: {len(tenders)}")
        print()
        print("Login credentials:")
        for u in users:
            print(f"  {u.email} / {u.role.value} / password: {u.email.split('@')[0]}123")


if __name__ == "__main__":
    asyncio.run(seed())
