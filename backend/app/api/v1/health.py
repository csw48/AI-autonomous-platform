"""Health check endpoint"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any
import logging

from app.core.config import settings
from app.core.notion import notion
from app.core.llm import llm_manager
from app.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any])
async def health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Health check endpoint

    Returns:
        Dict with status, version, and service availability
    """
    # Check database connection
    db_connected = False
    try:
        await db.execute(text("SELECT 1"))
        db_connected = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")

    health_status = {
        "status": "ok" if db_connected else "degraded",
        "version": settings.app_version,
        "app_name": settings.app_name,
        "services": {
            "database": db_connected,
            "llm": llm_manager.is_available(),
            "notion": notion.is_enabled()
        }
    }

    logger.debug(f"Health check: {health_status}")
    return health_status
