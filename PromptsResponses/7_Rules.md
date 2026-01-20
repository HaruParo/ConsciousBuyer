Create src/data_processing/rules.py with tier selection logic.

Function: apply_rules(facts_pack: dict) -> dict

Rules per item:
1. If budget_priority == "high":
   - Prefer cheaper tier
   - Exception: if baseline is already cheap, stay balanced

2. If packaging_priority == "high":
   - Score packaging: glass=10, paper=8, minimal_plastic=6, plastic=3
   - Prefer tier with best packaging score

3. If health_priority == "high":
   - Prefer organic/certified options
   - Check for certifications in conscious tier

4. Default: balanced tier (user's usual)

Output structure:
{
  "category": "miso_paste",
  "recommended_tier": "balanced",
  "reasoning_points": [
    "Your usual choice",
    "Glass packaging matches medium priority",
    "Mid-range price ($7.99)"
  ],
  "all_tiers": {
    "cheaper": {...},
    "balanced": {...},
    "conscious": {...}
  }
}

Make fully deterministic - same input always gives same output

Add comprehensive pytest tests:
- High budget priority -> cheaper
- High packaging priority -> best packaging
- High health priority -> conscious
- All medium -> balanced
