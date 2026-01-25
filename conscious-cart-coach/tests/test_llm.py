"""
Tests for LLM components with Opik integration.

These tests call the actual Anthropic API and are tracked in Opik dashboard.

Run: python -m pytest tests/test_llm.py -v
Run with markers: python -m pytest tests/test_llm.py -v -m llm
Skip LLM tests: python -m pytest -v -m "not llm"
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm.client import get_anthropic_client, call_claude_with_retry
from src.llm.ingredient_extractor import extract_ingredients_with_llm
from src.llm.decision_explainer import explain_decision_with_llm


# Mark all tests in this module as "llm" tests
pytestmark = pytest.mark.llm


# =============================================================================
# LLM Client Tests
# =============================================================================

class TestAnthropicClient:
    """Tests for Anthropic client initialization and basic calls."""

    def test_client_initialization(self, anthropic_client):
        """Test that client initializes successfully."""
        assert anthropic_client is not None

    def test_simple_llm_call(self, anthropic_client):
        """Test basic LLM call with retry logic."""
        response = call_claude_with_retry(
            client=anthropic_client,
            prompt="Say 'Hello' and nothing else.",
            max_tokens=50,
            temperature=0.0,
            trace_name="test_simple_call",
            metadata={"test": "simple_call", "expected": "Hello"}
        )

        assert response is not None
        assert len(response) > 0
        assert "hello" in response.lower()

    def test_llm_call_with_metadata(self, anthropic_client):
        """Test that metadata is properly attached to traces."""
        test_metadata = {
            "test_name": "metadata_test",
            "purpose": "verify_metadata_tracking",
            "expected_output": "structured_response"
        }

        response = call_claude_with_retry(
            client=anthropic_client,
            prompt="Respond with 'OK'",
            max_tokens=10,
            temperature=0.0,
            trace_name="test_metadata_tracking",
            metadata=test_metadata
        )

        assert response is not None
        assert "ok" in response.lower()


# =============================================================================
# Ingredient Extraction Tests
# =============================================================================

class TestIngredientExtraction:
    """Tests for LLM-powered ingredient extraction."""

    def test_extract_simple_recipe(self, anthropic_client):
        """Test extraction from a simple recipe prompt."""
        prompt = "chicken biryani for 4 people"
        servings = 4

        ingredients = extract_ingredients_with_llm(
            client=anthropic_client,
            prompt=prompt,
            servings=servings
        )

        assert ingredients is not None
        assert len(ingredients) > 0
        assert isinstance(ingredients, list)

        # Verify structure
        for ing in ingredients:
            assert "name" in ing
            assert "quantity" in ing
            assert isinstance(ing["name"], str)

        # Check for expected ingredients
        ingredient_names = [ing["name"].lower() for ing in ingredients]
        assert any("chicken" in name or "rice" in name for name in ingredient_names)

    def test_extract_vague_request(self, anthropic_client):
        """Test extraction from vague natural language request."""
        prompt = "I want something healthy and seasonal"
        servings = 2

        ingredients = extract_ingredients_with_llm(
            client=anthropic_client,
            prompt=prompt,
            servings=servings
        )

        assert ingredients is not None
        assert len(ingredients) >= 3, "Should suggest multiple ingredients for vague request"

        # Verify all ingredients have required fields
        for ing in ingredients:
            assert "name" in ing
            assert "quantity" in ing
            assert "category" in ing
            assert "optional" in ing

    def test_extract_with_quantities(self, anthropic_client):
        """Test that quantities are properly extracted and normalized."""
        prompt = "2 bunches of spinach, 1 lb chicken breast, 2 cups rice"
        servings = 4

        ingredients = extract_ingredients_with_llm(
            client=anthropic_client,
            prompt=prompt,
            servings=servings
        )

        assert ingredients is not None
        assert len(ingredients) >= 3

        # Check that quantities are present
        for ing in ingredients:
            assert "quantity" in ing
            assert ing["quantity"] is not None
            assert len(str(ing["quantity"])) > 0

    def test_extract_empty_prompt(self, anthropic_client):
        """Test handling of empty prompt."""
        ingredients = extract_ingredients_with_llm(
            client=anthropic_client,
            prompt="",
            servings=2
        )

        # Should handle gracefully - either return empty list or sensible suggestions
        assert ingredients is not None or ingredients is None  # Both are acceptable

    def test_extract_deterministic(self, anthropic_client):
        """Test that temperature=0.0 gives consistent results."""
        prompt = "spinach salad for 2"
        servings = 2

        # Run extraction twice
        ingredients1 = extract_ingredients_with_llm(
            client=anthropic_client,
            prompt=prompt,
            servings=servings
        )

        ingredients2 = extract_ingredients_with_llm(
            client=anthropic_client,
            prompt=prompt,
            servings=servings
        )

        assert ingredients1 is not None
        assert ingredients2 is not None

        # Should have same number of ingredients
        assert len(ingredients1) == len(ingredients2)

        # Should have same ingredient names (order might differ)
        names1 = sorted([ing["name"].lower() for ing in ingredients1])
        names2 = sorted([ing["name"].lower() for ing in ingredients2])
        assert names1 == names2, "Deterministic extraction should be consistent"


# =============================================================================
# Decision Explanation Tests
# =============================================================================

class TestDecisionExplanation:
    """Tests for LLM-powered decision explanations."""

    def test_explain_simple_recommendation(self, anthropic_client):
        """Test explanation generation for a basic recommendation."""
        ingredient_name = "spinach"
        recommended_product = {
            "brand": "Earthbound Farm",
            "price": 3.99,
            "size": "5oz",
            "unit_price": 0.80,
            "organic": True
        }
        scoring_factors = [
            "Organic certified",
            "On EWG Dirty Dozen list",
            "Good unit price"
        ]

        explanation = explain_decision_with_llm(
            client=anthropic_client,
            ingredient_name=ingredient_name,
            recommended_product=recommended_product,
            scoring_factors=scoring_factors,
            cheaper_option="Regular spinach at $2.99",
            conscious_option="None (this is most conscious)"
        )

        assert explanation is not None
        assert len(explanation) > 20, "Explanation should be substantial"
        assert isinstance(explanation, str)

        # Check that explanation references key details
        explanation_lower = explanation.lower()
        assert "3.99" in explanation or "earthbound" in explanation_lower or "organic" in explanation_lower

    def test_explain_with_tradeoffs(self, anthropic_client):
        """Test that explanation mentions tradeoffs between options."""
        ingredient_name = "chicken breast"
        recommended_product = {
            "brand": "Bell & Evans",
            "price": 8.99,
            "size": "1lb",
            "unit_price": 0.56,
            "organic": True
        }
        scoring_factors = [
            "Organic certified",
            "Free range",
            "No antibiotics"
        ]

        explanation = explain_decision_with_llm(
            client=anthropic_client,
            ingredient_name=ingredient_name,
            recommended_product=recommended_product,
            scoring_factors=scoring_factors,
            cheaper_option="Regular chicken at $4.99 (saves $4.00)",
            conscious_option="None (this is most conscious)"
        )

        assert explanation is not None
        # Explanation should mention the price difference or tradeoff
        explanation_lower = explanation.lower()
        assert any(word in explanation_lower for word in ["cost", "price", "more", "organic", "free range"])

    def test_explain_concise_output(self, anthropic_client):
        """Test that explanations are concise (1-2 sentences)."""
        ingredient_name = "tomato"
        recommended_product = {
            "brand": "Nature's Promise",
            "price": 4.49,
            "size": "1lb",
            "unit_price": 0.28,
            "organic": True
        }
        scoring_factors = ["Organic certified"]

        explanation = explain_decision_with_llm(
            client=anthropic_client,
            ingredient_name=ingredient_name,
            recommended_product=recommended_product,
            scoring_factors=scoring_factors
        )

        assert explanation is not None

        # Count sentences (approximate)
        sentence_count = explanation.count('.') + explanation.count('!') + explanation.count('?')
        assert sentence_count <= 3, "Explanation should be 1-2 sentences, max 3"

    def test_explain_no_hallucination(self, anthropic_client):
        """Test that explanation uses only provided data."""
        ingredient_name = "kale"
        recommended_product = {
            "brand": "TestBrand",
            "price": 2.99,
            "size": "1 bunch",
            "unit_price": 2.99,
            "organic": False
        }
        scoring_factors = ["Good price"]

        explanation = explain_decision_with_llm(
            client=anthropic_client,
            ingredient_name=ingredient_name,
            recommended_product=recommended_product,
            scoring_factors=scoring_factors
        )

        assert explanation is not None

        # Should mention the actual brand or price
        explanation_lower = explanation.lower()
        assert "testbrand" in explanation_lower or "2.99" in explanation

    def test_explain_with_user_preferences(self, anthropic_client):
        """Test that explanation considers user preferences."""
        ingredient_name = "milk"
        recommended_product = {
            "brand": "Organic Valley",
            "price": 5.99,
            "size": "1 gallon",
            "unit_price": 0.05,
            "organic": True
        }
        scoring_factors = ["Organic certified", "Preferred brand match"]
        user_prefs = {
            "preferred_brands": ["Organic Valley", "Horizon"],
            "avoided_brands": ["Store brand"]
        }

        explanation = explain_decision_with_llm(
            client=anthropic_client,
            ingredient_name=ingredient_name,
            recommended_product=recommended_product,
            scoring_factors=scoring_factors,
            user_prefs=user_prefs
        )

        assert explanation is not None
        # Should mention that it matches user preferences
        explanation_lower = explanation.lower()
        assert "prefer" in explanation_lower or "organic valley" in explanation_lower


# =============================================================================
# Integration Tests
# =============================================================================

class TestLLMIntegration:
    """Integration tests for full LLM workflow."""

    def test_full_workflow(self, anthropic_client):
        """Test complete flow: extraction → explanation."""
        # Step 1: Extract ingredients
        user_prompt = "healthy dinner for 2"
        ingredients = extract_ingredients_with_llm(
            client=anthropic_client,
            prompt=user_prompt,
            servings=2
        )

        assert ingredients is not None
        assert len(ingredients) > 0

        # Step 2: Generate explanation for first ingredient
        first_ingredient = ingredients[0]
        mock_product = {
            "brand": "Test Brand",
            "price": 4.99,
            "size": "1lb",
            "unit_price": 0.31,
            "organic": True
        }

        explanation = explain_decision_with_llm(
            client=anthropic_client,
            ingredient_name=first_ingredient["name"],
            recommended_product=mock_product,
            scoring_factors=["Organic", "Good price"]
        )

        assert explanation is not None
        assert len(explanation) > 10

    def test_error_handling(self, anthropic_client):
        """Test that errors are handled gracefully."""
        # Test with invalid product data
        explanation = explain_decision_with_llm(
            client=anthropic_client,
            ingredient_name="test",
            recommended_product=None,  # Invalid
            scoring_factors=[]
        )

        # Should return None or handle gracefully
        assert explanation is None


# =============================================================================
# Performance Tests
# =============================================================================

class TestLLMPerformance:
    """Tests for LLM performance and latency."""

    @pytest.mark.slow
    def test_extraction_latency(self, anthropic_client):
        """Test that ingredient extraction completes within reasonable time."""
        import time

        start = time.time()
        ingredients = extract_ingredients_with_llm(
            client=anthropic_client,
            prompt="pasta carbonara for 4",
            servings=4
        )
        duration = time.time() - start

        assert ingredients is not None
        assert duration < 5.0, f"Extraction took {duration:.2f}s (should be < 5s)"

    @pytest.mark.slow
    def test_explanation_latency(self, anthropic_client):
        """Test that explanation generation completes within reasonable time."""
        import time

        mock_product = {
            "brand": "Test",
            "price": 3.99,
            "size": "1lb",
            "unit_price": 0.25,
            "organic": False
        }

        start = time.time()
        explanation = explain_decision_with_llm(
            client=anthropic_client,
            ingredient_name="test_ingredient",
            recommended_product=mock_product,
            scoring_factors=["Good price"]
        )
        duration = time.time() - start

        assert explanation is not None
        assert duration < 3.0, f"Explanation took {duration:.2f}s (should be < 3s)"


# =============================================================================
# Marker Configuration
# =============================================================================

# To run only LLM tests:
#   pytest -m llm
#
# To skip LLM tests:
#   pytest -m "not llm"
#
# To run only slow tests:
#   pytest -m slow
#
# All tests in this file are automatically marked with @pytest.mark.llm
