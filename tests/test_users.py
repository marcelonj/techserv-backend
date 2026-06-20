import uuid

import pytest
from httpx import AsyncClient

from app.core.security import UserRole


@pytest.mark.asyncio
async def test_users_me_alias(client: AsyncClient, admin_token: str):
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "admin@techserv.local"


@pytest.mark.asyncio
async def test_list_tecnicos_as_supervisor(client: AsyncClient, supervisor_token: str):
    response = await client.get(
        "/api/v1/users/tecnicos",
        headers={"Authorization": f"Bearer {supervisor_token}"},
    )
    assert response.status_code == 200
    emails = [u["email"] for u in response.json()]
    assert "tecnico@techserv.local" in emails


@pytest.mark.asyncio
async def test_list_clientes_as_supervisor(client: AsyncClient, supervisor_token: str):
    response = await client.get(
        "/api/v1/users/clientes",
        headers={"Authorization": f"Bearer {supervisor_token}"},
    )
    assert response.status_code == 200
    emails = [u["email"] for u in response.json()]
    assert "cliente@techserv.local" in emails


@pytest.mark.asyncio
async def test_list_tecnicos_forbidden_as_cliente(client: AsyncClient, cliente_token: str):
    response = await client.get(
        "/api/v1/users/tecnicos",
        headers={"Authorization": f"Bearer {cliente_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_user_as_admin(client: AsyncClient, admin_token: str, seeded_session):
    response = await client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "creado@techserv.local",
            "password": "secret123",
            "full_name": "Usuario Creado",
            "role": UserRole.TECNICO,
            "company_id": str(seeded_session.info["company"].id),
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "creado@techserv.local"
    assert data["role"] == UserRole.TECNICO


@pytest.mark.asyncio
async def test_create_user_as_area_administrativa(client: AsyncClient, area_admin_token: str, seeded_session):
    response = await client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {area_admin_token}"},
        json={
            "email": "area-created@techserv.local",
            "password": "secret123",
            "full_name": "Creado por Area",
            "role": UserRole.CLIENTE,
            "company_id": str(seeded_session.info["company"].id),
        },
    )
    assert response.status_code == 201
    assert response.json()["role"] == UserRole.CLIENTE


@pytest.mark.asyncio
async def test_create_admin_forbidden(client: AsyncClient, admin_token: str):
    response = await client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "newadmin@techserv.local",
            "password": "secret123",
            "full_name": "New Admin",
            "role": UserRole.ADMINISTRADOR,
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_user_as_admin(client: AsyncClient, admin_token: str, seeded_users):
    cliente_id = seeded_users.info["cliente"].id
    response = await client.patch(
        f"/api/v1/users/{cliente_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"full_name": "Cliente Actualizado", "phone": "5559999999"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Cliente Actualizado"
    assert data["phone"] == "5559999999"


@pytest.mark.asyncio
async def test_update_user_not_found(client: AsyncClient, admin_token: str):
    response = await client.patch(
        f"/api/v1/users/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"full_name": "Nadie"},
    )
    assert response.status_code == 404
