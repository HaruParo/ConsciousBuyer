#!/usr/bin/env python3
"""Test API trace response"""
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.planner.engine import PlannerEngine

print("=" * 70)
print("API TRACE RESPONSE TEST")
print("=" * 70)

# Create planner engine
engine = PlannerEngine()

# Create plan with trace
plan = engine.create_plan(
    prompt="chicken biryani for 4",
    ingredients=["chicken thighs", "tomatoes"],
    servings=4,
    include_trace=True
)

# Convert to dict (simulating API serialization)
plan_dict = plan.model_dump()

# Find chicken item
chicken_item = next((i for i in plan_dict["items"] if "chicken" in i["ingredient_name"].lower()), None)

if not chicken_item or not chicken_item.get("decision_trace"):
    print("❌ No trace found")
    sys.exit(1)

trace = chicken_item["decision_trace"]

print(f"\n✅ Trace found for: {chicken_item['ingredient_name']}")
print(f"\n📊 Query Key: {trace['query_key']}")

print(f"\n🔍 Retrieved Summary:")
for summary in trace["retrieved_summary"]:
    print(f"   {summary['store_name']}: {summary['retrieved_count']} retrieved, {summary['considered_count']} considered")

print(f"\n🎯 Considered Summary:")
for summary in trace["considered_summary"]:
    print(f"   {summary['store_name']}: {summary['considered_count']} candidates")

print(f"\n🏆 Scores:")
print(f"   Winner: {trace['winner_score']}")
print(f"   Runner-up: {trace.get('runner_up_score', 'N/A')}")
print(f"   Margin: {trace['score_margin']}")

print(f"\n📈 Drivers ({len(trace['drivers'])} total):")
for driver in trace["drivers"]:
    print(f"   - {driver['rule']}: +{driver['delta']}")

print(f"\n⚖️  Tradeoffs Accepted ({len(trace['tradeoffs_accepted'])} total):")
if trace["tradeoffs_accepted"]:
    for tradeoff in trace["tradeoffs_accepted"]:
        print(f"   - {tradeoff}")
else:
    print("   (None)")

print(f"\n📦 Candidates ({len(trace['candidates'])} total):")
winner = next((c for c in trace["candidates"] if c["status"] == "winner"), None)
runner = next((c for c in trace["candidates"] if c["status"] == "runner_up"), None)
filtered = [c for c in trace["candidates"] if c["status"] == "filtered_out"]

if winner:
    print(f"   Winner: {winner['brand']} {winner['product'][:50]}... (${winner['price']})")
if runner:
    print(f"   Runner-up: {runner['brand']} {runner['product'][:50]}... (${runner['price']})")
print(f"   Filtered: {len(filtered)} candidates")

if filtered:
    print(f"\n🚫 Sample Filtered Candidates (showing first 3):")
    for c in filtered[:3]:
        print(f"   - {c['brand']} {c['product'][:40]}...")
        print(f"     Reason: {c.get('elimination_explanation', 'N/A')}")

print("\n" + "=" * 70)
print("✅ API TRACE RESPONSE TEST COMPLETE")
print("=" * 70)
print("\nThe trace data is properly serializable and ready for the frontend!")
