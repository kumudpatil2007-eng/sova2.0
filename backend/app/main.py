import os
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import upload, chat, system, documents, auth
from .services.file_service import ensure_upload_dir
from .services.auth_service import init_auth_db
from .services.model_registry import init_model_registry_db, sync_model_registry
from .llm.local_client import ollama_client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sovereign_ai")

app = FastAPI(
    title="SOVA Backend",
    description="SOVA: Sovereign, air-gapped on-premise industrial engineering document intelligence API",
    version="2.0.0"
)

# Enable CORS for local Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(system.router)
app.include_router(documents.router)


@app.on_event("startup")
async def startup_event():
    ensure_upload_dir()
    init_auth_db()
    init_model_registry_db()

    # Query Ollama and synchronize local database model registry
    health = await ollama_client.check_health()
    installed = health.get("installed_models", [])
    if health["online"]:
        sync_model_registry(installed)

    logger.info("=" * 65)
    logger.info(" SOVA Air-Gapped Engineering Workbench Started")
    logger.info(f" Local Ollama Base URL:    {settings.ollama_base_url}")
    logger.info(f" Vision Model (P&ID):      {settings.ollama_vision_model}")
    logger.info(f" Reasoning Model (Deep):   {settings.ollama_reasoning_model}")
    logger.info(f" Coder Model (Sandbox):    {settings.ollama_coder_model}")
    logger.info(f" Document Model (SOP):     {settings.ollama_document_model}")
    logger.info(f" Ollama Online Status:     {'CONNECTED' if health['online'] else 'OFFLINE'}")
    logger.info(f" Installed Models:         {', '.join(installed) if installed else 'None'}")
    logger.info(f" Air-Gapped Mode:          Strict Active (0 External Calls)")
    logger.info("=" * 65)


@app.get("/")
async def root():
    return {
        "service": "SOVA",
        "status": "operational",
        "models": settings.model_mapping,
        "default_model": settings.ollama_model,
        "architecture": "Local Ollama Multi-Model Routing + PyMuPDF + Telemetry Engine + Grounding Verification",
        "air_gapped": True
    }
