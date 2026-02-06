"""LLM-powered explanation generator for decision recommendations."""

import logging
from typing import Optional

# Type hints only - actual client is passed in
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

from .client import call_claude_with_retry

logger = logging.getLogger(__name__)

EXPLANATION_PROMPT = """Explain this grocery recommendation decision in 1-2 clear sentences.

INGREDIENT: {ingredient_name}
RECOMMENDED PRODUCT:
- Brand: {brand}
- Price: ${price:.2f} ({size})
- Unit Price: ${unit_price:.2f}/oz
- Organic: {organic}

SCORING FACTORS:
{scoring_factors}

AVAILABLE ALTERNATIVES:
Cheaper option: {cheaper_option}
Conscious option: {conscious_option}

USER CONTEXT:
- Preferences: {user_prefs}
- Strict safety mode: {strict_safety}

RULES:
1. Explain WHY this product was recommended (refer to specific scoring factors)
2. Mention the key tradeoff (e.g., "costs $2 more but organic")
3. Be concise and conversational
4. Reference actual prices and product attributes
5. NO hallucination - only use provided data

OUTPUT: Just the explanation text (no JSON, no markdown)"""


def explain_decision_with_llm(
    client: Anthropic,
    ingredient_name: str,
    recommended_product: dict,
    scoring_factors: list[str],
    cheaper_option: Optional[str] = None,
    conscious_option: Optional[str] = None,
    user_prefs: dict = None,
) -> Optional[str]:
    """
    Generate natural language explanation for a recommendation using LLM.

    Args:
        client: Anthropic client instance
        ingredient_name: Name of the ingredient
        recommended_product: Dict with product details
        scoring_factors: List of factors that influenced the score
        cheaper_option: Description of cheaper alternative
        conscious_option: Description of conscious alternative
        user_prefs: User preferences dict

    Returns:
        Natural language explanation string, or None if generation failed.
    """
    if not client:
        logger.warning("No Anthropic client provided")
        return None

    if not recommended_product:
        return None

    user_prefs = user_prefs or {}

    # Format scoring factors
    factors_text = "\n".join(f"- {factor}" for factor in scoring_factors) if scoring_factors else "- Standard scoring applied"

    # Format alternatives
    cheaper_text = cheaper_option if cheaper_option else "None (this is cheapest)"
    conscious_text = conscious_option if conscious_option else "None (this is most conscious)"

    # Format user prefs
    prefs_list = []
    if user_prefs.get("preferred_brands"):
        prefs_list.append(f"Prefers: {', '.join(user_prefs['preferred_brands'][:2])}")
    if user_prefs.get("avoided_brands"):
        prefs_list.append(f"Avoids: {', '.join(user_prefs['avoided_brands'][:2])}")
    prefs_text = ", ".join(prefs_list) if prefs_list else "No specific brand preferences"

    # Build prompt
    formatted_prompt = EXPLANATION_PROMPT.format(
        ingredient_name=ingredient_name,
        brand=recommended_product.get("brand", "Unknown"),
        price=recommended_product.get("price", 0.0),
        size=recommended_product.get("size", ""),
        unit_price=recommended_product.get("unit_price", 0.0),
        organic="Yes" if recommended_product.get("organic") else "No",
        scoring_factors=factors_text,
        cheaper_option=cheaper_text,
        conscious_option=conscious_text,
        user_prefs=prefs_text,
        strict_safety=user_prefs.get("strict_safety", False),
    )

    # Call Claude with Opik tracing
    explanation = call_claude_with_retry(
        client=client,
        prompt=formatted_prompt,
        max_tokens=256,
        temperature=0.3,  # Slightly creative but consistent
        trace_name="decision_explanation",
        metadata={
            "ingredient": ingredient_name,
            "product_brand": recommended_product.get("brand", "Unknown"),
            "product_price": recommended_product.get("price", 0.0),
            "operation": "explain_decision"
        }
    )

    if not explanation:
        logger.warning(f"Failed to generate explanation for {ingredient_name}")
        return None

    # Clean up response (remove any markdown or extra formatting)
    explanation = explanation.strip()
    explanation = explanation.replace("**", "").replace("*", "")

    logger.debug(f"Generated explanation for {ingredient_name}: {explanation[:100]}...")
    return explanation
