# Phase 2 — Backend (Python + FastAPI + LangChain + Chroma)

The RAG + Multi-Agent backend for the Enterprise Knowledge Assistant.

## Quick Start

### 1. Install dependencies

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment (optional)

```bash
cp .env.example .env
# Edit .env if you want to use OpenAI instead of the local TemplateLLM
```

By default, the backend uses:
- **HuggingFace sentence-transformers** (`all-MiniLM-L6-v2`) for embeddings — runs locally, no API key
- **Local TemplateLLM** for generation — composes grounded answers from retrieved context, no API key
- **Chroma** for the vector DB — local file-based, no signup

To use **OpenAI GPT-4o-mini** for generation, set `OPENAI_API_KEY` in `.env`. The backend will automatically swap to OpenAI at startup.

### 3. Run the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server auto-seeds sample documents on first run. Once running:

- **API docs (Swagger):** <http://localhost:8000/docs>
- **Health check:** <http://localhost:8000/api/health>
- **Frontend:** <http://localhost:8000/app/> (serves the Phase 1 frontend)

### 4. Test the chat endpoint

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How many casual leaves am I entitled to?", "agent": "hr"}'
```

Response shape:
```json
{
  "answer": "Based on the retrieved knowledge base...",
  "agent": "hr",
  "sources": [
    {"document": "HR_Policy_Manual_2024.pdf", "page": 1, "section": "1", "score": 0.82, "snippet": "..."}
  ],
  "latency_ms": 1340,
  "conversation_id": "abc-123",
  "timestamp": "2026-..."
}
```

### 5. Run tests

```bash
pytest tests/ -v
```

## API Reference

### `POST /api/chat`
Run the RAG pipeline. Body:
```json
{"question": "...", "agent": "hr|it|policy", "conversation_id": "optional"}
```

### `GET /api/documents`
List all indexed documents across all agents.

### `POST /api/documents/upload`
Upload and ingest a document. Multipart form:
- `file`: the file
- `agent`: `hr|it|policy`

### `DELETE /api/documents/{agent}/{doc_name}`
Delete all chunks of a document.

### `GET /api/analytics`
Return live metrics (query log counts) + RAGAS mock values.

### `GET /api/health`
Return backend status, version, LLM provider, collections.

### `POST /api/seed?force=true`
Re-seed the vector DB with sample documents.

## Architecture

```
backend/
├── app/
│   ├── main.py              ← FastAPI app + lifespan hooks
│   ├── config.py             ← settings (from .env)
│   ├── models.py             ← Pydantic request/response schemas
│   ├── agents/
│   │   ├── agent_specs.py    ← HR / IT / Policy agent definitions
│   │   └── router.py         ← keyword-based agent classifier
│   ├── rag/
│   │   ├── embeddings.py     ← HuggingFace sentence-transformers
│   │   ├── vectorstore.py    ← Chroma vector DB client
│   │   ├── llm.py            ← OpenAI or local TemplateLLM
│   │   └── pipeline.py       ← retrieve → rerank → generate
│   ├── ingestion/
│   │   ├── loader.py         ← PDF / DOCX / TXT / MD loaders
│   │   ├── chunker.py        ← RecursiveCharacterTextSplitter
│   │   └── ingest.py         ← full ingestion pipeline + seed
│   ├── api/
│   │   └── routes.py          ← all REST endpoints
│   └── data/
│       └── sample_docs_seed.py ← synthetic policy documents
├── data/
│   └── sample_docs/{hr,it,policy}/  ← same content as .txt files
├── tests/
│   ├── conftest.py           ← auto-seeds DB once per session
│   └── test_smoke.py         ← end-to-end smoke tests
├── requirements.txt
├── .env.example
└── .gitignore
```

## RAG Pipeline

```
1. Receive question + agent_id
2. Embed question (HuggingFace all-MiniLM-L6-v2 → 384-dim vector)
3. Vector search in agent's Chroma collection (top-K=5)
4. Rerank by score (top-3)
5. Build prompt: system prompt + context chunks + question
6. LLM generate (OpenAI GPT-4o-mini OR local TemplateLLM)
7. Return answer + sources + latency
```

## Sample Documents (11 total)

- **HR (4):** HR_Policy_Manual_2024, Leave_Policy, Payroll_Procedure, Onboarding_Checklist
- **IT (3):** IT_SOP_PasswordReset, IT_Network_Guide_v2, Asset_Policy
- **Policy (4):** InfoSec_Policy_v4, Code_of_Conduct_2024, Hybrid_Work_Policy_2024, Security_Incident_Response

Each document is chunked (chunk_size=512, overlap=64) and stored in its agent's Chroma collection (`eka_hr`, `eka_it`, `eka_policy`).

## Frontend Integration

The Phase 1 frontend automatically detects if this backend is running:

1. On page load, `js/app.js` probes `/api/health` at:
   - Same origin
   - `http://127.0.0.1:8000`
   - `http://localhost:8000`
2. If reachable, the chat UI shows "Backend live" and calls `/api/chat` for real responses.
3. If not reachable, it falls back to Phase 1 mock mode (offline-capable for GitHub Pages).

## Upgrading to Real LLM (OpenAI)

1. Get an API key from <https://platform.openai.com/api-keys>
2. Edit `backend/.env`:
   ```
   OPENAI_API_KEY=sk-your-real-key-here
   OPENAI_MODEL=gpt-4o-mini
   ```
3. Restart the server. The `llm.py` factory will auto-detect and swap to OpenAI.

No other code changes needed — the rest of the pipeline stays the same.

## Docker (optional)

```bash
# Build a simple image
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Phase 3 Roadmap

- [ ] Replace in-memory query log with Postgres
- [ ] Add LangGraph for multi-agent workflows
- [ ] Add cross-encoder reranker (BGE-reranker)
- [ ] Add SSE streaming for token-by-token responses
- [ ] Add LangSmith tracing
- [ ] Deploy to cloud (AWS ECS / Azure Container Apps)
- [ ] Wire up live RAGAS evaluation pipeline
