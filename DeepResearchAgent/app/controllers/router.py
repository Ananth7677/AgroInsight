from __future__ import annotations

from fastapi import APIRouter

from app.controllers.health_controller import router as health_router
from app.controllers.research_controller import router as research_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(research_router)
