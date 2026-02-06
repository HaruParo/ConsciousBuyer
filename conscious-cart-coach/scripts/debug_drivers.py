#!/usr/bin/env python3
"""
Debug script to show what drivers are being computed
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.planner.engine import PlannerEngine

print("=" * 70)
print("DRIVER DEBUG - Chicken Biryani")
print("=" * 70)

# Create planner engine
engine = PlannerEngine()

# Create plan with trace
plan = engine.create_plan(
    prompt="chicken biryani for 4",
    ingredients=["chicken thighs", "tomatoes", "onions", "ginger", "basmati rice"],
    servings=4,
    include_trace=True
)

print(f"\n{'Ingredient':<20} {'Reason Line':<40} {'Top Driver':<30} {'Delta'}")
print("=" * 120)

for item in plan.items:
    if item.decision_trace and item.decision_trace.drivers:
        top_driver = item.decision_trace.drivers[0]
        driver_text = f"{top_driver.rule} (+{top_driver.delta})"
    else:
        driver_text = "No drivers"

    print(f"{item.ingredient_name:<20} {item.reason_line:<40} {driver_text:<30}")

print("\n" + "=" * 70)
print("DETAILED BREAKDOWN FOR FIRST 3 ITEMS")
print("=" * 70)

for item in plan.items[:3]:
    print(f"\n### {item.ingredient_name} - {item.reason_line}")

    if item.decision_trace:
        trace = item.decision_trace

        # Show winner vs runner-up
        winner = next((c for c in trace.candidates if c.status == 'winner'), None)
        runner = next((c for c in trace.candidates if c.status == 'runner_up'), None)

        print(f"Has runner-up: {runner is not None}")

        if winner and runner:
            print(f"Winner: {winner.brand} - ${winner.price} - Organic: {winner.organic}")
            print(f"Runner: {runner.brand} - ${runner.price} - Organic: {runner.organic}")

            # Show score breakdown
            if winner.score_breakdown:
                wb = winner.score_breakdown
                rb = runner.score_breakdown or {}

                print("\nComponent Scores (Winner vs Runner):")
                for comp in ['base', 'ewg', 'form_fit', 'packaging', 'delivery', 'unit_value', 'outlier_penalty']:
                    w_score = wb.get(comp, 0)
                    r_score = rb.get(comp, 0) if rb else 0
                    delta = w_score - r_score
                    print(f"  {comp:15}: {w_score:3} vs {r_score:3} (delta: {delta:+3})")

        # Show all drivers
        if trace.drivers:
            print("\nAll Drivers:")
            for driver in trace.drivers:
                print(f"  - {driver.rule}: +{driver.delta}")
        else:
            print("\nNo drivers computed")
    else:
        print("No decision trace available")
