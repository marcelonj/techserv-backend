import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles, get_current_user_optional
from app.core.security import UserRole, hash_password
from app.models import User
from app.schemas.user import MeResponse, UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=MeResponse)
async def read_me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user


@router.get("", response_model=list[UserRead])
async def list_users(
    _: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[User]:
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return list(result.scalars().all())

@router.get("/tecnicos", response_model=list[UserRead])
async def list_tecnicos(
    _: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR, UserRole.AREA_ADMINISTRATIVA, UserRole.SUPERVISOR))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[User]:
    result = await db.execute(select(User).where(User.role == UserRole.TECNICO).order_by(User.full_name.asc()))
    return list(result.scalars().all())

@router.get("/clientes", response_model=list[UserRead])
async def list_clientes(
    _: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR, UserRole.AREA_ADMINISTRATIVA, UserRole.SUPERVISOR))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[User]:
    result = await db.execute(select(User).where(User.role == UserRole.CLIENTE).order_by(User.full_name.asc()))
    return list(result.scalars().all())


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    # Pasamos la función SIN paréntesis. current_user puede ser User o None.
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    
    roles_restringidos = (UserRole.ADMINISTRADOR, UserRole.AREA_ADMINISTRATIVA, UserRole.SUPERVISOR)
    
    is_admin = current_user and current_user.role == UserRole.ADMINISTRADOR
    
    if not is_admin and payload.role in roles_restringidos:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to assign high-privileged roles.",
        )

    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        id=payload.id or uuid.uuid4(),
        email=payload.email,
        full_name=payload.full_name,
        role=payload.role,
        company_id=payload.company_id,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    _: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    data = payload.model_dump(exclude_unset=True)
    if "password" in data:
        user.password_hash = hash_password(data.pop("password"))
    for field, value in data.items():
        setattr(user, field, value)
    await db.flush()
    await db.refresh(user)
    return user
