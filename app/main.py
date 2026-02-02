from fastapi import FastAPI
from app.config import settings
from app.api import health, webhooks, mock

app = FastAPI(
    title=settings.app_name,
    description="WhatsApp-first conversational surveillance system",
    version="0.1.0",
    debug=settings.debug,
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(mock.router, prefix="/api/v1/mock", tags=["mock"])


@app.get("/")
async def root():
    return {"name": settings.app_name, "version": "0.1.0"}
