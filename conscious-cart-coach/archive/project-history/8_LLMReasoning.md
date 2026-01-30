Create src/llm/decision_engine.py that uses LLM for constrained reasoning.

Function: decide_tiers(facts_pack: dict) -> dict

Prompt template:
"""
You are a conscious buying advisor helping users choose groceries.

USER REQUEST: {request}
USER PRIORITIES:
- Budget: {budget_priority}
- Health: {health_priority}  
- Packaging: {packaging_priority}

For each item below, recommend ONE tier (cheaper/balanced/conscious) and explain why in 1-2 sentences.

ITEM: {category}

BASELINE (what user usually buys):
- Brand: {baseline.brand}
- Price: ${baseline.price}
- Packaging: {baseline.packaging}

OPTIONS:
1. CHEAPER tier:
   - Brand: {cheaper.brand}
   - Price: ${cheaper.est_price}
   - Packaging: {cheaper.packaging}
   - Trade-offs: {cheaper.trade_offs}

2. BALANCED tier:
   - Brand: {balanced.brand}
   - Price: ${balanced.est_price}
   - Packaging: {balanced.packaging}
   - Notes: {balanced.notes}

3. CONSCIOUS tier:
   - Brand: {conscious.brand}
   - Price: ${conscious.est_price}
   - Packaging: {conscious.packaging}
   - Why conscious: {conscious.why_conscious}

RULES:
- Choose the tier that best matches user priorities
- Reference specific facts (prices, packaging, certifications)
- Explain trade-offs clearly
- NO HALLUCINATION - only use provided data

OUTPUT FORMAT (JSON):
{
  "recommended_tier": "cheaper|balanced|conscious",
  "reasoning": "1-2 sentence explanation referencing specific facts",
  "key_trade_off": "main consideration"
}
"""

Use Anthropic Claude API from .env

Include:
- Retry logic (max 2 attempts)
- JSON parsing with error handling
- Timeout (30 seconds)

Return full decision with all tiers + LLM recommendation
