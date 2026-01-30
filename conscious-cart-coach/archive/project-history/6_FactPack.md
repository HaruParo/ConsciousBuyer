Create src/data_processing/facts_pack.py that assembles decision context.

Function: generate_facts_pack(user_input: str) -> dict

Steps:
1. Parse user_input to extract intent
   - Simple keyword matching: "miso soup" -> ["miso_paste", "tofu", "seaweed", "scallions"]
   - Use predefined recipes mapping if exact match
   - LLM fallback for complex requests

2. For each ingredient/category:
   - Load baseline from baseline_stats.json
   - Load alternatives from alternatives.json
   - Check for any flags (recalls, seasonal, etc.)

3. Assemble facts_pack:

{
  "request": "miso soup ingredients",
  "items": [
    {
      "category": "miso_paste",
      "baseline": {
        "brand": "Miso Master Organic",
        "price": 7.99,
        "packaging": "glass jar",
        "your_usual": true
      },
      "alternatives": {
        "cheaper": {...},
        "balanced": {...},
        "conscious": {...}
      },
      "flags": []
    },
    ...
  ],
  "user_context": {
    "budget_priority": "medium",
    "health_priority": "medium",
    "packaging_priority": "medium"
  }
}

Include validation:
- All categories have alternatives
- Prices are reasonable
- No missing required fields

Add pytest tests with mock data
