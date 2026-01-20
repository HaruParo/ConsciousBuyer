"""
LLM Decision Engine module.
Uses Claude for constrained reasoning to recommend product tiers.

This module combines deterministic rules with LLM reasoning for nuanced
tier recommendations based on user priorities and product data.
"""

import json
import logging
import os
import re
from typing import Optional

from anthropic import Anthropic, APITimeoutError, APIError

logger = logging.getLogger(__name__)

# Timeout for API calls (30 seconds)
API_TIMEOUT = 30.0

# Maximum retry attempts
MAX_RETRIES = 2

# Claude model to use
MODEL = "claude-sonnet-4-20250514"

# Prompt template for tier recommendation
PROMPT_TEMPLATE = """You are a conscious buying advisor helping users choose groceries.

USER REQUEST: {request}
USER PRIORITIES:
- Budget: {budget_priority}
- Health: {health_priority}
- Packaging: {packaging_priority}

For each item below, recommend ONE tier (cheaper/balanced/conscious) and explain why in 1-2 sentences.

ITEM: {category}

BASELINE (what user usually buys):
- Brand: {baseline_brand}
- Price: {baseline_price}
- Packaging: {baseline_packaging}

OPTIONS:
1. CHEAPER tier:
   - Brand: {cheaper_brand}
   - Price: {cheaper_price}
   - Packaging: {cheaper_packaging}
   - Trade-offs: {cheaper_trade_offs}

2. BALANCED tier:
   - Brand: {balanced_brand}
   - Price: {balanced_price}
   - Packaging: {balanced_packaging}
   - Notes: {balanced_notes}

3. CONSCIOUS tier:
   - Brand: {conscious_brand}
   - Price: {conscious_price}
   - Packaging: {conscious_packaging}
   - Why conscious: {conscious_why}

RULES:
- Choose the tier that best matches user priorities
- Reference specific facts (prices, packaging, certifications)
- Explain trade-offs clearly
- NO HALLUCINATION - only use provided data

OUTPUT FORMAT (JSON only, no markdown):
{{
  "recommended_tier": "cheaper|balanced|conscious",
  "reasoning": "1-2 sentence explanation referencing specific facts",
  "key_trade_off": "main consideration"
}}"""


def get_client() -> Anthropic:
    """Initialize and return Anthropic client."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return Anthropic(api_key=api_key)


def _format_price(price: Optional[float]) -> str:
    """Format price for display, handling None values."""
    if price is None:
        return "N/A"
    return f"${price:.2f}"


def _safe_get(data: Optional[dict], key: str, default: str = "N/A") -> str:
    """Safely get a value from a dict, returning default if not found."""
    if not data:
        return default
    value = data.get(key)
    if value is None:
        return default
    return str(value)


def _format_prompt_for_item(
    item: dict,
    request: str,
    user_context: dict,
) -> str:
    """
    Format the prompt template for a single item.

    Args:
        item: Item dict with category, baseline, alternatives
        request: Original user request
        user_context: User priorities dict

    Returns:
        Formatted prompt string
    """
    category = item.get("category", "unknown")
    baseline = item.get("baseline") or {}
    alternatives = item.get("alternatives") or {}

    cheaper = alternatives.get("cheaper") or {}
    balanced = alternatives.get("balanced") or {}
    conscious = alternatives.get("conscious") or {}

    return PROMPT_TEMPLATE.format(
        request=request,
        budget_priority=user_context.get("budget_priority", "medium"),
        health_priority=user_context.get("health_priority", "medium"),
        packaging_priority=user_context.get("packaging_priority", "medium"),
        category=category,
        # Baseline
        baseline_brand=_safe_get(baseline, "brand"),
        baseline_price=_format_price(baseline.get("price")),
        baseline_packaging=_safe_get(baseline, "packaging"),
        # Cheaper tier
        cheaper_brand=_safe_get(cheaper, "brand"),
        cheaper_price=_format_price(cheaper.get("est_price")),
        cheaper_packaging=_safe_get(cheaper, "packaging"),
        cheaper_trade_offs=_safe_get(cheaper, "trade_offs", "None noted"),
        # Balanced tier
        balanced_brand=_safe_get(balanced, "brand"),
        balanced_price=_format_price(balanced.get("est_price")),
        balanced_packaging=_safe_get(balanced, "packaging"),
        balanced_notes=_safe_get(balanced, "why_this_tier", "Good middle ground"),
        # Conscious tier
        conscious_brand=_safe_get(conscious, "brand"),
        conscious_price=_format_price(conscious.get("est_price")),
        conscious_packaging=_safe_get(conscious, "packaging"),
        conscious_why=_safe_get(conscious, "why_this_tier", "Premium quality option"),
    )


def _extract_json_from_response(text: str) -> Optional[dict]:
    """
    Extract JSON object from LLM response text.

    Handles cases where JSON might be wrapped in markdown code blocks
    or have extra text around it.

    Args:
        text: Raw response text from LLM

    Returns:
        Parsed JSON dict or None if parsing fails
    """
    if not text:
        return None

    # Try direct JSON parsing first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code block
    code_block_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find JSON object in text
    json_match = re.search(r'\{[^{}]*"recommended_tier"[^{}]*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    # Try more aggressive JSON extraction
    brace_start = text.find('{')
    brace_end = text.rfind('}')
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        try:
            return json.loads(text[brace_start:brace_end + 1])
        except json.JSONDecodeError:
            pass

    return None


def _validate_llm_response(response: dict) -> bool:
    """
    Validate that LLM response has required fields.

    Args:
        response: Parsed JSON response

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(response, dict):
        return False

    required_fields = ["recommended_tier", "reasoning"]
    for field in required_fields:
        if field not in response:
            return False

    valid_tiers = ["cheaper", "balanced", "conscious"]
    if response.get("recommended_tier") not in valid_tiers:
        return False

    return True


def _call_llm_with_retry(
    client: Anthropic,
    prompt: str,
    max_retries: int = MAX_RETRIES,
) -> Optional[dict]:
    """
    Call Claude API with retry logic.

    Args:
        client: Anthropic client
        prompt: Formatted prompt string
        max_retries: Maximum number of retry attempts

    Returns:
        Parsed and validated LLM response dict, or None on failure
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            logger.debug(f"LLM call attempt {attempt + 1}/{max_retries}")

            response = client.messages.create(
                model=MODEL,
                max_tokens=500,
                timeout=API_TIMEOUT,
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )

            # Extract text from response
            response_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    response_text += block.text

            logger.debug(f"LLM response: {response_text[:200]}...")

            # Parse JSON from response
            parsed = _extract_json_from_response(response_text)
            if parsed is None:
                logger.warning(f"Failed to parse JSON from response: {response_text[:100]}")
                last_error = "JSON parsing failed"
                continue

            # Validate response structure
            if not _validate_llm_response(parsed):
                logger.warning(f"Invalid response structure: {parsed}")
                last_error = "Response validation failed"
                continue

            return parsed

        except APITimeoutError as e:
            logger.warning(f"API timeout on attempt {attempt + 1}: {e}")
            last_error = f"Timeout: {e}"

        except APIError as e:
            logger.warning(f"API error on attempt {attempt + 1}: {e}")
            last_error = f"API error: {e}"

        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            last_error = f"Unexpected error: {e}"

    logger.error(f"All {max_retries} LLM call attempts failed. Last error: {last_error}")
    return None


def decide_tier_for_item(
    item: dict,
    request: str,
    user_context: dict,
    client: Optional[Anthropic] = None,
) -> dict:
    """
    Use LLM to decide the recommended tier for a single item.

    Args:
        item: Item dict with category, baseline, alternatives
        request: Original user request
        user_context: User priorities dict
        client: Optional Anthropic client (created if not provided)

    Returns:
        Decision dict with recommended_tier, reasoning, all_tiers
    """
    category = item.get("category", "unknown")
    alternatives = item.get("alternatives") or {}

    # Build base result with all tiers
    result = {
        "category": category,
        "all_tiers": {
            "cheaper": alternatives.get("cheaper"),
            "balanced": alternatives.get("balanced"),
            "conscious": alternatives.get("conscious"),
        },
    }

    # Check if we have alternatives to recommend
    if not alternatives:
        result["recommended_tier"] = None
        result["reasoning"] = "No alternatives available for this category"
        result["llm_used"] = False
        return result

    # Format prompt
    prompt = _format_prompt_for_item(item, request, user_context)

    # Get or create client
    if client is None:
        try:
            client = get_client()
        except ValueError as e:
            logger.error(f"Failed to create Anthropic client: {e}")
            result["recommended_tier"] = "balanced"
            result["reasoning"] = "LLM unavailable, defaulting to balanced tier"
            result["llm_used"] = False
            return result

    # Call LLM
    llm_response = _call_llm_with_retry(client, prompt)

    if llm_response:
        result["recommended_tier"] = llm_response.get("recommended_tier", "balanced")
        result["reasoning"] = llm_response.get("reasoning", "")
        result["key_trade_off"] = llm_response.get("key_trade_off", "")
        result["llm_used"] = True
    else:
        # Fallback to balanced if LLM fails
        result["recommended_tier"] = "balanced"
        result["reasoning"] = "LLM call failed, defaulting to balanced tier"
        result["llm_used"] = False
        logger.warning(f"LLM call failed for category '{category}', using default")

    return result


def decide_tiers(facts_pack: dict, client: Optional[Anthropic] = None) -> dict:
    """
    Use LLM for constrained reasoning to decide tiers for all items.

    This function processes a facts pack and returns tier recommendations
    for each item, using Claude for nuanced decision-making based on
    user priorities.

    Args:
        facts_pack: Facts pack from generate_facts_pack() containing:
            - request: Original user request string
            - items: List of item dicts with category, baseline, alternatives
            - user_context: User priorities dict

    Returns:
        Decision dict with:
            - request: Original request
            - decisions: List of decision dicts per item
            - user_context: User priorities used
            - llm_model: Model used for reasoning

    Example:
        >>> facts_pack = generate_facts_pack("miso soup ingredients")
        >>> result = decide_tiers(facts_pack)
        >>> for decision in result["decisions"]:
        ...     print(f"{decision['category']}: {decision['recommended_tier']}")
    """
    request = facts_pack.get("request", "")
    items = facts_pack.get("items", [])
    user_context = facts_pack.get("user_context", {})

    logger.info(f"Deciding tiers for {len(items)} items using LLM")

    # Create client once for all items (if not provided)
    if client is None:
        try:
            client = get_client()
        except ValueError as e:
            logger.error(f"Failed to create Anthropic client: {e}")
            client = None

    decisions = []
    for item in items:
        decision = decide_tier_for_item(item, request, user_context, client)
        decisions.append(decision)

    return {
        "request": request,
        "decisions": decisions,
        "user_context": user_context,
        "llm_model": MODEL,
    }


# Keep existing stub functions for backwards compatibility
def analyze_product(product: dict, baseline: dict) -> dict:
    """Analyze a product against user's baseline and values."""
    # This function is deprecated in favor of decide_tiers()
    logger.warning("analyze_product() is deprecated, use decide_tiers() instead")
    return {}


def suggest_alternatives(product: dict, criteria: list[str]) -> list[dict]:
    """Suggest ethical/sustainable alternatives for a product."""
    # This function is deprecated in favor of decide_tiers()
    logger.warning("suggest_alternatives() is deprecated, use decide_tiers() instead")
    return []
