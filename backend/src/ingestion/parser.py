"""
parser.py
---------
Layer 1 — Ingestion.

Pipeline:
    PDF → extract_pages (PyMuPDF)
        → extract_tables (pdfplumber)
        → chunk_text (sliding window)
        → ingest (orchestrator, returns List[ChunkDict])

ChunkDict schema:
    chunk_id    : str   — "<document_id>_<index>"
    text        : str   — chunk content
    document_id : str   — UUID assigned on upload
    company     : str
    year        : int
    quarter     : str   — "Q1" / "Q2" / "Q3" / "Q4" / "FY"
    page        : int   — source page number (1-indexed)
    chunk_type  : str   — "text" | "table" | "header"
    char_count  : int
"""

import re
from pathlib import Path
from typing import Any, Dict, List

import fitz  # PyMuPDF
import pdfplumber
from loguru import logger


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_pages(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract raw text from each page using PyMuPDF.

    Returns:
        List of dicts with keys: page_num (1-indexed), raw_text, char_count.
        Pages with fewer than 20 characters are skipped (likely scanned images).
    """
    pages = []
    doc = fitz.open(pdf_path)

    for i, page in enumerate(doc, start=1):
        text = page.get_text("text")
        text = text.strip()

        if len(text) < 20:
            logger.warning(f"Page {i} has minimal text ({len(text)} chars) — possibly scanned. Skipping.")
            continue

        pages.append({
            "page_num": i,
            "raw_text": text,
            "char_count": len(text),
        })
        logger.debug(f"Page {i}: {len(text)} chars extracted")

    doc.close()
    logger.info(f"Extracted text from {len(pages)} pages in {pdf_path}")
    return pages


# ---------------------------------------------------------------------------
# Table extraction
# ---------------------------------------------------------------------------

def _table_to_markdown(table: List[List[Any]]) -> str:
    """
    Converts a pdfplumber table (list of rows, each a list of cell values)
    into a GitHub-flavoured markdown table string.

    Handles:
        - None cells → empty string
        - Multi-line cell text → collapsed to single line
    """
    if not table or not table[0]:
        return ""

    cleaned = []
    for row in table:
        cleaned_row = []
        for cell in row:
            if cell is None:
                cleaned_row.append("")
            else:
                # collapse newlines inside a cell
                cleaned_row.append(str(cell).replace("\n", " ").strip())
        cleaned.append(cleaned_row)

    # Build markdown
    header = "| " + " | ".join(cleaned[0]) + " |"
    separator = "| " + " | ".join(["---"] * len(cleaned[0])) + " |"
    rows = ["| " + " | ".join(row) + " |" for row in cleaned[1:]]

    return "\n".join([header, separator] + rows)


def extract_tables(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract tables from each page using pdfplumber and convert to markdown.

    Returns:
        List of dicts with keys: page_num (1-indexed), table_idx, markdown, char_count.
    """
    tables = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_tables = page.extract_tables()
            if not page_tables:
                continue

            for t_idx, table in enumerate(page_tables):
                md = _table_to_markdown(table)
                if not md:
                    continue

                tables.append({
                    "page_num": page_num,
                    "table_idx": t_idx,
                    "markdown": md,
                    "char_count": len(md),
                })
                logger.debug(f"Page {page_num}, table {t_idx}: {len(md)} chars")

    logger.info(f"Extracted {len(tables)} tables from {pdf_path}")
    return tables


# ---------------------------------------------------------------------------
# Chunking  (✍️ core logic — written to be defensible in interviews)
# ---------------------------------------------------------------------------

def _detect_chunk_type(text: str) -> str:
    """
    Heuristic classification of a text chunk.
    'header' : short lines that look like section headings
    'table'  : already tagged externally — never called for table text
    'text'   : default
    """
    stripped = text.strip()
    lines = stripped.splitlines()

    # Header: very short first line, all caps or title case, no terminal period
    if len(lines) >= 1:
        first = lines[0].strip()
        if len(first) < 80 and not first.endswith(".") and (first.isupper() or first.istitle()):
            return "header"

    return "text"


def chunk_text(
    text: str,
    metadata: Dict[str, Any],
    chunk_size: int = 512,
    chunk_overlap: int = 64,
    chunk_type: str = "text",
) -> List[Dict[str, Any]]:
    """
    Sliding-window chunking over whitespace-tokenised text.

    Args:
        text         : raw page text
        metadata     : dict with document_id, company, year, quarter, page_num
        chunk_size   : target token count per chunk (1 token ≈ 1 whitespace-split word)
        chunk_overlap: number of tokens shared between consecutive chunks
        chunk_type   : "text" | "table" | "header"

    Returns:
        List of ChunkDicts.

    Why sliding window:
        A naive split-by-N-words loses context at boundaries. Overlapping
        ensures that a sentence split across a boundary is fully present in
        at least one chunk, preserving retrieval recall.
    """
    tokens = text.split()
    if not tokens:
        return []

    chunks = []
    start = 0
    chunk_index = metadata.get("_chunk_index_offset", 0)

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text_str = " ".join(chunk_tokens)

        detected_type = chunk_type if chunk_type != "text" else _detect_chunk_type(chunk_text_str)

        chunks.append({
            "chunk_id": f"{metadata['document_id']}_{chunk_index}",
            "text": chunk_text_str,
            "document_id": metadata["document_id"],
            "company": metadata.get("company", ""),
            "year": metadata.get("year", 0),
            "quarter": metadata.get("quarter", ""),
            "page": metadata.get("page_num", 0),
            "chunk_type": detected_type,
            "char_count": len(chunk_text_str),
        })

        chunk_index += 1

        # If we've reached the end, stop
        if end == len(tokens):
            break

        # Slide forward by (chunk_size - overlap)
        start += chunk_size - chunk_overlap

    return chunks


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def ingest(
    pdf_path: str,
    document_id: str,
    metadata: Dict[str, Any],
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> List[Dict[str, Any]]:
    """
    Full ingestion pipeline for a single PDF.

    Args:
        pdf_path    : absolute path to the uploaded PDF
        document_id : UUID assigned on upload
        metadata    : {"company": str, "year": int, "quarter": str}
        chunk_size  : passed through to chunk_text
        chunk_overlap: passed through to chunk_text

    Returns:
        Flat list of ChunkDicts ready for indexing.
    """
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    all_chunks: List[Dict[str, Any]] = []
    global_chunk_index = 0

    # --- Text chunks ---
    pages = extract_pages(pdf_path)
    for page in pages:
        page_metadata = {
            **metadata,
            "document_id": document_id,
            "page_num": page["page_num"],
            "_chunk_index_offset": global_chunk_index,
        }
        page_chunks = chunk_text(
            text=page["raw_text"],
            metadata=page_metadata,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            chunk_type="text",
        )
        all_chunks.extend(page_chunks)
        global_chunk_index += len(page_chunks)

    # --- Table chunks (each table is one chunk, type="table") ---
    tables = extract_tables(pdf_path)
    for table in tables:
        table_metadata = {
            **metadata,
            "document_id": document_id,
            "page_num": table["page_num"],
            "_chunk_index_offset": global_chunk_index,
        }
        # Tables are treated as single atomic chunks — do not split across windows
        table_chunk = {
            "chunk_id": f"{document_id}_{global_chunk_index}",
            "text": table["markdown"],
            "document_id": document_id,
            "company": metadata.get("company", ""),
            "year": metadata.get("year", 0),
            "quarter": metadata.get("quarter", ""),
            "page": table["page_num"],
            "chunk_type": "table",
            "char_count": table["char_count"],
        }
        all_chunks.append(table_chunk)
        global_chunk_index += 1

    logger.info(
        f"Ingestion complete for document_id={document_id}: "
        f"{len(all_chunks)} chunks ({len(pages)} text pages, {len(tables)} tables)"
    )
    return all_chunks
