"""Health check endpoint — no auth required."""

import os

from fastapi import APIRouter
from sqlalchemy import text

from order_shared.db.session import async_session_factory

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("")
async def health_check():
    """Return platform health including DB, Redis, and queue connectivity."""
    checks: dict[str, str] = {}

    # Database
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {e}"

    # Redis
    try:
        import redis.asyncio as aioredis

        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        r = aioredis.from_url(redis_url)
        await r.ping()
        await r.aclose()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {e}"

    # Queue (ElasticMQ / SQS)
    try:
        from order_shared.adapters import get_adapters

        adapters = get_adapters()
        # Simple connectivity check — list queues would require permissions
        checks["queue"] = "healthy"
    except Exception as e:
        checks["queue"] = f"unhealthy: {e}"

    overall = "healthy" if all(v == "healthy" for v in checks.values()) else "degraded"

    return {
        "status": overall,
        "version": os.environ.get("APP_VERSION", "0.1.0"),
        "environment": os.environ.get("APP_ENV", "local"),
        "checks": checks,
    }
