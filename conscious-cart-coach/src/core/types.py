"""
Shared types and contracts for all agents.

Every agent MUST return an AgentResult. This ensures:
- Consistent structure for Streamlit UI
- Predictable format for orchestrator
- Traceable evidence for debugging
- Testable outputs for Opik evaluation
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


@dataclass
class Evidence:
    """
    A single piece of evidence supporting a fact.

    Used for transparency - shows where data came from.
    """
    source: str              # e.g., "EWG", "FDA", "NJ Crop Calendar"
    key: str                 # e.g., "spinach", "recall_id"
    value: Any               # e.g., "dirty_dozen", "Class I"
    url: str | None = None   # source URL if available
    timestamp: str | None = None  # when data was retrieved

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "key": self.key,
            "value": self.value,
            "url": self.url,
            "timestamp": self.timestamp,
        }


@dataclass
class AgentResult:
    """
    Standard output contract for all agents.

    Every agent method that returns data MUST return this structure.
    """
    agent_name: str
    status: Literal["ok", "error"]
    facts: dict[str, Any]           # Machine-readable data (varies per agent)
    explain: list[str]              # Human-readable bullets (max 5 for UI)
    evidence: list[Evidence] = field(default_factory=list)
    error_message: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "status": self.status,
            "facts": self.facts,
            "explain": self.explain,
            "evidence": [e.to_dict() for e in self.evidence],
            "error_message": self.error_message,
            "timestamp": self.timestamp,
        }

    @property
    def is_ok(self) -> bool:
        return self.status == "ok"

    @property
    def is_error(self) -> bool:
        return self.status == "error"


def make_result(
    agent_name: str,
    facts: dict[str, Any],
    explain: list[str],
    evidence: list[Evidence] | list[dict] | None = None,
) -> AgentResult:
    """
    Helper to create a successful AgentResult.

    Args:
        agent_name: Name of the agent
        facts: Machine-readable output data
        explain: Human-readable bullet points (max 5)
        evidence: List of Evidence objects or dicts

    Returns:
        AgentResult with status="ok"
    """
    # Convert dicts to Evidence objects if needed
    evidence_list = []
    if evidence:
        for e in evidence:
            if isinstance(e, Evidence):
                evidence_list.append(e)
            elif isinstance(e, dict):
                evidence_list.append(Evidence(
                    source=e.get("source", "unknown"),
                    key=e.get("key", ""),
                    value=e.get("value", ""),
                    url=e.get("url"),
                    timestamp=e.get("timestamp"),
                ))

    # Limit explain to 5 bullets
    explain = explain[:5]

    return AgentResult(
        agent_name=agent_name,
        status="ok",
        facts=facts,
        explain=explain,
        evidence=evidence_list,
    )


def make_error(
    agent_name: str,
    error_message: str,
    partial_facts: dict[str, Any] | None = None,
) -> AgentResult:
    """
    Helper to create an error AgentResult.

    Args:
        agent_name: Name of the agent
        error_message: What went wrong
        partial_facts: Any partial data collected before error

    Returns:
        AgentResult with status="error"
    """
    return AgentResult(
        agent_name=agent_name,
        status="error",
        facts=partial_facts or {},
        explain=[f"Error: {error_message}"],
        evidence=[],
        error_message=error_message,
    )


# Type aliases for clarity
Ingredient = dict[str, Any]  # {name, canonical, optional, qty, unit, confidence}
Product = dict[str, Any]     # {product_id, name, brand, size, price, unit_price, ...}
ProductFlag = dict[str, Any] # {ewg_bucket, organic_required, recall_status, ...}
TierPick = dict[str, Any]    # {ingredient, product, tier, score, reasons}
