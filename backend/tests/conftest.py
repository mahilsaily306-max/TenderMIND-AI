"""Pytest fixtures for integration tests using SQLite async."""

from collections.abc import AsyncGenerator
from datetime import date, timedelta

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Text
from sqlalchemy import event as sa_event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.main import app
from app.models.agency import Agency
from app.models.client_workspace import ClientWorkspace
from app.models.tender import Tender, TenderStatus
from app.models.user import User, UserRole

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

# Register type override for pgvector Vector -> Text for SQLite
from pgvector.sqlalchemy import Vector  # noqa: E402


@sa_event.listens_for(Base.metadata, "before_create")
def _replace_vector_types(target, connection, **kw):
    if "sqlite" in connection.engine.name:
        for table in target.tables.values():
            for col in table.columns:
                if isinstance(col.type, Vector):
                    col.type = Text()


test_engine = create_async_engine(TEST_DB_URL, echo=False)
test_async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with test_async_session() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session(setup_db) -> AsyncSession:
    async with test_async_session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def agency(db_session: AsyncSession) -> Agency:
    a = Agency(name="Test Agency", slug="test-agency")
    db_session.add(a)
    await db_session.commit()
    await db_session.refresh(a)
    return a


@pytest_asyncio.fixture(scope="function")
async def owner_user(db_session: AsyncSession, agency: Agency) -> User:
    u = User(
        agency_id=agency.id,
        email="owner@test.com",
        password_hash=get_password_hash("password"),
        full_name="Test Owner",
        role=UserRole.OWNER,
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture(scope="function")
async def manager_user(db_session: AsyncSession, agency: Agency) -> User:
    u = User(
        agency_id=agency.id,
        email="manager@test.com",
        password_hash=get_password_hash("password"),
        full_name="Test Manager",
        role=UserRole.MANAGER,
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture(scope="function")
async def employee_user(db_session: AsyncSession, agency: Agency) -> User:
    u = User(
        agency_id=agency.id,
        email="employee@test.com",
        password_hash=get_password_hash("password"),
        full_name="Test Employee",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture(scope="function")
async def workspace(db_session: AsyncSession, agency: Agency) -> ClientWorkspace:
    w = ClientWorkspace(agency_id=agency.id, name="Test Workspace")
    db_session.add(w)
    await db_session.commit()
    await db_session.refresh(w)
    return w


@pytest_asyncio.fixture(scope="function")
async def tender(db_session: AsyncSession, agency: Agency, workspace: ClientWorkspace, owner_user: User) -> Tender:
    t = Tender(
        agency_id=agency.id,
        client_workspace_id=workspace.id,
        title="Test Tender",
        status=TenderStatus.IDENTIFIED,
        bid_deadline=date.today() + timedelta(days=30),
        created_by=owner_user.id,
    )
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t
