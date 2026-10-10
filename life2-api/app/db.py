import asyncpg
from fastapi import HTTPException

from .config import get_settings

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is not None:
        return _pool

    settings = get_settings()
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="DATABASE_NOT_CONFIGURED")

    _pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=5)
    return _pool
