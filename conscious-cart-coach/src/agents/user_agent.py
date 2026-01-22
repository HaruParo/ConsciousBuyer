"""
User History Agent - tracks purchases and learns preferences

Responsibilities:
- Track purchase history per user
- Identify personal staples (3x+ purchases)
- Learn dietary preferences and restrictions
- Provide user context for personalized recommendations
"""

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from .base_agent import DataAgent


# Threshold for promoting an item to "personal staple"
STAPLE_THRESHOLD = 3


class UserHistoryAgent(DataAgent):
    """Agent that tracks user purchases and learns preferences."""

    def __init__(self, data_dir: Path, user_id: str = "default"):
        super().__init__(f"user_{user_id}", data_dir)
        self.user_id = user_id
        self.purchases_path = data_dir / f"user_{user_id}_purchases.csv"
        self.preferences_path = data_dir / f"user_{user_id}_preferences.json"
        self._load_history()

    def _load_history(self):
        """Load user purchase history and preferences."""
        self.purchases = self.read_csv(self.purchases_path)
        self._load_preferences()
        self._compute_staples()

    def _load_preferences(self):
        """Load user preferences from JSON."""
        import json

        if self.preferences_path.exists():
            with open(self.preferences_path) as f:
                self.preferences = json.load(f)
        else:
            self.preferences = {
                "dietary": [],  # e.g., ["vegetarian", "lactose-intolerant"]
                "tier_preference": None,  # e.g., "balanced"
                "organic_preference": "flexible",  # "always", "dirty_dozen_only", "flexible", "never"
                "local_preference": False,
                "cuisine_preferences": [],  # e.g., ["asian", "mediterranean"]
                "avoid_categories": [],  # e.g., ["produce_peppers"] for allergy
            }

    def _compute_staples(self):
        """Compute personal staples from purchase history."""
        # Count purchases by product
        product_counts = Counter()
        category_counts = Counter()

        for purchase in self.purchases:
            product_name = purchase.get("product_name", "")
            category = purchase.get("category", "")

            if product_name:
                product_counts[product_name] += 1
            if category:
                category_counts[category] += 1

        # Identify staples (3x+ threshold)
        self.personal_staples = {
            product: count for product, count in product_counts.items()
            if count >= STAPLE_THRESHOLD
        }

        self.frequent_categories = {
            category: count for category, count in category_counts.items()
            if count >= STAPLE_THRESHOLD
        }

        # Update stats
        self.stats["total_purchases"] = len(self.purchases)
        self.stats["personal_staples_count"] = len(self.personal_staples)
        self.stats["frequent_categories_count"] = len(self.frequent_categories)

    def query(
        self,
        category: str | None = None,
        product_name: str | None = None,
        get_staples: bool = False,
        get_preferences: bool = False,
        **kwargs
    ) -> dict[str, Any]:
        """
        Query user history and preferences.

        Args:
            category: Get history for specific category
            product_name: Check if specific product is a staple
            get_staples: Return all personal staples
            get_preferences: Return user preferences

        Returns:
            Dict with user context for recommendations
        """
        result = {
            "user_id": self.user_id,
            "is_personal_staple": False,
            "purchase_count": 0,
            "staples": {},
            "preferences": {},
            "recommendations": [],
        }

        # Check if product is a personal staple
        if product_name:
            count = sum(
                1 for p in self.purchases
                if p.get("product_name", "").lower() == product_name.lower()
            )
            result["purchase_count"] = count
            result["is_personal_staple"] = count >= STAPLE_THRESHOLD

            if result["is_personal_staple"]:
                result["recommendations"].append(
                    f"'{product_name}' is a personal staple ({count}x purchased)"
                )

        # Check category frequency
        if category:
            category_count = sum(
                1 for p in self.purchases
                if p.get("category") == category
            )
            result["category_frequency"] = category_count

            # Get favorite products in this category
            category_products = Counter()
            for p in self.purchases:
                if p.get("category") == category:
                    category_products[p.get("product_name", "")] += 1

            if category_products:
                favorite = category_products.most_common(1)[0]
                result["category_favorite"] = {
                    "product_name": favorite[0],
                    "count": favorite[1],
                }

        # Return all staples if requested
        if get_staples:
            result["staples"] = self.personal_staples
            result["frequent_categories"] = self.frequent_categories

        # Return preferences if requested
        if get_preferences:
            result["preferences"] = self.preferences

        result["freshness"] = self.get_freshness()
        return result

    def is_personal_staple(self, product_name: str) -> bool:
        """Quick check if a product is a personal staple."""
        # Check exact match first
        if product_name in self.personal_staples:
            return True

        # Check case-insensitive partial match
        product_lower = product_name.lower()
        for staple in self.personal_staples:
            if staple.lower() in product_lower or product_lower in staple.lower():
                return True

        return False

    def get_tier_recommendation(self) -> str | None:
        """Get recommended tier based on user's historical choices."""
        tier_counts = Counter()

        for purchase in self.purchases:
            tier = purchase.get("tier_selected")
            if tier:
                tier_counts[tier] += 1

        if tier_counts:
            return tier_counts.most_common(1)[0][0]
        return self.preferences.get("tier_preference")

    def learn(self, interaction: dict) -> None:
        """
        Learn from user interaction.

        Interaction types:
        - "purchase": User purchased a product
        - "preference_update": User updated preferences
        - "tier_selected": User chose a tier
        - "product_rejected": User rejected a recommendation
        """
        interaction_type = interaction.get("type")
        timestamp = datetime.now().isoformat()

        if interaction_type == "purchase":
            self._record_purchase(interaction, timestamp)

        elif interaction_type == "preference_update":
            self._update_preferences(interaction)

        elif interaction_type == "tier_selected":
            self._record_tier_selection(interaction, timestamp)

        elif interaction_type == "product_rejected":
            self._record_rejection(interaction, timestamp)

        self._save_metadata()

    def _record_purchase(self, interaction: dict, timestamp: str):
        """Record a purchase to history."""
        row = {
            "timestamp": timestamp,
            "category": interaction.get("category"),
            "product_name": interaction.get("product_name"),
            "brand": interaction.get("brand"),
            "price": interaction.get("price"),
            "tier_selected": interaction.get("tier"),
            "was_recommendation": interaction.get("was_recommendation", False),
        }

        self.append_csv(self.purchases_path, row)
        self.purchases.append(row)

        # Recompute staples
        self._compute_staples()

        # Check if this created a new staple
        product_name = interaction.get("product_name", "")
        if product_name in self.personal_staples:
            count = self.personal_staples[product_name]
            if count == STAPLE_THRESHOLD:
                # New staple detected!
                self.stats["new_staple_detected"] = product_name

    def _update_preferences(self, interaction: dict):
        """Update user preferences."""
        import json

        for key, value in interaction.items():
            if key in self.preferences and key != "type":
                self.preferences[key] = value

        # Save preferences
        with open(self.preferences_path, "w") as f:
            json.dump(self.preferences, f, indent=2)

    def _record_tier_selection(self, interaction: dict, timestamp: str):
        """Record tier selection for learning."""
        # This feeds back to ProductDataAgent for confidence scoring
        pass

    def _record_rejection(self, interaction: dict, timestamp: str):
        """Record when user rejects a recommendation."""
        # Track rejections to avoid recommending same items
        if not hasattr(self, "rejections"):
            self.rejections = []

        self.rejections.append({
            "timestamp": timestamp,
            "category": interaction.get("category"),
            "product_name": interaction.get("product_name"),
            "reason": interaction.get("reason"),
        })

    def refresh(self) -> None:
        """Refresh user data from storage."""
        self._load_history()
        self.last_updated = datetime.now()
        self._save_metadata()

    def get_context_for_facts_pack(self) -> dict:
        """
        Get user context formatted for facts_pack.py.

        Returns dict with user_context structure expected by decision engine.
        """
        tier_pref = self.get_tier_recommendation()

        return {
            "user_id": self.user_id,
            "tier_preference": tier_pref,
            "personal_staples": list(self.personal_staples.keys()),
            "frequent_categories": list(self.frequent_categories.keys()),
            "dietary": self.preferences.get("dietary", []),
            "organic_preference": self.preferences.get("organic_preference", "flexible"),
            "local_preference": self.preferences.get("local_preference", False),
            "cuisine_preferences": self.preferences.get("cuisine_preferences", []),
            "avoid_categories": self.preferences.get("avoid_categories", []),
        }

    def should_promote_specialty(
        self,
        product_name: str,
        category: str,
        is_in_season: bool = False
    ) -> tuple[bool, str]:
        """
        Determine if a specialty item should be promoted for this user.

        Args:
            product_name: Product to check
            category: Product category
            is_in_season: Whether product is in peak season

        Returns:
            Tuple of (should_promote, reason)
        """
        reasons = []

        # Check if it's a personal staple
        if self.is_personal_staple(product_name):
            reasons.append(f"personal staple ({self.personal_staples.get(product_name, 0)}x)")

        # Check cuisine preferences
        cuisine_keywords = {
            "asian": ["daikon", "kabocha", "shishito", "miso", "tofu"],
            "mediterranean": ["olive", "feta", "hummus"],
            "latin": ["tomatillo", "plantain", "yuca"],
        }

        for cuisine in self.preferences.get("cuisine_preferences", []):
            keywords = cuisine_keywords.get(cuisine, [])
            if any(kw in product_name.lower() for kw in keywords):
                reasons.append(f"matches {cuisine} cuisine preference")

        # Seasonality boost
        if is_in_season:
            reasons.append("in peak season")

        should_promote = len(reasons) > 0
        reason = " + ".join(reasons) if reasons else "no promotion criteria met"

        return should_promote, reason
