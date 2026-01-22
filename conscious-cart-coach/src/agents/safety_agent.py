"""
DEPRECATED: Legacy Safety Data Agent

This module loads CSV files directly which duplicates the facts store.
Use safety_agent_v2.py instead, which queries the SQLite facts store.

To migrate:
    # Old (deprecated)
    from src.agents.safety_agent import SafetyDataAgent
    agent = SafetyDataAgent(data_dir)

    # New (use this)
    from src.agents.safety_agent_v2 import SafetyAgent
    agent = SafetyAgent()

This file is kept for backward compatibility but will raise a warning.
"""

import warnings

warnings.warn(
    "safety_agent.py is deprecated. Use safety_agent_v2.py which queries the facts store.",
    DeprecationWarning,
    stacklevel=2
)

# Original docstring for reference:
# Safety Data Agent - maintains FDA recalls and EWG lists
# Data loaded from CSV files:
# - data/flags/fda_recalls.csv - FDA Food Recall data
# - data/flags/ewg_lists.csv - EWG Dirty Dozen / Clean Fifteen
#
# Responsibilities:
# - Track FDA recalls and advisories
# - Enforce EWG Dirty Dozen/Clean Fifteen rules
# - Monitor recall patterns by category
# - Provide safety queries for decision engine

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .base_agent import DataAgent

# Data file paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
FDA_RECALLS_CSV = DATA_DIR / "flags" / "fda_recalls.csv"
STORES_CSV = DATA_DIR / "stores" / "nj_middlesex_stores.csv"

# Import EWG lists from existing module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from data_processing.ewg_lists import (
        is_dirty_dozen,
        is_clean_fifteen,
        get_ewg_classification,
        DIRTY_DOZEN_ITEMS,
        CLEAN_FIFTEEN_ITEMS,
        get_ewg_data_info,
    )
    EWG_MODULE_AVAILABLE = True
except ImportError:
    EWG_MODULE_AVAILABLE = False
    # Fallback definitions if module not available
    DIRTY_DOZEN_ITEMS = {
        "strawberries", "spinach", "kale", "grapes", "peaches", "pears",
        "nectarines", "apples", "bell peppers", "cherries", "blueberries", "green beans"
    }
    CLEAN_FIFTEEN_ITEMS = {
        "avocados", "corn", "pineapple", "onions", "papaya", "peas",
        "asparagus", "honeydew", "kiwi", "cabbage", "watermelon", "mushrooms",
        "mangoes", "sweet potatoes", "carrots"
    }

    def is_dirty_dozen(name: str) -> bool:
        name_lower = name.lower()
        return any(item in name_lower for item in DIRTY_DOZEN_ITEMS)

    def is_clean_fifteen(name: str) -> bool:
        name_lower = name.lower()
        return any(item in name_lower for item in CLEAN_FIFTEEN_ITEMS)

    def get_ewg_classification(name: str) -> dict:
        if is_dirty_dozen(name):
            return {"list": "dirty_dozen", "organic_required": True}
        elif is_clean_fifteen(name):
            return {"list": "clean_fifteen", "organic_optional": True}
        return {"list": "middle", "organic_required": False, "organic_optional": False}

    def get_ewg_data_info() -> dict:
        return {"source": "Fallback data", "trust_level": "hardcoded"}


class SafetyDataAgent(DataAgent):
    """
    Agent that maintains safety flags, recalls, and EWG compliance.

    Data sources:
    - FDA Recalls: data/flags/fda_recalls.csv (refresh daily)
    - EWG Lists: data/flags/ewg_lists.csv (refresh annually March/April)
    - Product Flags: data/flags/product_flags.json (manual updates)

    FDA API: https://api.fda.gov/food/enforcement.json
    EWG Source: https://www.ewg.org/foodnews/
    """

    # EWG list version tracking
    EWG_LIST_VERSION = "2024"  # Update annually when EWG releases new list
    EWG_RELEASE_MONTH = 3  # March - typical release month

    def __init__(self, data_dir: Path):
        super().__init__("safety", data_dir)
        self.flags_path = data_dir / "product_flags.json"
        self.recall_history_path = data_dir / "recall_history.csv"
        self.fda_recalls_path = FDA_RECALLS_CSV
        self.stores_path = STORES_CSV
        self._load_flags()
        self._load_fda_recalls()
        self._load_stores()
        self._check_ewg_version()

    def _load_fda_recalls(self):
        """Load FDA recalls from CSV file."""
        self.fda_recalls = []

        if not self.fda_recalls_path.exists():
            return

        with open(self.fda_recalls_path, newline="", encoding="utf-8") as f:
            # Skip comment lines
            lines = [line for line in f if not line.startswith("#")]

        if not lines:
            return

        reader = csv.DictReader(lines)
        for row in reader:
            # Only include ongoing recalls
            if row.get("status", "").lower() == "ongoing":
                self.fda_recalls.append({
                    "recall_id": row.get("recall_id", ""),
                    "status": row.get("status", ""),
                    "classification": row.get("classification", ""),
                    "product_description": row.get("product_description", ""),
                    "reason": row.get("reason_for_recall", ""),
                    "contaminant": row.get("contaminant", ""),
                    "firm": row.get("recalling_firm", ""),
                    "city": row.get("city", ""),
                    "state": row.get("state", ""),
                    "distribution": row.get("distribution_pattern", ""),
                    "date": row.get("recall_initiation_date", ""),
                    "affected_categories": [c.strip() for c in row.get("affected_categories", "").split(",") if c.strip()],
                    "affected_brands": [b.strip() for b in row.get("affected_brands", "").split(",") if b.strip()],
                    "affected_upcs": [u.strip() for u in row.get("affected_upcs", "").split(",") if u.strip()],
                    "voluntary": row.get("voluntary", "Yes") == "Yes",
                    "source_url": row.get("source_url", ""),
                })

        self.stats["fda_recalls_loaded"] = len(self.fda_recalls)
        self.stats["class_i_recalls"] = sum(1 for r in self.fda_recalls if r["classification"] == "Class I")
        self.stats["class_ii_recalls"] = sum(1 for r in self.fda_recalls if r["classification"] == "Class II")

    def _load_stores(self):
        """Load store data from CSV file for recall filtering."""
        self.stores = []
        self.store_keywords = {}  # keyword -> store_name mapping

        if not self.stores_path.exists():
            return

        with open(self.stores_path, newline="", encoding="utf-8") as f:
            lines = [line for line in f if not line.startswith("#")]

        if not lines:
            return

        reader = csv.DictReader(lines)
        for row in reader:
            store_name = row.get("store_name", "")
            serves_middlesex = row.get("serves_middlesex", "").lower() == "yes"

            if serves_middlesex:
                store_data = {
                    "name": store_name,
                    "keywords": [k.strip().lower() for k in row.get("store_keywords", "").split(";") if k.strip()],
                    "type": row.get("store_type", ""),
                    "delivery": row.get("delivery_available", "").lower() == "yes",
                    "notes": row.get("notes", ""),
                }
                self.stores.append(store_data)

                # Build keyword lookup
                for keyword in store_data["keywords"]:
                    self.store_keywords[keyword] = store_name
                # Also add store name as keyword
                self.store_keywords[store_name.lower()] = store_name

        self.stats["stores_loaded"] = len(self.stores)

    def _load_flags(self):
        """Load product flags from JSON."""
        if self.flags_path.exists():
            with open(self.flags_path) as f:
                self.flags = json.load(f)
        else:
            self.flags = {}

        # Count active recalls from JSON flags
        recall_count = 0
        for category_flags in self.flags.values():
            for flag in category_flags:
                if flag.get("type", "").lower() == "recall":
                    recall_count += 1

        self.stats["active_recalls"] = recall_count
        self.stats["categories_with_flags"] = len(self.flags)

    def _check_ewg_version(self):
        """Check if EWG list may need updating (annual in March/April)."""
        current_year = datetime.now().year
        current_month = datetime.now().month

        # After March, we should have the current year's list
        expected_version = str(current_year) if current_month >= self.EWG_RELEASE_MONTH else str(current_year - 1)

        if self.EWG_LIST_VERSION != expected_version:
            self.stats["ewg_update_needed"] = True
            self.stats["ewg_current_version"] = self.EWG_LIST_VERSION
            self.stats["ewg_expected_version"] = expected_version
        else:
            self.stats["ewg_update_needed"] = False
            self.stats["ewg_version"] = self.EWG_LIST_VERSION

    def query(
        self,
        category: str | None = None,
        product_name: str | None = None,
        flag_type: str | None = None,
        include_ewg: bool = True,
        **kwargs
    ) -> dict[str, Any]:
        """
        Query safety information for a category or product.

        Args:
            category: Category to check (e.g., "produce_greens")
            product_name: Specific product name to check
            flag_type: Filter by flag type ("recall", "info", "seasonal")
            include_ewg: Include EWG classification

        Returns:
            Dict with safety info, flags, and EWG classification
        """
        result = {
            "flags": [],
            "fda_recalls": [],
            "ewg": None,
            "organic_required": False,
            "has_active_recall": False,
            "recommendations": [],
        }

        # Get flags for category from JSON
        if category and category in self.flags:
            flags = self.flags[category]

            if flag_type:
                flags = [f for f in flags if f.get("type", "").lower() == flag_type.lower()]

            result["flags"] = flags

            # Check for active recalls in JSON flags
            for flag in flags:
                if flag.get("type", "").lower() == "recall":
                    result["has_active_recall"] = True
                    result["recommendations"].append(
                        f"RECALL: {flag.get('title', 'Unknown')} - {flag.get('recommendation', 'Check product')}"
                    )

        # Check FDA recalls from CSV
        if category:
            for recall in self.fda_recalls:
                affected_cats = [c.strip() for c in recall.get("affected_categories", [])]
                if category in affected_cats or any(category in c for c in affected_cats):
                    result["fda_recalls"].append(recall)
                    result["has_active_recall"] = True
                    severity = recall.get("classification", "")
                    result["recommendations"].append(
                        f"FDA {severity}: {recall.get('product_description', '')} - {recall.get('reason', '')}"
                    )

        # Get EWG classification
        if include_ewg and (category or product_name):
            name_to_check = product_name or category
            ewg = get_ewg_classification(name_to_check)
            result["ewg"] = ewg

            if ewg.get("organic_required") or ewg.get("list") == "dirty_dozen":
                result["organic_required"] = True
                result["recommendations"].append(
                    f"EWG Dirty Dozen: Organic strongly recommended for {name_to_check}"
                )
            elif ewg.get("list") == "clean_fifteen":
                result["recommendations"].append(
                    f"EWG Clean Fifteen: Conventional acceptable for {name_to_check}"
                )

        result["freshness"] = self.get_freshness()
        return result

    def check_tier_safety(
        self,
        category: str,
        tier: str,
        has_organic: bool
    ) -> dict[str, Any]:
        """
        Check if a tier selection is safe.

        Args:
            category: Product category
            tier: Selected tier ("cheaper", "balanced", "conscious")
            has_organic: Whether the tier option is organic

        Returns:
            Dict with safety assessment
        """
        result = {
            "is_safe": True,
            "warnings": [],
            "errors": [],
        }

        # Check EWG compliance
        ewg = get_ewg_classification(category)

        if ewg.get("list") == "dirty_dozen":
            if tier == "cheaper" and not has_organic:
                result["warnings"].append(
                    f"Dirty Dozen item '{category}' at 'cheaper' tier without organic - "
                    "consider upgrading tier for health"
                )
            if not has_organic:
                result["warnings"].append(
                    f"EWG recommends organic for {category} (Dirty Dozen)"
                )

        # Check for active recalls
        if category in self.flags:
            for flag in self.flags[category]:
                if flag.get("type", "").lower() == "recall":
                    affected_tiers = flag.get("affected_tiers", [])
                    severity = flag.get("severity", "")

                    if not affected_tiers or tier in affected_tiers:
                        if severity == "Class I":
                            result["is_safe"] = False
                            result["errors"].append(
                                f"Class I Recall affects this tier: {flag.get('title')}"
                            )
                        else:
                            result["warnings"].append(
                                f"Recall ({severity}): {flag.get('title')}"
                            )

        return result

    def get_recall_patterns(self) -> dict[str, Any]:
        """Analyze recall patterns across categories."""
        patterns = {}

        for category, flags in self.flags.items():
            recall_count = sum(1 for f in flags if f.get("type", "").lower() == "recall")
            if recall_count > 0:
                patterns[category] = {
                    "recall_count": recall_count,
                    "risk_level": "high" if recall_count >= 2 else "moderate",
                }

        return patterns

    def learn(self, interaction: dict) -> None:
        """
        Learn from safety-related interaction.

        Interaction types:
        - "recall_added": New recall discovered
        - "recall_resolved": Recall ended
        - "ewg_updated": EWG list updated (annual)
        """
        interaction_type = interaction.get("type")
        timestamp = datetime.now().isoformat()

        if interaction_type == "recall_added":
            self._add_recall(interaction, timestamp)

        elif interaction_type == "recall_resolved":
            self._resolve_recall(interaction, timestamp)

        self._save_metadata()

    def _add_recall(self, interaction: dict, timestamp: str):
        """Add a new recall flag."""
        category = interaction.get("category")
        if not category:
            return

        if category not in self.flags:
            self.flags[category] = []

        new_flag = {
            "type": "recall",
            "title": interaction.get("title"),
            "description": interaction.get("description"),
            "severity": interaction.get("severity", "Class II"),
            "affected_tiers": interaction.get("affected_tiers", []),
            "affected_regions": interaction.get("affected_regions", []),
            "recommendation": interaction.get("recommendation"),
            "source_url": interaction.get("source_url"),
            "added_date": timestamp,
        }

        self.flags[category].append(new_flag)
        self._save_flags()

        # Log to history
        self.append_csv(self.recall_history_path, {
            "timestamp": timestamp,
            "action": "added",
            "category": category,
            "title": interaction.get("title"),
            "severity": interaction.get("severity"),
        })

    def _resolve_recall(self, interaction: dict, timestamp: str):
        """Mark a recall as resolved."""
        category = interaction.get("category")
        title = interaction.get("title")

        if category in self.flags:
            self.flags[category] = [
                f for f in self.flags[category]
                if not (f.get("type") == "recall" and f.get("title") == title)
            ]
            self._save_flags()

            # Log to history
            self.append_csv(self.recall_history_path, {
                "timestamp": timestamp,
                "action": "resolved",
                "category": category,
                "title": title,
                "severity": "",
            })

    def _save_flags(self):
        """Save flags to JSON file."""
        with open(self.flags_path, "w") as f:
            json.dump(self.flags, f, indent=2)

    def refresh(self) -> None:
        """Refresh safety data from CSV files and JSON."""
        # Reload from files
        self._load_flags()
        self._load_fda_recalls()
        self._load_stores()
        self._check_ewg_version()
        self.last_updated = datetime.now()
        self._save_metadata()

    def get_safety_for_facts_pack(self, category: str) -> dict:
        """
        Get safety data formatted for facts_pack.py.

        Returns dict with flags structure expected by decision engine.
        """
        safety = self.query(category=category, include_ewg=True)

        return {
            "category": category,
            "flags": safety["flags"],
            "fda_recalls": safety["fda_recalls"],
            "ewg_classification": safety["ewg"],
            "organic_required": safety["organic_required"],
            "has_active_recall": safety["has_active_recall"],
            "recommendations": safety["recommendations"],
        }

    def get_data_sources_info(self) -> dict:
        """
        Get information about data sources for transparency.

        Returns:
            Dict with source info and file paths
        """
        ewg_info = get_ewg_data_info() if EWG_MODULE_AVAILABLE else {}

        return {
            "fda_recalls": {
                "source": "FDA Food Recall API",
                "url": "https://api.fda.gov/food/enforcement.json",
                "trust_level": "official_government",
                "data_file": str(self.fda_recalls_path),
                "active_recalls": len(self.fda_recalls),
                "refresh_schedule": "Daily",
            },
            "ewg_lists": ewg_info,
            "product_flags": {
                "data_file": str(self.flags_path),
                "categories_with_flags": len(self.flags),
            },
            "stores": {
                "data_file": str(self.stores_path),
                "stores_serving_middlesex": len(self.stores),
                "purpose": "Filter recalls by local retailers",
            },
        }

    def get_all_active_recalls(self) -> list[dict]:
        """
        Get all active recalls from both CSV and JSON sources.

        Returns:
            List of all active recall dicts
        """
        recalls = []

        # FDA recalls from CSV
        for recall in self.fda_recalls:
            recalls.append({
                "source": "FDA CSV",
                "id": recall.get("recall_id"),
                "classification": recall.get("classification"),
                "product": recall.get("product_description"),
                "reason": recall.get("reason"),
                "firm": recall.get("firm"),
                "date": recall.get("date"),
            })

        # Recalls from JSON flags
        for category, flags in self.flags.items():
            for flag in flags:
                if flag.get("type", "").lower() == "recall":
                    recalls.append({
                        "source": "JSON flags",
                        "category": category,
                        "title": flag.get("title"),
                        "severity": flag.get("severity"),
                        "added_date": flag.get("added_date"),
                    })

        return recalls

    def check_product_recall(
        self,
        brand: str = "",
        upc: str = "",
        product_name: str = "",
    ) -> dict | None:
        """
        Check if a specific product is affected by an active recall.

        Args:
            brand: Brand name to check
            upc: UPC barcode to check
            product_name: Product name to check

        Returns:
            Recall dict if found, None otherwise
        """
        brand_lower = brand.lower()
        product_lower = product_name.lower()

        for recall in self.fda_recalls:
            # Check UPC match (exact)
            if upc and upc in recall.get("affected_upcs", []):
                return recall

            # Check brand match
            affected_brands = [b.lower() for b in recall.get("affected_brands", [])]
            if brand_lower and any(brand_lower in b or b in brand_lower for b in affected_brands):
                return recall

            # Check product description match
            recall_product = recall.get("product_description", "").lower()
            if product_lower and (product_lower in recall_product or recall_product in product_lower):
                return recall

        return None

    def get_recalls_for_region(self, state: str = "NJ") -> list[dict]:
        """
        Get recalls that affect a specific state/region.

        Args:
            state: State abbreviation (e.g., "NJ", "NY")

        Returns:
            List of recalls affecting that region
        """
        state_upper = state.upper()
        regional_recalls = []

        for recall in self.fda_recalls:
            distribution = recall.get("distribution", "").upper()
            # Check if nationwide or specific state mentioned
            if "NATIONWIDE" in distribution or state_upper in distribution:
                regional_recalls.append(recall)
            # Check for regional patterns
            elif state_upper == "NJ" and any(region in distribution for region in ["NORTHEAST", "MID-ATLANTIC", "EAST COAST"]):
                regional_recalls.append(recall)

        return regional_recalls

    def get_contaminant_summary(self) -> dict[str, int]:
        """
        Get summary of contaminants in active recalls.

        Returns:
            Dict mapping contaminant type to count
        """
        contaminants = {}
        for recall in self.fda_recalls:
            contaminant = recall.get("contaminant", "Unknown")
            contaminants[contaminant] = contaminants.get(contaminant, 0) + 1
        return contaminants

    def get_middlesex_stores(self) -> list[dict]:
        """
        Get all stores serving Middlesex County.

        Returns:
            List of store dicts with name, type, delivery info
        """
        return self.stores

    def get_recalls_for_stores(
        self,
        user_stores: list[str] | None = None,
        include_nationwide: bool = True,
    ) -> list[dict]:
        """
        Get recalls filtered by stores the user shops at.

        This improves recall accuracy by only showing recalls from
        stores that serve Middlesex County and that the user frequents.

        Args:
            user_stores: List of store names user shops at. If None, uses all Middlesex stores.
            include_nationwide: Include nationwide recalls (recommended True)

        Returns:
            List of recalls relevant to user's stores
        """
        relevant_recalls = []

        # Build set of relevant store keywords
        if user_stores:
            # User specified stores - normalize to lowercase
            store_set = set(s.lower() for s in user_stores)
        else:
            # Use all Middlesex stores
            store_set = set(self.store_keywords.keys())

        for recall in self.fda_recalls:
            distribution = recall.get("distribution", "")
            distribution_lower = distribution.lower()

            # Always include nationwide recalls if flag set
            if include_nationwide and "nationwide" in distribution_lower:
                relevant_recalls.append(recall)
                continue

            # Check if recall distribution mentions any user stores
            for keyword in store_set:
                if keyword in distribution_lower:
                    relevant_recalls.append(recall)
                    break

            # Check for NJ/Northeast regional patterns
            if "nj" in distribution_lower or "new jersey" in distribution_lower:
                if recall not in relevant_recalls:
                    relevant_recalls.append(recall)
            elif any(region in distribution_lower for region in ["northeast", "mid-atlantic", "east coast"]):
                if recall not in relevant_recalls:
                    relevant_recalls.append(recall)

        return relevant_recalls

    def check_recall_for_store(self, recall: dict, store_name: str) -> bool:
        """
        Check if a specific recall affects a specific store.

        Args:
            recall: Recall dict from fda_recalls
            store_name: Store name to check

        Returns:
            True if recall affects the store
        """
        distribution = recall.get("distribution", "").lower()
        store_lower = store_name.lower()

        # Nationwide affects all
        if "nationwide" in distribution:
            return True

        # Direct store mention
        if store_lower in distribution:
            return True

        # Check store keywords
        store_data = next((s for s in self.stores if s["name"].lower() == store_lower), None)
        if store_data:
            for keyword in store_data["keywords"]:
                if keyword in distribution:
                    return True

        return False

    def get_recalls_summary_for_user(
        self,
        user_stores: list[str] | None = None,
        state: str = "NJ",
    ) -> dict:
        """
        Get a comprehensive recall summary tailored for a Middlesex County user.

        Args:
            user_stores: Optional list of stores user frequents
            state: State abbreviation (default NJ)

        Returns:
            Dict with categorized recalls and recommendations
        """
        # Get recalls by different filters
        all_regional = self.get_recalls_for_region(state)
        store_filtered = self.get_recalls_for_stores(user_stores)

        # Categorize by severity
        class_i = [r for r in store_filtered if r.get("classification") == "Class I"]
        class_ii = [r for r in store_filtered if r.get("classification") == "Class II"]
        class_iii = [r for r in store_filtered if r.get("classification") == "Class III"]

        # Build recommendations
        recommendations = []
        if class_i:
            recommendations.append(f"URGENT: {len(class_i)} Class I recall(s) - serious health risk, avoid these products")
        if class_ii:
            recommendations.append(f"CAUTION: {len(class_ii)} Class II recall(s) - check your pantry")

        return {
            "total_relevant_recalls": len(store_filtered),
            "class_i_count": len(class_i),
            "class_ii_count": len(class_ii),
            "class_iii_count": len(class_iii),
            "class_i_recalls": class_i,
            "class_ii_recalls": class_ii,
            "class_iii_recalls": class_iii,
            "recommendations": recommendations,
            "stores_checked": user_stores or [s["name"] for s in self.stores],
            "contaminants": self.get_contaminant_summary(),
        }
