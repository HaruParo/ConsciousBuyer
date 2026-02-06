"""
Decision Engine - Deterministic two-stage scoring with neighbor selection.

Stage 1 (Hard Constraints): Disqualify candidates that fail dietary
restrictions or have confirmed product recalls.

Stage 2 (Soft Scoring): Score surviving candidates on EWG, seasonality,
organic status, brand trust, and user preferences.

The engine then picks a recommended product per ingredient, identifies
cheaper_neighbor and conscious_neighbor, and computes cart-level bundles.

Optional: LLM-powered explanations (scoring remains 100% deterministic).

Usage:
    from src.engine.decision_engine import DecisionEngine
    from src.contracts.models import ProductCandidate, SafetySignals, UserPrefs

    # Deterministic only (default)
    engine = DecisionEngine()
    bundle = engine.decide(
        candidates_by_ingredient={"spinach": [candidate1, candidate2, ...]},
        safety_signals={"spinach": safety_signal},
        seasonality={"spinach": seasonality_signal},
        user_prefs=user_prefs,
    )

    # With LLM explanations (scoring still deterministic)
    engine = DecisionEngine(use_llm_explanations=True)
    bundle = engine.decide(...)  # Now has reason_llm populated
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from anthropic import Anthropic

from ..contracts.models import (
    DecisionBundle,
    DecisionItem,
    ProductCandidate,
    RecallSignal,
    SafetySignals,
    SeasonalitySignal,
    TierSymbol,
    UserPrefs,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Scoring Weights (deterministic, no randomness)
# =============================================================================

WEIGHTS = {
    # EWG
    "dirty_dozen_no_organic": -20,
    "dirty_dozen_organic": 5,
    "middle_no_organic": -5,
    "middle_organic": 3,
    "clean_fifteen": 3,

    # Seasonality
    "peak_season": 15,
    "available_local": 10,
    "storage_local": 5,

    # Recall (soft penalties for category advisories)
    "recall_category_elevated": -10,
    "recall_category_recent": -5,
    "recall_data_gap": -3,

    # Quality signals
    "organic": 4,  # Regular organic bonus
    "organic_specialty": 15,  # Stronger bonus for organic spices/ethnic items (better quality at specialty stores)
    "local_brand": 5,

    # Value efficiency: best $/oz ratio gets a meaningful bonus
    "value_efficiency_best": 12,
    "value_efficiency_good": 6,

    # Balanced position: mid-range products get a bonus for BALANCED users
    "balanced_position": 8,

    # User preference alignment
    "matches_preferred_brand": 10,
    "avoids_brand": -25,
    "matches_tier_preference": 5,

    # Size filtering: penalize unrealistic package sizes
    "unrealistic_small_size": -30,
}

# Fresh herbs that should come in bunches or reasonable clamshells (not tiny boxes)
FRESH_HERBS = {
    "cilantro", "coriander", "coriander_leaves", "parsley", "basil",
    "mint", "mint_leaves", "dill", "chives", "thyme", "rosemary"
}

# Minimum reasonable sizes for fresh herbs (in oz)
MIN_FRESH_HERB_SIZE_OZ = 0.5

# Priority order for reason_short (first match wins)
REASON_PRIORITY = [
    ("recall_block", "Recall confirmed"),
    ("dietary_block", "Dietary restriction"),
    ("dirty_dozen_organic", "Organic recommended (EWG)"),
    ("dirty_dozen_no_organic", "No organic (EWG risk)"),
    ("peak_season", "Peak season local"),
    ("available_local", "Locally available"),
    ("matches_preferred_brand", "Preferred brand"),
    ("organic_specialty", "Organic specialty"),
    ("value_efficiency_best", "Best value per oz"),
    ("balanced_position", "Best match"),
    ("value_efficiency_good", "Good value"),
    ("organic", "Organic option"),
    ("local_brand", "Local brand"),
]


@dataclass
class _ScoredCandidate:
    """Internal: a candidate with its computed score and adjustments."""
    candidate: ProductCandidate
    score: int = 50
    adjustments: list[tuple[str, int]] = field(default_factory=list)
    disqualified: bool = False
    disqualify_reason: str = ""
    top_driver: str = ""  # Key into REASON_PRIORITY


class DecisionEngine:
    """
    Deterministic decision engine with optional LLM explanations.

    Scoring is ALWAYS deterministic (same input = same output).
    LLM is only used for natural language explanations (optional).

    Two-stage: hard constraints filter, then soft scoring.
    No data fetching - all data must be passed in.
    """

    def __init__(
        self,
        weights: dict | None = None,
        use_llm_explanations: bool = False,
        anthropic_client: Optional[Anthropic] = None,
    ):
        """
        Initialize DecisionEngine.

        Args:
            weights: Custom scoring weights (optional)
            use_llm_explanations: Generate LLM explanations (requires API key)
            anthropic_client: Optional pre-initialized Anthropic client
        """
        self.weights = weights or WEIGHTS
        self.use_llm_explanations = use_llm_explanations
        self.anthropic_client = anthropic_client

        # Lazy load LLM module
        self._llm_explainer = None
        if self.use_llm_explanations:
            try:
                from ..llm.client import get_anthropic_client
                from ..llm.decision_explainer import explain_decision_with_llm
                self._llm_explainer = explain_decision_with_llm
                if not self.anthropic_client:
                    self.anthropic_client = get_anthropic_client()
                if self.anthropic_client:
                    logger.info("DecisionEngine initialized with LLM explanations")
                else:
                    logger.warning("LLM explanations requested but no API key found")
                    self.use_llm_explanations = False
            except ImportError as e:
                logger.warning(f"LLM module not available: {e}")
                self.use_llm_explanations = False

    def decide(
        self,
        candidates_by_ingredient: dict[str, list[ProductCandidate]],
        safety_signals: dict[str, SafetySignals] | None = None,
        seasonality: dict[str, SeasonalitySignal] | None = None,
        user_prefs: UserPrefs | None = None,
    ) -> DecisionBundle:
        """
        Run the full decision pipeline.

        Args:
            candidates_by_ingredient: ingredient_name -> list of ProductCandidates
            safety_signals: ingredient_name -> SafetySignals
            seasonality: ingredient_name -> SeasonalitySignal
            user_prefs: User preferences

        Returns:
            DecisionBundle with items, totals, deltas, data_gaps, constraint_notes
        """
        safety_signals = safety_signals or {}
        seasonality = seasonality or {}
        user_prefs = user_prefs or UserPrefs()

        items: list[DecisionItem] = []
        data_gaps: list[str] = []
        constraint_notes: list[str] = []

        # Track totals for bundle-level calculations
        recommended_total = 0.0
        cheaper_total = 0.0
        conscious_total = 0.0

        for ingredient, candidates in candidates_by_ingredient.items():
            if not candidates:
                data_gaps.append(f"No candidates found for {ingredient}")
                continue

            safety = safety_signals.get(ingredient, SafetySignals())
            season = seasonality.get(ingredient, SeasonalitySignal())

            # Stage 1: Hard constraints
            scored = self._stage1_constraints(
                candidates, safety, user_prefs, constraint_notes
            )

            # Stage 2: Soft scoring
            self._stage2_scoring(scored, safety, season, user_prefs)

            # Filter to viable candidates (not disqualified)
            viable = [s for s in scored if not s.disqualified]

            if not viable:
                # All disqualified - take the least-bad option
                viable = sorted(scored, key=lambda s: s.score, reverse=True)[:1]
                constraint_notes.append(
                    f"{ingredient}: all options have constraints, using least-restricted"
                )

            # Sort by score descending
            viable.sort(key=lambda s: s.score, reverse=True)

            # Pick recommended (highest score)
            recommended = viable[0]

            # Identify neighbors
            cheaper_neighbor = self._find_cheaper_neighbor(recommended, viable)
            conscious_neighbor = self._find_conscious_neighbor(recommended, viable)

            # Determine tier symbol
            tier = self._assign_tier(recommended, viable, user_prefs)

            # Determine reason_short
            reason_short = self._get_reason_short(recommended, safety, season)

            # Build attributes
            attributes = self._build_attributes(recommended.candidate, safety, season)

            # Build safety notes
            safety_notes = self._build_safety_notes(safety)

            # Track data gaps
            if safety.recall.data_gap:
                data_gaps.append(f"{ingredient}: recall data may be stale")

            # Optional: Generate LLM explanation
            reason_llm = None
            if self.use_llm_explanations and self._llm_explainer and self.anthropic_client:
                try:
                    scoring_factors = [f"{adj[0]}: {adj[1]:+d}" for adj in recommended.adjustments]
                    cheaper_desc = None
                    if cheaper_neighbor:
                        cheaper_desc = f"{cheaper_neighbor.candidate.brand} at ${cheaper_neighbor.candidate.price:.2f}"
                    conscious_desc = None
                    if conscious_neighbor:
                        conscious_desc = f"{conscious_neighbor.candidate.brand} at ${conscious_neighbor.candidate.price:.2f}"

                    reason_llm = self._llm_explainer(
                        client=self.anthropic_client,
                        ingredient_name=ingredient,
                        recommended_product={
                            "brand": recommended.candidate.brand,
                            "price": recommended.candidate.price,
                            "size": recommended.candidate.size,
                            "unit_price": recommended.candidate.unit_price,
                            "organic": recommended.candidate.organic,
                        },
                        scoring_factors=scoring_factors,
                        cheaper_option=cheaper_desc,
                        conscious_option=conscious_desc,
                        user_prefs={
                            "preferred_brands": user_prefs.preferred_brands,
                            "avoided_brands": user_prefs.avoided_brands,
                            "strict_safety": user_prefs.strict_safety,
                        },
                    )
                except Exception as e:
                    logger.warning(f"Failed to generate LLM explanation for {ingredient}: {e}")
                    reason_llm = None

            item = DecisionItem(
                ingredient_name=ingredient,
                selected_product_id=recommended.candidate.product_id,
                tier_symbol=tier,
                reason_short=reason_short,
                reason_llm=reason_llm,
                attributes=attributes,
                safety_notes=safety_notes,
                cheaper_neighbor_id=(
                    cheaper_neighbor.candidate.product_id if cheaper_neighbor else None
                ),
                conscious_neighbor_id=(
                    conscious_neighbor.candidate.product_id if conscious_neighbor else None
                ),
                score=recommended.score,
                evidence_refs=safety.recall.sources,
            )
            items.append(item)

            # Accumulate totals
            recommended_total += recommended.candidate.price
            if cheaper_neighbor:
                cheaper_total += cheaper_neighbor.candidate.price
            else:
                cheaper_total += recommended.candidate.price
            if conscious_neighbor:
                conscious_total += conscious_neighbor.candidate.price
            else:
                conscious_total += recommended.candidate.price

        # Build bundle
        totals = {
            "recommended": round(recommended_total, 2),
            "cheaper": round(cheaper_total, 2),
            "conscious": round(conscious_total, 2),
        }

        deltas = {
            "cheaper_vs_recommended": round(cheaper_total - recommended_total, 2),
            "conscious_vs_recommended": round(conscious_total - recommended_total, 2),
        }

        return DecisionBundle(
            items=items,
            totals=totals,
            deltas=deltas,
            data_gaps=data_gaps,
            constraint_notes=constraint_notes,
        )

    # =========================================================================
    # Stage 1: Hard Constraints
    # =========================================================================

    def _stage1_constraints(
        self,
        candidates: list[ProductCandidate],
        safety: SafetySignals,
        user_prefs: UserPrefs,
        constraint_notes: list[str],
    ) -> list[_ScoredCandidate]:
        """Apply hard constraints to disqualify candidates."""
        scored = []

        for c in candidates:
            sc = _ScoredCandidate(candidate=c)

            # Constraint: product_match recall = disqualify
            if safety.recall.product_match:
                sc.disqualified = True
                sc.disqualify_reason = "Active recall on product"
                sc.top_driver = "recall_block"
                constraint_notes.append(
                    f"{c.ingredient_name}/{c.brand}: disqualified (recall)"
                )

            # Constraint: avoided brand
            if not sc.disqualified and c.brand.lower() in [
                b.lower() for b in user_prefs.avoided_brands
            ]:
                sc.disqualified = True
                sc.disqualify_reason = "Brand on avoid list"
                sc.top_driver = "dietary_block"

            # Constraint: strict_safety + dirty_dozen + not organic
            if (
                not sc.disqualified
                and user_prefs.strict_safety
                and safety.ewg_bucket == "dirty_dozen"
                and not c.organic
            ):
                sc.disqualified = True
                sc.disqualify_reason = "EWG Dirty Dozen requires organic (strict mode)"
                sc.top_driver = "dirty_dozen_no_organic"

            scored.append(sc)

        return scored

    # =========================================================================
    # Stage 2: Soft Scoring
    # =========================================================================

    def _stage2_scoring(
        self,
        scored: list[_ScoredCandidate],
        safety: SafetySignals,
        season: SeasonalitySignal,
        user_prefs: UserPrefs,
    ):
        """Apply soft scoring adjustments to all candidates."""
        # Pre-compute price stats for value efficiency scoring
        viable_prices = [
            s.candidate.unit_price for s in scored if not s.disqualified
        ]
        if viable_prices:
            min_price = min(viable_prices)
            max_price = max(viable_prices)
            price_range = max_price - min_price if max_price > min_price else 1.0
            mid_price = (min_price + max_price) / 2.0
        else:
            min_price = max_price = mid_price = price_range = 0.0

        for sc in scored:
            if sc.disqualified:
                sc.score = 0
                continue

            c = sc.candidate

            # EWG scoring
            self._apply_ewg_score(sc, safety)

            # Seasonality scoring
            self._apply_season_score(sc, season)

            # Recall category advisories (soft)
            self._apply_recall_advisory(sc, safety)

            # Organic bonus - stronger for spices/ethnic ingredients at specialty stores
            if c.organic:
                # Check if this is a spice or ethnic ingredient
                ingredient_normalized = c.ingredient_name.lower().strip().replace(" ", "_")
                is_spice = self._is_spice_or_ethnic(ingredient_normalized)

                if is_spice:
                    # Spices at specialty stores benefit greatly from organic (transparency, quality)
                    # Boost organic bonus significantly to ensure organic selection
                    sc.adjustments.append(("organic_specialty", self.weights.get("organic_specialty", 15)))
                else:
                    # Regular organic bonus for non-spice items
                    sc.adjustments.append(("organic", self.weights["organic"]))

            # Brand preference
            if c.brand.lower() in [b.lower() for b in user_prefs.preferred_brands]:
                sc.adjustments.append(("matches_preferred_brand", self.weights["matches_preferred_brand"]))

            # Size filtering: penalize unrealistically small packages for fresh herbs
            self._apply_size_penalty(sc)

            # Value efficiency: reward best price/oz ratio
            if price_range > 0:
                price_position = (c.unit_price - min_price) / price_range  # 0=cheapest, 1=most expensive
                if price_position <= 0.15:
                    sc.adjustments.append(("value_efficiency_best", self.weights["value_efficiency_best"]))
                elif price_position <= 0.40:
                    sc.adjustments.append(("value_efficiency_good", self.weights["value_efficiency_good"]))

            # Balanced position: reward mid-range when user prefers BALANCED
            if user_prefs.default_tier == TierSymbol.BALANCED and price_range > 0:
                distance_from_mid = abs(c.unit_price - mid_price) / price_range
                if distance_from_mid <= 0.25:  # Within 25% of midpoint
                    sc.adjustments.append(("balanced_position", self.weights["balanced_position"]))

            # Compute final score
            total_adj = sum(a[1] for a in sc.adjustments)
            sc.score = max(0, min(100, 50 + total_adj))

            # Determine top driver
            if not sc.top_driver and sc.adjustments:
                # Find the positive adjustment with the largest impact
                positive_adj = [a for a in sc.adjustments if a[1] > 0]
                if positive_adj:
                    best = max(positive_adj, key=lambda a: a[1])
                else:
                    best = max(sc.adjustments, key=lambda a: abs(a[1]))
                sc.top_driver = best[0]

    def _apply_ewg_score(self, sc: _ScoredCandidate, safety: SafetySignals):
        """Apply EWG-based scoring."""
        bucket = safety.ewg_bucket
        is_organic = sc.candidate.organic

        if bucket == "dirty_dozen":
            if is_organic:
                sc.adjustments.append(("dirty_dozen_organic", self.weights["dirty_dozen_organic"]))
                sc.top_driver = "dirty_dozen_organic"
            else:
                sc.adjustments.append(("dirty_dozen_no_organic", self.weights["dirty_dozen_no_organic"]))
                sc.top_driver = "dirty_dozen_no_organic"
        elif bucket == "middle":
            if is_organic:
                sc.adjustments.append(("middle_organic", self.weights["middle_organic"]))
            else:
                sc.adjustments.append(("middle_no_organic", self.weights["middle_no_organic"]))
        elif bucket == "clean_fifteen":
            sc.adjustments.append(("clean_fifteen", self.weights["clean_fifteen"]))

    def _apply_season_score(self, sc: _ScoredCandidate, season: SeasonalitySignal):
        """Apply seasonality scoring."""
        if season.status == "peak":
            sc.adjustments.append(("peak_season", self.weights["peak_season"]))
            if not sc.top_driver or sc.top_driver == "organic":
                sc.top_driver = "peak_season"
        elif season.status == "available":
            sc.adjustments.append(("available_local", self.weights["available_local"]))
            if not sc.top_driver:
                sc.top_driver = "available_local"
        elif season.status == "storage":
            sc.adjustments.append(("storage_local", self.weights["storage_local"]))

    def _apply_recall_advisory(self, sc: _ScoredCandidate, safety: SafetySignals):
        """Apply soft recall category advisory penalties."""
        advisory = safety.recall.category_advisory
        if advisory == "elevated":
            sc.adjustments.append(("recall_category_elevated", self.weights["recall_category_elevated"]))
        elif advisory == "recent":
            sc.adjustments.append(("recall_category_recent", self.weights["recall_category_recent"]))

        if safety.recall.data_gap:
            sc.adjustments.append(("recall_data_gap", self.weights["recall_data_gap"]))

    def _apply_size_penalty(self, sc: _ScoredCandidate):
        """Penalize unrealistically small package sizes for fresh herbs."""
        c = sc.candidate
        ingredient_normalized = c.ingredient_name.lower().strip().replace(" ", "_")

        # Check if this is a fresh herb
        is_fresh_herb = any(herb in ingredient_normalized for herb in FRESH_HERBS)

        if is_fresh_herb:
            # Parse size to get numeric value in oz
            size_oz = self._parse_size_to_oz(c.size)

            # Penalize if size is unrealistically small
            if size_oz is not None and size_oz < MIN_FRESH_HERB_SIZE_OZ:
                sc.adjustments.append(("unrealistic_small_size", self.weights["unrealistic_small_size"]))
                if not sc.top_driver:
                    sc.top_driver = "unrealistic_small_size"

    def _parse_size_to_oz(self, size_str: str) -> float | None:
        """
        Parse size string to oz value.

        Examples:
            "1 oz" -> 1.0
            "0.5 oz" -> 0.5
            "1 bunch" -> None (not measurable in oz)
            "5 oz" -> 5.0
        """
        import re

        # Match patterns like "1 oz", "0.5oz", "1.5 oz"
        match = re.search(r'(\d+\.?\d*)\s*oz', size_str.lower())
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None

        return None

    def _is_spice_or_ethnic(self, ingredient: str) -> bool:
        """
        Check if ingredient is a spice or ethnic specialty item.

        These items benefit greatly from organic at specialty stores due to:
        - Better quality and transparency
        - Direct sourcing from trusted suppliers
        - No pesticide residues in concentrated spices

        Includes: all spices, ethnic staples (rice, lentils, ghee, etc.)
        """
        # Spice patterns
        spice_patterns = [
            "turmeric", "cumin", "coriander", "cardamom", "cinnamon",
            "clove", "cloves", "bay_leaf", "bay_leaves", "curry",
            "garam_masala", "masala", "chaat", "tandoori",
            "mustard_seed", "fenugreek", "kasuri_methi",
            "asafoetida", "hing", "fennel",
            "black_pepper", "white_pepper", "pepper", "chili", "cayenne", "paprika",
            "saffron", "sumac", "za'atar"
        ]

        # Ethnic specialty staples
        ethnic_staples = [
            "ghee", "paneer", "dal", "lentils",
            "basmati", "jasmine_rice", "rice",
            "tamarind", "jaggery",
            "tahini", "miso", "kimchi", "gochugaru", "gochujang",
            "sesame_oil", "fish_sauce", "oyster_sauce"
        ]

        # Check direct match
        for pattern in spice_patterns + ethnic_staples:
            if pattern in ingredient:
                return True

        # Check suffix patterns (e.g., "curry_powder", "chili_powder")
        if any(ingredient.endswith(suffix) for suffix in ["_powder", "_seed", "_seeds", "_masala", "_paste"]):
            return True

        return False

    # =========================================================================
    # Neighbor Selection
    # =========================================================================

    def _find_cheaper_neighbor(
        self,
        recommended: _ScoredCandidate,
        viable: list[_ScoredCandidate],
    ) -> _ScoredCandidate | None:
        """Find the next-cheaper viable option (lower unit_price, nearest neighbor)."""
        cheaper_options = [
            s for s in viable
            if s.candidate.unit_price < recommended.candidate.unit_price
            and s.candidate.product_id != recommended.candidate.product_id
            and s.score >= 25  # Minimum viable score (relaxed)
        ]
        if not cheaper_options:
            return None
        # Pick the nearest cheaper neighbor (highest unit_price below recommended)
        return max(cheaper_options, key=lambda s: s.candidate.unit_price)

    def _find_conscious_neighbor(
        self,
        recommended: _ScoredCandidate,
        viable: list[_ScoredCandidate],
    ) -> _ScoredCandidate | None:
        """Find the next-more-conscious option (organic, ethical, or premium quality)."""
        # Primary: organic options that cost more than the recommended
        primary = [
            s for s in viable
            if s.candidate.product_id != recommended.candidate.product_id
            and s.candidate.organic
            and s.candidate.unit_price > recommended.candidate.unit_price
        ]
        if primary:
            # Pick cheapest among the organic upgrades (nearest neighbor)
            return min(primary, key=lambda s: s.candidate.unit_price)

        # Secondary: any organic option not already recommended
        secondary = [
            s for s in viable
            if s.candidate.product_id != recommended.candidate.product_id
            and s.candidate.organic
        ]
        if secondary:
            # Pick highest-scored organic option
            return max(secondary, key=lambda s: s.score)

        # Tertiary: any option more expensive than recommended (premium quality)
        tertiary = [
            s for s in viable
            if s.candidate.product_id != recommended.candidate.product_id
            and s.candidate.unit_price > recommended.candidate.unit_price
        ]
        if tertiary:
            return min(tertiary, key=lambda s: s.candidate.unit_price)

        return None

    # =========================================================================
    # Tier Assignment
    # =========================================================================

    def _assign_tier(
        self,
        recommended: _ScoredCandidate,
        viable: list[_ScoredCandidate],
        user_prefs: UserPrefs,
    ) -> TierSymbol:
        """
        Assign a tier symbol based on price position and user preference.

        Logic: the tier reflects WHERE the recommended product sits on the
        price spectrum relative to its neighbors, not a judgment about quality.
        """
        if not viable or len(viable) < 2:
            return user_prefs.default_tier

        prices = sorted(s.candidate.unit_price for s in viable)
        rec_price = recommended.candidate.unit_price
        min_price = prices[0]
        max_price = prices[-1]
        price_range = max_price - min_price

        if price_range == 0:
            return TierSymbol.BALANCED

        # Normalized position: 0.0 = cheapest, 1.0 = most expensive
        position = (rec_price - min_price) / price_range

        if position <= 0.30:
            return TierSymbol.CHEAPER
        elif position >= 0.70:
            return TierSymbol.CONSCIOUS
        return TierSymbol.BALANCED

    # =========================================================================
    # Reason & Attributes
    # =========================================================================

    def _get_reason_short(
        self,
        recommended: _ScoredCandidate,
        safety: SafetySignals,
        season: SeasonalitySignal,
    ) -> str:
        """Get 3-4 word reason from highest-priority driver."""
        driver = recommended.top_driver

        for key, reason in REASON_PRIORITY:
            if key == driver:
                return reason

        # Fallback: check if organic is a factor
        if recommended.candidate.organic and safety.ewg_bucket in ("dirty_dozen", "middle"):
            return "Organic recommended"

        # Fallback based on score position
        if recommended.score >= 65:
            return "Top rated option"
        elif recommended.score >= 55:
            return "Best match"
        return "Best available"

    def _build_attributes(
        self,
        candidate: ProductCandidate,
        safety: SafetySignals,
        season: SeasonalitySignal,
    ) -> list[str]:
        """Build attribute tags for display."""
        attrs = []
        if candidate.organic:
            attrs.append("Organic")
        if season.is_local:
            attrs.append("Local")
        if season.status == "peak":
            attrs.append("In Season")
        if safety.ewg_bucket == "clean_fifteen":
            attrs.append("Low Pesticide")
        return attrs

    def _build_safety_notes(self, safety: SafetySignals) -> list[str]:
        """Build safety notes for display."""
        notes = list(safety.safety_notes)
        if safety.ewg_bucket == "dirty_dozen" and safety.organic_recommended:
            notes.append("EWG recommends organic for this item")
        if safety.recall.category_advisory == "elevated":
            notes.append("Category has elevated recall activity")
        if safety.recall.data_gap:
            notes.append("Recall data freshness uncertain")
        return notes


# Convenience function
def get_decision_engine() -> DecisionEngine:
    """Get default decision engine instance."""
    return DecisionEngine()
