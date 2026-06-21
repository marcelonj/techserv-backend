from fastapi import APIRouter

from app.api.v1 import auth, health, users, tickets, equipos
from app.schemas.user import MeResponse

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.add_api_route("/me", users.read_me, methods=["GET"], tags=["users"], response_model=MeResponse)
api_router.include_router(tickets.router)
api_router.include_router(equipos.router)
