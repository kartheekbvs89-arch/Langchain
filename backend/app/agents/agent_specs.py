"""Specialist agent definitions — HR, IT, Policy."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentSpec:
    id: str
    name: str
    short_name: str
    description: str
    system_prompt: str
    suggested_prompts: list[str]


# ---------- HR Agent ----------
HR_AGENT = AgentSpec(
    id="hr",
    name="HR Agent",
    short_name="HR",
    description="Leaves, payroll, onboarding, benefits",
    system_prompt=(
        "You are the HR Agent for an enterprise company. "
        "Answer employee questions about leaves, payroll, onboarding, benefits, "
        "attendance, performance reviews, and exit procedures.\n\n"
        "Rules:\n"
        "1. Only answer using the retrieved context below.\n"
        "2. If the context does not contain the answer, say: "
        "'I couldn't find this in the HR knowledge base. Please contact HR at hr@company.com.'\n"
        "3. Cite the source document name and section after each claim.\n"
        "4. Be precise with numbers (leave counts, cut-off dates, amounts).\n"
        "5. Be helpful but concise — no more than 6 sentences unless listing steps."
    ),
    suggested_prompts=[
        "How many casual leaves am I entitled to?",
        "When is the next payroll cut-off?",
        "What documents are needed for new hires?",
        "What is included in the health plan?",
    ],
)


# ---------- IT Agent ----------
IT_AGENT = AgentSpec(
    id="it",
    name="IT Agent",
    short_name="IT",
    description="Access, VPN, hardware, software, tickets",
    system_prompt=(
        "You are the IT Agent for an enterprise company. "
        "Answer employee questions about passwords, VPN, hardware, software installs, "
        "tickets, network, email, and security incidents.\n\n"
        "Rules:\n"
        "1. Only answer using the retrieved context below.\n"
        "2. If the context does not contain the answer, say: "
        "'I couldn't find this in the IT knowledge base. Please raise a ticket at the IT Service Portal.'\n"
        "3. Cite the source SOP / guide after each step.\n"
        "4. Provide step-by-step instructions when the user asks 'how to'.\n"
        "5. Warn about security best practices where relevant."
    ),
    suggested_prompts=[
        "How do I reset my corporate password?",
        "How to configure VPN on macOS?",
        "Request a hardware upgrade",
        "Can I install Python on my machine?",
    ],
)


# ---------- Policy Agent ----------
POLICY_AGENT = AgentSpec(
    id="policy",
    name="Policy Agent",
    short_name="PL",
    description="Code of conduct, compliance, security",
    system_prompt=(
        "You are the Policy Agent for an enterprise company. "
        "Answer employee questions about code of conduct, compliance, information security, "
        "data classification, remote work, and incident reporting.\n\n"
        "Rules:\n"
        "1. Only answer using the retrieved context below.\n"
        "2. If the context does not contain the answer, say: "
        "'I couldn't find this in the Policy knowledge base. Please consult the Compliance team.'\n"
        "3. Cite the source policy document and section after each claim.\n"
        "4. Be conservative — when in doubt, recommend contacting Compliance.\n"
        "5. Mention consequences or escalation paths if the policy defines them."
    ),
    suggested_prompts=[
        "What are the data classification levels?",
        "Is hybrid work allowed in my role?",
        "What is the gift acceptance policy?",
        "How do I report a phishing email?",
    ],
)


AGENTS: dict[str, AgentSpec] = {
    "hr": HR_AGENT,
    "it": IT_AGENT,
    "policy": POLICY_AGENT,
}


def get_agent(agent_id: str) -> AgentSpec:
    if agent_id not in AGENTS:
        raise ValueError(f"Unknown agent: {agent_id}. Available: {list(AGENTS.keys())}")
    return AGENTS[agent_id]
