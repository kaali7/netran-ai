"""
Netran AI — FastAPI Web API Gateway Entry Point.
Initializes database, CORS, request telemetry, and mounts routers.
"""

import sys
import time
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Ensure root backend directory is on sys.path for relative module imports
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from api.config import settings
from api.db import init_db
from api.schemas import HealthResponse
from api.routers import auth, ingest, setup, questions, voice, reports, template, analytics, history, notifications


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle events handler (startup & shutdown)."""
    # Startup: Create database tables
    init_db()
    
    # Preload Kokoro TTS Model so the first interview doesn't lag 10s
    try:
        from model.voice_to_voice_model.model.speaker import preload_models as preload_speaker
        preload_speaker()
    except Exception as e:
        import logging
        logging.warning(f"Could not preload Kokoro TTS model: {e}")
        
    yield
    # Shutdown logic (if any)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Autonomous Multimodal AI Technical Interviewer Platform Web API Gateway.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Middleware for Next.js Web Client Integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Telemetry middleware tracking request processing latency in milliseconds."""
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = (time.perf_counter() - start_time) * 1000
    response.headers["X-Process-Time-MS"] = f"{process_time:.2f}"
    return response


@app.get("/health", response_model=HealthResponse, tags=["Health Check"])
def health_check():
    """Service health ping endpoint."""
    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        project=settings.PROJECT_NAME
    )


# Mount API V1 Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(ingest.router, prefix=settings.API_V1_STR)
app.include_router(setup.router, prefix=settings.API_V1_STR)
app.include_router(questions.router, prefix=settings.API_V1_STR)
app.include_router(voice.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(template.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(history.router, prefix=settings.API_V1_STR)
app.include_router(notifications.router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
