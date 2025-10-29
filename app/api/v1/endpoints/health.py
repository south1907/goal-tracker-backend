"""
Health check endpoints.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas import HealthCheck

router = APIRouter()


@router.get("/", response_model=HealthCheck)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint."""
    try:
        # Test database connection
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    overall_status = "healthy" if db_status == "healthy" else "unhealthy"
    
    return HealthCheck(
        status=overall_status,
        version=settings.APP_VERSION,
        database=db_status,
        timestamp=datetime.utcnow(),
    )
