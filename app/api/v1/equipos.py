import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.security import EstadoTicket, UrgenciaTicket, UserRole
from app.models import Equipo, User
from app.schemas.equipo import EquipoRead, EquipoCreate

router = APIRouter(prefix="/equipos", tags=["equipos"])

@router.get("", response_model=list[EquipoRead])
async def list_equipos(
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR, UserRole.AREA_ADMINISTRATIVA, UserRole.TECNICO, UserRole.CLIENTE, UserRole.SUPERVISOR))],
    db: Annotated[AsyncSession, Depends(get_db)],
)->list[Equipo]:
    query = select(Equipo).order_by(Equipo.fecha_creacion.desc())

    if current_user.role == UserRole.CLIENTE:
        query = query.where(Equipo.cliente_id == current_user.id)

    result = await db.execute(query)
    return list(result.scalars().all())

@router.post("", response_model=EquipoCreate, status_code=status.HTTP_201_CREATED)
async def create_equipo(
    payload: EquipoCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR, UserRole.SUPERVISOR, UserRole.CLIENTE))],
    db: Annotated[AsyncSession, Depends(get_db)],
)-> Equipo:
    equipo = Equipo(
        id=uuid.uuid4(),
        tipo=payload.tipo,
        marca=payload.marca,
        modelo=payload.modelo,
        numero_serie=payload.numero_serie,
        cliente_id=payload.cliente_id or current_user.id
    )
    db.add(equipo)
    await db.flush()
    await db.refresh(equipo)
    return equipo