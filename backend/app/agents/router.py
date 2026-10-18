"""Agent router — classifies a user question into HR / IT / Policy."""

from __future__ import annotations

import re

from app.agents.agent_specs import AGENTS


# Lightweight keyword-based router (no LLM call — keeps Phase 2 runnable
# without an API key). When OpenAI is enabled, this can be swapped for an
# LLM classifier (see Phase 2 roadmap in README).

KEYWORDS: dict[str, list[str]] = {
    "hr": [
        "leave", "leaves", "payroll", "salary", "onboarding", "onboard",
        "benefits", "health plan", "insurance", "attendance", "reimbursement",
        "performance review", "appraisal", "exit", "resignation", "joining",
        "offer letter", "pf", "provident", "tax", "form 16",
    ],
    "it": [
        "password", "vpn", "laptop", "hardware", "software", "install",
        "ticket", "network", "email", "outlook", "wifi", "printer",
        "mfa", "2fa", "authenticator", "reset", "login", "access",
        "anyconnect", "antivirus", "phishing", "ransomware", "firewall",
    ],
    "policy": [
        "policy", "policies", "compliance", "code of conduct", "ethics",
        "data classification", "remote work", "hybrid", "wfh",
        "gift", "conflict of interest", "information security",
        "incident", "breach", "gdpr", "pii", "confidential",
        "restricted", "internal use", "iso 27001", "audit",
    ],
}


def classify_question(question: str, fallback: str = "hr") -> str:
    """Classify a question into one of the agent namespaces.

    Args:
        question: the user's question.
        fallback: which agent to use if no keyword matches.

    Returns:
        One of 'hr', 'it', 'policy'.
    """
    q = question.lower()
    scores: dict[str, int] = {a: 0 for a in AGENTS}
    for agent_id, words in KEYWORDS.items():
        for w in words:
            if w in q:
                scores[agent_id] += 1
    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    if scores[best] == 0:
        return fallback
    return best


def _extract_fallback_agent(question: str) -> str:
    """Tiny regex heuristic — if user explicitly names an agent, use it."""
    q = question.lower()
    if re.search(r"\bhr\b|human resource", q):
        return "hr"
    if re.search(r"\bit\b|information technology", q):
        return "it"
    if re.search(r"\bpolicy\b|policies|compliance", q):
        return "policy"
    return "hr"
