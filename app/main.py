from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import settings
from app.api import health, webhooks, mock, perception
from app.services.storage import db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to database
    await db.connect()
    yield
    # Disconnect from database
    if db.is_connected():
        await db.disconnect()

app = FastAPI(
    title=settings.app_name,
    description="WhatsApp-first conversational surveillance system",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(perception.router, prefix="/api/v1", tags=["perception"])
app.include_router(mock.router, prefix="/api/v1/mock", tags=["mock"])


@app.get("/")
async def root():
    return {"name": settings.app_name, "version": "0.1.0"}
