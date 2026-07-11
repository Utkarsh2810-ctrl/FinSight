"""
api/routes/upload.py
--------------------
POST /api/upload — ingest a PDF and index it for retrieval.

Flow:
    1. Validate file is a PDF
    2. Save to temp directory
    3. Run ingestion pipeline (parser.ingest)
    4. Index chunks in HybridRetriever (ChromaDB + BM25)
    5. Register in document store
    6. Return document_id + chunk count
"""

import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ingestion.parser import ingest

router = APIRouter()

UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------

class UploadResponse(BaseModel):
    document_id: str
    filename: str
    company: str
    year: int
    quarter: str
    chunk_count: int
    status: str
    indexed_at: str


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    company: str = Form(...),
    year: int = Form(...),
    quarter: str = Form(...),
):
    """
    Upload and index a financial PDF.

    Form fields:
        file    : PDF file (multipart)
        company : company name (e.g. "Apple Inc.")
        year    : fiscal year (e.g. 2024)
        quarter : fiscal period (e.g. "Q3", "FY")
    """
    # --- Validate file type ---
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    if not company.strip():
        raise HTTPException(status_code=422, detail="company field is required.")

    if year < 1990 or year > 2100:
        raise HTTPException(status_code=422, detail="year must be a valid 4-digit year.")

    valid_quarters = {"Q1", "Q2", "Q3", "Q4", "FY", "H1", "H2"}
    if quarter.upper() not in valid_quarters:
        raise HTTPException(
            status_code=422,
            detail=f"quarter must be one of {sorted(valid_quarters)}."
        )

    document_id = str(uuid.uuid4())
    save_path = UPLOAD_DIR / f"{document_id}.pdf"

    # --- Save file ---
    try:
        content = await file.read()
        async with aiofiles.open(save_path, "wb") as f:
            await f.write(content)
        logger.info(f"Saved PDF: {save_path} ({len(content):,} bytes)")
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file.")

    # --- Ingest ---
    config = request.app.state.config
    ingestion_cfg = config.get("ingestion", {})

    metadata = {
        "company": company.strip(),
        "year": year,
        "quarter": quarter.upper(),
    }

    try:
        chunks = ingest(
            pdf_path=str(save_path),
            document_id=document_id,
            metadata=metadata,
            chunk_size=ingestion_cfg.get("chunk_size", 512),
            chunk_overlap=ingestion_cfg.get("chunk_overlap", 64),
        )
    except Exception as e:
        logger.error(f"Ingestion failed for document_id={document_id}: {e}")
        save_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"PDF parsing failed: {str(e)}")

    if not chunks:
        save_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422,
            detail="No text could be extracted from the PDF. It may be a scanned document."
        )

    # --- Index ---
    try:
        request.app.state.retriever.index_document(document_id, chunks)
    except Exception as e:
        logger.error(f"Indexing failed for document_id={document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

    # --- Register ---
    indexed_at = datetime.utcnow().isoformat() + "Z"
    doc_entry = {
        "document_id": document_id,
        "filename": file.filename,
        "company": company.strip(),
        "year": year,
        "quarter": quarter.upper(),
        "chunk_count": len(chunks),
        "status": "indexed",
        "indexed_at": indexed_at,
    }
    request.app.state.document_store[document_id] = doc_entry

    logger.info(
        f"Document indexed: document_id={document_id} | "
        f"{company} {quarter} {year} | {len(chunks)} chunks"
    )

    return UploadResponse(**doc_entry)
