"""
Tests for the rules module.
Verifies tier selection logic is deterministic and correct.
"""

import pytest

from src.data_processing.rules import (
    apply_rules,
    select_tier_for_item,
    score_packaging,
    score_tier_packaging,
    has_certifications,
    get_tier_price,
    PACKAGING_SCORES,
    CHEAP_THRESHOLD,
)


# Test fixtures
@pytest.fixture
def sample_alternatives():
    """Sample alternatives data for testing."""
    return {
        "cheaper": {
            "brand": "Store Brand",
            "product_name": "Basic Miso",
            "est_price": 4.99,
            "packaging": "plastic tub",
            "certifications": [],
        },
        "balanced": {
            "brand": "Miso Master",
            "product_name": "Organic Miso",
            "est_price": 7.99,
            "packaging": "glass jar",
            "certifications": ["USDA Organic"],
        },
        "conscious": {
            "brand": "South River",
            "product_name": "Traditional Miso",
            "est_price": 14.99,
            "packaging": "glass jar, metal lid",
            "certifications": ["USDA Organic", "Non-GMO"],
        },
    }


@pytest.fixture
def sample_baseline():
    """Sample baseline data for testing."""
    return {
        "brand": "Miso Master",
        "price": 7.99,
        "packaging": "glass jar",
        "your_usual": True,
    }


@pytest.fixture
def sample_item(sample_alternatives, sample_baseline):
    """Sample item for testing."""
    return {
        "category": "fermented",
        "baseline": sample_baseline,
        "alternatives": sample_alternatives,
        "flags": [],
    }


@pytest.fixture
def sample_facts_pack(sample_item):
    """Sample facts pack for testing."""
    return {
        "request": "miso soup ingredients",
        "items": [sample_item],
        "user_context": {
            "budget_priority": "medium",
            "health_priority": "medium",
            "packaging_priority": "medium",
        },
    }


class TestScorePackaging:
    """Tests for packaging scoring."""

    def test_glass_highest_score(self):
        """Glass should have highest score."""
        assert score_packaging("glass jar") == 10
        assert score_packaging("Glass Bottle") == 10

    def test_metal_high_score(self):
        """Metal should have high score."""
        assert score_packaging("metal can") == 10
        assert score_packaging("aluminum tin") == 10

    def test_paper_good_score(self):
        """Paper/cardboard should have good score."""
        assert score_packaging("paper bag") == 8
        assert score_packaging("cardboard box") == 8

    def test_plastic_low_score(self):
        """Plastic should have low score."""
        assert score_packaging("plastic container") == 3
        assert score_packaging("plastic bag") == 3

    def test_styrofoam_lowest_score(self):
        """Styrofoam should have lowest score."""
        assert score_packaging("styrofoam tray") == 1
        assert score_packaging("polystyrene") == 1

    def test_empty_returns_default(self):
        """Empty string should return default score."""
        assert score_packaging("") == 4
        assert score_packaging(None) == 4

    def test_unknown_material_default(self):
        """Unknown material should return default score."""
        assert score_packaging("mystery material") == 4

    def test_mixed_materials_best_score(self):
        """Mixed materials should return best score."""
        # Glass jar with plastic lid - should score for glass
        assert score_packaging("glass jar, plastic lid") == 10


class TestScoreTierPackaging:
    """Tests for tier-level packaging scoring."""

    def test_score_from_packaging_string(self):
        """Score from simple packaging string."""
        tier = {"packaging": "glass jar"}
        assert score_tier_packaging(tier) == 10

    def test_score_from_packaging_details_good(self):
        """Score from packaging_details with good rating."""
        tier = {"packaging_details": {"packaging_rating": "good"}}
        assert score_tier_packaging(tier) == 10

    def test_score_from_packaging_details_poor(self):
        """Score from packaging_details with poor rating."""
        tier = {"packaging_details": {"packaging_rating": "poor"}}
        assert score_tier_packaging(tier) == 3

    def test_score_from_packaging_details_mixed(self):
        """Score from packaging_details with mixed rating."""
        tier = {"packaging_details": {"packaging_rating": "mixed"}}
        assert score_tier_packaging(tier) == 6

    def test_score_from_materials_list(self):
        """Score from materials list in packaging_details."""
        tier = {"packaging_details": {"materials": ["glass", "metal"]}}
        assert score_tier_packaging(tier) == 10

    def test_empty_tier_default(self):
        """Empty tier should return default score."""
        assert score_tier_packaging({}) == 4
        assert score_tier_packaging(None) == 4


class TestHasCertifications:
    """Tests for certification checking."""

    def test_has_organic_certification(self):
        """Organic certification should be detected."""
        tier = {"certifications": ["USDA Organic"]}
        assert has_certifications(tier) is True

    def test_has_non_gmo_certification(self):
        """Non-GMO certification should be detected."""
        tier = {"certifications": ["Non-GMO Project"]}
        assert has_certifications(tier) is True

    def test_has_fair_trade(self):
        """Fair trade certification should be detected."""
        tier = {"certifications": ["Fair Trade Certified"]}
        assert has_certifications(tier) is True

    def test_no_certifications(self):
        """Empty certifications should return False."""
        tier = {"certifications": []}
        assert has_certifications(tier) is False

    def test_none_tier(self):
        """None tier should return False."""
        assert has_certifications(None) is False
        assert has_certifications({}) is False

    def test_string_certifications(self):
        """Comma-separated string should work."""
        tier = {"certifications": "USDA Organic, Non-GMO"}
        assert has_certifications(tier) is True


class TestGetTierPrice:
    """Tests for price extraction."""

    def test_get_price(self):
        """Should extract price from tier."""
        tier = {"est_price": 7.99}
        assert get_tier_price(tier) == 7.99

    def test_get_price_integer(self):
        """Should handle integer price."""
        tier = {"est_price": 8}
        assert get_tier_price(tier) == 8.0

    def test_no_price(self):
        """Should return None when no price."""
        tier = {"brand": "Test"}
        assert get_tier_price(tier) is None

    def test_none_tier(self):
        """Should handle None tier."""
        assert get_tier_price(None) is None


class TestSelectTierForItem:
    """Tests for tier selection logic."""

    def test_default_balanced(self, sample_item):
        """Default (all medium) should select balanced."""
        context = {
            "budget_priority": "medium",
            "health_priority": "medium",
            "packaging_priority": "medium",
        }
        result = select_tier_for_item(sample_item, context)

        assert result["recommended_tier"] == "balanced"
        assert result["category"] == "fermented"
        assert "Your usual choice" in result["reasoning_points"]

    def test_high_budget_selects_cheaper(self, sample_item):
        """High budget priority should select cheaper tier."""
        context = {
            "budget_priority": "high",
            "health_priority": "medium",
            "packaging_priority": "medium",
        }
        result = select_tier_for_item(sample_item, context)

        assert result["recommended_tier"] == "cheaper"
        assert any("budget" in r.lower() or "cheaper" in r.lower() for r in result["reasoning_points"])

    def test_high_budget_stays_balanced_if_baseline_cheap(self, sample_item):
        """High budget should stay balanced if baseline already cheap."""
        sample_item["baseline"]["price"] = 2.50  # Below CHEAP_THRESHOLD
        context = {
            "budget_priority": "high",
            "health_priority": "medium",
            "packaging_priority": "medium",
        }
        result = select_tier_for_item(sample_item, context)

        assert result["recommended_tier"] == "balanced"
        assert any("already budget-friendly" in r.lower() for r in result["reasoning_points"])

    def test_high_packaging_selects_best_packaging(self, sample_item):
        """High packaging priority should select tier with best packaging."""
        context = {
            "budget_priority": "medium",
            "health_priority": "medium",
            "packaging_priority": "high",
        }
        result = select_tier_for_item(sample_item, context)

        # Both balanced and conscious have glass (score 10)
        # Should prefer conscious in tie
        assert result["recommended_tier"] in ("balanced", "conscious")
        assert any("packaging" in r.lower() for r in result["reasoning_points"])

    def test_high_packaging_prefers_glass_over_plastic(self, sample_item):
        """High packaging should prefer glass over plastic."""
        # Make cheaper the only option with glass
        sample_item["alternatives"]["cheaper"]["packaging"] = "glass bottle"
        sample_item["alternatives"]["balanced"]["packaging"] = "plastic tub"
        sample_item["alternatives"]["conscious"]["packaging"] = "plastic container"

        context = {
            "budget_priority": "medium",
            "health_priority": "medium",
            "packaging_priority": "high",
        }
        result = select_tier_for_item(sample_item, context)

        assert result["recommended_tier"] == "cheaper"

    def test_high_health_selects_conscious(self, sample_item):
        """High health priority should select conscious tier."""
        context = {
            "budget_priority": "medium",
            "health_priority": "high",
            "packaging_priority": "medium",
        }
        result = select_tier_for_item(sample_item, context)

        assert result["recommended_tier"] == "conscious"
        assert any("health" in r.lower() or "organic" in r.lower() or "certified" in r.lower()
                   for r in result["reasoning_points"])

    def test_high_health_no_conscious_stays_balanced(self, sample_item):
        """High health should stay balanced if no conscious tier."""
        del sample_item["alternatives"]["conscious"]
        context = {
            "budget_priority": "medium",
            "health_priority": "high",
            "packaging_priority": "medium",
        }
        result = select_tier_for_item(sample_item, context)

        assert result["recommended_tier"] == "balanced"

    def test_missing_alternatives(self):
        """Should handle missing alternatives gracefully."""
        item = {
            "category": "unknown",
            "baseline": None,
            "alternatives": None,
            "flags": [],
        }
        context = {"budget_priority": "medium", "health_priority": "medium", "packaging_priority": "medium"}
        result = select_tier_for_item(item, context)

        assert result["recommended_tier"] == "balanced"
        assert result["all_tiers"]["cheaper"] is None

    def test_deterministic_same_input_same_output(self, sample_item):
        """Same input should always produce same output."""
        context = {
            "budget_priority": "high",
            "health_priority": "medium",
            "packaging_priority": "medium",
        }

        results = [select_tier_for_item(sample_item, context) for _ in range(5)]

        # All results should be identical
        for result in results[1:]:
            assert result["recommended_tier"] == results[0]["recommended_tier"]
            assert result["reasoning_points"] == results[0]["reasoning_points"]


class TestApplyRules:
    """Tests for the main apply_rules function."""

    def test_apply_rules_basic(self, sample_facts_pack):
        """Basic apply_rules test."""
        result = apply_rules(sample_facts_pack)

        assert result["request"] == "miso soup ingredients"
        assert len(result["recommendations"]) == 1
        assert result["user_context"] == sample_facts_pack["user_context"]

    def test_apply_rules_multiple_items(self, sample_item):
        """Should process multiple items."""
        facts_pack = {
            "request": "test request",
            "items": [sample_item, sample_item.copy()],
            "user_context": {"budget_priority": "medium", "health_priority": "medium", "packaging_priority": "medium"},
        }
        result = apply_rules(facts_pack)

        assert len(result["recommendations"]) == 2

    def test_apply_rules_high_budget_all_items(self, sample_item):
        """High budget should apply to all items."""
        item2 = sample_item.copy()
        item2["category"] = "produce_greens"

        facts_pack = {
            "request": "test request",
            "items": [sample_item, item2],
            "user_context": {"budget_priority": "high", "health_priority": "medium", "packaging_priority": "medium"},
        }
        result = apply_rules(facts_pack)

        for rec in result["recommendations"]:
            assert rec["recommended_tier"] == "cheaper"

    def test_apply_rules_empty_items(self):
        """Should handle empty items list."""
        facts_pack = {
            "request": "empty",
            "items": [],
            "user_context": {"budget_priority": "medium", "health_priority": "medium", "packaging_priority": "medium"},
        }
        result = apply_rules(facts_pack)

        assert result["recommendations"] == []

    def test_apply_rules_preserves_all_tiers(self, sample_facts_pack):
        """Should preserve all tier data in output."""
        result = apply_rules(sample_facts_pack)
        rec = result["recommendations"][0]

        assert "all_tiers" in rec
        assert "cheaper" in rec["all_tiers"]
        assert "balanced" in rec["all_tiers"]
        assert "conscious" in rec["all_tiers"]

    def test_apply_rules_deterministic(self, sample_facts_pack):
        """apply_rules should be deterministic."""
        results = [apply_rules(sample_facts_pack) for _ in range(5)]

        for result in results[1:]:
            assert result == results[0]


class TestPriorityInteractions:
    """Tests for interactions between different priorities."""

    def test_budget_takes_precedence_over_packaging(self, sample_item):
        """Budget high should take precedence over packaging high."""
        context = {
            "budget_priority": "high",
            "health_priority": "medium",
            "packaging_priority": "high",  # This should be ignored
        }
        result = select_tier_for_item(sample_item, context)

        # Budget priority is checked first
        assert result["recommended_tier"] == "cheaper"

    def test_packaging_takes_precedence_over_health(self, sample_item):
        """Packaging high should take precedence over health high when budget is medium."""
        context = {
            "budget_priority": "medium",
            "health_priority": "high",  # This should be ignored
            "packaging_priority": "high",
        }
        result = select_tier_for_item(sample_item, context)

        # Packaging priority is checked second
        assert any("packaging" in r.lower() for r in result["reasoning_points"])

    def test_all_low_defaults_to_balanced(self, sample_item):
        """All low priorities should default to balanced."""
        context = {
            "budget_priority": "low",
            "health_priority": "low",
            "packaging_priority": "low",
        }
        result = select_tier_for_item(sample_item, context)

        assert result["recommended_tier"] == "balanced"


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_missing_user_context(self, sample_item):
        """Should handle missing user context."""
        result = select_tier_for_item(sample_item, {})
        assert result["recommended_tier"] == "balanced"

    def test_partial_alternatives(self, sample_item):
        """Should handle partial alternatives data."""
        del sample_item["alternatives"]["conscious"]
        context = {"budget_priority": "medium", "health_priority": "medium", "packaging_priority": "medium"}
        result = select_tier_for_item(sample_item, context)

        assert result["recommended_tier"] == "balanced"
        assert result["all_tiers"]["conscious"] is None

    def test_only_cheaper_available(self, sample_item):
        """Should handle only cheaper tier available."""
        sample_item["alternatives"] = {"cheaper": sample_item["alternatives"]["cheaper"]}
        context = {"budget_priority": "medium", "health_priority": "high", "packaging_priority": "medium"}
        result = select_tier_for_item(sample_item, context)

        # Should still default to balanced even if tier doesn't exist
        assert result["recommended_tier"] == "balanced"

    def test_price_at_threshold(self, sample_item):
        """Test price exactly at cheap threshold."""
        sample_item["baseline"]["price"] = CHEAP_THRESHOLD
        context = {"budget_priority": "high", "health_priority": "medium", "packaging_priority": "medium"}
        result = select_tier_for_item(sample_item, context)

        # At threshold should stay balanced
        assert result["recommended_tier"] == "balanced"

    def test_price_just_above_threshold(self, sample_item):
        """Test price just above cheap threshold."""
        sample_item["baseline"]["price"] = CHEAP_THRESHOLD + 0.01
        context = {"budget_priority": "high", "health_priority": "medium", "packaging_priority": "medium"}
        result = select_tier_for_item(sample_item, context)

        # Above threshold should go cheaper
        assert result["recommended_tier"] == "cheaper"

    def test_no_baseline_price(self, sample_item):
        """Should handle missing baseline price."""
        del sample_item["baseline"]["price"]
        context = {"budget_priority": "high", "health_priority": "medium", "packaging_priority": "medium"}
        result = select_tier_for_item(sample_item, context)

        # Should still select cheaper since no price to compare
        assert result["recommended_tier"] == "cheaper"


class TestReasoningPoints:
    """Tests for reasoning point generation."""

    def test_reasoning_includes_price(self, sample_item):
        """Reasoning should include price when relevant."""
        context = {"budget_priority": "high", "health_priority": "medium", "packaging_priority": "medium"}
        result = select_tier_for_item(sample_item, context)

        # Should mention price in reasoning
        assert any("$" in r for r in result["reasoning_points"])

    def test_reasoning_includes_packaging(self, sample_item):
        """Reasoning should include packaging when relevant."""
        context = {"budget_priority": "medium", "health_priority": "medium", "packaging_priority": "high"}
        result = select_tier_for_item(sample_item, context)

        assert any("packaging" in r.lower() for r in result["reasoning_points"])

    def test_reasoning_includes_certifications(self, sample_item):
        """Reasoning should include certifications for health priority."""
        context = {"budget_priority": "medium", "health_priority": "high", "packaging_priority": "medium"}
        result = select_tier_for_item(sample_item, context)

        # Should mention organic or certifications
        reasons_text = " ".join(result["reasoning_points"]).lower()
        assert "organic" in reasons_text or "certified" in reasons_text or "health" in reasons_text
