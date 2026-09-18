from fastapi import APIRouter
from fastapi.responses import JSONResponse

from veya.core.config import settings
from veya.infrastructure.health.service import HealthService


router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
@router.get("/live")
async def live() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.service_version,
    }


@router.get("/ready")
def ready():
    result = HealthService().check()
    payload = {
        "status": result.status,
        "service": settings.app_name,
        "version": settings.service_version,
        "dependencies": {
            "database": result.database,
            "redis": result.redis,
        },
    }

    if result.status != "ok":
        return JSONResponse(status_code=503, content=payload)

    return payload
