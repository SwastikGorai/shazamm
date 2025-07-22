from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

from database import engine
from api.routes import router as api_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up async Shazam clone...")
    yield
    logger.info("Shutting down...")
    await engine.dispose()


app = FastAPI(
    title="async Shazam Clone API",
    description="audio recognition service",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(api_router, prefix="/api", tags=["audio"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "async": True}