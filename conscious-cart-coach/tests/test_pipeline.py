"""
Tests for the refactored pipeline: ProductAgent, FactsGateway, DecisionEngine, Orchestrator.

Run: python -m pytest tests/test_pipeline.py -v
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.product_agent import ProductAgent, parse_size_oz
from src.contracts.models import (
    DecisionBundle,
    DecisionItem,
    ProductCandidate,
    RecallSignal,
    SafetySignals,
    SeasonalitySignal,
    TierSymbol,
    UserPrefs,
)
from src.engine.decision_engine import DecisionEngine


# =============================================================================
# ProductAgent: Unit Price Normalization
# =============================================================================

class TestParseSizeOz:
    """Tests for parse_size_oz unit conversion."""

    def test_oz_simple(self):
        assert parse_size_oz("5oz") == 5.0

    def test_oz_with_space(self):
        assert parse_size_oz("16 oz") == 16.0

    def test_oz_decimal(self):
        assert abs(parse_size_oz("2.31oz") - 2.31) < 0.01

    def test_lb_conversion(self):
        assert parse_size_oz("1 lb") == 16.0
        assert parse_size_oz("2lb") == 32.0

    def test_dozen(self):
        assert parse_size_oz("dozen") == 12.0

    def test_grams(self):
        result = parse_size_oz("100g")
        assert abs(result - 3.527) < 0.01

    def test_kg(self):
        result = parse_size_oz("1kg")
        assert abs(result - 35.27) < 0.01

    def test_no_unit_defaults_oz(self):
        assert parse_size_oz("5") == 5.0

    def test_empty_returns_one(self):
        assert parse_size_oz("") == 1.0


class TestProductAgent:
    """Tests for ProductAgent.get_candidates()."""

    def test_returns_candidates_for_known_ingredient(self):
        agent = ProductAgent()
        result = agent.get_candidates([{"name": "spinach"}])
        assert result.status == "ok"
        candidates = result.facts["candidates_by_ingredient"]
        assert "spinach" in candidates
        assert len(candidates["spinach"]) >= 2

    def test_candidates_sorted_by_unit_price(self):
        agent = ProductAgent()
        result = agent.get_candidates([{"name": "spinach"}])
        candidates = result.facts["candidates_by_ingredient"]["spinach"]
        prices = [c["unit_price"] for c in candidates]
        assert prices == sorted(prices)

    def test_candidates_have_unit_price(self):
        agent = ProductAgent()
        result = agent.get_candidates([{"name": "chicken"}])
        candidates = result.facts["candidates_by_ingredient"]["chicken"]
        for c in candidates:
            assert "unit_price" in c
            assert c["unit_price"] > 0
            assert c["unit_price_unit"] == "oz"

    def test_no_tier_labels(self):
        agent = ProductAgent()
        result = agent.get_candidates([{"name": "spinach"}])
        candidates = result.facts["candidates_by_ingredient"]["spinach"]
        for c in candidates:
            assert "tier" not in c

    def test_unknown_ingredient_in_not_found(self):
        agent = ProductAgent()
        result = agent.get_candidates([{"name": "dragon fruit"}])
        assert "dragon fruit" in result.facts["not_found"]

    def test_alias_resolution(self):
        agent = ProductAgent()
        result = agent.get_candidates([{"name": "baby spinach"}])
        assert "baby spinach" in result.facts["candidates_by_ingredient"]


# =============================================================================
# DecisionEngine: Constraints-First + Determinism
# =============================================================================

class TestDecisionEngineConstraints:
    """Tests for DecisionEngine hard constraints."""

    def _make_candidates(self, ingredient: str) -> list[ProductCandidate]:
        return [
            ProductCandidate(
                product_id="p1", ingredient_name=ingredient,
                title="Organic Item", brand="GoodBrand", size="5oz",
                price=5.99, unit_price=1.198, organic=True,
            ),
            ProductCandidate(
                product_id="p2", ingredient_name=ingredient,
                title="Regular Item", brand="BadBrand", size="5oz",
                price=3.99, unit_price=0.798, organic=False,
            ),
            ProductCandidate(
                product_id="p3", ingredient_name=ingredient,
                title="Cheap Item", brand="StoreBrand", size="8oz",
                price=1.99, unit_price=0.249, organic=False,
            ),
        ]

    def test_recall_disqualifies_candidates(self):
        engine = DecisionEngine()
        candidates = self._make_candidates("spinach")
        safety = SafetySignals(
            recall=RecallSignal(product_match=True, confidence="high")
        )

        bundle = engine.decide(
            candidates_by_ingredient={"spinach": candidates},
            safety_signals={"spinach": safety},
        )

        assert len(bundle.items) == 1
        # All disqualified, but engine picks least-bad
        assert "recall" in bundle.constraint_notes[0].lower()

    def test_avoided_brand_disqualified(self):
        engine = DecisionEngine()
        candidates = self._make_candidates("spinach")
        prefs = UserPrefs(avoided_brands=["BadBrand"])

        bundle = engine.decide(
            candidates_by_ingredient={"spinach": candidates},
            user_prefs=prefs,
        )

        item = bundle.items[0]
        # Should not select p2 (BadBrand)
        assert item.selected_product_id != "p2"

    def test_strict_safety_dirty_dozen_no_organic(self):
        engine = DecisionEngine()
        candidates = self._make_candidates("spinach")
        safety = SafetySignals(ewg_bucket="dirty_dozen", organic_recommended=True)
        prefs = UserPrefs(strict_safety=True)

        bundle = engine.decide(
            candidates_by_ingredient={"spinach": candidates},
            safety_signals={"spinach": safety},
            user_prefs=prefs,
        )

        item = bundle.items[0]
        # Only organic candidate should survive (p1)
        assert item.selected_product_id == "p1"


class TestDecisionEngineDeterminism:
    """Tests that the engine is deterministic."""

    def _make_candidates(self) -> list[ProductCandidate]:
        return [
            ProductCandidate(
                product_id="a1", ingredient_name="tomatoes",
                title="Organic Heirloom", brand="LocalFarm", size="16oz",
                price=6.99, unit_price=0.437, organic=True,
            ),
            ProductCandidate(
                product_id="a2", ingredient_name="tomatoes",
                title="Roma Tomatoes", brand="StoreBrand", size="16oz",
                price=2.99, unit_price=0.187, organic=False,
            ),
            ProductCandidate(
                product_id="a3", ingredient_name="tomatoes",
                title="Vine Tomatoes", brand="StoreBrand", size="16oz",
                price=3.49, unit_price=0.218, organic=False,
            ),
        ]

    def test_same_input_same_output(self):
        engine = DecisionEngine()
        candidates = {"tomatoes": self._make_candidates()}
        safety = {"tomatoes": SafetySignals(ewg_bucket="middle")}
        season = {"tomatoes": SeasonalitySignal(status="available", is_local=True)}

        bundle1 = engine.decide(candidates, safety, season)
        bundle2 = engine.decide(candidates, safety, season)

        assert bundle1.items[0].selected_product_id == bundle2.items[0].selected_product_id
        assert bundle1.items[0].score == bundle2.items[0].score
        assert bundle1.totals == bundle2.totals

    def test_returns_decision_bundle(self):
        engine = DecisionEngine()
        candidates = {"tomatoes": self._make_candidates()}

        bundle = engine.decide(candidates)

        assert isinstance(bundle, DecisionBundle)
        assert len(bundle.items) == 1
        assert bundle.totals["recommended"] > 0

    def test_neighbors_populated(self):
        engine = DecisionEngine()
        candidates = {"tomatoes": self._make_candidates()}

        bundle = engine.decide(candidates)
        item = bundle.items[0]

        # With 3 candidates at different prices, we should have neighbors
        # (depends on scoring, but at least one should exist)
        has_neighbor = (
            item.cheaper_neighbor_id is not None or
            item.conscious_neighbor_id is not None
        )
        assert has_neighbor


class TestDecisionEngineScoring:
    """Tests for soft scoring behavior."""

    def test_ewg_dirty_dozen_penalizes_non_organic(self):
        engine = DecisionEngine()
        candidates = [
            ProductCandidate("p1", "spinach", "Organic", "Brand", "5oz", 5.99, 1.2, organic=True),
            ProductCandidate("p2", "spinach", "Regular", "Brand", "5oz", 3.99, 0.8, organic=False),
        ]
        safety = SafetySignals(ewg_bucket="dirty_dozen", organic_recommended=True)

        bundle = engine.decide(
            {"spinach": candidates},
            safety_signals={"spinach": safety},
        )

        # Organic should score higher for dirty dozen
        item = bundle.items[0]
        assert item.selected_product_id == "p1"

    def test_peak_season_bonus(self):
        engine = DecisionEngine()
        candidates = [
            ProductCandidate("p1", "blueberries", "Berries", "Brand", "6oz", 4.99, 0.83),
        ]
        season_peak = SeasonalitySignal(status="peak", is_local=True)
        season_imported = SeasonalitySignal(status="imported", is_local=False)

        bundle_peak = engine.decide(
            {"blueberries": candidates},
            seasonality={"blueberries": season_peak},
        )
        bundle_imported = engine.decide(
            {"blueberries": candidates},
            seasonality={"blueberries": season_imported},
        )

        assert bundle_peak.items[0].score > bundle_imported.items[0].score

    def test_reason_short_populated(self):
        engine = DecisionEngine()
        candidates = [
            ProductCandidate("p1", "spinach", "Organic", "Brand", "5oz", 5.99, 1.2, organic=True),
        ]
        safety = SafetySignals(ewg_bucket="dirty_dozen")

        bundle = engine.decide(
            {"spinach": candidates},
            safety_signals={"spinach": safety},
        )

        assert bundle.items[0].reason_short != ""
        assert len(bundle.items[0].reason_short) <= 30


class TestDecisionEngineBundles:
    """Tests for cart-level bundle totals."""

    def test_totals_computed(self):
        engine = DecisionEngine()
        candidates = {
            "spinach": [
                ProductCandidate("s1", "spinach", "Organic", "B", "5oz", 5.99, 1.2, organic=True),
                ProductCandidate("s2", "spinach", "Regular", "B", "5oz", 2.99, 0.6),
            ],
            "onion": [
                ProductCandidate("o1", "onion", "Organic", "B", "32oz", 3.99, 0.125, organic=True),
                ProductCandidate("o2", "onion", "Regular", "B", "48oz", 1.99, 0.041),
            ],
        }

        bundle = engine.decide(candidates)

        assert "recommended" in bundle.totals
        assert "cheaper" in bundle.totals
        assert "conscious" in bundle.totals
        assert bundle.totals["recommended"] > 0

    def test_deltas_computed(self):
        engine = DecisionEngine()
        candidates = {
            "spinach": [
                ProductCandidate("s1", "spinach", "Organic", "B", "5oz", 5.99, 1.2, organic=True),
                ProductCandidate("s2", "spinach", "Regular", "B", "8oz", 1.99, 0.249),
            ],
        }

        bundle = engine.decide(candidates)

        assert "cheaper_vs_recommended" in bundle.deltas
        assert "conscious_vs_recommended" in bundle.deltas


# =============================================================================
# Orchestrator: Gating
# =============================================================================

class TestOrchestratorGating:
    """Tests for Orchestrator state machine and gating."""

    def test_full_flow_returns_bundle(self):
        from src.orchestrator.orchestrator import Orchestrator

        orch = Orchestrator()
        bundle = orch.process_prompt("chicken biryani for 4")

        assert isinstance(bundle, DecisionBundle)
        assert bundle.item_count > 0

    def test_step_by_step_flow(self):
        from src.orchestrator.orchestrator import Orchestrator

        orch = Orchestrator()

        # Step 1
        result = orch.step_ingredients("spinach salad", servings=2)
        assert orch.state.stage == "ingredients_extracted"

        # Gate
        orch.confirm_ingredients()
        assert orch.state.stage == "ingredients_confirmed"

        # Step 2
        orch.step_candidates()
        assert orch.state.stage == "candidates_fetched"

        # Step 3
        orch.step_enrich()
        assert orch.state.stage == "enriched"

        # Step 4
        bundle = orch.step_decide()
        assert isinstance(bundle, DecisionBundle)
        assert orch.state.stage == "decided"

    def test_candidates_gate_requires_confirmation(self):
        from src.orchestrator.orchestrator import Orchestrator

        orch = Orchestrator()
        orch.step_ingredients("spinach salad")

        # Try to get candidates without confirming
        result = orch.step_candidates()
        assert result.status == "error"

    def test_confirm_with_modifications(self):
        from src.orchestrator.orchestrator import Orchestrator

        orch = Orchestrator()
        orch.step_ingredients("spinach salad")

        # Override with custom ingredients
        custom = [{"name": "kale"}, {"name": "tomatoes"}]
        orch.confirm_ingredients(custom)

        assert orch.state.ingredients == custom
        assert orch.state.stage == "ingredients_confirmed"

    def test_bundle_totals_in_full_flow(self):
        from src.orchestrator.orchestrator import Orchestrator

        orch = Orchestrator()
        bundle = orch.process_prompt("spinach salad")

        assert bundle.totals["recommended"] > 0
        assert bundle.totals["cheaper"] > 0

    def test_tracker_records_spans(self):
        from src.orchestrator.orchestrator import Orchestrator

        orch = Orchestrator()
        orch.process_prompt("spinach salad")

        spans = orch.tracker.get_spans()
        span_names = [s.name for s in spans]
        assert "step_ingredients" in span_names
        assert "step_candidates" in span_names
        assert "step_enrich" in span_names
        assert "step_decide" in span_names


# =============================================================================
# Run directly
# =============================================================================

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
