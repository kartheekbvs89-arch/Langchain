"""Smoke tests for the Phase 2 backend.

Run with:
    cd backend
    pytest tests/test_smoke.py -v
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Make the backend app importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_imports():
    """All key modules should import without error."""
    from app.config import settings
    from app.agents import AGENTS, get_agent, classify_question
    from app.rag.embeddings import get_embeddings
    from app.rag.vectorstore import count_chunks
    from app.rag.pipeline import run_rag
    from app.ingestion.ingest import seed_sample_docs
    from app.models import ChatRequest, ChatResponse
    from app.api.routes import router

    assert settings.app_name
    assert "hr" in AGENTS
    assert "it" in AGENTS
    assert "policy" in AGENTS


def test_agent_specs():
    from app.agents import get_agent

    hr = get_agent("hr")
    assert hr.id == "hr"
    assert "leave" in hr.system_prompt.lower()

    with pytest.raises(ValueError):
        get_agent("nonexistent")


def test_router_classification():
    from app.agents.router import classify_question

    assert classify_question("how many leaves am I entitled to?") == "hr"
    assert classify_question("how to reset my password") == "it"
    assert classify_question("vpn configuration on macos") == "it"
    assert classify_question("what are the data classification levels?") == "policy"
    assert classify_question("gift acceptance policy") == "policy"
    assert classify_question("random question with no keywords") == "hr"  # fallback


def test_sample_docs_seed():
    """Seed the DB and verify chunks were added."""
    from app.ingestion.ingest import seed_sample_docs
    from app.rag.vectorstore import count_chunks

    # Force re-seed
    results = seed_sample_docs(force=True)
    seeded = [r for r in results if "error" not in r]
    assert len(seeded) == 11  # 4 HR + 3 IT + 4 Policy

    # Each agent should have chunks
    assert count_chunks("hr") > 0
    assert count_chunks("it") > 0
    assert count_chunks("policy") > 0


def test_rag_pipeline_hr():
    """End-to-end RAG: ask an HR question, get an answer with sources."""
    from app.rag.pipeline import run_rag

    result = run_rag("hr", "How many casual leaves am I entitled to?")
    assert result.agent == "hr"
    assert len(result.answer) > 50
    assert len(result.sources) > 0
    # The retrieved source should mention HR or leave
    sources_text = " ".join(s.document.lower() for s in result.sources)
    assert "hr" in sources_text or "leave" in sources_text


def test_rag_pipeline_it():
    from app.rag.pipeline import run_rag

    result = run_rag("it", "How do I reset my corporate password?")
    assert result.agent == "it"
    assert "password" in result.answer.lower()


def test_rag_pipeline_policy():
    from app.rag.pipeline import run_rag

    result = run_rag("policy", "What are the data classification levels?")
    assert result.agent == "policy"
    assert "public" in result.answer.lower() or "classification" in result.answer.lower()


def test_chat_endpoint_via_test_client():
    """Test the FastAPI chat endpoint via TestClient."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.post(
        "/api/chat",
        json={"question": "How many casual leaves am I entitled to?", "agent": "hr"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert data["agent"] == "hr"
    assert len(data["sources"]) > 0


def test_documents_endpoint():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data
    assert data["total"] >= 0


def test_analytics_endpoint():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "accuracy" in data
    assert "queries_by_agent" in data
    assert "ragas_metrics" in data


def test_health_endpoint():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "agents" in data
    assert "hr" in data["agents"]


def test_eval_runner():
    """Phase 3: eval pipeline runs against the gold set."""
    from app.eval import run_eval, eval_set_summary

    summary = eval_set_summary()
    assert summary["total_questions"] == 24
    assert summary["by_agent"]["hr"] == 8
    assert summary["by_agent"]["it"] == 8
    assert summary["by_agent"]["policy"] == 8

    # Run a subset (4 questions) to keep test fast
    from app.eval.runner import DEFAULT_EVAL_SET
    subset = DEFAULT_EVAL_SET[:4]
    report = run_eval(eval_set=subset)
    assert report.total_questions == 4
    assert 0 <= report.avg_overall <= 1
    assert report.p50_latency_ms >= 0


def test_eval_endpoints():
    """Phase 3: /api/eval/summary and /api/eval/latest endpoints work."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    r = client.get("/api/eval/summary")
    assert r.status_code == 200
    assert r.json()["total_questions"] == 24

    r = client.get("/api/eval/latest")
    assert r.status_code == 200  # may be empty message or actual results


def test_metrics_endpoint():
    """Phase 3: /api/metrics returns Prometheus format."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    # Trigger a chat to populate metrics
    client.post("/api/chat", json={"question": "test", "agent": "hr"})

    response = client.get("/api/metrics")
    assert response.status_code == 200
    assert "chat_queries_total" in response.text
