"""LLM module for Conscious Cart Coach.

Provides optional LLM integration for:
- IngredientAgent: Natural language ingredient extraction
- DecisionEngine: Enhanced explanations for recommendations

All LLM features have deterministic fallbacks.
"""

from .client import get_anthropic_client, call_claude_with_retry
from .ingredient_extractor import extract_ingredients_with_llm
from .decision_explainer import explain_decision_with_llm

__all__ = [
    "get_anthropic_client",
    "call_claude_with_retry",
    "extract_ingredients_with_llm",
    "explain_decision_with_llm",
]
