"""
Agent Orchestrator - coordinates all data agents for the decision engine.

This is the main entry point for the hybrid multi-agent architecture.
It queries all agents and assembles the facts_pack for the LLM decision engine.

Supports multi-dimensional impact scoring:
- Health (EWG, recalls)
- Environmental (local, carbon)
- Social (fair trade, labor)
- Packaging (recyclability)
- Animal Welfare (certifications)
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from .product_agent import ProductDataAgent
from .safety_agent import SafetyDataAgent
from .user_agent import UserHistoryAgent

# Import impact scoring
import sys
_data_processing_path = Path(__file__).parent.parent / "data_processing"
if str(_data_processing_path) not in sys.path:
    sys.path.insert(0, str(_data_processing_path.parent))

try:
    from data_processing.impact_scoring import (
        score_product,
        compare_products,
        PREFERENCE_PRESETS,
        DEFAULT_WEIGHTS,
    )
    IMPACT_SCORING_AVAILABLE = True
except ImportError:
    IMPACT_SCORING_AVAILABLE = False
    DEFAULT_WEIGHTS = None
    PREFERENCE_PRESETS = None

# Import seasonal/regional module
try:
    from data_processing.seasonal_regional import (
        get_seasonal_status,
        get_seasonal_recommendations,
        is_regional_source,
        DEFAULT_LOCATION,
    )
    SEASONAL_AVAILABLE = True
except ImportError:
    SEASONAL_AVAILABLE = False


class AgentOrchestrator:
    """
    Orchestrates multiple data agents to build facts_pack for decisions.

    The orchestrator:
    1. Initializes all agents with their data stores
    2. Coordinates queries across agents
    3. Assembles complete facts_pack for the decision engine
    4. Distributes learning signals back to appropriate agents
    """

    def __init__(self, data_dir: Path | str, user_id: str = "default"):
        """
        Initialize the orchestrator with all agents.

        Args:
            data_dir: Base directory for agent data stores
            user_id: User identifier for personalization
        """
        self.data_dir = Path(data_dir)
        self.user_id = user_id

        # Initialize agents
        self.product_agent = ProductDataAgent(self.data_dir / "alternatives")
        self.safety_agent = SafetyDataAgent(self.data_dir / "flags")
        self.user_agent = UserHistoryAgent(self.data_dir / "users", user_id)

        self.agents = {
            "product": self.product_agent,
            "safety": self.safety_agent,
            "user": self.user_agent,
        }

        # Impact scoring weights (can be customized per user)
        self.impact_weights = DEFAULT_WEIGHTS if IMPACT_SCORING_AVAILABLE else None

    def build_facts_pack(self, categories: list[str], store: str = "freshdirect") -> dict:
        """
        Build complete facts_pack by querying all agents.

        Args:
            categories: List of categories to include (e.g., ["produce_greens", "milk_whole"])
            store: Store identifier

        Returns:
            Complete facts_pack dict for decision engine
        """
        # Get current seasonal recommendations if available
        seasonal_context = None
        if SEASONAL_AVAILABLE:
            seasonal_context = get_seasonal_recommendations()

        facts_pack = {
            "store": store,
            "timestamp": datetime.now().isoformat(),
            "user_context": self.user_agent.get_context_for_facts_pack(),
            "location": {
                "state": DEFAULT_LOCATION.state if SEASONAL_AVAILABLE else "NJ",
                "county": DEFAULT_LOCATION.county if SEASONAL_AVAILABLE else "Middlesex",
                "local_radius_miles": DEFAULT_LOCATION.local_radius if SEASONAL_AVAILABLE else 100,
            },
            "seasonal_context": seasonal_context,
            "items": [],
            "agent_metadata": self._get_agent_metadata(),
        }

        for category in categories:
            item = self._build_category_item(category)
            facts_pack["items"].append(item)

        return facts_pack

    def _build_category_item(self, category: str) -> dict:
        """Build a single category item by querying all agents."""
        # Get product data
        product_data = self.product_agent.get_products_for_facts_pack(category)

        # Get safety data
        safety_data = self.safety_agent.get_safety_for_facts_pack(category)

        # Get user context for this category
        user_data = self.user_agent.query(category=category, get_preferences=True)

        # Check for specialty promotions with dynamic seasonality
        specialty_promotions = []
        for specialty in product_data.get("specialty_promotable", []):
            product_name = specialty.get("product_name", "")

            # Use dynamic seasonality if available, fallback to static text
            if SEASONAL_AVAILABLE:
                seasonal_status = get_seasonal_status(product_name, category)
                is_in_season = seasonal_status.is_in_season
                seasonal_info = seasonal_status.to_dict()
            else:
                is_in_season = "peak now" in specialty.get("seasonality", "").lower()
                seasonal_info = None

            should_promote, reason = self.user_agent.should_promote_specialty(
                product_name=product_name,
                category=category,
                is_in_season=is_in_season,
            )
            if should_promote:
                promotion = {
                    "product": specialty,
                    "reason": reason,
                }
                if seasonal_info:
                    promotion["seasonal_status"] = seasonal_info
                specialty_promotions.append(promotion)

        # Calculate impact scores for each alternative if available
        impact_scores = {}
        if IMPACT_SCORING_AVAILABLE:
            ewg = safety_data.get("ewg_classification")
            has_recall = safety_data.get("has_active_recall", False)

            for tier_name, alt_data in product_data.get("alternatives", {}).items():
                if alt_data:
                    # Build product dict for scoring
                    product_for_scoring = {
                        "product_name": alt_data.get("product_name", ""),
                        "brand": alt_data.get("brand", ""),
                        "certifications": ", ".join(alt_data.get("certifications", [])),
                        "notes": alt_data.get("why_this_tier", ""),
                    }
                    score = score_product(product_for_scoring, category, ewg, has_recall)
                    impact_scores[tier_name] = {
                        "dimensions": score.to_dict()["dimensions"],
                        "weighted_score": score.weighted_score(self.impact_weights),
                        "certifications_found": score.certifications_found,
                        "warnings": score.warnings,
                    }

        # Get category-level seasonal status
        category_seasonal = None
        if SEASONAL_AVAILABLE:
            category_seasonal = get_seasonal_status("", category).to_dict()

        # Assemble the item
        item = {
            "category": category,
            "alternatives": product_data.get("alternatives", {}),
            "flags": safety_data.get("flags", []),
            "ewg_classification": safety_data.get("ewg_classification"),
            "organic_required": safety_data.get("organic_required", False),
            "has_active_recall": safety_data.get("has_active_recall", False),
            "availability_issues": product_data.get("availability_issues", []),
            "specialty_promotions": specialty_promotions,
            "user_category_data": {
                "is_frequent_category": category in self.user_agent.frequent_categories,
                "category_favorite": user_data.get("category_favorite"),
            },
            "impact_scores": impact_scores if impact_scores else None,
            "seasonal_status": category_seasonal,
        }

        return item

    def _get_agent_metadata(self) -> dict:
        """Get metadata from all agents for transparency."""
        return {
            "product_agent": {
                "freshness": self.product_agent.get_freshness(),
                "stats": self.product_agent.stats,
            },
            "safety_agent": {
                "freshness": self.safety_agent.get_freshness(),
                "stats": self.safety_agent.stats,
            },
            "user_agent": {
                "freshness": self.user_agent.get_freshness(),
                "stats": self.user_agent.stats,
            },
        }

    def learn_from_decision(self, decision: dict, feedback: dict | None = None) -> None:
        """
        Distribute learning signals to appropriate agents.

        Args:
            decision: The decision output from the LLM
            feedback: Optional user feedback on the decision
        """
        category = decision.get("category")
        tier = decision.get("recommended_tier")

        # Product agent learns tier selection
        self.product_agent.learn({
            "type": "tier_selected",
            "category": category,
            "selected_tier": tier,
        })

        # User agent learns if there was a purchase
        if feedback and feedback.get("purchased"):
            self.user_agent.learn({
                "type": "purchase",
                "category": category,
                "product_name": feedback.get("product_name"),
                "brand": feedback.get("brand"),
                "price": feedback.get("price"),
                "tier": tier,
                "was_recommendation": True,
            })

        # If user rejected the recommendation
        if feedback and feedback.get("rejected"):
            self.user_agent.learn({
                "type": "product_rejected",
                "category": category,
                "product_name": feedback.get("product_name"),
                "reason": feedback.get("reason"),
            })

    def refresh_all_agents(self, force: bool = False) -> dict[str, str]:
        """
        Refresh data for all agents.

        Args:
            force: If True, refresh all agents regardless of schedule.
                   If False, only refresh agents that need it per schedule.

        Returns:
            Dict with refresh status for each agent
        """
        results = {}
        for name, agent in self.agents.items():
            try:
                if force or agent.needs_refresh():
                    agent.refresh()
                    results[name] = "refreshed"
                else:
                    results[name] = "skipped (not due)"
            except Exception as e:
                results[name] = f"error: {str(e)}"
        return results

    def get_refresh_schedules(self) -> dict[str, dict]:
        """
        Get refresh schedule info for all agents.

        Returns:
            Dict mapping agent name to schedule info
        """
        return {
            name: agent.get_refresh_schedule()
            for name, agent in self.agents.items()
        }

    def check_data_freshness(self) -> dict:
        """
        Check overall data freshness and return warnings.

        Returns:
            Dict with freshness status and any warnings
        """
        schedules = self.get_refresh_schedules()
        warnings = []
        needs_refresh = []

        for name, schedule in schedules.items():
            if schedule["needs_refresh"]:
                needs_refresh.append(name)
                if name == "safety":
                    warnings.append(
                        f"Safety data is stale - FDA recalls may be outdated. "
                        f"Last updated: {schedule['last_updated'] or 'never'}"
                    )
                elif name == "product":
                    warnings.append(
                        f"Product data may be outdated - prices/availability could have changed. "
                        f"Last updated: {schedule['last_updated'] or 'never'}"
                    )

        return {
            "all_fresh": len(needs_refresh) == 0,
            "needs_refresh": needs_refresh,
            "warnings": warnings,
            "schedules": schedules,
        }

    def get_recommendation(
        self,
        category: str,
        user_tier_preference: str | None = None
    ) -> dict:
        """
        Get a quick recommendation without full facts_pack.

        Useful for simple queries where full LLM decision isn't needed.

        Args:
            category: Product category
            user_tier_preference: Override user's default tier preference

        Returns:
            Recommendation dict with product and reasoning
        """
        # Get tier products
        tiers = self.product_agent.get_tier_products(category)

        # Get safety info
        safety = self.safety_agent.query(category=category)

        # Determine which tier to recommend
        tier_pref = user_tier_preference or self.user_agent.get_tier_recommendation() or "balanced"

        # Check if tier is safe
        recommended_product = tiers.get(tier_pref)
        if recommended_product:
            has_organic = "organic" in recommended_product.get("certifications", "").lower()
            safety_check = self.safety_agent.check_tier_safety(category, tier_pref, has_organic)

            if not safety_check["is_safe"]:
                # Upgrade to safer tier
                for upgrade_tier in ["balanced", "conscious"]:
                    if upgrade_tier != tier_pref and tiers.get(upgrade_tier):
                        upgraded_product = tiers[upgrade_tier]
                        upgraded_organic = "organic" in upgraded_product.get("certifications", "").lower()
                        upgraded_safety = self.safety_agent.check_tier_safety(category, upgrade_tier, upgraded_organic)
                        if upgraded_safety["is_safe"]:
                            return {
                                "category": category,
                                "recommended_tier": upgrade_tier,
                                "product": upgraded_product,
                                "upgraded_from": tier_pref,
                                "upgrade_reason": safety_check["errors"] + safety_check["warnings"],
                                "safety": upgraded_safety,
                            }

        return {
            "category": category,
            "recommended_tier": tier_pref,
            "product": recommended_product,
            "safety": safety_check if recommended_product else None,
            "availability_issues": self.product_agent.get_availability_issues(category),
        }

    def get_shopping_list(self, categories: list[str]) -> list[dict]:
        """
        Generate a complete shopping list with recommendations for multiple categories.

        Args:
            categories: List of categories to shop for

        Returns:
            List of recommendations, one per category
        """
        shopping_list = []

        for category in categories:
            recommendation = self.get_recommendation(category)
            shopping_list.append(recommendation)

        return shopping_list

    def set_impact_preference(self, preset_or_weights: str | dict) -> None:
        """
        Set user's impact scoring preference.

        Args:
            preset_or_weights: Either a preset name ("eco_warrior", "health_focused",
                "budget_conscious", "animal_lover", "balanced") or a custom weights dict
        """
        if not IMPACT_SCORING_AVAILABLE:
            return

        if isinstance(preset_or_weights, str):
            if preset_or_weights in PREFERENCE_PRESETS:
                self.impact_weights = PREFERENCE_PRESETS[preset_or_weights]
            else:
                self.impact_weights = DEFAULT_WEIGHTS
        elif isinstance(preset_or_weights, dict):
            self.impact_weights = preset_or_weights
        else:
            self.impact_weights = DEFAULT_WEIGHTS

    def get_impact_dimensions(self) -> dict:
        """
        Get available impact dimensions and current weights.

        Returns:
            Dict with dimension info for UI display
        """
        if not IMPACT_SCORING_AVAILABLE:
            return {"available": False}

        return {
            "available": True,
            "dimensions": [
                {"key": "health", "name": "Health & Safety", "description": "EWG pesticides, recalls, nutrition"},
                {"key": "environmental", "name": "Environmental", "description": "Carbon footprint, local sourcing, seasonality"},
                {"key": "social", "name": "Social/Ethics", "description": "Fair trade, labor practices"},
                {"key": "packaging", "name": "Packaging", "description": "Recyclability, plastic reduction"},
                {"key": "animal_welfare", "name": "Animal Welfare", "description": "Cage-free, pasture-raised"},
            ],
            "current_weights": self.impact_weights,
            "presets": list(PREFERENCE_PRESETS.keys()) if PREFERENCE_PRESETS else [],
        }

    def get_whats_in_season(self) -> dict:
        """
        Get what's currently in season for NJ/Mid-Atlantic region.

        Returns:
            Dict with peak, available, and storage crops for current month
        """
        if not SEASONAL_AVAILABLE:
            return {"available": False, "reason": "Seasonal module not loaded"}

        return get_seasonal_recommendations()

    def get_location_info(self) -> dict:
        """
        Get current location configuration for local sourcing.

        Returns:
            Dict with location details and trusted regional sources
        """
        if not SEASONAL_AVAILABLE:
            return {
                "available": False,
                "default_state": "NJ",
                "default_county": "Middlesex",
            }

        from data_processing.seasonal_regional import TRUSTED_REGIONAL_SOURCES

        return {
            "available": True,
            "state": DEFAULT_LOCATION.state,
            "county": DEFAULT_LOCATION.county,
            "latitude": DEFAULT_LOCATION.latitude,
            "longitude": DEFAULT_LOCATION.longitude,
            "local_radius_miles": DEFAULT_LOCATION.local_radius,
            "trusted_sources": list(TRUSTED_REGIONAL_SOURCES.keys()),
        }


# Convenience function for quick access
def create_orchestrator(
    data_dir: str = "conscious-cart-coach/data",
    user_id: str = "default"
) -> AgentOrchestrator:
    """Create an orchestrator with default paths."""
    return AgentOrchestrator(Path(data_dir), user_id)
