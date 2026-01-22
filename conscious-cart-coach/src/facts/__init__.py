"""
Facts module - single gateway to the SQLite facts store.

All agents access data through this module. No direct CSV loading.
"""

from .facts_gateway import FactsGateway, get_facts

__all__ = ["FactsGateway", "get_facts"]
