import uuid

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import UserRole, create_access_token, create_refresh_token, hash_password, verify_password, decode_jwt
from app.models import User
from app.core.deps import get_current_user
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, RefreshRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    if payload.role == UserRole.ADMINISTRADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot self-register as administrador",
        )

    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        id=uuid.uuid4(),
        email=payload.email,
        full_name=payload.full_name,
        role=payload.role,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    await db.flush()

    token = create_access_token(user.id, user.email, UserRole(user.role))
    refresh_token = create_refresh_token(user.id, user.email, UserRole(user.role), 10080)
    return TokenResponse(access_token=token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user is None or not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

    token = create_access_token(user.id, user.email, UserRole(user.role))
    refresh_token = create_refresh_token(user.id, user.email, UserRole(user.role), user.token_version, 10080)
    return TokenResponse(access_token=token, refresh_token=refresh_token)

@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TokenResponse:
    try:
        refresh_jwt = decode_jwt(payload.refresh_token)
    except:
        raise HTTPException(status_code=401, detail="Wrong refresh token")
    query = select(User).where(User.id == refresh_jwt.sub)
    result = await db.execute(query)
    user = result.scalars().first()
    if refresh_jwt.version < user.token_version:
        setattr(user, "token_version", user.token_version + 1)
        await db.commit()
        raise HTTPException(status_code=401, detail="Version token expired")
    token = create_access_token(refresh_jwt.sub, refresh_jwt.email, refresh_jwt.role)
    refresh_token = create_refresh_token(refresh_jwt.sub, refresh_jwt.email, refresh_jwt.role, user.token_version + 1, 10080)
    setattr(user, "token_version", user.token_version + 1)
    await db.commit()
    return TokenResponse(access_token=token, refresh_token=refresh_token)