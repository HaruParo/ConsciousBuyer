#!/usr/bin/env python3
"""
Test which chicken product is selected for biryani
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agents.product_agent import ProductAgent

def test_chicken_selection():
    """Test chicken product selection with flexible scoring"""

    agent = ProductAgent()

    # Test with generic "chicken" request
    ingredients = [
        {
            "name": "chicken",
            "form": "cut",
            "quantity": 2,
            "unit": "lb"
        }
    ]

    result = agent.get_candidates(ingredients=ingredients)

    if result.is_error:
        print(f"❌ Error: {result.error_message}")
        return

    candidates = result.facts.get("candidates_by_ingredient", {}).get("chicken", [])

    print(f"\n{'='*80}")
    print(f"CHICKEN CANDIDATES FOR BIRYANI (Top 10)")
    print(f"{'='*80}\n")

    for i, candidate in enumerate(candidates[:10], 1):
        organic_badge = "✓ ORG" if candidate.get("organic") else "      "
        print(f"{i:2}. {organic_badge} | ${candidate['price']:5.2f}/lb | ${candidate['unit_price']:.4f}/oz")
        print(f"    {candidate['title'][:60]}")
        print(f"    Brand: {candidate['brand']}")
        print(f"    Store: {candidate.get('available_stores', ['unknown'])[0]}")
        print()

    # Show scoring explanation
    print(f"\n{'='*80}")
    print("SCORING VERIFICATION:")
    print("With flexible scoring, ALL chicken cuts should have form_score=0")
    print("So organic chicken products should rank highest by unit price")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    test_chicken_selection()
