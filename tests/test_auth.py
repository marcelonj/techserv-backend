import uuid

import pytest
from httpx import AsyncClient

from app.core.security import UserRole, hash_password
from app.models import User


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "nuevo@techserv.local",
            "password": "secret123",
            "full_name": "Nuevo Cliente",
            "role": UserRole.CLIENTE,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_admin_forbidden(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "hack@techserv.local",
            "password": "secret123",
            "full_name": "Fake Admin",
            "role": UserRole.ADMINISTRADOR,
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {
        "email": "dup@techserv.local",
        "password": "secret123",
        "full_name": "Usuario Uno",
        "role": UserRole.CLIENTE,
    }
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 400
    assert second.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient, seeded_session):
    inactive_id = uuid.uuid4()
    seeded_session.add(
        User(
            id=inactive_id,
            email="inactive@techserv.local",
            full_name="Inactive User",
            role=UserRole.CLIENTE,
            company_id=seeded_session.info["company"].id,
            password_hash=hash_password("secret123"),
            is_active=False,
        )
    )
    await seeded_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@techserv.local", "password": "secret123"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "User account is inactive"
