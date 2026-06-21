import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum

import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings


class UserRole(StrEnum):
    CLIENTE = "cliente"
    TECNICO = "tecnico"
    SUPERVISOR = "supervisor"
    ADMINISTRADOR = "administrador"
    AREA_ADMINISTRATIVA = "area_administrativa"


class EstadoTicket(StrEnum):
    ABIERTO = "abierto"
    EN_DIAGNOSTICO = "en_diagnostico"
    EN_PROCESO = "en_proceso"
    RESUELTO = "resuelto"


class UrgenciaTicket(StrEnum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class TokenPayload(BaseModel):
    sub: str
    email: str | None = None
    role: str | None = None
    exp: int | None = None
    token_type: str | None = None
    version: int | None = None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(
    user_id: uuid.UUID,
    email: str,
    role: UserRole,
    expires_minutes: int | None = None,
) -> str:
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=expires_minutes or settings.jwt_expire_minutes)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role.value if isinstance(role, UserRole) else role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "token_type": "access",
    }
    print(f"JWT enviado: {jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)}")
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def create_refresh_token(
    user_id: uuid.UUID,
    email: str,
    role: UserRole,
    version: int,
    expires_minutes: int | None = None,
) -> str:
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=expires_minutes or settings.jwt_expire_minutes)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role.value if isinstance(role, UserRole) else role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "token_type": "refresh",
        "version": version,
    }
    print(f"JWT enviado: {jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)}")
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def decode_jwt(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc

    sub = payload.get("sub")
    if not sub:
        raise ValueError("Token missing subject")

    return TokenPayload(
        sub=sub,
        email=payload.get("email"),
        role=payload.get("role"),
        exp=payload.get("exp"),
        token_type=payload.get("token_type"),
        version=payload.get("version"),
    )


def create_test_token(
    user_id: uuid.UUID,
    email: str = "test@techserv.local",
    role: UserRole = UserRole.ADMINISTRADOR,
) -> str:
    return create_access_token(user_id, email, role, expires_minutes=60)
