"""
Orchestrator - Gated flow coordinator for Conscious Cart Coach.

Flow:
1. step_ingredients → Extract ingredients from user prompt
2. confirm_ingredients → Gate: user confirms/modifies ingredient list
3. step_candidates → Get product candidates (no tiers yet)
4. step_enrich → Safety + seasonality signals (parallel)
5. step_decide → DecisionEngine: constraints → scoring → neighbors → bundle
6. Export → Optional CSV export

Optional LLM Features:
- use_llm_extraction: Natural language ingredient parsing (Claude)
- use_llm_explanations: Enhanced decision explanations (Claude)
- Both default to False (deterministic only)

Usage:
    from src.orchestrator import Orchestrator

    # Deterministic only (default, no API calls)
    orch = Orchestrator()
    bundle = orch.process_prompt("chicken biryani for 4")

    # With LLM features enabled
    orch = Orchestrator(use_llm_extraction=True, use_llm_explanations=True)
    bundle = orch.process_prompt("I want something healthy and seasonal")

    # Step-by-step with gates
    orch.step_ingredients("chicken biryani", servings=4)
    orch.confirm_ingredients()  # accepts as-is
    orch.step_candidates()
    orch.step_enrich()
    bundle = orch.step_decide()
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, Optional

from anthropic import Anthropic

logger = logging.getLogger(__name__)

from ..contracts.models import (
    DecisionBundle,
    IngredientSpec,
    ProductCandidate,
    RecallSignal,
    SafetySignals,
    SeasonalitySignal,
    UserPrefs,
)
from ..core.types import AgentResult, Evidence, make_result, make_error
from ..agents.ingredient_agent import IngredientAgent
from ..agents.product_agent import ProductAgent
from ..agents.safety_agent_v2 import SafetyAgent
from ..agents.seasonal_agent import SeasonalAgent
from ..agents.user_history_agent import UserHistoryAgent
from ..engine.decision_engine import DecisionEngine
from ..opik_integration.tracker import OpikTracker


@dataclass
class FlowState:
    """State of the orchestration flow."""
    stage: Literal[
        "start",
        "ingredients_extracted",
        "ingredients_confirmed",
        "candidates_fetched",
        "enriched",
        "decided",
        "completed",
        "error",
    ] = "start"
    user_prompt: str = ""
    servings: int | None = None
    ingredients: list[dict] = field(default_factory=list)
    candidates_by_ingredient: dict[str, list[dict]] = field(default_factory=dict)
    safety_signals: dict[str, SafetySignals] = field(default_factory=dict)
    seasonality: dict[str, SeasonalitySignal] = field(default_factory=dict)
    user_prefs: UserPrefs = field(default_factory=UserPrefs)
    bundle: DecisionBundle | None = None
    errors: list[str] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str | None = None


class Orchestrator:
    """
    Gated flow coordinator.

    Each step advances the state machine. Gates require confirmation
    before proceeding (or auto_confirm=True to skip).

    Optional LLM features can be enabled for ingredient extraction
    and decision explanations.
    """

    def __init__(
        self,
        user_id: str = "default",
        use_llm_extraction: bool = False,
        use_llm_explanations: bool = False,
        anthropic_client: Optional[Anthropic] = None,
    ):
        """
        Initialize Orchestrator.

        Args:
            user_id: User identifier for history tracking
            use_llm_extraction: Enable Claude for ingredient parsing
            use_llm_explanations: Enable Claude for decision explanations
            anthropic_client: Optional shared Anthropic client (created if needed)
        """
        self.user_id = user_id
        self.use_llm_extraction = use_llm_extraction
        self.use_llm_explanations = use_llm_explanations
        self.state = FlowState()
        self.tracker = OpikTracker()

        # Initialize shared Anthropic client if LLM features enabled
        self.anthropic_client = anthropic_client
        if (use_llm_extraction or use_llm_explanations) and not self.anthropic_client:
            try:
                from ..llm.client import get_anthropic_client
                self.anthropic_client = get_anthropic_client()
                if self.anthropic_client:
                    logger.info("Orchestrator initialized with LLM features enabled")
                else:
                    logger.warning("LLM features requested but no API key available")
                    self.use_llm_extraction = False
                    self.use_llm_explanations = False
            except ImportError:
                logger.warning("LLM module not available")
                self.use_llm_extraction = False
                self.use_llm_explanations = False

        # Initialize agents
        self.ingredient_agent = IngredientAgent(
            use_llm=use_llm_extraction,
            anthropic_client=self.anthropic_client,
        )
        self.product_agent = ProductAgent()
        self.safety_agent = SafetyAgent()
        self.seasonal_agent = SeasonalAgent()
        self.user_history_agent = UserHistoryAgent(user_id)
        self.decision_engine = DecisionEngine(
            use_llm_explanations=use_llm_explanations,
            anthropic_client=self.anthropic_client,
        )

    def process_prompt(
        self,
        user_prompt: str,
        servings: int | None = None,
        auto_confirm: bool = True,
        user_prefs: UserPrefs | None = None,
    ) -> DecisionBundle:
        """
        Run the full flow from user prompt to DecisionBundle.

        Args:
            user_prompt: e.g., "chicken biryani for 4"
            servings: Optional serving count
            auto_confirm: Skip ingredient confirmation gate
            user_prefs: Optional user preferences

        Returns:
            DecisionBundle with items, totals, deltas
        """
        self.state = FlowState(user_prompt=user_prompt, servings=servings)
        if user_prefs:
            self.state.user_prefs = user_prefs

        self.tracker.start_trace(user_prompt, {"servings": servings})

        # Step 1: Extract ingredients
        self.tracker.start_span("step_ingredients", {"prompt": user_prompt})
        self.step_ingredients(user_prompt, servings)
        self.tracker.end_span({"count": len(self.state.ingredients)})
        if self.state.stage == "error":
            self.tracker.end_trace({"error": self.state.errors})
            return DecisionBundle(data_gaps=self.state.errors)

        # Gate: confirm
        if auto_confirm:
            self.confirm_ingredients()

        # Step 2: Get candidates
        self.tracker.start_span("step_candidates", {"ingredients": len(self.state.ingredients)})
        self.step_candidates()
        self.tracker.end_span({"matched": len(self.state.candidates_by_ingredient)})
        if self.state.stage == "error":
            self.tracker.end_trace({"error": self.state.errors})
            return DecisionBundle(data_gaps=self.state.errors)

        # Step 3: Enrich (safety + seasonal)
        self.tracker.start_span("step_enrich")
        self.step_enrich()
        self.tracker.end_span({
            "safety": len(self.state.safety_signals),
            "seasonal": len(self.state.seasonality),
        })

        # Step 4: Decide
        self.tracker.start_span("step_decide")
        bundle = self.step_decide()
        self.tracker.end_span({
            "items": bundle.item_count,
            "recommended_total": bundle.totals.get("recommended", 0),
        })

        self.state.stage = "completed"
        self.state.completed_at = datetime.now().isoformat()
        self.tracker.end_trace({"totals": bundle.totals})

        return bundle

    # =========================================================================
    # Step 1: Ingredients
    # =========================================================================

    def step_ingredients(
        self,
        user_prompt: str,
        servings: int | None = None,
    ) -> AgentResult:
        """Extract ingredients from user prompt."""
        try:
            self.state.user_prompt = user_prompt
            self.state.servings = servings

            result = self.ingredient_agent.extract(user_prompt, servings)

            if result.status == "error":
                self.state.stage = "error"
                self.state.errors.append(result.error_message or "Ingredient extraction failed")
                return result

            self.state.ingredients = result.facts.get("ingredients", [])
            self.state.stage = "ingredients_extracted"

            return make_result(
                agent_name="orchestrator",
                facts={
                    "stage": "ingredients_extracted",
                    "ingredients": self.state.ingredients,
                    "ingredient_count": len(self.state.ingredients),
                    "detected_recipe": result.facts.get("detected_recipe"),
                    "needs_confirmation": True,
                },
                explain=result.explain,
                evidence=result.evidence,
            )

        except Exception as e:
            self.state.stage = "error"
            self.state.errors.append(str(e))
            return make_error("orchestrator", str(e))

    # =========================================================================
    # Gate: Confirm Ingredients
    # =========================================================================

    def confirm_ingredients(
        self,
        confirmed_ingredients: list[dict] | None = None,
    ) -> AgentResult:
        """
        Confirm or modify extracted ingredients.

        Args:
            confirmed_ingredients: Modified list, or None to accept as-is
        """
        if confirmed_ingredients is not None:
            self.state.ingredients = confirmed_ingredients

        self.state.stage = "ingredients_confirmed"

        return make_result(
            agent_name="orchestrator",
            facts={
                "stage": "ingredients_confirmed",
                "ingredients": self.state.ingredients,
            },
            explain=[f"Confirmed {len(self.state.ingredients)} ingredients"],
            evidence=[],
        )

    # =========================================================================
    # Step 2: Get Candidates
    # =========================================================================

    def step_candidates(self) -> AgentResult:
        """Get product candidates for confirmed ingredients."""
        try:
            if self.state.stage not in ("ingredients_confirmed", "candidates_fetched"):
                return make_error("orchestrator", "Must confirm ingredients first")

            result = self.product_agent.get_candidates(self.state.ingredients)

            if result.status == "error":
                self.state.stage = "error"
                self.state.errors.append(result.error_message or "Product matching failed")
                return result

            self.state.candidates_by_ingredient = result.facts.get(
                "candidates_by_ingredient", {}
            )
            self.state.stage = "candidates_fetched"

            return make_result(
                agent_name="orchestrator",
                facts={
                    "stage": "candidates_fetched",
                    "candidates_by_ingredient": self.state.candidates_by_ingredient,
                    "matched_count": result.facts.get("matched_count", 0),
                    "not_found": result.facts.get("not_found", []),
                },
                explain=result.explain,
                evidence=result.evidence,
            )

        except Exception as e:
            self.state.stage = "error"
            self.state.errors.append(str(e))
            return make_error("orchestrator", str(e))

    # =========================================================================
    # Step 3: Enrich (Safety + Seasonal)
    # =========================================================================

    def step_enrich(self) -> AgentResult:
        """Check safety and seasonality for candidate ingredients."""
        try:
            # Build product list for agents (one entry per ingredient)
            products_for_check = []
            for ingredient, candidates in self.state.candidates_by_ingredient.items():
                # Use the first candidate's info as representative
                brand = candidates[0]["brand"] if candidates else ""
                products_for_check.append({
                    "name": ingredient,
                    "brand": brand,
                })

            # Safety check
            safety_result = self.safety_agent.check_products(products_for_check)
            if safety_result.status == "ok":
                self._build_safety_signals(safety_result.facts)

            # Seasonal check
            seasonal_result = self.seasonal_agent.check_products(products_for_check)
            if seasonal_result.status == "ok":
                self._build_seasonality_signals(seasonal_result.facts)

            self.state.stage = "enriched"

            explain = []
            explain.extend(safety_result.explain[:2])
            explain.extend(seasonal_result.explain[:2])

            return make_result(
                agent_name="orchestrator",
                facts={
                    "stage": "enriched",
                    "safety_count": len(self.state.safety_signals),
                    "seasonal_count": len(self.state.seasonality),
                },
                explain=explain,
                evidence=safety_result.evidence + seasonal_result.evidence,
            )

        except Exception as e:
            self.state.stage = "error"
            self.state.errors.append(str(e))
            return make_error("orchestrator", str(e))

    def _build_safety_signals(self, facts: dict):
        """Convert raw safety agent facts into typed SafetySignals."""
        ewg_results = facts.get("ewg_results", {})

        for ingredient in self.state.candidates_by_ingredient:
            ewg = ewg_results.get(ingredient, {})

            bucket = ewg.get("bucket", "unknown")
            recall_info = facts.get("recall_status", {}).get(ingredient, {})

            recall_signal = RecallSignal(
                product_match=recall_info.get("product_match", False),
                category_advisory=recall_info.get("category_advisory", "none"),
                confidence=recall_info.get("confidence", "low"),
                data_gap=recall_info.get("data_gap", False),
                details=recall_info.get("details", []),
                sources=recall_info.get("sources", []),
            )

            self.state.safety_signals[ingredient] = SafetySignals(
                ewg_bucket=bucket,
                ewg_rank=ewg.get("rank"),
                pesticide_score=ewg.get("pesticide_score"),
                organic_recommended=(bucket in ("dirty_dozen", "middle")),
                recall=recall_signal,
                safety_notes=ewg.get("notes", []) if isinstance(ewg.get("notes"), list) else [],
            )

    def _build_seasonality_signals(self, facts: dict):
        """Convert raw seasonal agent facts into typed SeasonalitySignal."""
        seasonality = facts.get("seasonality", {})

        for ingredient in self.state.candidates_by_ingredient:
            season = seasonality.get(ingredient, {})
            self.state.seasonality[ingredient] = SeasonalitySignal(
                status=season.get("status", "unknown"),
                is_local=season.get("is_local", False),
                notes=season.get("reasoning", ""),
            )

    # =========================================================================
    # Step 4: Decide
    # =========================================================================

    def step_decide(self) -> DecisionBundle:
        """Run the DecisionEngine and return a DecisionBundle."""
        # Convert candidate dicts to ProductCandidate objects
        typed_candidates: dict[str, list[ProductCandidate]] = {}

        for ingredient, candidates in self.state.candidates_by_ingredient.items():
            typed_candidates[ingredient] = [
                ProductCandidate(
                    product_id=c["product_id"],
                    ingredient_name=c["ingredient_name"],
                    title=c["title"],
                    brand=c["brand"],
                    size=c["size"],
                    price=c["price"],
                    unit_price=c["unit_price"],
                    unit_price_unit=c.get("unit_price_unit", "oz"),
                    organic=c.get("organic", False),
                    in_stock=c.get("in_stock", True),
                )
                for c in candidates
            ]

        # Load user prefs from history agent
        prefs_result = self.user_history_agent.get_preferences()
        if prefs_result.status == "ok":
            pref_data = prefs_result.facts.get("preferences", {})
            self.state.user_prefs = UserPrefs(
                default_tier=self.state.user_prefs.default_tier,
                preferred_brands=pref_data.get("preferred_brands", []),
                avoided_brands=pref_data.get("avoided_brands", []),
                dietary_restrictions=pref_data.get("dietary_restrictions", []),
                strict_safety=pref_data.get("strict_safety", False),
                ingredient_overrides=pref_data.get("ingredient_overrides", {}),
            )

        bundle = self.decision_engine.decide(
            candidates_by_ingredient=typed_candidates,
            safety_signals=self.state.safety_signals,
            seasonality=self.state.seasonality,
            user_prefs=self.state.user_prefs,
        )

        self.state.bundle = bundle
        self.state.stage = "decided"
        return bundle

    # =========================================================================
    # Post-Decision: Record & Export
    # =========================================================================

    def record_selection(
        self,
        ingredient: str,
        tier: str,
        product_id: str | None = None,
    ) -> AgentResult:
        """Record a user's tier selection for learning."""
        return self.user_history_agent.record_selection(
            ingredient=ingredient,
            tier=tier,
            product_id=product_id,
            context={"prompt": self.state.user_prompt},
        )

    # =========================================================================
    # State Accessors
    # =========================================================================

    def get_state(self) -> FlowState:
        """Get current flow state."""
        return self.state

    def get_bundle(self) -> DecisionBundle | None:
        """Get the last computed DecisionBundle."""
        return self.state.bundle

    def reset(self):
        """Reset orchestrator state for a new flow."""
        self.state = FlowState()


# Convenience function
def get_orchestrator(user_id: str = "default") -> Orchestrator:
    """Get orchestrator instance for a user."""
    return Orchestrator(user_id)
