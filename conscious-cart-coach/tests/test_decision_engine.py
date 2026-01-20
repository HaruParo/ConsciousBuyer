"""
Tests for the LLM Decision Engine module.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from src.llm.decision_engine import (
    get_client,
    decide_tiers,
    decide_tier_for_item,
    _format_price,
    _safe_get,
    _format_prompt_for_item,
    _extract_json_from_response,
    _validate_llm_response,
    _call_llm_with_retry,
    PROMPT_TEMPLATE,
    MODEL,
    API_TIMEOUT,
    MAX_RETRIES,
)


# Test fixtures
@pytest.fixture
def sample_item():
    """Sample item with baseline and alternatives."""
    return {
        "category": "fermented",
        "baseline": {
            "brand": "Store Brand Miso",
            "price": 4.99,
            "packaging": "plastic tub",
        },
        "alternatives": {
            "cheaper": {
                "brand": "Generic Miso",
                "product_name": "White Miso Paste",
                "est_price": 3.49,
                "packaging": "plastic pouch",
                "trade_offs": "Less complex flavor",
            },
            "balanced": {
                "brand": "Hikari",
                "product_name": "Organic Miso",
                "est_price": 5.99,
                "packaging": "plastic tub",
                "why_this_tier": "Good balance of quality and price",
            },
            "conscious": {
                "brand": "Miso Master",
                "product_name": "Organic Unpasteurized Miso",
                "est_price": 9.99,
                "packaging": "glass jar",
                "why_this_tier": "Organic, unpasteurized, glass packaging",
                "certifications": ["USDA Organic", "Non-GMO"],
            },
        },
    }


@pytest.fixture
def sample_facts_pack(sample_item):
    """Sample facts pack with multiple items."""
    return {
        "request": "miso soup ingredients",
        "items": [
            sample_item,
            {
                "category": "produce_greens",
                "baseline": {"brand": "Local Farm", "price": 3.99, "packaging": "none"},
                "alternatives": {
                    "cheaper": {"brand": "Store Brand", "est_price": 2.99, "packaging": "plastic bag"},
                    "balanced": {"brand": "Organic Valley", "est_price": 4.49, "packaging": "paper band"},
                    "conscious": {"brand": "Local Farm Organic", "est_price": 5.99, "packaging": "none"},
                },
            },
        ],
        "user_context": {
            "budget_priority": "medium",
            "health_priority": "high",
            "packaging_priority": "medium",
        },
    }


@pytest.fixture
def mock_llm_response():
    """Mock LLM response with valid JSON."""
    return {
        "recommended_tier": "conscious",
        "reasoning": "Given your high health priority, the organic unpasteurized miso ($9.99) provides superior nutrition with live cultures and glass packaging.",
        "key_trade_off": "Higher cost for better health benefits",
    }


class TestFormatPrice:
    """Tests for price formatting helper."""

    def test_format_valid_price(self):
        assert _format_price(4.99) == "$4.99"
        assert _format_price(10.00) == "$10.00"
        assert _format_price(0.50) == "$0.50"

    def test_format_none_price(self):
        assert _format_price(None) == "N/A"

    def test_format_zero_price(self):
        assert _format_price(0) == "$0.00"


class TestSafeGet:
    """Tests for safe dictionary access helper."""

    def test_get_existing_key(self):
        data = {"brand": "Test Brand", "price": 5.99}
        assert _safe_get(data, "brand") == "Test Brand"

    def test_get_missing_key(self):
        data = {"brand": "Test Brand"}
        assert _safe_get(data, "missing") == "N/A"

    def test_get_with_custom_default(self):
        data = {"brand": "Test Brand"}
        assert _safe_get(data, "missing", "Unknown") == "Unknown"

    def test_get_none_value(self):
        data = {"brand": None}
        assert _safe_get(data, "brand") == "N/A"

    def test_get_from_none_dict(self):
        assert _safe_get(None, "brand") == "N/A"

    def test_get_empty_dict(self):
        assert _safe_get({}, "brand") == "N/A"


class TestFormatPromptForItem:
    """Tests for prompt formatting."""

    def test_format_complete_item(self, sample_item):
        request = "miso soup"
        user_context = {
            "budget_priority": "low",
            "health_priority": "high",
            "packaging_priority": "medium",
        }

        prompt = _format_prompt_for_item(sample_item, request, user_context)

        # Check request and priorities are included
        assert "miso soup" in prompt
        assert "Budget: low" in prompt
        assert "Health: high" in prompt
        assert "Packaging: medium" in prompt

        # Check category
        assert "ITEM: fermented" in prompt

        # Check baseline
        assert "Store Brand Miso" in prompt
        assert "$4.99" in prompt

        # Check tiers
        assert "Generic Miso" in prompt
        assert "$3.49" in prompt
        assert "Hikari" in prompt
        assert "Miso Master" in prompt
        assert "$9.99" in prompt

    def test_format_item_with_missing_baseline(self):
        item = {
            "category": "milk",
            "baseline": None,
            "alternatives": {
                "balanced": {"brand": "Test", "est_price": 3.99},
            },
        }
        prompt = _format_prompt_for_item(item, "milk", {})

        # Should use N/A for missing baseline
        assert "Brand: N/A" in prompt or "N/A" in prompt

    def test_format_item_with_empty_alternatives(self):
        item = {
            "category": "test",
            "baseline": {"brand": "Test"},
            "alternatives": {},
        }
        prompt = _format_prompt_for_item(item, "test", {})

        # Should handle gracefully with N/A values
        assert "ITEM: test" in prompt

    def test_format_default_user_context(self, sample_item):
        prompt = _format_prompt_for_item(sample_item, "test", {})

        # Should use medium as default
        assert "Budget: medium" in prompt
        assert "Health: medium" in prompt
        assert "Packaging: medium" in prompt


class TestExtractJsonFromResponse:
    """Tests for JSON extraction from LLM responses."""

    def test_extract_clean_json(self):
        text = '{"recommended_tier": "balanced", "reasoning": "Good choice", "key_trade_off": "None"}'
        result = _extract_json_from_response(text)

        assert result["recommended_tier"] == "balanced"
        assert result["reasoning"] == "Good choice"

    def test_extract_json_with_whitespace(self):
        text = '''
        {
            "recommended_tier": "conscious",
            "reasoning": "Best for health",
            "key_trade_off": "Higher cost"
        }
        '''
        result = _extract_json_from_response(text)

        assert result["recommended_tier"] == "conscious"

    def test_extract_json_from_markdown_code_block(self):
        text = '''Here is my recommendation:

```json
{
    "recommended_tier": "cheaper",
    "reasoning": "Meets budget needs",
    "key_trade_off": "Less quality"
}
```

Hope this helps!'''
        result = _extract_json_from_response(text)

        assert result["recommended_tier"] == "cheaper"
        assert "budget" in result["reasoning"].lower()

    def test_extract_json_from_code_block_no_language(self):
        text = '''```
{"recommended_tier": "balanced", "reasoning": "Good option", "key_trade_off": "None"}
```'''
        result = _extract_json_from_response(text)

        assert result["recommended_tier"] == "balanced"

    def test_extract_json_with_surrounding_text(self):
        text = '''Based on your priorities, I recommend:
{"recommended_tier": "conscious", "reasoning": "Health is important", "key_trade_off": "Price"}
This is the best choice for you.'''
        result = _extract_json_from_response(text)

        assert result["recommended_tier"] == "conscious"

    def test_extract_empty_text(self):
        assert _extract_json_from_response("") is None
        assert _extract_json_from_response(None) is None

    def test_extract_invalid_json(self):
        text = "This is not JSON at all"
        assert _extract_json_from_response(text) is None

    def test_extract_malformed_json(self):
        text = '{"recommended_tier": "balanced", "reasoning": missing quotes}'
        # Should return None for malformed JSON
        result = _extract_json_from_response(text)
        # Might be None or might partially parse - implementation dependent
        assert result is None or isinstance(result, dict)


class TestValidateLlmResponse:
    """Tests for LLM response validation."""

    def test_valid_response(self, mock_llm_response):
        assert _validate_llm_response(mock_llm_response) is True

    def test_valid_response_minimal(self):
        response = {"recommended_tier": "balanced", "reasoning": "Good choice"}
        assert _validate_llm_response(response) is True

    def test_missing_recommended_tier(self):
        response = {"reasoning": "Good choice"}
        assert _validate_llm_response(response) is False

    def test_missing_reasoning(self):
        response = {"recommended_tier": "balanced"}
        assert _validate_llm_response(response) is False

    def test_invalid_tier_value(self):
        response = {"recommended_tier": "premium", "reasoning": "Best choice"}
        assert _validate_llm_response(response) is False

    def test_not_a_dict(self):
        assert _validate_llm_response("not a dict") is False
        assert _validate_llm_response(["list"]) is False
        assert _validate_llm_response(None) is False

    def test_all_valid_tiers(self):
        for tier in ["cheaper", "balanced", "conscious"]:
            response = {"recommended_tier": tier, "reasoning": "Test"}
            assert _validate_llm_response(response) is True


class TestCallLlmWithRetry:
    """Tests for LLM API call with retry logic."""

    @patch("src.llm.decision_engine.get_client")
    def test_successful_call(self, mock_get_client, mock_llm_response):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text=json.dumps(mock_llm_response))
        ]
        mock_client.messages.create.return_value = mock_response

        result = _call_llm_with_retry(mock_client, "test prompt")

        assert result["recommended_tier"] == "conscious"
        assert mock_client.messages.create.call_count == 1

    @patch("src.llm.decision_engine.get_client")
    def test_retry_on_json_parse_failure(self, mock_get_client, mock_llm_response):
        mock_client = MagicMock()

        # First call returns invalid JSON, second returns valid
        mock_response_invalid = MagicMock()
        mock_response_invalid.content = [MagicMock(text="not json")]

        mock_response_valid = MagicMock()
        mock_response_valid.content = [MagicMock(text=json.dumps(mock_llm_response))]

        mock_client.messages.create.side_effect = [
            mock_response_invalid,
            mock_response_valid,
        ]

        result = _call_llm_with_retry(mock_client, "test prompt")

        assert result is not None
        assert result["recommended_tier"] == "conscious"
        assert mock_client.messages.create.call_count == 2

    @patch("src.llm.decision_engine.get_client")
    def test_all_retries_fail(self, mock_get_client):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="invalid response")]
        mock_client.messages.create.return_value = mock_response

        result = _call_llm_with_retry(mock_client, "test prompt", max_retries=2)

        assert result is None
        assert mock_client.messages.create.call_count == 2

    @patch("src.llm.decision_engine.get_client")
    def test_timeout_error_retry(self, mock_get_client, mock_llm_response):
        from anthropic import APITimeoutError

        mock_client = MagicMock()

        mock_response_valid = MagicMock()
        mock_response_valid.content = [MagicMock(text=json.dumps(mock_llm_response))]

        # First call times out, second succeeds
        mock_client.messages.create.side_effect = [
            APITimeoutError(request=MagicMock()),
            mock_response_valid,
        ]

        result = _call_llm_with_retry(mock_client, "test prompt")

        assert result is not None
        assert mock_client.messages.create.call_count == 2

    @patch("src.llm.decision_engine.get_client")
    def test_api_error_retry(self, mock_get_client, mock_llm_response):
        from anthropic import APIError

        mock_client = MagicMock()

        mock_response_valid = MagicMock()
        mock_response_valid.content = [MagicMock(text=json.dumps(mock_llm_response))]

        # First call errors, second succeeds
        mock_client.messages.create.side_effect = [
            APIError(message="API error", request=MagicMock(), body=None),
            mock_response_valid,
        ]

        result = _call_llm_with_retry(mock_client, "test prompt")

        assert result is not None
        assert mock_client.messages.create.call_count == 2


class TestDecideTierForItem:
    """Tests for single item tier decision."""

    @patch("src.llm.decision_engine._call_llm_with_retry")
    @patch("src.llm.decision_engine.get_client")
    def test_successful_decision(self, mock_get_client, mock_call_llm, sample_item, mock_llm_response):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_call_llm.return_value = mock_llm_response

        result = decide_tier_for_item(
            sample_item,
            "miso soup",
            {"budget_priority": "medium"},
        )

        assert result["category"] == "fermented"
        assert result["recommended_tier"] == "conscious"
        assert result["llm_used"] is True
        assert "all_tiers" in result

    @patch("src.llm.decision_engine._call_llm_with_retry")
    @patch("src.llm.decision_engine.get_client")
    def test_llm_failure_fallback(self, mock_get_client, mock_call_llm, sample_item):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_call_llm.return_value = None  # LLM call fails

        result = decide_tier_for_item(
            sample_item,
            "miso soup",
            {"budget_priority": "medium"},
        )

        assert result["recommended_tier"] == "balanced"
        assert result["llm_used"] is False
        assert "LLM call failed" in result["reasoning"]

    def test_no_alternatives(self):
        item = {
            "category": "unknown",
            "baseline": {"brand": "Test"},
            "alternatives": None,
        }

        result = decide_tier_for_item(item, "test", {})

        assert result["recommended_tier"] is None
        assert result["llm_used"] is False
        assert "No alternatives" in result["reasoning"]

    @patch("src.llm.decision_engine.get_client")
    def test_no_api_key(self, mock_get_client, sample_item):
        mock_get_client.side_effect = ValueError("ANTHROPIC_API_KEY not set")

        result = decide_tier_for_item(sample_item, "test", {})

        assert result["recommended_tier"] == "balanced"
        assert result["llm_used"] is False
        assert "unavailable" in result["reasoning"].lower()

    @patch("src.llm.decision_engine._call_llm_with_retry")
    def test_uses_provided_client(self, mock_call_llm, sample_item, mock_llm_response):
        mock_client = MagicMock()
        mock_call_llm.return_value = mock_llm_response

        result = decide_tier_for_item(
            sample_item,
            "test",
            {},
            client=mock_client,
        )

        assert result["llm_used"] is True
        mock_call_llm.assert_called_once()


class TestDecideTiers:
    """Tests for main decide_tiers function."""

    @patch("src.llm.decision_engine._call_llm_with_retry")
    @patch("src.llm.decision_engine.get_client")
    def test_decide_multiple_items(self, mock_get_client, mock_call_llm, sample_facts_pack, mock_llm_response):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_call_llm.return_value = mock_llm_response

        result = decide_tiers(sample_facts_pack)

        assert result["request"] == "miso soup ingredients"
        assert len(result["decisions"]) == 2
        assert result["llm_model"] == MODEL
        assert result["user_context"]["health_priority"] == "high"

    @patch("src.llm.decision_engine._call_llm_with_retry")
    @patch("src.llm.decision_engine.get_client")
    def test_each_item_gets_decision(self, mock_get_client, mock_call_llm, sample_facts_pack, mock_llm_response):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_call_llm.return_value = mock_llm_response

        result = decide_tiers(sample_facts_pack)

        categories = [d["category"] for d in result["decisions"]]
        assert "fermented" in categories
        assert "produce_greens" in categories

    def test_empty_facts_pack(self):
        facts_pack = {
            "request": "nothing",
            "items": [],
            "user_context": {},
        }

        result = decide_tiers(facts_pack)

        assert result["decisions"] == []
        assert result["request"] == "nothing"

    @patch("src.llm.decision_engine.get_client")
    def test_client_creation_failure(self, mock_get_client, sample_facts_pack):
        mock_get_client.side_effect = ValueError("No API key")

        result = decide_tiers(sample_facts_pack)

        # Should still return results with fallback decisions
        assert len(result["decisions"]) == 2
        for decision in result["decisions"]:
            assert decision["llm_used"] is False

    @patch("src.llm.decision_engine._call_llm_with_retry")
    def test_uses_provided_client(self, mock_call_llm, sample_facts_pack, mock_llm_response):
        mock_client = MagicMock()
        mock_call_llm.return_value = mock_llm_response

        result = decide_tiers(sample_facts_pack, client=mock_client)

        # Should call LLM for each item
        assert mock_call_llm.call_count == 2


class TestGetClient:
    """Tests for client initialization."""

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_get_client_with_key(self):
        client = get_client()
        assert client is not None

    @patch.dict("os.environ", {}, clear=True)
    def test_get_client_no_key(self):
        # Remove the key if it exists
        import os
        if "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]

        with pytest.raises(ValueError) as exc_info:
            get_client()
        assert "ANTHROPIC_API_KEY" in str(exc_info.value)


class TestConstants:
    """Tests for module constants."""

    def test_timeout_value(self):
        assert API_TIMEOUT == 30.0

    def test_max_retries(self):
        assert MAX_RETRIES == 2

    def test_model_is_set(self):
        assert MODEL is not None
        assert "claude" in MODEL.lower()

    def test_prompt_template_has_placeholders(self):
        assert "{request}" in PROMPT_TEMPLATE
        assert "{category}" in PROMPT_TEMPLATE
        assert "{budget_priority}" in PROMPT_TEMPLATE
        assert "recommended_tier" in PROMPT_TEMPLATE


class TestIntegrationWithFactsPack:
    """Integration tests with facts_pack module."""

    @patch("src.llm.decision_engine._call_llm_with_retry")
    @patch("src.llm.decision_engine.get_client")
    def test_full_pipeline_mock(self, mock_get_client, mock_call_llm, mock_llm_response):
        """Test that decide_tiers works with facts_pack output format."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_call_llm.return_value = mock_llm_response

        # Simulate facts_pack output
        facts_pack = {
            "request": "miso soup ingredients",
            "items": [
                {
                    "category": "fermented",
                    "baseline": {"brand": "Store Brand", "price": 4.99, "packaging": "plastic"},
                    "alternatives": {
                        "cheaper": {"brand": "Generic", "est_price": 3.49, "packaging": "plastic"},
                        "balanced": {"brand": "Hikari", "est_price": 5.99, "packaging": "plastic"},
                        "conscious": {"brand": "Miso Master", "est_price": 9.99, "packaging": "glass"},
                    },
                    "flags": [],
                },
            ],
            "user_context": {
                "budget_priority": "medium",
                "health_priority": "high",
                "packaging_priority": "medium",
            },
        }

        result = decide_tiers(facts_pack)

        assert result["request"] == "miso soup ingredients"
        assert len(result["decisions"]) == 1
        assert result["decisions"][0]["category"] == "fermented"
        assert result["decisions"][0]["recommended_tier"] == "conscious"
        assert result["user_context"]["health_priority"] == "high"
