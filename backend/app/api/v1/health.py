"""Health check endpoint"""

from fastapi import APIRouter
from typing import Dict, Any
import logging

from app.core.config import settings
from app.core.notion import notion

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint

    Returns:
        Dict with status, version, and service availability
    """
    health_status = {
        "status": "ok",
        "version": settings.app_version,
        "app_name": settings.app_name,
        "services": {
            "notion": notion.is_enabled()
        }
    }

    logger.debug(f"Health check: {health_status}")
    return health_status
