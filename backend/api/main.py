"""
Netran AI — FastAPI Web API Gateway Entry Point.
Initializes database, CORS, request telemetry, and mounts routers.
"""

import sys
import time
import asyncio
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


async def _ollama_keepalive_loop():
    """
    Background heartbeat: pings Ollama every 4 minutes to keep the LLM model
    loaded in VRAM. Prevents 24-second cold-reload latency spikes (TTFA ~33s)
    caused by Ollama's default 5-minute keep_alive eviction policy.
    This loop runs for the lifetime of the FastAPI process.
    """
    HEARTBEAT_INTERVAL_SEC = 240  # 4 minutes — safely under the 30m keep_alive window
    await asyncio.sleep(HEARTBEAT_INTERVAL_SEC)  # First ping after 4 min, not on startup
    while True:
        try:
            from model.voice_to_voice_model.model.brain import keepalive_ping
            ok = keepalive_ping()
            print(f"[Heartbeat] Ollama keepalive ping: {'OK' if ok else 'FAILED'}", flush=True)
        except Exception as e:
            print(f"[Heartbeat] Keepalive error: {e}", flush=True)
        await asyncio.sleep(HEARTBEAT_INTERVAL_SEC)


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

    # Preload Ollama LLM Model (Stage 3 Brain) so first turn does not cold-start
    try:
        from model.voice_to_voice_model.model.brain import preload as preload_brain
        preload_brain()
    except Exception as e:
        import logging
        logging.warning(f"Could not preload Ollama brain model: {e}")

    # Launch periodic Ollama keepalive heartbeat to prevent VRAM eviction
    heartbeat_task = asyncio.create_task(_ollama_keepalive_loop())

    yield

    # Shutdown: cancel heartbeat cleanly
    heartbeat_task.cancel()
    try:
        await heartbeat_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Autonomous Multimodal AI Technical Interviewer Platform Web API Gateway.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Middleware for Web Client Integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
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
