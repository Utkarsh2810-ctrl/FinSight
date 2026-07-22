"""
api/main.py
-----------
FastAPI application entrypoint.

Startup (lifespan):
    - Loads config
    - Initialises HybridRetriever (loads embedding model + cross-encoder + ChromaDB)
    - Initialises QAPipeline (connects to Groq)
    - Creates in-memory document store

CORS is configured to allow the React dev server (localhost:5173).
Update ALLOWED_ORIGINS for production deployment.
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))

from config_loader import get_config
from src.qa.pipeline import QAPipeline
from src.retrieval.hybrid_retriever import HybridRetriever

from api.routes import eval as eval_router
from api.routes import forecast as forecast_router
from api.routes import qa as qa_router
from api.routes import upload as upload_router

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> — {message}",
    level="INFO",
)

Path("logs").mkdir(exist_ok=True)
logger.add("logs/finsight.log", rotation="10 MB", retention="7 days", level="DEBUG")

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FinSight API starting up...")
    config = get_config()

    app.state.config = config
    app.state.retriever = HybridRetriever(config)
    app.state.qa_pipeline = QAPipeline(config)
    # document_id -> {filename, company, year, quarter, chunk_count, indexed_at}
    app.state.document_store: Dict[str, Any] = {}

    logger.info("FinSight API ready ✓")
    yield
    logger.info("FinSight API shutting down")


# ---------------------------------------------------------------------------
# App + middleware
# ---------------------------------------------------------------------------

app = FastAPI(
    title="FinSight API",
    description="Financial Document Intelligence — Hybrid RAG + LSTM Forecasting",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(upload_router.router,   prefix="/api", tags=["ingestion"])
app.include_router(qa_router.router,       prefix="/api", tags=["qa"])
app.include_router(forecast_router.router, prefix="/api", tags=["forecasting"])
app.include_router(eval_router.router,     prefix="/api", tags=["evaluation"])

# ---------------------------------------------------------------------------
# Core routes
# ---------------------------------------------------------------------------

@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "service": "finsight-api", "version": "1.0.0"}


@app.get("/api/documents", tags=["meta"])
async def list_documents(request: Request):
    """Returns all indexed documents — used by the frontend document selector."""
    return {"documents": list(request.app.state.document_store.values())}
