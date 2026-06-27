"""Radiografia AI — FastAPI application entry point.

A clinical decision-support API for chest X-ray triage. Inference is ALWAYS
advisory: no study is finalized without a registered human (radiologist) review.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.db import init_db
from app.api import auth, studies, audit, models

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "Decision-support API for chest X-ray analysis. AI output is advisory "
        "and requires mandatory human review before any result is finalized."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "service": settings.app_name, "ml_backend": settings.ml_backend}


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(studies.router, prefix="/studies", tags=["studies"])
app.include_router(audit.router, prefix="/audit", tags=["audit"])
app.include_router(models.router, prefix="/models", tags=["models"])
