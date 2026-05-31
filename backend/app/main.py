"""
LungSight AI — FastAPI Application Entry Point
Production-grade chest X-ray diagnostic AI backend.
"""
from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.config import settings
from app.database import create_tables
from app.api.routes.predict   import router as predict_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.auth      import router as auth_router
from app.api.routes.reports   import router as reports_router


# ──────────────────────────────────────────────────────────────────────────────
# Startup / shutdown
# ──────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 LungSight AI starting up …")

    # Create DB tables
    try:
        await create_tables()
        logger.info("✅ Database tables ready")
    except Exception as exc:
        logger.warning(f"⚠️  Database init skipped: {exc}")

    # Ensure upload / report directories exist
    for d in [settings.UPLOAD_DIR, settings.REPORTS_DIR, settings.MODELS_DIR]:
        Path(d).mkdir(parents=True, exist_ok=True)

    logger.info("✅ LungSight AI ready — Swagger: /docs")
    yield

    logger.info("🛑 LungSight AI shutting down …")


# ──────────────────────────────────────────────────────────────────────────────
# App
# ──────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="LungSight AI",
    description="""
## Explainable Pneumonia Detection, Localization & Severity Assessment

**LungSight AI** is a production-grade computer vision research platform for chest X-ray analysis.

### Features
- 🔬 Multi-model classification: DenseNet121, EfficientNetB3, ResNet50, VGG16, Ensemble
- 🫁 U-Net lung segmentation with Dice/IoU metrics
- 🔥 Explainable AI: Grad-CAM, Grad-CAM++, Saliency, Integrated Gradients
- 📊 Severity assessment (Normal → Critical) with clinical recommendations
- 🎯 Monte Carlo Dropout uncertainty quantification
- 📋 Professional PDF diagnostic report generation
- 🏥 DICOM support with metadata extraction
- 📈 Model benchmarking & leaderboard
    """,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ──────────────────────────────────────────────────────────────────────────────
# Middleware
# ──────────────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1024)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    t0 = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{(time.perf_counter() - t0)*1000:.1f}ms"
    return response


# ──────────────────────────────────────────────────────────────────────────────
# Routers
# ──────────────────────────────────────────────────────────────────────────────

API_PREFIX = "/api/v1"

app.include_router(auth_router,      prefix=API_PREFIX)
app.include_router(predict_router,   prefix=API_PREFIX)
app.include_router(analytics_router, prefix=API_PREFIX)
app.include_router(reports_router,   prefix=API_PREFIX)


# ──────────────────────────────────────────────────────────────────────────────
# Root
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Root"], summary="Service info")
async def root():
    return {
        "service": "LungSight AI",
        "version": settings.APP_VERSION,
        "description": "Explainable Pneumonia Detection via Chest X-Ray",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again."},
    )
