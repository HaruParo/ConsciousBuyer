"""LLM-powered explanation generator for decision recommendations."""

import logging
import os
from typing import Optional

from ..utils.llm_client import BaseLLMClient

# Opik tracking (optional)
try:
    import opik
    # Configure Opik on import if API key available
    opik_api_key = os.environ.get("OPIK_API_KEY")
    if opik_api_key:
        opik.configure(
            api_key=opik_api_key,
            workspace=os.environ.get("OPIK_WORKSPACE", "default"),
        )
    OPIK_AVAILABLE = True
except ImportError:
    opik = None
    OPIK_AVAILABLE = False
except Exception:
    opik = None
    OPIK_AVAILABLE = False

logger = logging.getLogger(__name__)

# System prompt - concise, reusable (cached by Anthropic API)
EXPLANATION_SYSTEM_PROMPT = """You explain grocery product recommendations concisely.
Rules:
- 1-2 sentences max
- Reference actual prices and attributes
- Mention key tradeoff if relevant (e.g., "costs $2 more but organic")
- Be conversational, not technical
- NO hallucination - only use provided data"""

# User prompt - minimal, variable data only
EXPLANATION_USER_PROMPT = """Explain why {brand} {ingredient_name} (${price:.2f}, {size}) was recommended.

Scoring: {scoring_factors}
Cheaper option: {cheaper_option}
Organic: {organic}

Example: "The Earthbound Farm spinach at $3.99 offers organic certification for just $1 more than conventional, worth it for a Dirty Dozen item."

Explanation:"""


def explain_decision_with_llm(
    client: BaseLLMClient,
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
        client: LLM client instance (BaseLLMClient - Anthropic, Ollama, Gemini, etc.)
        ingredient_name: Name of the ingredient
        recommended_product: Dict with product details
        scoring_factors: List of factors that influenced the score
        cheaper_option: Description of cheaper alternative
        conscious_option: Description of conscious alternative
        user_prefs: User preferences dict (unused currently, for future)

    Returns:
        Natural language explanation string, or None if generation failed.
    """
    if not client:
        logger.warning("No LLM client provided")
        return None

    if not recommended_product:
        return None

    # Format scoring factors (compact)
    factors_text = ", ".join(scoring_factors[:3]) if scoring_factors else "standard scoring"

    # Format cheaper option
    cheaper_text = cheaper_option if cheaper_option else "none (this is cheapest)"

    # Build prompt
    formatted_prompt = EXPLANATION_USER_PROMPT.format(
        ingredient_name=ingredient_name,
        brand=recommended_product.get("brand", "Unknown"),
        price=recommended_product.get("price", 0.0),
        size=recommended_product.get("size", "") or "standard",
        scoring_factors=factors_text,
        cheaper_option=cheaper_text,
        organic="Yes" if recommended_product.get("organic") else "No",
    )

    # Start Opik trace for this LLM call
    trace = None
    if OPIK_AVAILABLE and opik:
        try:
            trace = opik.trace(
                name="decision_explanation",
                input={
                    "ingredient": ingredient_name,
                    "product": recommended_product.get("brand", "Unknown"),
                    "price": recommended_product.get("price", 0.0),
                    "prompt": formatted_prompt,
                },
                project_name=os.environ.get("OPIK_PROJECT_NAME", "consciousbuyer"),
            )
        except Exception as e:
            logger.debug(f"Opik trace failed to start: {e}")

    # Call LLM with system prompt (cached)
    explanation = None
    try:
        print(f"[LLM] Calling decision explainer for {ingredient_name}...")
        response = client.generate_sync(
            prompt=formatted_prompt,
            system=EXPLANATION_SYSTEM_PROMPT,
            max_tokens=100,  # Short explanations only
            temperature=0.3,  # Slightly creative but consistent
        )
        explanation = response.text if response else None
        print(f"[LLM] Decision explainer response: {explanation[:50] if explanation else 'None'}...")
    except Exception as e:
        print(f"[LLM] Decision explainer API error: {e}")
        logger.error(f"LLM API call failed for decision explanation: {e}")
        if trace:
            trace.end(output={"error": str(e)})
        return None

    if not explanation:
        logger.warning(f"Failed to generate explanation for {ingredient_name}")
        if trace:
            trace.end(output={"error": "Empty response"})
        return None

    # Clean up response (remove any markdown or extra formatting)
    explanation = explanation.strip()
    explanation = explanation.replace("**", "").replace("*", "")

    # Truncate if too long (shouldn't happen with max_tokens=100)
    if len(explanation) > 200:
        explanation = explanation[:197] + "..."

    # End Opik trace with output
    if trace:
        trace.end(output={"explanation": explanation})

    logger.debug(f"Generated explanation for {ingredient_name}: {explanation[:80]}...")
    return explanation


# Batched explanation prompt for multiple ingredients at once
BATCH_EXPLANATION_SYSTEM = """You explain grocery product recommendations concisely.
For each ingredient, provide a 1-sentence explanation.
Be conversational, reference prices, mention key tradeoffs.
Output as JSON: {"ingredient_name": "explanation", ...}"""

BATCH_EXPLANATION_PROMPT = """Explain why these products were recommended:

{items_text}

Output JSON with one explanation per ingredient (1 sentence each):"""


def explain_decisions_batch(
    client: BaseLLMClient,
    items: list[dict],
) -> dict[str, str]:
    """
    Generate explanations for ALL items in ONE LLM call.

    Args:
        client: LLM client instance
        items: List of dicts with keys: ingredient_name, brand, price, scoring_factors, cheaper_option

    Returns:
        Dict mapping ingredient_name -> explanation
    """
    if not client or not items:
        return {}

    # Build items text
    items_lines = []
    for item in items:
        factors = ", ".join(item.get("scoring_factors", [])[:2]) or "standard"
        cheaper = item.get("cheaper_option") or "none"
        items_lines.append(
            f"- {item['ingredient_name']}: {item['brand']} ${item['price']:.2f} "
            f"(scoring: {factors}, cheaper: {cheaper})"
        )

    items_text = "\n".join(items_lines)
    prompt = BATCH_EXPLANATION_PROMPT.format(items_text=items_text)

    print(f"[LLM] Calling BATCHED decision explainer for {len(items)} items...")

    try:
        response = client.generate_sync(
            prompt=prompt,
            system=BATCH_EXPLANATION_SYSTEM,
            max_tokens=500,
            temperature=0.3,
        )

        if not response or not response.text:
            print("[LLM] Batched explainer: empty response")
            return {}

        # Parse JSON response
        import json
        import re

        text = response.text.strip()
        # Try to extract JSON from response
        json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if json_match:
            explanations = json.loads(json_match.group())
            print(f"[LLM] Batched explainer: got {len(explanations)} explanations")
            return explanations
        else:
            print(f"[LLM] Batched explainer: couldn't parse JSON from: {text[:100]}")
            return {}

    except Exception as e:
        print(f"[LLM] Batched explainer error: {e}")
        return {}
