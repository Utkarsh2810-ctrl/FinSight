# FinSight FastAPI service — production Dockerfile
# Uses Python 3.13 (unlike local dev on 3.14) specifically because it has
# clean prebuilt wheels for BOTH the ML stack (torch, sentence-transformers,
# chromadb) AND ragas/langchain — eliminating the need for the local
# two-venv/subprocess workaround. Single environment, single process.

FROM python:3.13-slim

WORKDIR /app

# System deps needed by some packages (chromadb/sqlite, pdf parsing libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# --- Install CPU-only torch FIRST and explicitly ---
# Default `pip install torch` pulls the CUDA build (multi-GB, unnecessary
# on Render's free tier which has no GPU). This must come before the rest
# of requirements.txt so pip doesn't resolve a CUDA build as a dependency
# of sentence-transformers.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# --- Main app + evaluation deps in one merged requirements file ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Patch ragas's dead VertexAI import (see README for context) ---
# Same one-line fix applied locally to eval_venv — done here at build time
# so it survives every deploy without manual intervention.
RUN python -c "\
import ragas, os; \
path = os.path.join(os.path.dirname(ragas.__file__), 'llms', 'base.py'); \
content = open(path).read(); \
old = 'from langchain_community.chat_models.vertexai import ChatVertexAI'; \
new = 'try:\n    from langchain_community.chat_models.vertexai import ChatVertexAI\nexcept ImportError:\n    class ChatVertexAI:\n        pass'; \
open(path, 'w').write(content.replace(old, new)) if old in content else None \
"

COPY . .

# Single worker: on a memory-constrained free tier, extra uvicorn workers
# each duplicate the loaded embedding/cross-encoder/torch models in RAM.
# One worker is deliberate, not a mistake.
ENV PORT=8000
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port $PORT --workers 1"]
