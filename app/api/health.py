from fastapi import APIRouter
from app.config import settings

router = APIRouter()


@router.get("/")
async def health_check():
    return {"status": "healthy", "environment": settings.app_env}


@router.get("/db")
async def db_check():
    return {"status": "healthy", "database": settings.database_url}


@router.get("/redis")
async def redis_check():
    return {"status": "healthy", "redis": settings.redis_url}
