"""
LLM Decision Engine module using Claude (Anthropic).
Uses Claude for constrained reasoning to recommend product tiers.
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Optional

from anthropic import Anthropic, APITimeoutError, APIError

from src.data_processing.seasonal_regional import (
    get_seasonal_note,
    filter_recalls_by_region,
    get_local_sourcing_note,
    get_region_from_location,
)

logger = logging.getLogger(__name__)

# Timeout for API calls (30 seconds)
API_TIMEOUT = 30.0

# Maximum retry attempts
MAX_RETRIES = 2

# Claude model to use
MODEL = "claude-sonnet-4-20250514"

# EWG Dirty Dozen - high pesticide items where organic matters
EWG_DIRTY_DOZEN = {
    "strawberries", "strawberry", "spinach", "kale", "collard greens",
    "grapes", "grape", "peaches", "peach", "pears", "pear",
    "nectarines", "nectarine", "apples", "apple", "bell peppers",
    "peppers", "cherries", "cherry", "blueberries", "blueberry",
    "green beans", "green bean",
}

# Prompt template for tier recommendation
PROMPT_TEMPLATE = """You are a conscious buying advisor helping users choose groceries.

USER REQUEST: {request}
LOCATION: {location}
DATE: {current_date}

USER PRIORITIES:
- Budget: {budget_priority}
- Health: {health_priority}
- Packaging: {packaging_priority}

ITEM: {category}
{seasonal_note}
{ewg_warning}
{recall_warning}
{local_sourcing_note}
BASELINE (what user usually buys):
- Brand: {baseline_brand}
- Price: {baseline_price} {baseline_size}
- Packaging: {baseline_packaging}

OPTIONS:
1. CHEAPER tier:
   - Brand: {cheaper_brand}
   - Price: {cheaper_price} {cheaper_size}
   - Packaging: {cheaper_packaging}
   - Certifications: {cheaper_certifications}
   - Trade-offs: {cheaper_trade_offs}

2. BALANCED tier:
   - Brand: {balanced_brand}
   - Price: {balanced_price} {balanced_size}
   - Packaging: {balanced_packaging}
   - Certifications: {balanced_certifications}
   - Notes: {balanced_notes}

3. CONSCIOUS tier:
   - Brand: {conscious_brand}
   - Price: {conscious_price} {conscious_size}
   - Packaging: {conscious_packaging}
   - Certifications: {conscious_certifications}
   - Why conscious: {conscious_why}

RULES:
- Choose the tier that best matches user priorities
- Consider price PER SIZE for value comparison
- Reference specific facts (prices, packaging, certifications)
- If item has EWG Dirty Dozen warning, STRONGLY prefer organic options
- NEVER recommend a tier with active RECALL in user's region
- Consider seasonal availability - in-season produce is fresher and often cheaper
- Mention local sourcing benefits when available
- Explain trade-offs clearly
- NO HALLUCINATION - only use provided data

OUTPUT FORMAT (JSON only, no markdown):
{{
  "recommended_tier": "cheaper|balanced|conscious",
  "reasoning": "1-2 sentence explanation referencing specific facts",
  "key_trade_off": "main consideration"
}}"""


def get_client() -> Optional[Anthropic]:
    """Initialize and return Anthropic client."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY environment variable not set")
        return None
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


def _format_size(data: Optional[dict]) -> str:
    """Format size/quantity info for display."""
    if not data:
        return ""
    size = data.get("size") or data.get("quantity") or data.get("unit_size")
    if size:
        return f"({size})"
    return ""


def _format_certifications(data: Optional[dict]) -> str:
    """Format certifications list for display."""
    if not data:
        return "None"
    certs = data.get("certifications", [])
    if not certs:
        return "None"
    return ", ".join(certs)


def _is_dirty_dozen(category: str) -> bool:
    """Check if category is an EWG Dirty Dozen item."""
    category_lower = category.lower().replace("_", " ")
    for item in EWG_DIRTY_DOZEN:
        if item in category_lower or category_lower in item:
            return True
    return False


def _tier_has_organic(tier_data: dict) -> bool:
    """Check if a tier has organic certification."""
    if not tier_data:
        return False
    certs = tier_data.get("certifications", [])
    for cert in certs:
        if "organic" in cert.lower():
            return True
    # Also check product name and brand
    product_name = tier_data.get("product_name", "").lower()
    brand = tier_data.get("brand", "").lower()
    return "organic" in product_name or "organic" in brand


def _get_recalled_tiers(item: dict, location: str) -> set:
    """Get set of tier names that have active recalls in user's region."""
    flags = item.get("flags", [])
    recall_flags = [f for f in flags if "recall" in f.get("type", "").lower()]

    if location and recall_flags:
        recall_flags = filter_recalls_by_region(recall_flags, location)

    recalled_tiers = set()
    for flag in recall_flags:
        affected = flag.get("affected_tiers", [])
        for tier in affected:
            recalled_tiers.add(tier.lower())

    return recalled_tiers


def _smart_tier_fallback(
    item: dict,
    user_context: dict,
) -> tuple[str, str, str]:
    """
    Smart rule-based tier selection when LLM is unavailable.

    Considers:
    - User priorities (budget, health, packaging)
    - EWG Dirty Dozen (prefer organic)
    - Active recalls (avoid recalled tiers)

    Returns:
        Tuple of (recommended_tier, reasoning, key_trade_off)
    """
    category = item.get("category", "unknown")
    alternatives = item.get("alternatives") or {}
    location = user_context.get("location", "")

    # Get user priorities (default to "medium")
    budget_priority = user_context.get("budget_priority", "medium").lower()
    health_priority = user_context.get("health_priority", "medium").lower()
    packaging_priority = user_context.get("packaging_priority", "medium").lower()

    # Get recalled tiers
    recalled_tiers = _get_recalled_tiers(item, location)

    # Available tiers (not recalled)
    available_tiers = []
    for tier_name in ["cheaper", "balanced", "conscious"]:
        if tier_name not in recalled_tiers and alternatives.get(tier_name):
            available_tiers.append(tier_name)

    if not available_tiers:
        return "balanced", "No safe alternatives available", "Safety concern"

    # Check if it's a Dirty Dozen item (organic strongly preferred)
    is_dirty_dozen = _is_dirty_dozen(category)

    if is_dirty_dozen:
        # For Dirty Dozen, find first tier with organic certification
        for tier_name in ["conscious", "balanced", "cheaper"]:
            if tier_name in available_tiers:
                tier_data = alternatives.get(tier_name, {})
                if _tier_has_organic(tier_data):
                    brand = tier_data.get("brand", "this option")
                    return (
                        tier_name,
                        f"EWG Dirty Dozen item - {brand} has organic certification for lower pesticide exposure",
                        "Pesticide residue concern"
                    )
        # No organic available, warn user
        if "balanced" in available_tiers:
            return (
                "balanced",
                f"EWG Dirty Dozen item - no organic option available, recommending balanced tier",
                "Consider buying organic when available"
            )

    # Score-based selection for non-Dirty-Dozen items
    priority_scores = {"high": 2, "medium": 1, "low": 0}
    budget_score = priority_scores.get(budget_priority, 1)
    health_score = priority_scores.get(health_priority, 1)
    packaging_score = priority_scores.get(packaging_priority, 1)

    # If budget is the top priority, prefer cheaper
    if budget_score > health_score and budget_score > packaging_score:
        if "cheaper" in available_tiers:
            tier_data = alternatives.get("cheaper", {})
            brand = tier_data.get("brand", "Budget option")
            price = tier_data.get("est_price")
            price_str = f"${price:.2f}" if price else "lower cost"
            return (
                "cheaper",
                f"Based on your budget priority - {brand} at {price_str} offers best value",
                "Lower cost, may have fewer certifications"
            )

    # If health is the top priority, prefer conscious
    if health_score > budget_score and health_score >= packaging_score:
        if "conscious" in available_tiers:
            tier_data = alternatives.get("conscious", {})
            brand = tier_data.get("brand", "Premium option")
            certs = tier_data.get("certifications", [])
            cert_str = ", ".join(certs[:2]) if certs else "premium quality"
            return (
                "conscious",
                f"Based on your health priority - {brand} offers {cert_str}",
                "Higher price for better quality/certifications"
            )

    # If packaging is the top priority, find best packaging option
    if packaging_score > budget_score and packaging_score > health_score:
        eco_packaging = ["glass", "paper", "cardboard", "recyclable", "compostable"]
        for tier_name in ["conscious", "balanced", "cheaper"]:
            if tier_name in available_tiers:
                tier_data = alternatives.get(tier_name, {})
                packaging = tier_data.get("packaging", "").lower()
                if any(eco in packaging for eco in eco_packaging):
                    brand = tier_data.get("brand", "This option")
                    return (
                        tier_name,
                        f"Based on your packaging priority - {brand} uses {packaging}",
                        "Eco-friendly packaging"
                    )

    # Default to balanced when priorities are equal or medium
    if "balanced" in available_tiers:
        tier_data = alternatives.get("balanced", {})
        brand = tier_data.get("brand", "Balanced option")
        return (
            "balanced",
            f"{brand} offers good balance of price, quality, and sustainability",
            "Middle ground option"
        )

    # Fallback to first available tier
    first_available = available_tiers[0]
    tier_data = alternatives.get(first_available, {})
    brand = tier_data.get("brand", "Available option")
    return (
        first_available,
        f"{brand} is the recommended available option",
        "Limited options available"
    )


def _format_recall_warning(item: dict, location: Optional[str] = None) -> str:
    """Format recall warnings from item flags, filtered by location."""
    flags = item.get("flags", [])

    # Filter recalls by region if location provided
    recall_flags = [f for f in flags if "recall" in f.get("type", "").lower()]
    if location and recall_flags:
        recall_flags = filter_recalls_by_region(recall_flags, location)

    warnings = []
    for flag in recall_flags:
        affected = flag.get("affected_tiers", [])
        desc = flag.get("description", "Active recall")
        regions = flag.get("affected_regions", [])
        region_note = f" ({', '.join(regions)})" if regions else ""

        if affected:
            warnings.append(f"⚠️ RECALL on {', '.join(affected)} tier{region_note}: {desc}")
        else:
            warnings.append(f"⚠️ RECALL WARNING{region_note}: {desc}")
    return "\n".join(warnings) if warnings else ""


def _format_prompt_for_item(
    item: dict,
    request: str,
    user_context: dict,
) -> str:
    """Format the prompt template for a single item."""
    category = item.get("category", "unknown")
    baseline = item.get("baseline") or {}
    alternatives = item.get("alternatives") or {}

    cheaper = alternatives.get("cheaper") or {}
    balanced = alternatives.get("balanced") or {}
    conscious = alternatives.get("conscious") or {}

    # Get location from user context
    location = user_context.get("location", "")
    current_date = datetime.now().strftime("%B %d, %Y")

    # Check for EWG Dirty Dozen warning
    ewg_warning = ""
    if _is_dirty_dozen(category):
        ewg_warning = "⚠️ EWG DIRTY DOZEN: This item has high pesticide residue. PREFER ORGANIC options.\n"

    # Check for recalls (filtered by location)
    recall_warning = _format_recall_warning(item, location)
    if recall_warning:
        recall_warning = recall_warning + "\n"

    # Get seasonal note for produce items
    seasonal_note = ""
    if location and category.startswith("produce"):
        note = get_seasonal_note(category, location)
        if note:
            seasonal_note = note + "\n"

    # Get local sourcing note
    local_sourcing_note = ""
    if location:
        note = get_local_sourcing_note(category, location)
        if note:
            local_sourcing_note = f"🌱 LOCAL: {note}\n"

    return PROMPT_TEMPLATE.format(
        request=request,
        location=location if location else "Not specified",
        current_date=current_date,
        budget_priority=user_context.get("budget_priority", "medium"),
        health_priority=user_context.get("health_priority", "medium"),
        packaging_priority=user_context.get("packaging_priority", "medium"),
        category=category,
        seasonal_note=seasonal_note,
        ewg_warning=ewg_warning,
        recall_warning=recall_warning,
        local_sourcing_note=local_sourcing_note,
        # Baseline
        baseline_brand=_safe_get(baseline, "brand"),
        baseline_price=_format_price(baseline.get("price")),
        baseline_size=_format_size(baseline),
        baseline_packaging=_safe_get(baseline, "packaging"),
        # Cheaper tier
        cheaper_brand=_safe_get(cheaper, "brand"),
        cheaper_price=_format_price(cheaper.get("est_price")),
        cheaper_size=_format_size(cheaper),
        cheaper_packaging=_safe_get(cheaper, "packaging"),
        cheaper_certifications=_format_certifications(cheaper),
        cheaper_trade_offs=_safe_get(cheaper, "trade_offs", "None noted"),
        # Balanced tier
        balanced_brand=_safe_get(balanced, "brand"),
        balanced_price=_format_price(balanced.get("est_price")),
        balanced_size=_format_size(balanced),
        balanced_packaging=_safe_get(balanced, "packaging"),
        balanced_certifications=_format_certifications(balanced),
        balanced_notes=_safe_get(balanced, "why_this_tier", "Good middle ground"),
        # Conscious tier
        conscious_brand=_safe_get(conscious, "brand"),
        conscious_price=_format_price(conscious.get("est_price")),
        conscious_size=_format_size(conscious),
        conscious_packaging=_safe_get(conscious, "packaging"),
        conscious_certifications=_format_certifications(conscious),
        conscious_why=_safe_get(conscious, "why_this_tier", "Premium quality option"),
    )


def _extract_json_from_response(text: str) -> Optional[dict]:
    """Extract JSON object from LLM response text."""
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
    """Validate that LLM response has required fields."""
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


def _call_claude_with_retry(
    client: Anthropic,
    prompt: str,
    max_retries: int = MAX_RETRIES,
) -> Optional[dict]:
    """Call Claude API with retry logic."""
    last_error = None

    for attempt in range(max_retries):
        try:
            logger.debug(f"Claude call attempt {attempt + 1}/{max_retries}")

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

            logger.debug(f"Claude response: {response_text[:200]}...")

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

    logger.error(f"All {max_retries} Claude call attempts failed. Last error: {last_error}")
    return None


def decide_tier_for_item(
    item: dict,
    request: str,
    user_context: dict,
    client: Optional[Anthropic] = None,
) -> dict:
    """Use Claude to decide the recommended tier for a single item."""
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

    # Get or create client
    if client is None:
        client = get_client()
        if client is None:
            # Use smart fallback when no API key
            tier, reasoning, trade_off = _smart_tier_fallback(item, user_context)
            result["recommended_tier"] = tier
            result["reasoning"] = f"[Rule-based] {reasoning}"
            result["key_trade_off"] = trade_off
            result["llm_used"] = False
            logger.info(f"Using smart fallback for '{category}': {tier}")
            return result

    # Format prompt
    prompt = _format_prompt_for_item(item, request, user_context)

    # Call Claude
    llm_response = _call_claude_with_retry(client, prompt)

    if llm_response:
        result["recommended_tier"] = llm_response.get("recommended_tier", "balanced")
        result["reasoning"] = llm_response.get("reasoning", "")
        result["key_trade_off"] = llm_response.get("key_trade_off", "")
        result["llm_used"] = True
    else:
        # Use smart fallback if LLM fails
        tier, reasoning, trade_off = _smart_tier_fallback(item, user_context)
        result["recommended_tier"] = tier
        result["reasoning"] = f"[Rule-based] {reasoning}"
        result["key_trade_off"] = trade_off
        result["llm_used"] = False
        logger.warning(f"Claude call failed for '{category}', using smart fallback: {tier}")

    return result


def decide_tiers(facts_pack: dict, client: Optional[Anthropic] = None) -> dict:
    """
    Use Claude for constrained reasoning to decide tiers for all items.

    Args:
        facts_pack: Facts pack from generate_facts_pack()
        client: Optional Anthropic client (created if not provided)

    Returns:
        Decision dict with request, decisions, user_context, llm_model
    """
    request = facts_pack.get("request", "")
    items = facts_pack.get("items", [])
    user_context = facts_pack.get("user_context", {})

    logger.info(f"Deciding tiers for {len(items)} items using Claude")

    # Create client once for all items (if not provided)
    if client is None:
        client = get_client()

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
