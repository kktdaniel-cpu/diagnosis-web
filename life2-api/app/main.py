from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .awareness.router import router as awareness_router
from .config import get_settings

settings = get_settings()
app = FastAPI(title="LIFE 2.0 API", version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-Id"],
)

app.include_router(awareness_router)


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "service": "life2-api",
        "version": settings.app_version,
        "env": settings.app_env,
    }


@app.get("/v1/meta/guardrails")
def guardrails() -> dict:
    return {
        "unknown_is_zero": False,
        "generic_fact_write": False,
        "ai_is_authoritative_fact_source": False,
        "precision_engine": "diagnosis-api",
    }
