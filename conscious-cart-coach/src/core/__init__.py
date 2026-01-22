"""
Core module - shared types, decision engine, orchestrator.
"""

from .types import AgentResult, Evidence, make_result, make_error

__all__ = ["AgentResult", "Evidence", "make_result", "make_error"]
