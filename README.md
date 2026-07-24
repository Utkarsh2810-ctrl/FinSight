# FinSight

A full-stack financial document intelligence system combining hybrid RAG-based Q&A, LSTM revenue forecasting, and automated retrieval-quality evaluation — built as a polyglot microservices architecture (Python, Java, JavaScript).

## What It Does

- **Q&A over financial PDFs** — upload an earnings report, ask questions, get grounded answers with source citations (company, quarter, page, chunk type)
- **Revenue forecasting** — trains an LSTM on a company's quarterly financials (via yfinance) to project next-quarter revenue
- **Retrieval evaluation** — runs a benchmark question set through the pipeline and scores answer quality with RAGAS (faithfulness, relevancy, context precision/recall)

## Architecture

Three independent services, each in its own language, talking over HTTP:

```
React (Vite + Tailwind)     :5173   — Q&A, Forecasting, Evaluation UI
FastAPI (Python)            :8000   — ML pipeline: ingestion, retrieval, QA, forecast, eval
Spring Boot (Java)          :8080   — JWT auth, user management, document ownership registry
```

**Why three services instead of one:** auth/user-management and ML inference have very different scaling and reliability needs. Splitting them means the ML service can be memory/compute-heavy without dragging down auth, and auth can enforce strict security boundaries independent of the ML stack's dependency surface.

**Auth flow:** Spring Boot issues JWTs on register/login → FastAPI verifies them locally (no round-trip to Spring Boot needed per request) → both services share a JWT secret.

**Upload flow:** PDF goes to FastAPI first (parsed, chunked, embedded, indexed) → the returned `document_id` is then registered against the user in Spring Boot's database, so ownership and ML indexing are handled by the service best suited to each.

## RAG Pipeline

- **Hybrid retrieval**: dense search (ChromaDB + `all-MiniLM-L6-v2`) fused with sparse search (BM25) via Reciprocal Rank Fusion, then reranked with a cross-encoder (`ms-marco-MiniLM-L-6-v2`) for final relevance ordering
- **Ingestion**: PyMuPDF for text extraction, pdfplumber for table extraction (tables converted to markdown so the LLM can reason over structured financial data directly)
- **Generation**: Groq-hosted Llama 3.1 with a strict finance system prompt (answers must cite `[Company | Period | Page | Type]` and refuse to answer beyond provided context)

## Forecasting

A 2-layer LSTM trained per-ticker on quarterly fundamentals (revenue, gross profit, operating income, net income, EBITDA) pulled from `yfinance`, with early stopping and gradient clipping. Predicts next-quarter revenue and QoQ growth.

**Known limitation:** `yfinance`'s free tier only exposes ~4-5 quarters of history per ticker, which is thin data for an LSTM. Validation loss diverging from training loss during longer runs is a visible symptom of this — documented here rather than hidden, since understanding *why* a model underperforms is as important as the model working at all. A production version would source longer history (e.g. Alpha Vantage or Financial Modeling Prep) rather than lowering the sequence length further.

## Evaluation

RAGAS scores answer quality against a hand-written benchmark of question/ground-truth pairs, run through the live pipeline (real retrieval + real generation, not cached).

## Tech Stack

| Layer | Stack |
|---|---|
| Frontend | React, Vite, Tailwind CSS |
| ML Backend | FastAPI, PyTorch, ChromaDB, sentence-transformers, RAGAS, Groq |
| Auth Backend | Spring Boot, Spring Security, JWT, H2 |
| Data | yfinance (forecasting), PyMuPDF + pdfplumber (ingestion) |

## Running Locally

**Prerequisites:** Python 3.13, Java 17, Node 20+, Maven, a Groq API key ([console.groq.com](https://console.groq.com))

**1. Spring Boot (auth service)**
```bash
cd spring-service
mvn spring-boot:run
```

**2. FastAPI (ML service)**
```bash
cd backend
python -m venv venv
venv\Scripts\activate   # or source venv/bin/activate on macOS/Linux
pip install -r requirements.txt
```
Create `backend/.env`:
```
GROQ_API_KEY=your_key_here
JWT_SECRET=<any string 32+ characters, must match spring-service config>
```
```bash
cd backend
uvicorn api.main:app --reload --port 8000
```

**3. React (frontend)**
```bash
cd frontend
npm install
npm run dev
```

Then open `http://localhost:5173`, register an account, and upload a PDF to get started.

## Status

This is an active portfolio project, not a finished product. Core Q&A and forecasting are functional; deployment and further RAGAS metric coverage are in progress.

## Author

Utkarsh Gupta — B.Tech Data Science & AI, IIIT Bangalore
