"""
Data layer for Conscious Cart Coach.

facts_store - SQLite-backed unified data store
refresh_jobs - Scheduled data refresh logic
"""

from .facts_store import FactsStore, get_store

__all__ = ["FactsStore", "get_store"]
