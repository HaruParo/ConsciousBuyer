"""
Decision Engine - Deterministic two-stage scoring with neighbor selection.

Stage 1 (Hard Constraints): Disqualify candidates that fail dietary
restrictions or have confirmed product recalls.

Stage 2 (Soft Scoring): Score surviving candidates on EWG, seasonality,
organic status, brand trust, and user preferences.

The engine then picks a recommended product per ingredient, identifies
cheaper_neighbor and conscious_neighbor, and computes cart-level bundles.

Usage:
    from src.engine.decision_engine import DecisionEngine
    from src.contracts.models import ProductCandidate, SafetySignals, UserPrefs

    engine = DecisionEngine()
    bundle = engine.decide(
        candidates_by_ingredient={"spinach": [candidate1, candidate2, ...]},
        safety_signals={"spinach": safety_signal},
        seasonality={"spinach": seasonality_signal},
        user_prefs=user_prefs,
    )
"""

from dataclasses import dataclass, field
from typing import Any

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
    "organic": 8,
    "local_brand": 6,

    # User preference alignment
    "matches_preferred_brand": 10,
    "avoids_brand": -25,
    "matches_tier_preference": 5,
}

# Priority order for reason_short (first match wins)
REASON_PRIORITY = [
    ("recall_block", "Recall confirmed"),
    ("dietary_block", "Dietary restriction"),
    ("dirty_dozen_organic", "Organic required (EWG)"),
    ("dirty_dozen_no_organic", "No organic (EWG risk)"),
    ("peak_season", "Peak season local"),
    ("available_local", "Locally available"),
    ("organic_conscious", "Organic + conscious"),
    ("preferred_brand", "Preferred brand"),
    ("best_value", "Best value"),
    ("balanced_pick", "Balanced pick"),
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
    Deterministic decision engine.

    Two-stage: hard constraints filter, then soft scoring.
    No data fetching - all data must be passed in.
    """

    def __init__(self, weights: dict | None = None):
        self.weights = weights or WEIGHTS

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

            item = DecisionItem(
                ingredient_name=ingredient,
                selected_product_id=recommended.candidate.product_id,
                tier_symbol=tier,
                reason_short=reason_short,
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

            # Organic bonus
            if c.organic:
                sc.adjustments.append(("organic", self.weights["organic"]))

            # Brand preference
            if c.brand.lower() in [b.lower() for b in user_prefs.preferred_brands]:
                sc.adjustments.append(("matches_preferred_brand", self.weights["matches_preferred_brand"]))

            # Tier preference alignment (unit_price based)
            # Lower unit_price -> cheaper tier alignment, higher -> conscious
            # This is applied during neighbor selection, not here

            # Compute final score
            total_adj = sum(a[1] for a in sc.adjustments)
            sc.score = max(0, min(100, 50 + total_adj))

            # Determine top driver
            if not sc.top_driver and sc.adjustments:
                # Find the adjustment with the largest absolute impact
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

    # =========================================================================
    # Neighbor Selection
    # =========================================================================

    def _find_cheaper_neighbor(
        self,
        recommended: _ScoredCandidate,
        viable: list[_ScoredCandidate],
    ) -> _ScoredCandidate | None:
        """Find the next-cheaper viable option (lower unit_price, still decent score)."""
        cheaper_options = [
            s for s in viable
            if s.candidate.unit_price < recommended.candidate.unit_price
            and s.candidate.product_id != recommended.candidate.product_id
            and s.score >= 30  # Must have a minimum viable score
        ]
        if not cheaper_options:
            return None
        # Pick the one with best score among cheaper options
        return max(cheaper_options, key=lambda s: s.score)

    def _find_conscious_neighbor(
        self,
        recommended: _ScoredCandidate,
        viable: list[_ScoredCandidate],
    ) -> _ScoredCandidate | None:
        """Find the next-more-conscious option (organic, local, or higher score)."""
        conscious_options = [
            s for s in viable
            if s.candidate.product_id != recommended.candidate.product_id
            and (s.candidate.organic or s.score > recommended.score)
            and s.candidate.unit_price >= recommended.candidate.unit_price
        ]
        if not conscious_options:
            return None
        # Pick the one with highest score
        return max(conscious_options, key=lambda s: s.score)

    # =========================================================================
    # Tier Assignment
    # =========================================================================

    def _assign_tier(
        self,
        recommended: _ScoredCandidate,
        viable: list[_ScoredCandidate],
        user_prefs: UserPrefs,
    ) -> TierSymbol:
        """Assign a tier symbol based on where the recommendation falls."""
        if not viable or len(viable) < 2:
            return user_prefs.default_tier

        prices = sorted(s.candidate.unit_price for s in viable)
        rec_price = recommended.candidate.unit_price

        if len(prices) < 3:
            # With few options, use relative position
            median = prices[len(prices) // 2]
            if rec_price < median:
                return TierSymbol.CHEAPER
            elif rec_price > median:
                return TierSymbol.CONSCIOUS
            return TierSymbol.BALANCED

        # Divide into thirds
        third = len(prices) // 3
        lower_bound = prices[third]
        upper_bound = prices[-(third + 1)]

        if rec_price <= lower_bound:
            return TierSymbol.CHEAPER
        elif rec_price >= upper_bound:
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

        # Fallback based on score
        if recommended.score >= 70:
            return "Strong overall score"
        elif recommended.score >= 50:
            return "Balanced pick"
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
