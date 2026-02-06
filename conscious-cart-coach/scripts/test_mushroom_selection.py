#!/usr/bin/env python3
"""Test mushroom product selection"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agents.product_agent import ProductAgent

def test_mushroom_selection():
    """Test mushroom product selection and display results"""

    agent = ProductAgent()

    # Test with generic "mushrooms" request
    ingredients = [
        {
            "name": "mushrooms",
            "form": "whole",
            "quantity": 8,
            "unit": "oz"
        }
    ]

    result = agent.get_candidates(ingredients=ingredients)

    if result.is_error:
        print(f"❌ Error: {result.error_message}")
        return

    candidates = result.facts.get("candidates_by_ingredient", {}).get("mushrooms", [])

    print(f"\n{'='*100}")
    print(f"MUSHROOM PRODUCTS AVAILABLE ({len(candidates)} total)")
    print(f"{'='*100}\n")

    # Group by organic status
    organic = [c for c in candidates if c.get("organic")]
    non_organic = [c for c in candidates if not c.get("organic")]

    print(f"🍄 ORGANIC MUSHROOMS ({len(organic)} products)")
    print("-" * 100)
    for i, c in enumerate(organic[:10], 1):
        print(f"{i:2}. ${c['price']:5.2f} | ${c['unit_price']:.4f}/oz | {c['size']:8} | {c['brand'][:20]:20} | {c['title'][:45]}")

    print(f"\n🍄 NON-ORGANIC MUSHROOMS ({len(non_organic)} products)")
    print("-" * 100)
    for i, c in enumerate(non_organic[:10], 1):
        print(f"{i:2}. ${c['price']:5.2f} | ${c['unit_price']:.4f}/oz | {c['size']:8} | {c['brand'][:20]:20} | {c['title'][:45]}")

    print(f"\n{'='*100}")
    print("✅ Mushroom inventory successfully loaded!")
    print(f"   Total products: {len(candidates)}")
    print(f"   Organic: {len(organic)}")
    print(f"   Non-organic: {len(non_organic)}")
    print(f"{'='*100}\n")

    # Show top recommendation
    if candidates:
        top = candidates[0]
        print(f"💡 Top recommendation for 'mushrooms':")
        print(f"   {top['title']}")
        print(f"   Brand: {top['brand']}")
        print(f"   Price: ${top['price']}/{top['size']}")
        print(f"   Unit price: ${top['unit_price']:.4f}/oz")
        print(f"   Organic: {'Yes' if top.get('organic') else 'No'}")
        print()

if __name__ == '__main__':
    test_mushroom_selection()
