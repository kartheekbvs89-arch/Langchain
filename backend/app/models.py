"""Pydantic models for API request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ---------- Chat ----------

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    agent: Literal["hr", "it", "policy"] = "hr"
    conversation_id: str | None = None


class SourceChunk(BaseModel):
    document: str
    page: int | None = None
    section: str | None = None
    score: float
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    agent: str
    sources: list[SourceChunk]
    latency_ms: int
    conversation_id: str
    timestamp: str


# ---------- Documents ----------

class DocumentInfo(BaseModel):
    id: str
    name: str
    agent: Literal["hr", "it", "policy"]
    size_bytes: int
    chunks: int
    status: Literal["indexed", "processing", "failed"]
    uploaded_at: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo]
    total: int
    by_agent: dict[str, int]


class DocumentUploadResponse(BaseModel):
    document: DocumentInfo
    message: str


# ---------- Analytics ----------

class AnalyticsResponse(BaseModel):
    accuracy: float
    retrieval_recall_at_5: float
    p50_latency_ms: int
    p95_latency_ms: int
    queries_this_week: int
    unique_users: int
    queries_by_agent: dict[str, int]
    queries_by_day: dict[str, int]
    ragas_metrics: dict[str, dict[str, float]]


# ---------- Health ----------

class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "down"]
    version: str
    openai_enabled: bool
    vector_db_path: str
    agents: list[str]
    collections: dict[str, str]
