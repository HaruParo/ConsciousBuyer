"""
User History Agent - Tracks user preferences and past selections.

Returns AgentResult contract for all outputs.

Usage:
    from src.agents.user_history_agent import UserHistoryAgent

    agent = UserHistoryAgent()

    # Record a selection
    agent.record_selection("spinach", "conscious", {"reason": "prefer organic"})

    # Get user preferences
    result = agent.get_preferences()
    # Returns AgentResult with learned preferences
"""

from datetime import datetime
from typing import Any, Literal

from ..core.types import AgentResult, Evidence, make_result, make_error


# In-memory storage for hackathon demo
# In production, this would be persisted to a database
_user_history: dict[str, list[dict]] = {}
_user_preferences: dict[str, dict] = {}


class UserHistoryAgent:
    """
    User history agent that tracks:
    - Past tier selections
    - Ingredient preferences
    - Budget patterns
    - Dietary restrictions

    Uses in-memory storage for demo.
    """

    AGENT_NAME = "user_history"

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self._ensure_user_exists()

    def _ensure_user_exists(self):
        """Ensure user has history and preferences initialized."""
        if self.user_id not in _user_history:
            _user_history[self.user_id] = []
        if self.user_id not in _user_preferences:
            _user_preferences[self.user_id] = {
                "default_tier": "balanced",
                "organic_preference": "when_dirty_dozen",
                "budget_limit": None,
                "dietary_restrictions": [],
                "favorite_brands": [],
                "avoided_brands": [],
                "ingredient_overrides": {},  # e.g., {"spinach": "conscious"}
            }

    def record_selection(
        self,
        ingredient: str,
        tier: Literal["cheaper", "balanced", "conscious"],
        product_id: str | None = None,
        context: dict | None = None,
    ) -> AgentResult:
        """
        Record a user's tier selection for an ingredient.

        Args:
            ingredient: Ingredient name
            tier: Selected tier
            product_id: Optional specific product selected
            context: Optional context (reason, etc.)

        Returns:
            AgentResult confirming the recording
        """
        try:
            selection = {
                "timestamp": datetime.now().isoformat(),
                "ingredient": ingredient.lower(),
                "tier": tier,
                "product_id": product_id,
                "context": context or {},
            }

            _user_history[self.user_id].append(selection)

            # Update ingredient override if consistent pattern
            self._update_ingredient_preference(ingredient, tier)

            explain = [f"Recorded {tier} tier selection for {ingredient}"]

            # Check if this establishes a pattern
            pattern = self._check_pattern(ingredient)
            if pattern:
                explain.append(f"Pattern detected: usually selects {pattern} for {ingredient}")

            return make_result(
                agent_name=self.AGENT_NAME,
                facts={
                    "recorded": selection,
                    "total_selections": len(_user_history[self.user_id]),
                },
                explain=explain,
                evidence=[Evidence(
                    source="User History",
                    key="selection",
                    value=f"{ingredient}:{tier}",
                    timestamp=selection["timestamp"],
                )],
            )

        except Exception as e:
            return make_error(self.AGENT_NAME, str(e))

    def _update_ingredient_preference(self, ingredient: str, tier: str):
        """Update ingredient preference based on selection pattern."""
        ingredient_lower = ingredient.lower()

        # Get recent selections for this ingredient
        recent = [
            s for s in _user_history[self.user_id][-20:]
            if s["ingredient"] == ingredient_lower
        ]

        # If 3+ selections with same tier, set as preference
        if len(recent) >= 3:
            tiers = [s["tier"] for s in recent[-3:]]
            if len(set(tiers)) == 1:
                _user_preferences[self.user_id]["ingredient_overrides"][ingredient_lower] = tiers[0]

    def _check_pattern(self, ingredient: str) -> str | None:
        """Check if there's a pattern for this ingredient."""
        ingredient_lower = ingredient.lower()
        return _user_preferences[self.user_id]["ingredient_overrides"].get(ingredient_lower)

    def get_preferences(self) -> AgentResult:
        """
        Get user's learned preferences.

        Returns:
            AgentResult with preference data
        """
        try:
            prefs = _user_preferences[self.user_id]
            history = _user_history[self.user_id]

            # Calculate tier distribution
            tier_counts = {"cheaper": 0, "balanced": 0, "conscious": 0}
            for selection in history:
                tier = selection.get("tier")
                if tier in tier_counts:
                    tier_counts[tier] += 1

            total = sum(tier_counts.values())
            tier_distribution = {
                tier: round(count / total * 100, 1) if total > 0 else 0
                for tier, count in tier_counts.items()
            }

            explain = []
            if total > 0:
                most_common = max(tier_counts, key=tier_counts.get)
                explain.append(f"Most selected tier: {most_common} ({tier_distribution[most_common]}%)")

            overrides = prefs.get("ingredient_overrides", {})
            if overrides:
                explain.append(f"{len(overrides)} ingredient-specific preferences learned")

            if prefs.get("dietary_restrictions"):
                explain.append(f"Dietary: {', '.join(prefs['dietary_restrictions'])}")

            return make_result(
                agent_name=self.AGENT_NAME,
                facts={
                    "preferences": prefs,
                    "tier_distribution": tier_distribution,
                    "total_selections": total,
                    "ingredient_overrides": overrides,
                },
                explain=explain,
                evidence=[Evidence(
                    source="User Preferences",
                    key="default_tier",
                    value=prefs["default_tier"],
                )],
            )

        except Exception as e:
            return make_error(self.AGENT_NAME, str(e))

    def set_preference(
        self,
        key: str,
        value: Any,
    ) -> AgentResult:
        """
        Set a user preference.

        Args:
            key: Preference key (default_tier, budget_limit, etc.)
            value: Preference value

        Returns:
            AgentResult confirming the update
        """
        try:
            valid_keys = [
                "default_tier",
                "organic_preference",
                "budget_limit",
                "dietary_restrictions",
                "favorite_brands",
                "avoided_brands",
            ]

            if key not in valid_keys:
                return make_error(
                    self.AGENT_NAME,
                    f"Invalid preference key: {key}. Valid keys: {valid_keys}",
                )

            old_value = _user_preferences[self.user_id].get(key)
            _user_preferences[self.user_id][key] = value

            explain = [f"Updated {key}: {old_value} → {value}"]

            return make_result(
                agent_name=self.AGENT_NAME,
                facts={
                    "key": key,
                    "old_value": old_value,
                    "new_value": value,
                },
                explain=explain,
                evidence=[Evidence(
                    source="User Preferences",
                    key=key,
                    value=str(value),
                    timestamp=datetime.now().isoformat(),
                )],
            )

        except Exception as e:
            return make_error(self.AGENT_NAME, str(e))

    def get_tier_for_ingredient(self, ingredient: str) -> AgentResult:
        """
        Get the recommended tier for an ingredient based on history.

        Args:
            ingredient: Ingredient name

        Returns:
            AgentResult with recommended tier
        """
        try:
            ingredient_lower = ingredient.lower()
            prefs = _user_preferences[self.user_id]

            # Check for explicit override
            override = prefs["ingredient_overrides"].get(ingredient_lower)
            if override:
                return make_result(
                    agent_name=self.AGENT_NAME,
                    facts={
                        "ingredient": ingredient,
                        "recommended_tier": override,
                        "source": "learned_preference",
                    },
                    explain=[f"User usually selects {override} for {ingredient}"],
                    evidence=[Evidence(
                        source="User History",
                        key=ingredient_lower,
                        value=override,
                    )],
                )

            # Fall back to default tier
            default = prefs["default_tier"]
            return make_result(
                agent_name=self.AGENT_NAME,
                facts={
                    "ingredient": ingredient,
                    "recommended_tier": default,
                    "source": "default_preference",
                },
                explain=[f"No specific preference for {ingredient}, using default: {default}"],
                evidence=[],
            )

        except Exception as e:
            return make_error(self.AGENT_NAME, str(e))

    def get_history(self, limit: int = 20) -> AgentResult:
        """
        Get recent selection history.

        Args:
            limit: Maximum number of records to return

        Returns:
            AgentResult with recent history
        """
        try:
            history = _user_history[self.user_id]
            recent = history[-limit:] if limit else history

            explain = [f"Showing {len(recent)} of {len(history)} selections"]

            return make_result(
                agent_name=self.AGENT_NAME,
                facts={
                    "history": recent,
                    "total_count": len(history),
                    "returned_count": len(recent),
                },
                explain=explain,
                evidence=[],
            )

        except Exception as e:
            return make_error(self.AGENT_NAME, str(e))

    def apply_preferences_to_matches(
        self,
        matches: dict,
    ) -> AgentResult:
        """
        Apply user preferences to product matches.

        Args:
            matches: Matches dict from ProductAgent

        Returns:
            AgentResult with preference-adjusted matches
        """
        try:
            prefs = _user_preferences[self.user_id]
            adjusted = {}
            changes = []

            for ingredient, match in matches.items():
                adjusted[ingredient] = match.copy()
                ingredient_lower = ingredient.lower()

                # Check for ingredient override
                override = prefs["ingredient_overrides"].get(ingredient_lower)
                if override:
                    adjusted[ingredient]["recommended_tier"] = override
                    adjusted[ingredient]["recommendation_source"] = "learned_preference"
                    changes.append(f"{ingredient}: recommend {override} (learned)")
                else:
                    adjusted[ingredient]["recommended_tier"] = prefs["default_tier"]
                    adjusted[ingredient]["recommendation_source"] = "default"

            explain = []
            if changes:
                explain.append(f"{len(changes)} ingredient(s) have learned preferences")
            else:
                explain.append(f"Using default tier: {prefs['default_tier']}")

            return make_result(
                agent_name=self.AGENT_NAME,
                facts={
                    "adjusted_matches": adjusted,
                    "changes": changes,
                    "default_tier": prefs["default_tier"],
                },
                explain=explain,
                evidence=[],
            )

        except Exception as e:
            return make_error(self.AGENT_NAME, str(e))

    def clear_history(self) -> AgentResult:
        """
        Clear user's selection history.

        Returns:
            AgentResult confirming the clear
        """
        try:
            count = len(_user_history[self.user_id])
            _user_history[self.user_id] = []
            _user_preferences[self.user_id]["ingredient_overrides"] = {}

            return make_result(
                agent_name=self.AGENT_NAME,
                facts={"cleared_count": count},
                explain=[f"Cleared {count} selections and learned preferences"],
                evidence=[],
            )

        except Exception as e:
            return make_error(self.AGENT_NAME, str(e))


# Convenience function
def get_user_history_agent(user_id: str = "default") -> UserHistoryAgent:
    """Get user history agent for a specific user."""
    return UserHistoryAgent(user_id)
