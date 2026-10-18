# Phase 3 — Cloud Deployment + Evaluation

Production deployment configs + observability + live RAGAS evaluation pipeline.

## What's included

```
deploy/
├── nginx.conf                   # Frontend nginx config (Docker Compose / standalone)
├── aws/
│   ├── cloudformation.yaml      # Full AWS stack: ECS Fargate + S3 + CloudFront + ALB
│   ├── deploy.sh                # One-command deploy script
│   └── README.md                # AWS-specific docs
├── azure/
│   └── main.bicep               # Azure Container Apps + Blob + CDN + Log Analytics
└── gcp/
    └── deployment.yaml          # GCP Cloud Run + Cloud Storage + Load Balancer

backend/app/eval/
├── __init__.py
└── runner.py                    # RAGAS-style eval pipeline (24 questions, 8 per agent)

backend/app/rag/
└── tracing.py                   # LangSmith tracing integration

backend/app/metrics.py           # Prometheus metrics (counters + histograms)

.github/workflows/
└── ci-cd.yml                     # 7-job CI/CD pipeline
```

## Quick start: Docker Compose (local)

The fastest way to run the entire stack on a single host:

```bash
docker compose up --build
```

This brings up:
- **Backend**: http://localhost:8000 (FastAPI + LangChain + Chroma)
- **Frontend**: http://localhost:8080 (nginx serving Phase 1 UI)
- API docs: http://localhost:8000/docs
- Metrics: http://localhost:8000/api/metrics

Environment variables (set in `.env` or shell):
```bash
OPENAI_API_KEY=sk-...      # Optional — falls back to local TemplateLLM
LANGSMITH_API_KEY=ls_...   # Optional — enables LangSmith tracing
```

## Quick start: AWS ECS Fargate (production)

```bash
# 1. Create the stack (first time)
aws cloudformation deploy \
  --template-file deploy/aws/cloudformation.yaml \
  --stack-name eka-prod \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides EnvironmentName=prod OpenAIApiKey=sk-your-key

# 2. Build, push, deploy
cd deploy/aws && ./deploy.sh prod
```

See [`deploy/aws/README.md`](./aws/README.md) for full AWS docs including cost estimates, observability, and teardown.

## Quick start: Azure Container Apps

```bash
# 1. Create resource group
az group create -n eka-prod-rg -l eastus

# 2. Deploy
az deployment group create \
  --resource-group eka-prod-rg \
  --template-file deploy/azure/main.bicep \
  --parameters environmentName=prod openaiApiKey=sk-your-key
```

## Quick start: GCP Cloud Run

```bash
# 1. Enable APIs
gcloud services enable run.googleapis.com compute.googleapis.com storage.googleapis.com

# 2. Deploy
gcloud deployment-manager deployments create eka-prod \
  --config deploy/gcp/deployment.yaml
```

## Live RAGAS Evaluation

The `/api/eval/run` endpoint runs the full 24-question evaluation pipeline against the gold set:

```bash
curl -X POST http://localhost:8000/api/eval/run | python3 -m json.tool
```

Returns per-question + aggregated scores:
- **Faithfulness** (0..1) — answer grounded in retrieved context
- **Answer Relevancy** (0..1) — answer addresses the question
- **Context Precision** (0..1) — retrieved chunks are relevant
- **Context Recall** (0..1) — needed chunks were retrieved
- **Overall** (0..1) — composite weighted score

The frontend Analytics page has a "Run Evaluation" button that triggers this from the UI.

## Prometheus Metrics

The `/api/metrics` endpoint exposes metrics in Prometheus exposition format:

```
chat_queries_total{agent="hr"} 42
chat_queries_total{agent="it"} 18
chat_queries_total{agent="policy"} 7
chat_chunks_retrieved_total{agent="hr"} 126
chat_latency_ms{agent="hr","quantile":"0.5"} 1340
chat_latency_ms{agent="hr","quantile":"0.95"} 2180
```

Scrape with Prometheus + visualize in Grafana:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'eka-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: /api/metrics
```

## LangSmith Tracing

When `LANGSMITH_API_KEY` is set in the environment, the RAG pipeline automatically wraps each call in a LangSmith trace span:

1. **rag.retrieve** span — captures agent_id, question, chunks_found, chunks_used, duration
2. **rag.generate** span — captures llm_provider, answer_chars, duration

View traces at [smith.langchain.com](https://smith.langchain.com).

## GitHub Actions CI/CD

The pipeline (`.github/workflows/ci-cd.yml`) has 7 jobs:

| Job | Trigger | Purpose |
|-----|---------|---------|
| `test-backend` | all pushes + PRs | Run pytest smoke tests + RAGAS eval |
| `lint-frontend` | all pushes + PRs | Validate HTML structure + JS syntax |
| `deploy-pages` | push to main | Deploy frontend to GitHub Pages |
| `build-docker` | tag `v*` | Build backend image, push to GHCR |
| `deploy-aws` | tag `v*` | Deploy to AWS staging |
| `nightly-eval` | cron | Run full RAGAS eval + upload report |
| `security-scan` | all pushes + PRs | Trivy vulnerability scan |

To enable AWS deployment, set these repo secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_ACCOUNT_ID`

## Cost Estimates (light traffic, ~3k queries/month)

| Cloud | Setup | Monthly cost |
|-------|-------|--------------|
| AWS | ECS Fargate (2 tasks, 1vCPU/2GB) + ALB + S3 + CloudFront | ~$50 |
| Azure | Container Apps (2 replicas) + Blob + CDN + Log Analytics | ~$45 |
| GCP | Cloud Run (2 instances) + Storage + Load Balancer | ~$40 |

All three support auto-scaling — costs scale linearly with traffic.

## Production Checklist

Before going live:
- [ ] Set `OPENAI_API_KEY` for real LLM-powered answers (otherwise TemplateLLM)
- [ ] Set `LANGSMITH_API_KEY` for tracing
- [ ] Configure Prometheus + Grafana for monitoring
- [ ] Set up alerting on:
  - P95 latency > 3s
  - Error rate > 5%
  - Vector DB disk usage > 80%
- [ ] Configure nightly RAGAS eval — alert if `avg_overall < 0.7`
- [ ] Back up Chroma DB (EFS / Azure Files / persistent disk)
- [ ] Set up log retention (30-day default, adjust per compliance)
- [ ] Enable DDoS protection (CloudFront / Azure Front Door / Cloud Armor)
- [ ] Configure SSO / OIDC for the frontend (replaces mock auth)
