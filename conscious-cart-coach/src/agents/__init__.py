"""
Agents for Conscious Cart Coach.

All agents return AgentResult contract for consistent output.
"""

from .ingredient_agent import IngredientAgent, get_ingredient_agent
from .product_agent import ProductAgent, get_product_agent
from .safety_agent_v2 import SafetyAgent, get_safety_agent
from .seasonal_agent import SeasonalAgent, get_seasonal_agent
from .user_history_agent import UserHistoryAgent, get_user_history_agent

__all__ = [
    "IngredientAgent",
    "ProductAgent",
    "SafetyAgent",
    "SeasonalAgent",
    "UserHistoryAgent",
    "get_ingredient_agent",
    "get_product_agent",
    "get_safety_agent",
    "get_seasonal_agent",
    "get_user_history_agent",
]
