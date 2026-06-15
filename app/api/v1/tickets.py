import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.security import EstadoTicket, UrgenciaTicket, UserRole
from app.models import Ticket, User
from app.schemas.ticket import TicketRead, TicketCreate, TicketUpdate

router = APIRouter(prefix="/tickets", tags=["tickets"])

@router.get("", response_model=list[TicketRead])
async def list_tickets(
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR, UserRole.AREA_ADMINISTRATIVA, UserRole.TECNICO, UserRole.CLIENTE, UserRole.SUPERVISOR))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[Ticket]:
    query = select(Ticket).options(
        joinedload(Ticket.cliente), 
        joinedload(Ticket.tecnico), 
        joinedload(Ticket.equipo)).order_by(Ticket.fecha_creacion.desc())

    if current_user.role == UserRole.CLIENTE:
        query = query.where(Ticket.cliente_id == current_user.id)

    if current_user.role == UserRole.TECNICO:
        query = query.where(Ticket.tecnico_id == current_user.id)
    
    result = await db.execute(query)
    return list(result.scalars().all())

@router.get("/{id}", response_model=TicketRead, status_code=status.HTTP_200_OK)
async def one_ticket(
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR, UserRole.AREA_ADMINISTRATIVA, UserRole.TECNICO, UserRole.CLIENTE, UserRole.SUPERVISOR))],
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[Ticket]:
    query = select(Ticket).options(
        joinedload(Ticket.cliente), 
        joinedload(Ticket.tecnico), 
        joinedload(Ticket.equipo)).where(Ticket.id == id)
    result = await db.execute(query)
    ticket = result.scalars().first()

    if not ticket: raise HTTPException(404, "Ticket not found")

    if current_user.role == UserRole.CLIENTE:
        if current_user.id != ticket.cliente_id : raise HTTPException(403, "Insufficient privileges")

    if current_user.role == UserRole.TECNICO:
        if current_user.id != ticket.tecnico_id : raise HTTPException(403, "Insufficient privileges")
    
    return ticket

@router.post("", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: TicketCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR, UserRole.SUPERVISOR, UserRole.CLIENTE))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Ticket:
    ticket = Ticket(
        id=payload.id or uuid.uuid4(),
        titulo=payload.titulo,
        descripcion=payload.descripcion,
        estado=payload.estado or EstadoTicket.ABIERTO,
        urgencia=payload.urgencia,
        direccion=payload.direccion,
        cliente_id=payload.cliente_id or current_user.id,
        tecnico_id=payload.tecnico_id,
        equipo_id=payload.equipo_id
    )
    db.add(ticket)
    await db.flush()
    query_vuelto_a_cargar = (
        select(Ticket)
        .options(
            joinedload(Ticket.cliente),
            joinedload(Ticket.equipo)
        )
        .where(Ticket.id == ticket.id)
    )
    result = await db.execute(query_vuelto_a_cargar)
    ticket = result.scalars().first()
    return ticket

@router.patch("/{id}", response_model=TicketRead, status_code=status.HTTP_200_OK)
async def update_ticket(
    id: uuid.UUID,
    payload: TicketUpdate,
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR, UserRole.SUPERVISOR, UserRole.TECNICO))],
    db: Annotated[AsyncSession, Depends(get_db)],
)-> Ticket:
    query = select(Ticket).where(Ticket.id == id)
    result = await db.execute(query)
    ticket = result.scalars().first()

    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    
    update_dict = payload.model_dump(exclude_unset=True)

    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se proporcionaron campos para actualizar"
        )
    
    for key, value in update_dict.items():
        setattr(ticket, key, value)

    await db.commit()

    query_vuelto_a_cargar = (
        select(Ticket)
        .options(
            joinedload(Ticket.cliente),
            joinedload(Ticket.tecnico),
            joinedload(Ticket.equipo)
        )
        .where(Ticket.id == id)
    )
    result = await db.execute(query_vuelto_a_cargar)
    ticket = result.scalars().first()
    return ticket