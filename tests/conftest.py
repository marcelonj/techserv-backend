import os

os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only")

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import (
    EstadoTicket,
    UrgenciaTicket,
    UserRole,
    create_access_token,
    create_test_token,
    hash_password,
)
from app.main import app
from app.models import Company, Equipo, Ticket, User

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine_test, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _add_user(
    session: AsyncSession,
    *,
    email: str,
    role: UserRole,
    company_id: uuid.UUID,
    password: str = "pass123",
    full_name: str | None = None,
    phone: str = "5551234567",
    is_active: bool = True,
) -> User:
    user = User(
        id=uuid.uuid4(),
        email=email,
        full_name=full_name or email.split("@")[0].title(),
        role=role,
        company_id=company_id,
        phone=phone,
        password_hash=hash_password(password),
        is_active=is_active,
    )
    session.add(user)
    return user


@pytest_asyncio.fixture
async def seeded_session(db_session: AsyncSession) -> AsyncSession:
    company = Company(id=uuid.uuid4(), name="TechServ Demo")
    admin = await _add_user(
        db_session,
        email="admin@techserv.local",
        role=UserRole.ADMINISTRADOR,
        company_id=company.id,
        password="admin123",
        full_name="Admin User",
    )
    db_session.add(company)
    await db_session.commit()
    db_session.info["admin"] = admin
    db_session.info["company"] = company
    return db_session


@pytest_asyncio.fixture
async def seeded_users(seeded_session: AsyncSession) -> AsyncSession:
    company_id = seeded_session.info["company"].id
    cliente = await _add_user(
        seeded_session,
        email="cliente@techserv.local",
        role=UserRole.CLIENTE,
        company_id=company_id,
        phone="5551111111",
    )
    tecnico = await _add_user(
        seeded_session,
        email="tecnico@techserv.local",
        role=UserRole.TECNICO,
        company_id=company_id,
        phone="5552222222",
    )
    supervisor = await _add_user(
        seeded_session,
        email="supervisor@techserv.local",
        role=UserRole.SUPERVISOR,
        company_id=company_id,
        phone="5553333333",
    )
    area_admin = await _add_user(
        seeded_session,
        email="area@techserv.local",
        role=UserRole.AREA_ADMINISTRATIVA,
        company_id=company_id,
        phone="5554444444",
    )
    await seeded_session.commit()
    seeded_session.info["cliente"] = cliente
    seeded_session.info["tecnico"] = tecnico
    seeded_session.info["supervisor"] = supervisor
    seeded_session.info["area_admin"] = area_admin
    return seeded_session


@pytest_asyncio.fixture
async def sample_equipo(seeded_users: AsyncSession) -> Equipo:
    equipo = Equipo(
        id=uuid.uuid4(),
        tipo="Laptop",
        marca="Dell",
        modelo="XPS 15",
        numero_serie="SN-001",
        cliente_id=seeded_users.info["cliente"].id,
    )
    seeded_users.add(equipo)
    await seeded_users.commit()
    return equipo


@pytest_asyncio.fixture
async def sample_ticket(seeded_users: AsyncSession, sample_equipo: Equipo) -> Ticket:
    ticket = Ticket(
        id=uuid.uuid4(),
        titulo="Ticket de prueba",
        descripcion="Descripcion del ticket",
        estado=EstadoTicket.ABIERTO,
        urgencia=UrgenciaTicket.MEDIA,
        direccion="Av. Principal 123",
        cliente_id=seeded_users.info["cliente"].id,
        tecnico_id=seeded_users.info["tecnico"].id,
        equipo_id=sample_equipo.id,
    )
    seeded_users.add(ticket)
    await seeded_users.commit()
    return ticket


@pytest_asyncio.fixture
async def client(seeded_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield seeded_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(seeded_session: AsyncSession) -> str:
    admin: User = seeded_session.info["admin"]
    return create_access_token(admin.id, admin.email, UserRole(admin.role))


@pytest.fixture
def cliente_token(seeded_users: AsyncSession) -> str:
    user: User = seeded_users.info["cliente"]
    return create_test_token(user.id, user.email, UserRole.CLIENTE)


@pytest.fixture
def tecnico_token(seeded_users: AsyncSession) -> str:
    user: User = seeded_users.info["tecnico"]
    return create_test_token(user.id, user.email, UserRole.TECNICO)


@pytest.fixture
def supervisor_token(seeded_users: AsyncSession) -> str:
    user: User = seeded_users.info["supervisor"]
    return create_test_token(user.id, user.email, UserRole.SUPERVISOR)


@pytest.fixture
def area_admin_token(seeded_users: AsyncSession) -> str:
    user: User = seeded_users.info["area_admin"]
    return create_test_token(user.id, user.email, UserRole.AREA_ADMINISTRATIVA)
