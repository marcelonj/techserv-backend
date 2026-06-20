import pytest
from httpx import AsyncClient

from app.core.security import UserRole


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_health_head(client: AsyncClient):
    response = await client.head("/api/v1/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_token(client: AsyncClient, admin_token: str):
    response = await client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@techserv.local"
    assert data["role"] == UserRole.ADMINISTRADOR


@pytest.mark.asyncio
async def test_list_users_as_admin(client: AsyncClient, admin_token: str):
    response = await client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@techserv.local", "password": "admin123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@techserv.local", "password": "wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_users_forbidden_without_admin(client: AsyncClient, seeded_session):
    import uuid

    from app.core.security import create_test_token
    from app.models import User

    tecnico_id = uuid.uuid4()
    seeded_session.add(
        User(
            id=tecnico_id,
            email="tecnico@techserv.local",
            full_name="Tecnico",
            role=UserRole.TECNICO,
            company_id=seeded_session.info["company"].id,
        )
    )
    await seeded_session.commit()

    token = create_test_token(tecnico_id, "tecnico@techserv.local", UserRole.TECNICO)
    response = await client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
