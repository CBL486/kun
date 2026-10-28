from fastapi import FastAPI, HTTPException

from app.db import database_ready

APP_NAME = "AI World"
APP_VERSION = "0.1.0"

app = FastAPI(title=APP_NAME, version=APP_VERSION)


@app.get("/health")
async def health() -> dict[str, str]:
    """Report basic service liveness without exposing deployment details."""
    return {
        "status": "ok",
        "service": "ai-world",
        "version": APP_VERSION,
    }


@app.get("/ready")
async def ready() -> dict[str, str]:
    """Report whether the API can reach the authoritative database."""
    if not await database_ready():
        raise HTTPException(status_code=503, detail="database unavailable")
    return {
        "status": "ready",
        "service": "ai-world",
    }
