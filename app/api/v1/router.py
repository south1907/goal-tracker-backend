"""
Main API router that includes all sub-routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, goals, logs, stats, health

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(goals.router, prefix="/goals", tags=["Goals"])
api_router.include_router(logs.router, prefix="/logs", tags=["Logs"])
api_router.include_router(stats.router, prefix="/stats", tags=["Statistics"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])
