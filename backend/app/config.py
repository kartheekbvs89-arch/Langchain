"""Application configuration loaded from environment / .env file."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    app_name: str = "Enterprise Knowledge Assistant"
    app_version: str = "2.0.0"
    environment: Literal["dev", "staging", "prod"] = "dev"
    host: str = "0.0.0.0"
    port: int = 8000

    # --- Frontend CORS ---
    # Allow the GitHub Pages origin and localhost for dev
    cors_origins: str = (
        "http://localhost:8000,http://localhost:5500,http://127.0.0.1:8000,"
        "https://kartheekbvs89-arch.github.io"
    )

    # --- Vector DB ---
    vector_db_path: str = str(
        Path(__file__).resolve().parent.parent / "data" / "chroma_db"
    )
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384
    collection_prefix: str = "eka_"  # eka_hr, eka_it, eka_policy

    # --- RAG retrieval ---
    retrieval_top_k: int = 5
    rerank_top_k: int = 3
    chunk_size: int = 512
    chunk_overlap: int = 64

    # --- LLM ---
    # If OPENAI_API_KEY is set, use OpenAI. Otherwise fall back to a local
    # template-based LLM that produces grounded answers from retrieved context.
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 512

    # --- Agents ---
    enabled_agents: str = "hr,it,policy"

    # --- Analytics (in-memory counters; replace with DB in Phase 3) ---
    enable_analytics: bool = True

    # --- Phase 3: Tracing + Eval ---
    # LangSmith tracing (optional — leave blank to disable)
    langsmith_api_key: str = ""
    langsmith_project: str = "enterprise-knowledge-assistant"
    # OpenTelemetry endpoint (optional — for Jaeger/Tempo)
    otel_exporter_otlp_endpoint: str = ""

    # --- Phase 3: Eval config ---
    eval_question_count: int = 24  # 8 questions per agent


settings = Settings()


def agent_collections() -> dict[str, str]:
    """Return mapping of agent_id → Chroma collection name."""
    return {
        agent_id: f"{settings.collection_prefix}{agent_id}"
        for agent_id in settings.enabled_agents.split(",")
        if agent_id.strip()
    }


def is_openai_enabled() -> bool:
    return bool(settings.openai_api_key) or bool(os.getenv("OPENAI_API_KEY"))
