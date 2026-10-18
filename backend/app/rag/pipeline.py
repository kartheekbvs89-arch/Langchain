"""RAG pipeline — retrieve → rerank → generate."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from app.agents.agent_specs import get_agent
from app.config import settings
from app.rag.embeddings import get_embeddings
from app.rag.llm import get_llm, llm_provider_name
from app.rag.vectorstore import get_vectorstore_for_agent


@dataclass
class RetrievedChunk:
    document: str
    page: int | None
    section: str | None
    score: float
    snippet: str


@dataclass
class RagResult:
    answer: str
    agent: str
    sources: list[RetrievedChunk]
    latency_ms: int
    llm_provider: str


def retrieve(agent_id: str, question: str) -> list[RetrievedChunk]:
    """Retrieve top-K chunks from the agent's vector namespace."""
    embeddings = get_embeddings()
    vs = get_vectorstore_for_agent(agent_id, embeddings)
    try:
        docs_with_scores = vs.similarity_search_with_relevance_scores(
            question, k=settings.retrieval_top_k
        )
    except Exception:
        # Fallback for older langchain-chroma versions
        try:
            docs = vs.similarity_search(question, k=settings.retrieval_top_k)
            docs_with_scores = [(d, 0.5) for d in docs]
        except Exception:
            return []

    chunks: list[RetrievedChunk] = []
    for doc, score in docs_with_scores:
        meta = doc.metadata or {}
        chunks.append(
            RetrievedChunk(
                document=meta.get("source", "unknown"),
                page=meta.get("page"),
                section=meta.get("section"),
                score=float(score) if score is not None else 0.0,
                snippet=doc.page_content[:300],
            )
        )
    return chunks


def rerank(chunks: list[RetrievedChunk], top_k: int | None = None) -> list[RetrievedChunk]:
    """Simple rerank by score (descending).

    In Phase 3 this can be replaced with a cross-encoder reranker (e.g.,
    BGE-reranker or Cohere Rerank) for better precision.
    """
    k = top_k or settings.rerank_top_k
    return sorted(chunks, key=lambda c: c.score, reverse=True)[:k]


def build_prompt(agent_id: str, question: str, context: str) -> str:
    """Build the final prompt sent to the LLM."""
    spec = get_agent(agent_id)
    return (
        f"System: {spec.system_prompt}\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        f"Answer:"
    )


def format_context(chunks: list[RetrievedChunk]) -> str:
    """Format retrieved chunks into the context block for the prompt."""
    if not chunks:
        return "(no relevant context retrieved)"
    parts = []
    for i, c in enumerate(chunks, 1):
        loc = ""
        if c.page:
            loc += f" p.{c.page}"
        if c.section:
            loc += f" §{c.section}"
        parts.append(
            f"---\nChunk {i} [Source: {c.document}{loc} | score: {c.score:.2f}]\n{c.snippet}"
        )
    return "\n".join(parts)


def run_rag(agent_id: str, question: str) -> RagResult:
    """Execute the full RAG pipeline for one question.

    Steps:
        1. Retrieve top-K chunks from the agent's vector namespace.
        2. Rerank to top-N (default 3).
        3. Build the prompt (system + context + question).
        4. Generate the answer via LLM (OpenAI or local TemplateLLM).
        5. Return the answer + sources + latency.
    """
    from app.rag.tracing import trace, is_langsmith_enabled

    start = time.time()

    with trace("rag.retrieve", agent_id=agent_id, question=question) as retrieve_span:
        chunks = retrieve(agent_id, question)
        top_chunks = rerank(chunks)
        retrieve_span.metadata["chunks_found"] = len(chunks)
        retrieve_span.metadata["chunks_used"] = len(top_chunks)

    with trace("rag.generate", agent_id=agent_id, question=question, chunks=len(top_chunks)) as gen_span:
        context = format_context(top_chunks)
        prompt = build_prompt(agent_id, question, context)

        llm = get_llm()
        try:
            answer = llm.invoke(prompt)
            if hasattr(answer, "content"):
                answer_text = answer.content
            else:
                answer_text = str(answer)
        except Exception as e:
            answer_text = (
                f"I encountered an error while generating the answer: {e}. "
                "Please try again or contact support."
            )
            gen_span.finish(error=str(e))
        else:
            gen_span.metadata["llm_provider"] = llm_provider_name()
            gen_span.metadata["answer_chars"] = len(answer_text)

    latency_ms = int((time.time() - start) * 1000)

    return RagResult(
        answer=answer_text.strip(),
        agent=agent_id,
        sources=top_chunks,
        latency_ms=latency_ms,
        llm_provider=llm_provider_name(),
    )
