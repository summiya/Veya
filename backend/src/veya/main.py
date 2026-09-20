from contextlib import asynccontextmanager

from fastapi import FastAPI

from veya.api.middleware.rate_limit import RateLimitMiddleware
from veya.api.middleware.request_context import RequestContextMiddleware
from veya.api.routes.analytics import router as analytics_router
from veya.api.routes.authentication import router as authentication_router
from veya.api.routes.background_sync import router as background_sync_router
from veya.api.routes.health import router as health_router
from veya.api.routes.insights import router as insights_router
from veya.api.routes.instagram import router as instagram_router
from veya.api.routes.safety import router as safety_router
from veya.api.routes.sentiment import router as sentiment_router
from veya.core.config import settings
from veya.core.logging import configure_logging
from veya.core.monitoring import initialize_error_monitoring
from veya.core.runtime import validate_runtime_configuration


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(level=settings.log_level)
    initialize_error_monitoring()
    validate_runtime_configuration()
    yield


app = FastAPI(
    title="Veya API",
    version=settings.service_version,
    description="Creator-focused social sentiment and wellbeing platform.",
    lifespan=lifespan,
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestContextMiddleware)

app.include_router(health_router)
app.include_router(authentication_router)
app.include_router(instagram_router)
app.include_router(sentiment_router)
app.include_router(safety_router)
app.include_router(insights_router)
app.include_router(analytics_router)
app.include_router(background_sync_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "status": "running",
        "version": settings.service_version,
    }
