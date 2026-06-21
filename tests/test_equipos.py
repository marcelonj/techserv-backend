import uuid

import pytest
from httpx import AsyncClient

from app.models import Equipo


@pytest.mark.asyncio
async def test_list_equipos_as_admin(client: AsyncClient, admin_token: str, sample_equipo: Equipo):
    response = await client.get(
        "/api/v1/equipos",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_list_equipos_as_cliente_scoped(
    client: AsyncClient,
    cliente_token: str,
    sample_equipo: Equipo,
    seeded_users,
):
    otro = Equipo(
        id=uuid.uuid4(),
        tipo="Servidor",
        marca="HP",
        modelo="ProLiant",
        numero_serie="SN-100",
        cliente_id=seeded_users.info["supervisor"].id,
    )
    seeded_users.add(otro)
    await seeded_users.commit()

    response = await client.get(
        "/api/v1/equipos",
        headers={"Authorization": f"Bearer {cliente_token}"},
    )
    assert response.status_code == 200
    equipos = response.json()
    assert len(equipos) == 1
    assert equipos[0]["id"] == str(sample_equipo.id)


@pytest.mark.asyncio
async def test_create_equipo_as_cliente(client: AsyncClient, cliente_token: str, seeded_users):
    response = await client.post(
        "/api/v1/equipos",
        headers={"Authorization": f"Bearer {cliente_token}"},
        json={
            "tipo": "Desktop",
            "marca": "Lenovo",
            "modelo": "ThinkCentre",
            "numero_serie": "SN-NEW-001",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["marca"] == "Lenovo"
    assert data["cliente_id"] == str(seeded_users.info["cliente"].id)
