from fastapi import FastAPI

from veya.api.routes.authentication import router as authentication_router
from veya.api.routes.health import router as health_router
from veya.api.routes.instagram import router as instagram_router

app = FastAPI(
    title="Veya API",
    version="0.1.0",
    description="Creator-focused social sentiment and wellbeing platform.",
)

app.include_router(health_router)
app.include_router(authentication_router)
app.include_router(instagram_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": "Veya", "status": "running"}
