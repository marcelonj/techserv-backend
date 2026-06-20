import uuid

import pytest
from httpx import AsyncClient

from app.core.security import EstadoTicket, UrgenciaTicket
from app.models import Equipo, Ticket


@pytest.mark.asyncio
async def test_list_tickets_as_admin_sees_all(
    client: AsyncClient,
    admin_token: str,
    sample_ticket: Ticket,
    seeded_users,
    sample_equipo: Equipo,
):
    otro_equipo = Equipo(
        id=uuid.uuid4(),
        tipo="Impresora",
        marca="HP",
        modelo="LaserJet",
        numero_serie="SN-002",
        cliente_id=seeded_users.info["supervisor"].id,
    )
    seeded_users.add(otro_equipo)
    otro_ticket = Ticket(
        id=uuid.uuid4(),
        titulo="Otro ticket",
        descripcion="Otra descripcion",
        estado=EstadoTicket.ABIERTO,
        urgencia=UrgenciaTicket.BAJA,
        direccion="Calle Secundaria 456",
        cliente_id=seeded_users.info["supervisor"].id,
        equipo_id=otro_equipo.id,
    )
    seeded_users.add(otro_ticket)
    await seeded_users.commit()

    response = await client.get(
        "/api/v1/tickets",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) >= 2


@pytest.mark.asyncio
async def test_list_tickets_as_cliente_scoped(
    client: AsyncClient,
    cliente_token: str,
    sample_ticket: Ticket,
    seeded_users,
):
    otro_equipo = Equipo(
        id=uuid.uuid4(),
        tipo="Monitor",
        marca="LG",
        modelo="27UL",
        numero_serie="SN-003",
        cliente_id=seeded_users.info["supervisor"].id,
    )
    seeded_users.add(otro_equipo)
    otro_ticket = Ticket(
        id=uuid.uuid4(),
        titulo="Ticket ajeno",
        descripcion="No deberia verse",
        estado=EstadoTicket.ABIERTO,
        urgencia=UrgenciaTicket.ALTA,
        direccion="Otra direccion",
        cliente_id=seeded_users.info["supervisor"].id,
        equipo_id=otro_equipo.id,
    )
    seeded_users.add(otro_ticket)
    await seeded_users.commit()

    response = await client.get(
        "/api/v1/tickets",
        headers={"Authorization": f"Bearer {cliente_token}"},
    )
    assert response.status_code == 200
    tickets = response.json()
    assert len(tickets) == 1
    assert tickets[0]["id"] == str(sample_ticket.id)


@pytest.mark.asyncio
async def test_list_tickets_as_tecnico_scoped(
    client: AsyncClient,
    tecnico_token: str,
    sample_ticket: Ticket,
    seeded_users,
):
    otro_equipo = Equipo(
        id=uuid.uuid4(),
        tipo="Tablet",
        marca="Samsung",
        modelo="Tab S9",
        numero_serie="SN-004",
        cliente_id=seeded_users.info["cliente"].id,
    )
    seeded_users.add(otro_equipo)
    otro_ticket = Ticket(
        id=uuid.uuid4(),
        titulo="Sin tecnico asignado",
        descripcion="No asignado a mi",
        estado=EstadoTicket.ABIERTO,
        urgencia=UrgenciaTicket.MEDIA,
        direccion="Dir 789",
        cliente_id=seeded_users.info["cliente"].id,
        equipo_id=otro_equipo.id,
    )
    seeded_users.add(otro_ticket)
    await seeded_users.commit()

    response = await client.get(
        "/api/v1/tickets",
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert response.status_code == 200
    tickets = response.json()
    assert len(tickets) == 1
    assert tickets[0]["id"] == str(sample_ticket.id)


@pytest.mark.asyncio
async def test_get_ticket_as_cliente_own(client: AsyncClient, cliente_token: str, sample_ticket: Ticket):
    response = await client.get(
        f"/api/v1/tickets/{sample_ticket.id}",
        headers={"Authorization": f"Bearer {cliente_token}"},
    )
    assert response.status_code == 200
    assert response.json()["titulo"] == sample_ticket.titulo


@pytest.mark.asyncio
async def test_get_ticket_as_cliente_forbidden(
    client: AsyncClient,
    cliente_token: str,
    seeded_users,
):
    otro_equipo = Equipo(
        id=uuid.uuid4(),
        tipo="Router",
        marca="Cisco",
        modelo="RV340",
        numero_serie="SN-005",
        cliente_id=seeded_users.info["supervisor"].id,
    )
    seeded_users.add(otro_equipo)
    ajeno = Ticket(
        id=uuid.uuid4(),
        titulo="Ticket ajeno",
        descripcion="De otro cliente",
        estado=EstadoTicket.ABIERTO,
        urgencia=UrgenciaTicket.BAJA,
        direccion="Dir remota",
        cliente_id=seeded_users.info["supervisor"].id,
        equipo_id=otro_equipo.id,
    )
    seeded_users.add(ajeno)
    await seeded_users.commit()

    response = await client.get(
        f"/api/v1/tickets/{ajeno.id}",
        headers={"Authorization": f"Bearer {cliente_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_ticket_as_cliente(client: AsyncClient, cliente_token: str, sample_equipo: Equipo, seeded_users):
    response = await client.post(
        "/api/v1/tickets",
        headers={"Authorization": f"Bearer {cliente_token}"},
        json={
            "titulo": "Nuevo ticket",
            "descripcion": "Problema con equipo",
            "urgencia": UrgenciaTicket.ALTA,
            "direccion": "Calle Nueva 10",
            "equipo_id": str(sample_equipo.id),
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["titulo"] == "Nuevo ticket"
    assert data["estado"] == EstadoTicket.ABIERTO
    assert data["cliente"]["id"] == str(seeded_users.info["cliente"].id)


@pytest.mark.asyncio
async def test_create_ticket_as_supervisor(
    client: AsyncClient,
    supervisor_token: str,
    sample_equipo: Equipo,
    seeded_users,
):
    response = await client.post(
        "/api/v1/tickets",
        headers={"Authorization": f"Bearer {supervisor_token}"},
        json={
            "titulo": "Ticket supervisor",
            "descripcion": "Creado por supervisor",
            "urgencia": UrgenciaTicket.MEDIA,
            "direccion": "Oficina central",
            "equipo_id": str(sample_equipo.id),
            "cliente_id": str(seeded_users.info["cliente"].id),
        },
    )
    assert response.status_code == 201
    assert response.json()["cliente"]["id"] == str(seeded_users.info["cliente"].id)


@pytest.mark.asyncio
async def test_update_ticket_as_tecnico(client: AsyncClient, tecnico_token: str, sample_ticket: Ticket):
    response = await client.patch(
        f"/api/v1/tickets/{sample_ticket.id}",
        headers={"Authorization": f"Bearer {tecnico_token}"},
        json={"estado": EstadoTicket.EN_DIAGNOSTICO},
    )
    assert response.status_code == 200
    assert response.json()["estado"] == EstadoTicket.EN_DIAGNOSTICO


@pytest.mark.asyncio
async def test_update_ticket_empty_body(client: AsyncClient, admin_token: str, sample_ticket: Ticket):
    response = await client.patch(
        f"/api/v1/tickets/{sample_ticket.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_ticket_not_found(client: AsyncClient, admin_token: str):
    response = await client.get(
        f"/api/v1/tickets/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404
