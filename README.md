# Enterprise Knowledge Assistant

**An enterprise knowledge chatbot built using RAG (Retrieval-Augmented Generation), Multi-Agent Architecture, and Generative AI.**

> **Repository:** [kartheekbvs89-arch/Langchain](https://github.com/kartheekbvs89-arch/Langchain)  
> **Live Demo (Frontend):** [GitHub Pages](https://kartheekbvs89-arch.github.io/Langchain/)  
> **Status:** Phase 1 (Frontend) ✅ · Phase 2 (RAG backend) ✅ · Phase 3 (Cloud + Eval) ✅ — **All 3 phases delivered**

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [The 3-Phase Project Plan](#3-the-3-phase-project-plan)
4. [Phase 1 — Frontend UI](#4-phase-1--frontend-ui)
5. [Phase 2 — Backend](#5-phase-2--backend)
6. [Phase 3 — Cloud + Eval (NEW)](#6-phase-3--cloud--eval-new)
7. [Running Locally](#7-running-locally)
8. [Live Demo on GitHub Pages](#8-live-demo-on-github-pages)
9. [What's Real vs Mocked](#9-whats-real-vs-mocked)
10. [Evaluation Metrics](#10-evaluation-metrics)
11. [Tech Stack](#11-tech-stack)
12. [License](#12-license)

---

## 1. Overview

The **Enterprise Knowledge Assistant** is a chatbot that lets employees ask natural-language questions about company HR policies, IT procedures, and compliance documents — and get accurate, **source-cited** answers in seconds.

Three specialist AI agents handle different domains:

| Agent | Domain | Example Questions |
|-------|--------|-------------------|
| **HR Agent** | Leaves, payroll, onboarding, benefits | "How many casual leaves am I entitled to?" |
| **IT Agent** | Access, VPN, hardware, software, tickets | "How do I configure VPN on macOS?" |
| **Policy Agent** | Code of conduct, compliance, security | "What are the data classification levels?" |

Each agent grounds its answer in retrieved documents using **RAG**, so every response includes a citation to the source document, page, section, and retrieval score.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER (Employee Browser)                       │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTPS
┌───────────────────────────────▼─────────────────────────────────┐
│                  FRONTEND (Phase 1 — delivered)                   │
│  HTML · CSS · JavaScript                                          │
│  ├── Login page                                                  │
│  ├── Chat interface (3-agent selector)                            │
│  ├── Document management                                         │
│  └── Analytics dashboard                                          │
└───────────────────────────────┬─────────────────────────────────┘
                                │ REST (auto-detected: backend or mock)
┌───────────────────────────────▼─────────────────────────────────┐
│                  BACKEND (Phase 2 — delivered)                    │
│  Python · FastAPI · LangChain · Chroma                          │
│  ├── Multi-Agent Router (HR / IT / Policy)                       │
│  ├── RAG pipeline (retrieve → rerank → generate)                  │
│  ├── Document ingestion (load → chunk → embed → store)           │
│  └── Citation formatter                                           │
└─────────┬─────────────────────────────────────────┬───────────────┘
          │                                         │
┌─────────▼─────────────────┐   ┌──────────────────▼─────────────┐
│   VECTOR DATABASE          │   │         LLM PROVIDER            │
│  Chroma (local file-based)│   │   OpenAI GPT-4o-mini (if key)   │
│                            │   │   OR local TemplateLLM (no key) │
│  Per-agent collections:    │   │                                 │
│   eka_hr, eka_it,          │   │   Generates grounded answers    │
│   eka_policy               │   │   from retrieved context         │
└────────────────────────────┘   └────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│              CLOUD DEPLOYMENT (Phase 3 — upcoming)                │
│   Container orchestration · Load balancing · Observability        │
└───────────────────────────────────────────────────────────────────┘
```

### RAG Data Flow (Per Query)

```
1. User question → frontend POSTs to /api/chat
2. Backend embeds question (HuggingFace all-MiniLM-L6-v2, 384-dim)
3. Vector search in agent's Chroma collection (top-K=5 chunks)
4. Rerank by score (top-3)
5. Build prompt (system prompt + context + question)
6. LLM generates answer (OpenAI if key set, else local TemplateLLM)
7. Return JSON {answer, sources[], latency_ms}
8. Frontend renders answer + source chips
```

---

## 3. The 3-Phase Project Plan

| Phase | Scope | Tech | Status |
|-------|-------|------|--------|
| **Phase 1** | Frontend UI — login, chat, documents, analytics dashboard | HTML, CSS, JavaScript | ✅ Delivered |
| **Phase 2** | RAG + Multi-Agent backend — LangChain, Chroma vector DB, HR/IT/Policy agents, document ingestion pipeline | Python, FastAPI, LangChain, Chroma, HuggingFace | ✅ Delivered |
| **Phase 3** | Cloud deployment + evaluation — infrastructure, observability, accuracy & retrieval metrics | Cloud Computing, Docker, Prometheus, LangSmith, RAGAS | ✅ Delivered |

---

## 4. Phase 1 — Frontend UI

### 4.1 Login Page (`index.html`)

Split-screen design: black brand panel on left, white sign-in form on right. Mock auth via `sessionStorage`. Demo credentials pre-filled.

### 4.2 Chat Page (`chat.html`)

- Agent picker sidebar (HR / IT / Policy)
- Recent conversations list
- Suggested prompts in empty state
- Message thread with source citations
- Typing indicator animation
- Composer: auto-grow textarea, Enter to send, Shift+Enter for newline
- **Auto-detects backend** — shows "Backend live" badge when Phase 2 is running, "Mock mode" otherwise

### 4.3 Documents Page (`documents.html`)

- Top stats (docs, chunks, storage, embeddings)
- Per-agent knowledge-base cards with progress bars
- Drag-and-drop upload zone with agent-namespace selector
- Document table with status pills (indexed / processing / failed), search, agent filter

### 4.4 Analytics Page (`analytics.html`)

- 3-phase roadmap tracker (Phase 1 at 100%, Phases 2 & 3 at 0%)
- KPIs: accuracy, recall@5, P95 latency, weekly queries
- Pure-CSS/SVG charts: bar (query volume), donut (agent split), line (accuracy trend)
- Latency breakdown table
- RAGAS evaluation table per agent

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for full design system details.

---

## 5. Phase 2 — Backend (NEW)

The Phase 2 backend is a Python FastAPI application using LangChain for RAG orchestration and Chroma as the vector database.

### Key Features

- **FastAPI** REST API with Swagger docs at `/docs`
- **LangChain** orchestration: prompt templates, retrievers, document loaders, text splitters
- **Chroma** local vector database — no signup, no external dependencies
- **HuggingFace sentence-transformers** (`all-MiniLM-L6-v2`) for embeddings — runs locally on CPU, no API key needed
- **Three specialist agents** (HR / IT / Policy), each with its own vector namespace, system prompt, and retrieval config
- **Local TemplateLLM** — a fallback LLM that composes grounded answers from retrieved context (no external API calls). When `OPENAI_API_KEY` is set, it auto-swaps to OpenAI GPT-4o-mini.
- **Document ingestion pipeline** — load PDF/DOCX/TXT/MD → chunk (size=512, overlap=64) → embed → upsert to vector DB
- **11 sample documents** seeded on first run (4 HR + 3 IT + 4 Policy)
- **Auto-seeding** on startup if the vector DB is empty
- **CORS** configured to allow the GitHub Pages frontend
- **End-to-end smoke tests** with pytest + FastAPI TestClient

### Quick Start

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run (auto-seeds sample docs on first start)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then visit:
- **API docs:** <http://localhost:8000/docs>
- **Frontend (served by backend):** <http://localhost:8000/app/>
- **Health check:** <http://localhost:8000/api/health>

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/chat` | Run RAG pipeline, return grounded answer + sources |
| `GET` | `/api/documents` | List all indexed documents |
| `POST` | `/api/documents/upload` | Upload + ingest a document (multipart form) |
| `DELETE` | `/api/documents/{agent}/{doc_name}` | Delete a document's chunks |
| `GET` | `/api/analytics` | Live metrics (query log + RAGAS mock values) |
| `GET` | `/api/health` | Backend status, version, LLM provider, collections |
| `POST` | `/api/seed?force=true` | Re-seed the vector DB |

### Run Tests

```bash
cd backend
pytest tests/ -v
```

The tests verify: imports, agent specs, router classification, sample doc seeding, end-to-end RAG for all 3 agents, and the FastAPI endpoints via TestClient.

See [`backend/README.md`](./backend/README.md) for full backend docs.

---

## 6. How the Project Works

### User Journey

1. **Sign in** on `index.html` (demo creds: `sample123@gmail.com` / `123456`)
2. Land on the **Chat page** — HR Agent pre-selected
3. Click an agent (HR / IT / Policy) or use a suggested prompt
4. Type a question. The frontend:
   - **If backend is live** (Phase 2 running locally): POSTs to `/api/chat`, gets real RAG-grounded answer with source citations
   - **If backend is offline** (e.g., on GitHub Pages): falls back to mock responses from the `AGENTS[].mockReplies` array
5. Switch to **Documents** to see the indexed knowledge base
6. Switch to **Analytics** to view performance metrics

### Frontend ↔ Backend Auto-Detection

`js/app.js` probes `/api/health` at:
- Same origin (when served by FastAPI at `http://localhost:8000/app/`)
- `http://127.0.0.1:8000`
- `http://localhost:8000`

If reachable, the UI shows a "Backend live" badge and calls real endpoints. If not, it falls back to mock mode — making the GitHub Pages deployment still work without a backend.

---

## 7. File Structure

```
Langchain/
├── README.md                         ← this file
├── ARCHITECTURE.md                   ← design system & architecture deep-dive
├── LICENSE
├── .gitignore
│
├── index.html                         ← Login page (Phase 1)
├── chat.html                          ← Chat interface (Phase 1, calls Phase 2)
├── documents.html                     ← Document management (Phase 1)
├── analytics.html                     ← Performance dashboard (Phase 1)
│
├── css/
│   ├── style.css                      ← Design system (tokens, components)
│   └── pages.css                      ← Page-specific styles
│
├── js/
│   └── app.js                         ← App shell + API client + mock data
│
└── backend/                           ← Phase 2 — RAG + Multi-Agent
    ├── README.md                      ← Backend-specific docs
    ├── requirements.txt
    ├── .env.example
    ├── .gitignore
    ├── app/
    │   ├── main.py                    ← FastAPI app + lifespan (auto-seed)
    │   ├── config.py                  ← Settings (from .env)
    │   ├── models.py                  ← Pydantic schemas
    │   ├── agents/
    │   │   ├── agent_specs.py          ← HR / IT / Policy definitions
    │   │   └── router.py               ← Keyword-based classifier
    │   ├── rag/
    │   │   ├── embeddings.py           ← HuggingFace sentence-transformers
    │   │   ├── vectorstore.py          ← Chroma client
    │   │   ├── llm.py                  ← OpenAI or local TemplateLLM
    │   │   └── pipeline.py             ← retrieve → rerank → generate
    │   ├── ingestion/
    │   │   ├── loader.py               ← PDF / DOCX / TXT / MD loaders
    │   │   ├── chunker.py              ← RecursiveCharacterTextSplitter
    │   │   └── ingest.py               ← Full pipeline + sample seeding
    │   ├── api/
    │   │   └── routes.py               ← All REST endpoints
    │   └── data/
    │       └── sample_docs_seed.py     ← 11 synthetic policy documents
    ├── data/
    │   └── sample_docs/{hr,it,policy}/ ← Same content as .txt files
    └── tests/
        ├── conftest.py                 ← Auto-seeds DB before tests
        └── test_smoke.py               ← End-to-end smoke tests
```

---

## 8. Running Locally

### Phase 1 only (frontend, mock mode)

```bash
cd Langchain
python3 -m http.server 8000
# Visit http://localhost:8000
```

Login with `sample123@gmail.com` / `123456`.

### Phase 1 + Phase 2 (full stack)

```bash
# Terminal 1: backend
cd Langchain/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 2: frontend (separate port)
cd Langchain
python3 -m http.server 5500
# Visit http://localhost:5500 — frontend auto-detects backend at :8000
```

Or run everything from one origin:

```bash
cd Langchain/backend
uvicorn app.main:app --port 8000
# Visit http://localhost:8000/app/ — serves frontend + backend together
```

---

## 9. Live Demo on GitHub Pages

The Phase 1 frontend is deployed via **GitHub Pages** (static hosting only — no Python backend).

**URL:** <https://kartheekbvs89-arch.github.io/Langchain/>

Since GitHub Pages can't run Python, the live demo runs in **mock mode** (Phase 1 mock responses). To see real RAG responses, run the Phase 2 backend locally and the frontend will auto-detect it.

### Limitations of GitHub Pages

- Only serves static files (HTML/CSS/JS) — no Python, no FastAPI, no Chroma
- The Phase 2 backend must run on a cloud platform (AWS / Azure / GCP) — that's Phase 3

---

## 10. What's Real vs Mocked

| Component | Phase 1 (mock) | Phase 2 (real) | Live on Pages |
|-----------|----------------|-----------------|----------------|
| Authentication | `sessionStorage`, any creds | Same (still mock) | Mock |
| Chat responses | Hard-coded reply arrays | **LangChain RAG → LLM** (OpenAI or TemplateLLM) | Mock (Pages) / Real (local) |
| Source citations | Static `pools` object | **Real Chroma vector search** with cosine scores | Mock (Pages) / Real (local) |
| Document ingestion | `MOCK_DOCS` array | **Backend pipeline: chunk → embed → store** | Mock (Pages) / Real (local) |
| Analytics metrics | Pre-computed values | **Live query log + DB counts** + RAGAS mock | Mock (Pages) / Real (local) |
| Vector DB | None | **Chroma (local file-based)** | n/a |

---

## 11. Phase 3 — Cloud + Eval (NEW)

Phase 3 delivers production-ready cloud deployment, observability, and live RAGAS evaluation pipeline.

### What's delivered

#### Docker + Docker Compose
- Multi-stage Dockerfile with CPU-only PyTorch (200MB instead of 3GB)
- `docker-compose.yml` brings up backend + nginx frontend on one host
- Persistent volumes for Chroma DB
- Health checks at `/api/health`

#### Cloud deployment configs (3 providers)

| Cloud | File | Service |
|-------|------|---------|
| **AWS** | `deploy/aws/cloudformation.yaml` | ECS Fargate + S3 + CloudFront + ALB + auto-scaling |
| **Azure** | `deploy/azure/main.bicep` | Container Apps + Blob + CDN + Log Analytics |
| **GCP** | `deploy/gcp/deployment.yaml` | Cloud Run + Cloud Storage + Load Balancer |

One-command AWS deploy: `cd deploy/aws && ./deploy.sh prod` (after `aws configure`).

#### LangSmith tracing
- `backend/app/rag/tracing.py` — wraps every RAG call in a trace span
- Two spans per query: `rag.retrieve` and `rag.generate`
- Auto-enables LangChain tracing when `LANGSMITH_API_KEY` is set
- View traces at [smith.langchain.com](https://smith.langchain.com)

#### Live RAGAS evaluation pipeline
- `backend/app/eval/runner.py` — 24-question gold set (8 per agent)
- Metrics: Faithfulness, Answer Relevancy, Context Precision, Context Recall
- Heuristic scorer (keyword + source overlap) — no LLM-as-judge API needed
- Endpoints: `POST /api/eval/run`, `GET /api/eval/latest`, `GET /api/eval/summary`
- Frontend "Run Evaluation" button triggers live eval and renders results
- Nightly eval via GitHub Actions cron

#### Prometheus metrics
- `backend/app/metrics.py` — counters + histograms
- `GET /api/metrics` exposes Prometheus exposition format
- Tracks: `chat_queries_total`, `chat_chunks_retrieved_total`, `chat_latency_ms` (p50/p95)
- Scrape with Prometheus + Grafana

#### GitHub Actions CI/CD (`.github/workflows/ci-cd.yml`)
7 jobs:
1. `test-backend` — pytest + RAGAS eval on every push
2. `lint-frontend` — HTML + JS validation
3. `deploy-pages` — auto-deploys frontend to GitHub Pages
4. `build-docker` — builds + pushes image to GHCR on `v*` tags
5. `deploy-aws` — deploys to AWS staging on `v*` tags
6. `nightly-eval` — runs full RAGAS eval nightly, uploads report
7. `security-scan` — Trivy vulnerability scanner

### Production Architecture

```
                   ┌──────────────────┐
                   │  CloudFront/CDN  │  (HTTPS, global)
                   └─────────┬────────┘
                   ┌─────────▼────────┐
                   │   Load Balancer   │
                   └─────────┬────────┘
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼───────┐   ┌────────▼────────┐   ┌──────▼──────┐
│  Frontend     │   │  Backend API    │   │  Ingestion  │
│  (S3 + CDN)  │   │  (ECS/Container │   │  Worker     │
│              │   │   Apps/Cloud Run│   │  (optional) │
└───────────────┘   └────────┬────────┘   └──────┬──────┘
                   ┌─────────▼────────┐          │
                   │  LLM Provider    │          │
                   │  (OpenAI/Azure/ │          │
                   │   local TLLM)   │          │
                   └──────────────────┘          │
                                                 │
                   ┌─────────────────────────────▼──┐
                   │  Chroma (EFS / Azure Files /    │
                   │   Persistent Disk)             │
                   └────────────────────────────────┘
                                 │
                   ┌─────────────▼────────────────┐
                   │  Observability                │
                   │  • Prometheus + Grafana       │
                   │  • LangSmith tracing          │
                   │  • CloudWatch / Log Analytics │
                   └──────────────────────────────┘
```

See [`deploy/README.md`](./deploy/README.md) for full deployment docs.

---

## 12. Evaluation Metrics

| Metric | What it measures | Target | Current |
|--------|------------------|--------|---------|
| **Faithfulness** | % grounded in retrieved context | ≥ 0.90 | Live via `/api/eval/run` |
| **Answer Relevancy** | How directly addresses query | ≥ 0.85 | Live via `/api/eval/run` |
| **Context Precision** | Relevance of top-K chunks | ≥ 0.85 | Live via `/api/eval/run` |
| **Context Recall** | Coverage of needed chunks | ≥ 0.88 | Live via `/api/eval/run` |
| **Answer accuracy** | End-to-end correctness | ≥ 90% | Live via `/api/eval/run` |
| **Retrieval recall@5** | % of gold chunks in top-5 | ≥ 0.90 | Live via `/api/eval/run` |
| **P50 latency** | Median query → response | ≤ 1.5s | Live via `/api/metrics` |
| **P95 latency** | 95th-percentile latency | ≤ 3.0s | Live via `/api/metrics` |

Run the live eval:
```bash
curl -X POST http://localhost:8000/api/eval/run | python3 -m json.tool
```

Or click the "Run Evaluation" button on the Analytics page.

---

## 13. Tech Stack

### Phase 1 (delivered)

- HTML5, CSS3, vanilla JavaScript (ES6+) — no frameworks, no build step
- Inter + JetBrains Mono fonts

### Phase 2 (delivered)

- Python 3.11+
- FastAPI — async REST API
- LangChain — RAG orchestration
- Chroma — local vector database
- HuggingFace sentence-transformers — embeddings (`all-MiniLM-L6-v2`)
- langchain-openai — optional OpenAI LLM swap-in
- PyPDF, python-docx — document loaders
- Pydantic v2 — request/response schemas
- pytest — smoke tests

### Phase 3 (delivered)

- **Docker + Docker Compose** — full-stack local + cloud deployment
- **AWS CloudFormation** — ECS Fargate + S3 + CloudFront + ALB + auto-scaling
- **Azure Bicep** — Container Apps + Blob Storage + CDN + Log Analytics
- **GCP Deployment Manager** — Cloud Run + Cloud Storage + Load Balancer
- **LangSmith** — automatic RAG call tracing (when `LANGSMITH_API_KEY` set)
- **Prometheus metrics** — `/api/metrics` endpoint with counters + histograms
- **RAGAS evaluation pipeline** — 24-question gold set + 4 metrics + heuristic scorer
- **GitHub Actions** — 7-job CI/CD pipeline (test, lint, build, deploy, eval, security)
- **Trivy** — vulnerability scanning on every push

---

## 13. License

MIT License — see [LICENSE](./LICENSE).
