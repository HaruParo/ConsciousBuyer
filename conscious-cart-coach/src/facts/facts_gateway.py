"""
Facts Gateway - Single point of access to the facts store.

This is the ONLY way agents should access factual data.
No agent should load CSV files directly.

Usage:
    from src.facts import get_facts

    facts = get_facts()
    ewg = facts.get_ewg_bucket("spinach")
    recalls = facts.get_recalls("Fresh Express")
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from ..data.facts_store import FactsStore

# Singleton instance
_facts_instance: "FactsGateway | None" = None


class FactsGateway:
    """
    Gateway to all factual data.

    Wraps FactsStore with agent-friendly methods.
    Auto-refreshes stale tables on initialization.
    """

    def __init__(self, store: FactsStore | None = None, auto_refresh: bool = True):
        self.store = store or FactsStore()
        if auto_refresh:
            self._refresh_if_stale()

    def _refresh_if_stale(self):
        """Auto-refresh any stale tables from CSV sources."""
        stale_tables = self.store.needs_refresh()
        refresh_map = {
            "recalls": self.store.refresh_recalls,
            "ewg": self.store.refresh_ewg,
            "stores": self.store.refresh_stores,
            "crops": self.store.refresh_crops,
            "sources": self.store.refresh_sources,
        }
        for table in stale_tables:
            fn = refresh_map.get(table)
            if fn:
                fn()

    # =========================================================================
    # EWG Methods
    # =========================================================================

    def get_ewg_bucket(self, produce_name: str) -> dict:
        """
        Get EWG classification bucket for a produce item.

        Args:
            produce_name: Name of produce (e.g., "spinach", "avocado")

        Returns:
            {
                "bucket": "dirty_dozen" | "middle" | "clean_fifteen" | "unknown",
                "rank": int or None (1-47, higher = more contaminated),
                "organic_required": bool,    # dirty_dozen
                "organic_beneficial": bool,  # middle
                "pesticide_score": int or None,
            }
        """
        result = self.store.get_ewg_classification(produce_name)

        return {
            "bucket": result.get("list", "unknown"),
            "rank": result.get("rank"),
            "organic_required": result.get("organic_required", False),
            "organic_beneficial": result.get("organic_beneficial", False),
            "pesticide_score": result.get("pesticide_score"),
        }

    def is_dirty_dozen(self, produce_name: str) -> bool:
        """Check if produce is on Dirty Dozen list."""
        bucket = self.get_ewg_bucket(produce_name)
        return bucket["bucket"] == "dirty_dozen"

    def is_clean_fifteen(self, produce_name: str) -> bool:
        """Check if produce is on Clean Fifteen list."""
        bucket = self.get_ewg_bucket(produce_name)
        return bucket["bucket"] == "clean_fifteen"

    # =========================================================================
    # Recall Methods
    # =========================================================================

    def get_recalls(
        self,
        product_name_or_brand: str | None = None,
        date_window_days: int = 365,
        state: str = "NJ",
    ) -> list[dict]:
        """
        Get FDA recalls, optionally filtered.

        Args:
            product_name_or_brand: Filter by product name or brand
            date_window_days: How far back to look (default 365)
            state: State to filter by (default NJ)

        Returns:
            List of recall dicts
        """
        recalls = self.store.get_recalls(state=state)

        if product_name_or_brand:
            search_lower = product_name_or_brand.lower()
            filtered = []
            for r in recalls:
                product = r.get("product_description", "").lower()
                brands = r.get("affected_brands", "").lower()
                if search_lower in product or search_lower in brands:
                    filtered.append(r)
            recalls = filtered

        return recalls

    def check_recall_status(self, product_name: str, brand: str = "") -> dict:
        """
        Legacy wrapper. Use check_recall_signal() instead.
        """
        signal = self.check_recall_signal(product_name, brand)
        # Convert to legacy format for backward compatibility
        if signal["product_match"]:
            return {"status": "recalled", "recalls": signal["details"], "classification": "Class I"}
        elif signal["category_advisory"] != "none":
            return {"status": "recalled", "recalls": signal["details"], "classification": "Class II"}
        return {"status": "clear", "recalls": [], "classification": None}

    def check_recall_signal(self, product_name: str, brand: str = "") -> dict:
        """
        Structured recall assessment with nuanced taxonomy.

        Returns:
            {
                "product_match": bool,         # Direct product/brand recall match
                "category_advisory": str,      # "none" | "recent" | "elevated"
                "confidence": str,             # "high" | "medium" | "low"
                "data_gap": bool,              # True if insufficient data
                "details": list[str],          # Human-readable details
                "sources": list[str],          # Source identifiers
            }
        """
        product_recalls = self.get_recalls(product_name) if product_name else []
        brand_recalls = self.get_recalls(brand) if brand else []

        # Dedupe
        seen_ids = set()
        all_recalls = []
        for r in product_recalls + brand_recalls:
            rid = r.get("recall_id", "")
            if rid and rid not in seen_ids:
                seen_ids.add(rid)
                all_recalls.append(r)

        # Determine product_match (direct hit on product name or brand)
        product_match = False
        details = []
        sources = []

        for r in all_recalls:
            desc = r.get("product_description", "").lower()
            brands = r.get("affected_brands", "").lower()
            if (product_name.lower() in desc or
                (brand and brand.lower() in brands)):
                product_match = True
                details.append(f"Recall: {r.get('reason', 'Unknown reason')} ({r.get('classification', 'Unknown')})")
                sources.append(r.get("recall_id", "unknown"))

        # Determine category advisory
        category_advisory = "none"
        if len(all_recalls) >= 3:
            category_advisory = "elevated"
        elif len(all_recalls) >= 1 and not product_match:
            category_advisory = "recent"

        if not product_match and all_recalls:
            details = [f"Category has {len(all_recalls)} recent recall(s) in region"]

        # Confidence assessment
        if product_match:
            confidence = "high"
        elif all_recalls:
            confidence = "medium"
        else:
            confidence = "low"

        # Data gap check
        data_gap = self.is_data_stale("recalls")

        if data_gap:
            details.append("Recall data may be outdated")

        return {
            "product_match": product_match,
            "category_advisory": category_advisory,
            "confidence": confidence,
            "data_gap": data_gap,
            "details": details,
            "sources": sources,
        }

    # =========================================================================
    # Seasonality Methods
    # =========================================================================

    def get_seasonality(
        self,
        item: str,
        region: str = "NJ",
        month: int | None = None,
    ) -> dict:
        """
        Get seasonality info for a produce item.

        Args:
            item: Produce name
            region: Region (currently only NJ supported)
            month: Month number (1-12), default current month

        Returns:
            {
                "status": "peak" | "available" | "storage" | "imported" | "unknown",
                "is_local": bool,
                "bonus": int (scoring bonus),
                "reasoning": str,
            }
        """
        if month is None:
            month = datetime.now().month

        month_names = ["jan", "feb", "mar", "apr", "may", "jun",
                       "jul", "aug", "sep", "oct", "nov", "dec"]
        month_str = month_names[month - 1]

        # Search crops
        crops = self.store.get_seasonal_crops()
        item_lower = item.lower()

        for crop in crops:
            crop_name = crop.get("crop", "").lower()
            if crop_name in item_lower or item_lower in crop_name:
                availability = crop.get(month_str, "").lower()

                if availability == "peak":
                    return {
                        "status": "peak",
                        "is_local": True,
                        "bonus": 15,
                        "reasoning": f"{item} is at peak season in NJ ({month_str})",
                    }
                elif availability == "available":
                    return {
                        "status": "available",
                        "is_local": True,
                        "bonus": 10,
                        "reasoning": f"{item} is locally available in NJ ({month_str})",
                    }
                elif availability == "storage":
                    return {
                        "status": "storage",
                        "is_local": True,
                        "bonus": 5,
                        "reasoning": f"{item} is available from NJ storage ({month_str})",
                    }

        # Not found or not in season
        return {
            "status": "imported",
            "is_local": False,
            "bonus": 0,
            "reasoning": f"{item} is likely imported (not in NJ season for {month_str})",
        }

    def get_in_season_now(self) -> list[str]:
        """Get list of produce currently in season in NJ."""
        crops = self.store.get_in_season_now()
        return [c.get("crop", "") for c in crops]

    # =========================================================================
    # Packaging Methods
    # =========================================================================

    def get_packaging_signal(self, packaging_text: str) -> dict:
        """
        Analyze packaging for sustainability signals.

        Args:
            packaging_text: Description of packaging (e.g., "plastic clamshell")

        Returns:
            {
                "score": int (-10 to +10),
                "signals": list of detected signals,
                "reasoning": str,
            }
        """
        text_lower = packaging_text.lower()
        signals = []
        score = 0

        # Positive signals
        if "glass" in text_lower:
            signals.append("glass_recyclable")
            score += 5
        if "cardboard" in text_lower or "paper" in text_lower:
            signals.append("paper_recyclable")
            score += 3
        if "compostable" in text_lower:
            signals.append("compostable")
            score += 7
        if "bulk" in text_lower or "no packaging" in text_lower:
            signals.append("minimal_packaging")
            score += 10

        # Negative signals
        if "plastic" in text_lower and "recyclable" not in text_lower:
            signals.append("plastic_non_recyclable")
            score -= 5
        if "styrofoam" in text_lower or "polystyrene" in text_lower:
            signals.append("styrofoam")
            score -= 10
        if "clamshell" in text_lower:
            signals.append("clamshell_plastic")
            score -= 3

        reasoning = f"Packaging: {', '.join(signals) if signals else 'no signals detected'}"

        return {
            "score": max(-10, min(10, score)),  # Clamp to -10 to +10
            "signals": signals,
            "reasoning": reasoning,
        }

    # =========================================================================
    # Brand Methods
    # =========================================================================

    def get_brand_signals(self, brand: str) -> dict:
        """
        Get known signals about a brand.

        Args:
            brand: Brand name

        Returns:
            {
                "is_local": bool or None,
                "is_organic_certified": bool or None,
                "is_coop": bool or None,
                "trust_level": str or None,
                "signals": list of known signals,
            }
        """
        # Check regional sources for brand match
        sources = self.store.get_regional_sources()
        brand_lower = brand.lower()

        for source in sources:
            keywords = source.get("source_keywords", "").lower()
            name = source.get("source_name", "").lower()

            if brand_lower in keywords or brand_lower in name:
                return {
                    "is_local": source.get("state") in ["NJ", "PA", "NY"],
                    "is_organic_certified": "organic" in source.get("certification_type", "").lower(),
                    "is_coop": "coop" in source.get("certification_type", "").lower(),
                    "trust_level": source.get("trust_level"),
                    "signals": [f"Found in regional sources: {source.get('source_name')}"],
                }

        # Unknown brand
        return {
            "is_local": None,
            "is_organic_certified": None,
            "is_coop": None,
            "trust_level": None,
            "signals": [],
        }

    # =========================================================================
    # Store Methods
    # =========================================================================

    def get_stores(self, delivery_only: bool = False) -> list[dict]:
        """Get stores serving Middlesex County."""
        return self.store.get_stores(serves_middlesex=True, delivery_only=delivery_only)

    def get_store_keywords(self) -> dict[str, str]:
        """Get mapping of store keywords to store names."""
        stores = self.get_stores()
        keywords = {}
        for s in stores:
            name = s.get("store_name", "")
            for kw in s.get("store_keywords", "").split(";"):
                kw = kw.strip().lower()
                if kw:
                    keywords[kw] = name
            keywords[name.lower()] = name
        return keywords

    # =========================================================================
    # Metadata Methods
    # =========================================================================

    def get_data_freshness(self) -> dict:
        """Get freshness info for all data sources."""
        return self.store.get_refresh_info()

    def is_data_stale(self, table: str = "recalls") -> bool:
        """Check if specific data is stale."""
        thresholds = {
            "recalls": 24,
            "ewg": 8760,
            "stores": 720,
            "crops": 8760,
            "sources": 2160,
        }
        return self.store.is_stale(table, thresholds.get(table, 24))


def get_facts() -> FactsGateway:
    """Get the singleton facts gateway instance."""
    global _facts_instance
    if _facts_instance is None:
        _facts_instance = FactsGateway()
    return _facts_instance
