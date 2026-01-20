"""Tests for LLM output validator."""

import pytest

from src.data_processing.validator import (
    validate_decision,
    extract_prices_from_text,
    extract_brands_from_facts_pack,
    extract_prices_from_facts_pack,
    price_matches_facts_pack,
    is_dirty_dozen_item,
    is_clean_fifteen_item,
    check_dirty_dozen_tier_compliance,
    check_recall_compliance,
)


@pytest.fixture
def sample_facts_pack():
    """Sample facts_pack for testing."""
    return {
        "request": "miso soup ingredients",
        "items": [
            {
                "category": "fermented",
                "baseline": {
                    "brand": "Hikari",
                    "price": 5.99,
                    "packaging": "plastic tub",
                },
                "alternatives": {
                    "cheaper": {
                        "brand": "Marukome",
                        "product_name": "White Miso",
                        "est_price": 4.49,
                        "packaging": "plastic bag",
                        "certifications": [],
                    },
                    "balanced": {
                        "brand": "Hikari",
                        "product_name": "Organic Miso",
                        "est_price": 6.99,
                        "packaging": "glass jar",
                        "certifications": ["USDA Organic"],
                    },
                    "conscious": {
                        "brand": "Miso Master",
                        "product_name": "Unpasteurized Miso",
                        "est_price": 9.99,
                        "packaging": "glass jar",
                        "certifications": ["USDA Organic", "Non-GMO"],
                    },
                },
                "flags": [],
            },
            {
                "category": "produce_greens",
                "baseline": {
                    "brand": "Generic",
                    "price": 2.99,
                    "packaging": "plastic clamshell",
                },
                "alternatives": {
                    "cheaper": {
                        "brand": "Store Brand",
                        "product_name": "Green Onions",
                        "est_price": 1.29,
                        "packaging": "rubber band",
                        "certifications": [],
                    },
                    "balanced": {
                        "brand": "Organic Girl",
                        "product_name": "Organic Scallions",
                        "est_price": 2.49,
                        "packaging": "compostable wrap",
                        "certifications": ["USDA Organic"],
                    },
                    "conscious": {
                        "brand": "Local Farm",
                        "product_name": "Farm Fresh Scallions",
                        "est_price": 3.49,
                        "packaging": "none",
                        "certifications": ["USDA Organic", "Local"],
                    },
                },
                "flags": [],
            },
        ],
        "user_context": {
            "budget_priority": "medium",
            "health_priority": "medium",
            "packaging_priority": "medium",
        },
    }


class TestValidDecision:
    """Tests for valid decisions that should pass validation."""

    def test_valid_decision_passes(self, sample_facts_pack):
        """A properly formed decision with facts from facts_pack passes validation."""
        decision = {
            "recommended_tier": "balanced",
            "reasoning": "The Hikari Organic Miso at $6.99 offers good value with USDA Organic certification. The glass jar packaging is recyclable and the product maintains quality standards.",
            "key_trade_off": "Slightly higher price than cheaper option for organic certification",
        }

        is_valid, errors = validate_decision(decision, sample_facts_pack)

        assert is_valid is True
        assert errors == []

    def test_valid_decision_cheaper_tier(self, sample_facts_pack):
        """Valid decision with cheaper tier passes."""
        decision = {
            "recommended_tier": "cheaper",
            "reasoning": "The Marukome White Miso at $4.49 is the most budget-friendly option. While it lacks organic certification, it still provides good quality for the price.",
            "key_trade_off": "Lower cost but no organic certification",
        }

        is_valid, errors = validate_decision(decision, sample_facts_pack)

        assert is_valid is True
        assert errors == []

    def test_valid_decision_conscious_tier(self, sample_facts_pack):
        """Valid decision with conscious tier passes."""
        decision = {
            "recommended_tier": "conscious",
            "reasoning": "The Miso Master Unpasteurized Miso at $9.99 offers premium quality with USDA Organic and Non-GMO certifications in a glass jar.",
            "key_trade_off": "Higher price for maximum quality and sustainability",
        }

        is_valid, errors = validate_decision(decision, sample_facts_pack)

        assert is_valid is True
        assert errors == []

    def test_price_within_tolerance_passes(self, sample_facts_pack):
        """Price within $0.50 tolerance passes validation."""
        decision = {
            "recommended_tier": "balanced",
            "reasoning": "At approximately $7.00, the balanced option provides good value for organic miso paste in recyclable packaging.",
            "key_trade_off": "Small price premium for organic certification",
        }

        is_valid, errors = validate_decision(decision, sample_facts_pack)

        assert is_valid is True
        assert errors == []


class TestHallucinatedPrice:
    """Tests for decisions with hallucinated/invented prices."""

    def test_hallucinated_price_fails(self, sample_facts_pack):
        """Decision with a price not in facts_pack fails validation."""
        decision = {
            "recommended_tier": "balanced",
            "reasoning": "The organic miso at $12.99 offers excellent value with premium certifications and sustainable packaging options.",
            "key_trade_off": "Worth the investment for quality",
        }

        is_valid, errors = validate_decision(decision, sample_facts_pack)

        assert is_valid is False
        assert any("hallucinated price $12.99" in error for error in errors)

    def test_multiple_hallucinated_prices_fail(self, sample_facts_pack):
        """Decision with multiple invented prices reports all of them."""
        decision = {
            "recommended_tier": "balanced",
            "reasoning": "Compare the $15.99 premium option with the $0.25 budget choice. Both offer different value propositions.",
            "key_trade_off": "Price vs quality",
        }

        is_valid, errors = validate_decision(decision, sample_facts_pack)

        assert is_valid is False
        assert any("$15.99" in error for error in errors)
        assert any("$0.25" in error for error in errors)

    def test_slightly_off_price_within_tolerance(self, sample_facts_pack):
        """Price within $0.50 of facts_pack price passes."""
        decision = {
            "recommended_tier": "balanced",
            "reasoning": "The Hikari option at $7.25 provides good organic certification with quality packaging.",
            "key_trade_off": "Reasonable premium for organic",
        }

        is_valid, errors = validate_decision(decision, sample_facts_pack)

        assert is_valid is True
        assert errors == []


class TestInvalidTier:
    """Tests for decisions with invalid tier values."""

    def test_invalid_tier_fails(self, sample_facts_pack):
        """Decision with invalid tier value fails validation."""
        decision = {
            "recommended_tier": "premium",
            "reasoning": "This is a substantive reasoning that explains the choice based on the available facts and data.",
            "key_trade_off": "Quality over cost",
        }

        is_valid, errors = validate_decision(decision, sample_facts_pack)

        assert is_valid is False
        assert any("invalid recommended_tier 'premium'" in error for error in errors)

    def test_missing_tier_fails(self, sample_facts_pack):
        """Decision without recommended_tier fails validation."""
        decision = {
            "reasoning": "This is a substantive reasoning that explains the choice based on the available facts.",
            "key_trade_off": "Balance of factors",
        }

        is_valid, errors = validate_decision(decision, sample_facts_pack)

        assert is_valid is False
        assert any("missing recommended_tier" in error for error in errors)

    def test_empty_tier_fails(self, sample_facts_pack):
        """Decision with empty string tier fails validation."""
        decision = {
            "recommended_tier": "",
            "reasoning": "This is a substantive reasoning that explains the choice based on available facts.",
            "key_trade_off": "Cost vs sustainability",
        }

        is_valid, errors = validate_decision(decision, sample_facts_pack)

        assert is_valid is False
        assert any("missing recommended_tier" in error for error in errors)


class TestMissingReasoning:
    """Tests for decisions with missing or inadequate reasoning."""

    def test_missing_reasoning_fails(self, sample_facts_pack):
        """Decision without reasoning fails validation."""
        decision = {
            "recommended_tier": "balanced",
            "key_trade_off": "Quality vs price",
        }

        is_valid, errors = validate_decision(decision, sample_facts_pack)

        assert is_valid is False
        assert any("missing reasoning" in error for error in errors)

    def test_empty_reasoning_fails(self, sample_facts_pack):
        """Decision with empty reasoning fails validation."""
        decision = {
            "recommended_tier": "balanced",
            "reasoning": "",
            "key_trade_off": "Quality vs price",
        }

        is_valid, errors = validate_decision(decision, sample_facts_pack)

        assert is_valid is False
        assert any("missing reasoning" in error for error in errors)

    def test_short_reasoning_fails(self, sample_facts_pack):
        """Decision with reasoning <=20 characters fails validation."""
        decision = {
            "recommended_tier": "balanced",
            "reasoning": "It's good.",
            "key_trade_off": "Quality vs price",
        }

        is_valid, errors = validate_decision(decision, sample_facts_pack)

        assert is_valid is False
        assert any("reasoning too short" in error for error in errors)

    def test_reasoning_exactly_20_chars_fails(self, sample_facts_pack):
        """Reasoning with exactly 20 characters fails (must be >20)."""
        decision = {
            "recommended_tier": "balanced",
            "reasoning": "12345678901234567890",  # exactly 20 chars
            "key_trade_off": "Trade-off here",
        }

        is_valid, errors = validate_decision(decision, sample_facts_pack)

        assert is_valid is False
        assert any("reasoning too short" in error for error in errors)


class TestMissingKeyTradeOff:
    """Tests for decisions with missing key_trade_off."""

    def test_missing_key_trade_off_fails(self, sample_facts_pack):
        """Decision without key_trade_off fails validation."""
        decision = {
            "recommended_tier": "balanced",
            "reasoning": "The balanced option provides good value with organic certification and sustainable packaging.",
        }

        is_valid, errors = validate_decision(decision, sample_facts_pack)

        assert is_valid is False
        assert any("missing key_trade_off" in error for error in errors)

    def test_empty_key_trade_off_fails(self, sample_facts_pack):
        """Decision with empty key_trade_off fails validation."""
        decision = {
            "recommended_tier": "balanced",
            "reasoning": "The balanced option provides good value with organic certification.",
            "key_trade_off": "",
        }

        is_valid, errors = validate_decision(decision, sample_facts_pack)

        assert is_valid is False
        assert any("missing key_trade_off" in error for error in errors)


class TestHallucinatedCertifications:
    """Tests for decisions with hallucinated certifications."""

    def test_hallucinated_certification_fails(self, sample_facts_pack):
        """Decision mentioning certification not in facts_pack fails."""
        decision = {
            "recommended_tier": "balanced",
            "reasoning": "This product has Fair Trade certification and supports sustainable farming practices with excellent packaging.",
            "key_trade_off": "Premium for ethical sourcing",
        }

        is_valid, errors = validate_decision(decision, sample_facts_pack)

        assert is_valid is False
        assert any("hallucinated certification" in error.lower() for error in errors)


class TestMultipleErrors:
    """Tests for decisions with multiple validation failures."""

    def test_multiple_errors_reported(self, sample_facts_pack):
        """All validation errors are reported, not just the first one."""
        decision = {
            "recommended_tier": "ultra-premium",
            "reasoning": "Short",
            # missing key_trade_off
        }

        is_valid, errors = validate_decision(decision, sample_facts_pack)

        assert is_valid is False
        assert len(errors) >= 3  # invalid tier, short reasoning, missing key_trade_off


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_extract_prices_from_text(self):
        """extract_prices_from_text correctly finds dollar amounts."""
        text = "The product costs $5.99 or $6.00 for the larger size."
        prices = extract_prices_from_text(text)

        assert 5.99 in prices
        assert 6.00 in prices
        assert len(prices) == 2

    def test_extract_prices_no_prices(self):
        """extract_prices_from_text returns empty list when no prices."""
        text = "This product is affordable and high quality."
        prices = extract_prices_from_text(text)

        assert prices == []

    def test_extract_brands_from_facts_pack(self, sample_facts_pack):
        """extract_brands_from_facts_pack finds all brands."""
        brands = extract_brands_from_facts_pack(sample_facts_pack)

        assert "hikari" in brands
        assert "marukome" in brands
        assert "miso master" in brands
        assert "store brand" in brands
        assert "organic girl" in brands
        assert "local farm" in brands

    def test_extract_prices_from_facts_pack(self, sample_facts_pack):
        """extract_prices_from_facts_pack finds all prices."""
        prices = extract_prices_from_facts_pack(sample_facts_pack)

        assert 4.49 in prices
        assert 6.99 in prices
        assert 9.99 in prices
        assert 1.29 in prices
        assert 2.49 in prices
        assert 3.49 in prices

    def test_price_matches_within_tolerance(self):
        """price_matches_facts_pack returns True within tolerance."""
        facts_pack_prices = [5.99, 6.99, 9.99]

        assert price_matches_facts_pack(5.99, facts_pack_prices) is True
        assert price_matches_facts_pack(6.00, facts_pack_prices) is True  # within 0.50
        assert price_matches_facts_pack(6.49, facts_pack_prices) is True  # within 0.50 of 6.99
        assert price_matches_facts_pack(7.49, facts_pack_prices) is True  # within 0.50 of 6.99

    def test_price_does_not_match_outside_tolerance(self):
        """price_matches_facts_pack returns False outside tolerance."""
        facts_pack_prices = [5.99, 6.99, 9.99]

        assert price_matches_facts_pack(4.00, facts_pack_prices) is False
        assert price_matches_facts_pack(8.00, facts_pack_prices) is False
        assert price_matches_facts_pack(12.99, facts_pack_prices) is False


class TestEmptyFactsPack:
    """Tests with empty or minimal facts_pack."""

    def test_empty_items_list(self):
        """Validation with empty items list."""
        facts_pack = {"items": [], "request": "test", "user_context": {}}
        decision = {
            "recommended_tier": "balanced",
            "reasoning": "This is a valid reasoning with enough characters for validation.",
            "key_trade_off": "No specific trade-off",
        }

        is_valid, errors = validate_decision(decision, facts_pack)

        # Should pass basic validation but any price/cert mentions would fail
        assert is_valid is True

    def test_decision_with_price_against_empty_facts_pack(self):
        """Price in decision fails when facts_pack has no prices."""
        facts_pack = {"items": [], "request": "test", "user_context": {}}
        decision = {
            "recommended_tier": "balanced",
            "reasoning": "The product at $5.99 is a good choice for quality.",
            "key_trade_off": "Value for money",
        }

        is_valid, errors = validate_decision(decision, facts_pack)

        assert is_valid is False
        assert any("hallucinated price" in error for error in errors)


class TestEWGDirtyDozen:
    """Tests for EWG Dirty Dozen validation."""

    @pytest.fixture
    def spinach_facts_pack(self):
        """Facts pack with spinach (Dirty Dozen item)."""
        return {
            "request": "spinach for salad",
            "items": [
                {
                    "category": "produce_spinach",
                    "baseline": {"brand": "Generic", "price": 2.99, "packaging": "plastic"},
                    "alternatives": {
                        "cheaper": {
                            "brand": "Store Brand",
                            "product_name": "Conventional Spinach",
                            "est_price": 1.99,
                            "packaging": "plastic bag",
                            "certifications": [],
                        },
                        "balanced": {
                            "brand": "Earthbound",
                            "product_name": "Organic Baby Spinach",
                            "est_price": 3.99,
                            "packaging": "plastic clamshell",
                            "certifications": ["USDA Organic"],
                        },
                        "conscious": {
                            "brand": "Local Farm",
                            "product_name": "Organic Spinach Bunch",
                            "est_price": 4.99,
                            "packaging": "rubber band",
                            "certifications": ["USDA Organic", "Local"],
                        },
                    },
                    "flags": [],
                }
            ],
            "user_context": {},
        }

    def test_dirty_dozen_cheaper_non_organic_fails(self, spinach_facts_pack):
        """Recommending cheaper non-organic spinach fails (Dirty Dozen)."""
        decision = {
            "recommended_tier": "cheaper",
            "reasoning": "The Store Brand Conventional Spinach at $1.99 is the most affordable option for budget-conscious shoppers.",
            "key_trade_off": "Lower cost but no organic certification",
        }

        is_valid, errors = validate_decision(decision, spinach_facts_pack)

        assert is_valid is False
        assert any("Dirty Dozen" in error for error in errors)
        assert any("spinach" in error.lower() for error in errors)

    def test_dirty_dozen_balanced_organic_passes(self, spinach_facts_pack):
        """Recommending balanced organic spinach passes."""
        decision = {
            "recommended_tier": "balanced",
            "reasoning": "The Earthbound Organic Baby Spinach at $3.99 offers USDA Organic certification at a reasonable price point.",
            "key_trade_off": "Moderate price for organic certification",
        }

        is_valid, errors = validate_decision(decision, spinach_facts_pack)

        assert is_valid is True
        assert errors == []

    def test_dirty_dozen_conscious_passes(self, spinach_facts_pack):
        """Recommending conscious tier for Dirty Dozen passes."""
        decision = {
            "recommended_tier": "conscious",
            "reasoning": "The Local Farm Organic Spinach Bunch at $4.99 provides both organic certification and local sourcing.",
            "key_trade_off": "Higher price for organic and local benefits",
        }

        is_valid, errors = validate_decision(decision, spinach_facts_pack)

        assert is_valid is True
        assert errors == []

    def test_is_dirty_dozen_item_detection(self):
        """is_dirty_dozen_item correctly identifies Dirty Dozen items."""
        assert is_dirty_dozen_item("spinach") is True
        assert is_dirty_dozen_item("produce_spinach") is True
        assert is_dirty_dozen_item("strawberries") is True
        assert is_dirty_dozen_item("kale") is True
        assert is_dirty_dozen_item("bell_peppers") is True
        assert is_dirty_dozen_item("green_beans") is True

    def test_is_dirty_dozen_item_non_match(self):
        """is_dirty_dozen_item returns False for non-Dirty Dozen items."""
        assert is_dirty_dozen_item("avocado") is False
        assert is_dirty_dozen_item("onions") is False
        assert is_dirty_dozen_item("carrots") is False
        assert is_dirty_dozen_item("miso") is False

    def test_is_clean_fifteen_item_detection(self):
        """is_clean_fifteen_item correctly identifies Clean Fifteen items."""
        assert is_clean_fifteen_item("avocado") is True
        assert is_clean_fifteen_item("onions") is True
        assert is_clean_fifteen_item("carrots") is True
        assert is_clean_fifteen_item("sweet_corn") is True
        assert is_clean_fifteen_item("pineapple") is True


class TestRecallCompliance:
    """Tests for recall compliance validation."""

    @pytest.fixture
    def recalled_product_facts_pack(self):
        """Facts pack with a product that has an active recall."""
        return {
            "request": "tomatoes",
            "items": [
                {
                    "category": "produce_tomatoes",
                    "baseline": {"brand": "Generic", "price": 2.99, "packaging": "none"},
                    "alternatives": {
                        "cheaper": {
                            "brand": "Budget Brand",
                            "product_name": "Roma Tomatoes",
                            "est_price": 1.99,
                            "packaging": "none",
                            "certifications": [],
                        },
                        "balanced": {
                            "brand": "Quality Farms",
                            "product_name": "Vine Tomatoes",
                            "est_price": 3.49,
                            "packaging": "cardboard",
                            "certifications": [],
                        },
                        "conscious": {
                            "brand": "Organic Valley",
                            "product_name": "Organic Tomatoes",
                            "est_price": 4.99,
                            "packaging": "cardboard",
                            "certifications": ["USDA Organic"],
                        },
                    },
                    "flags": [
                        {
                            "type": "recall",
                            "affected_tiers": ["cheaper"],
                            "description": "Budget Brand tomatoes recalled due to contamination",
                            "date": "2025-12-01",
                        }
                    ],
                }
            ],
            "user_context": {},
        }

    def test_recommending_recalled_tier_fails(self, recalled_product_facts_pack):
        """Recommending a tier with active recall fails validation."""
        decision = {
            "recommended_tier": "cheaper",
            "reasoning": "The Budget Brand Roma Tomatoes at $1.99 offer the best value for everyday cooking needs.",
            "key_trade_off": "Lower cost for basic tomatoes",
        }

        is_valid, errors = validate_decision(decision, recalled_product_facts_pack)

        assert is_valid is False
        assert any("RECALL WARNING" in error for error in errors)

    def test_recommending_non_recalled_tier_passes(self, recalled_product_facts_pack):
        """Recommending a tier without recall passes validation."""
        decision = {
            "recommended_tier": "balanced",
            "reasoning": "The Quality Farms Vine Tomatoes at $3.49 provide good quality with sustainable cardboard packaging.",
            "key_trade_off": "Moderate price for better quality",
        }

        is_valid, errors = validate_decision(decision, recalled_product_facts_pack)

        assert is_valid is True
        assert errors == []

    def test_general_category_recall_warning(self):
        """Category-wide recall (no specific tier) generates warning."""
        facts_pack = {
            "request": "lettuce",
            "items": [
                {
                    "category": "produce_lettuce",
                    "alternatives": {
                        "cheaper": {"brand": "A", "est_price": 1.99, "certifications": []},
                        "balanced": {"brand": "B", "est_price": 2.99, "certifications": []},
                        "conscious": {"brand": "C", "est_price": 3.99, "certifications": []},
                    },
                    "flags": [
                        {
                            "type": "recall",
                            "description": "Multiple lettuce brands recalled",
                        }
                    ],
                }
            ],
            "user_context": {},
        }
        decision = {
            "recommended_tier": "balanced",
            "reasoning": "The B brand lettuce at $2.99 provides a good balance of quality and value for your salad needs.",
            "key_trade_off": "Mid-range option",
        }

        is_valid, errors = validate_decision(decision, facts_pack)

        assert is_valid is False
        assert any("RECALL WARNING" in error for error in errors)

    def test_no_recall_flags_passes(self, sample_facts_pack):
        """Products without recall flags pass recall validation."""
        decision = {
            "recommended_tier": "balanced",
            "reasoning": "The Hikari Organic Miso at $6.99 offers good value with USDA Organic certification.",
            "key_trade_off": "Reasonable premium for organic",
        }

        is_valid, errors = validate_decision(decision, sample_facts_pack)

        assert is_valid is True
        # No recall errors
        assert not any("RECALL" in error for error in errors)
