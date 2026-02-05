#!/usr/bin/env python3
"""
Show chicken thigh candidates with scoring details
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agents.product_agent import ProductAgent

def show_chicken_scores():
    """Display all chicken thigh candidates with scores"""

    # Initialize product agent
    agent = ProductAgent()

    # Get candidates for chicken thighs
    ingredients = [
        {
            "name": "chicken thighs",
            "form": "cut",
            "quantity": 1,
            "unit": "unit"
        }
    ]

    result = agent.get_candidates(
        ingredients=ingredients
    )

    if not result.success:
        print(f"❌ Error: {result.error}")
        return

    candidates = result.facts.get("candidates_by_ingredient", {}).get("chicken thighs", [])

    print(f"\n{'='*80}")
    print(f"CHICKEN THIGHS CANDIDATES ({len(candidates)} found)")
    print(f"{'='*80}\n")

    for i, candidate in enumerate(candidates, 1):
        print(f"{i}. {candidate['title']}")
        print(f"   Brand: {candidate['brand']}")
        print(f"   Price: ${candidate['price']}/lb")
        print(f"   Size: {candidate['size']}")
        print(f"   Unit Price: ${candidate['unit_price']}/oz")
        print(f"   Organic: {'Yes' if candidate.get('organic') else 'No'}")
        print(f"   Store: {candidate.get('available_stores', ['unknown'])[0]}")
        print()


if __name__ == '__main__':
    show_chicken_scores()
