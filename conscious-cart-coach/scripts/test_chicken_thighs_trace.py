#!/usr/bin/env python3
"""
Test chicken thighs retrieval and decision trace

Validates that:
1. query_key is normalized ("chicken thighs cut" → "chicken thighs")
2. retrieved_summary shows candidates retrieved from each store
3. considered_summary shows candidates after filters
4. drivers are populated with component deltas
5. tradeoffs_accepted are extracted from negative components
6. elimination_explanation is populated for all filtered candidates
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("CHICKEN THIGHS TRACE VALIDATION")
print("=" * 70)
print()

try:
    from src.planner.engine import PlannerEngine
    print("✅ Imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Create planner engine
engine = PlannerEngine()

# Create plan with trace enabled
print("\n📋 Creating plan for 'chicken biryani for 4' with trace enabled...")
try:
    plan = engine.create_plan(
        prompt="chicken biryani for 4",
        ingredients=["chicken thighs"],
        servings=4,
        include_trace=True
    )
    print("✅ Plan created successfully")
except Exception as e:
    print(f"❌ Plan creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Find chicken item
chicken_item = next((i for i in plan.items if "chicken" in i.ingredient_name.lower()), None)
if not chicken_item:
    print("❌ No chicken item found in plan")
    sys.exit(1)

print(f"✅ Found chicken item: {chicken_item.ingredient_name}")

# Check if trace exists
if not chicken_item.decision_trace:
    print("❌ No decision_trace found on chicken item")
    sys.exit(1)

print("✅ decision_trace exists")

trace = chicken_item.decision_trace

# ============================================================================
# Validation Tests
# ============================================================================

print("\n" + "=" * 70)
print("VALIDATION TESTS")
print("=" * 70)

# Test 1: Query key
print(f"\n1️⃣  Query Key")
print(f"   Value: '{trace.query_key}'")
if trace.query_key != "chicken thighs":
    print(f"   ⚠️  Expected 'chicken thighs', got '{trace.query_key}'")
else:
    print("   ✅ Query key normalized correctly")

# Test 2: Retrieved summary
print(f"\n2️⃣  Retrieved Summary (from ProductIndex)")
if not trace.retrieved_summary:
    print("   ❌ retrieved_summary is empty")
    sys.exit(1)

for summary in trace.retrieved_summary:
    print(f"   {summary.store_name}: {summary.retrieved_count} candidates")

fd_retrieved = next((s.retrieved_count for s in trace.retrieved_summary if s.store_id == "freshdirect"), 0)
if fd_retrieved == 0:
    print(f"   ⚠️  FreshDirect retrieved 0 candidates (expected >1)")
elif fd_retrieved == 1:
    print(f"   ⚠️  FreshDirect only retrieved 1 candidate (expected >1)")
else:
    print(f"   ✅ FreshDirect retrieved {fd_retrieved} candidates (expected >1)")

# Test 3: Considered summary
print(f"\n3️⃣  Considered Summary (after filters)")
if not trace.considered_summary:
    print("   ⚠️  considered_summary is empty")
else:
    for summary in trace.considered_summary:
        print(f"   {summary.store_name}: {summary.considered_count} candidates")
    print("   ✅ considered_summary populated")

# Test 4: Drivers
print(f"\n4️⃣  Score Drivers")
if not trace.drivers:
    print("   ⚠️  drivers list is empty")
else:
    for driver in trace.drivers:
        print(f"   {driver.rule}: +{driver.delta}")
    print(f"   ✅ {len(trace.drivers)} drivers populated")

# Test 5: Tradeoffs accepted
print(f"\n5️⃣  Tradeoffs Accepted")
if not trace.tradeoffs_accepted:
    print("   (None - winner has no negative components)")
else:
    for tradeoff in trace.tradeoffs_accepted:
        print(f"   - {tradeoff}")
    print(f"   ✅ {len(trace.tradeoffs_accepted)} tradeoffs")

# Test 6: Elimination explanations
print(f"\n6️⃣  Elimination Explanations")
filtered = [c for c in trace.candidates if c.status == "filtered_out"]
if not filtered:
    print("   (No filtered candidates)")
else:
    missing_explanations = []
    for c in filtered:
        if not c.elimination_explanation:
            missing_explanations.append(c.product)

    if missing_explanations:
        print(f"   ❌ {len(missing_explanations)} candidates missing explanations:")
        for product in missing_explanations[:3]:
            print(f"      - {product}")
    else:
        print(f"   ✅ All {len(filtered)} filtered candidates have explanations")

# Test 7: Winner and runner-up scores
print(f"\n7️⃣  Scores")
print(f"   Winner: {trace.winner_score}")
if trace.runner_up_score:
    print(f"   Runner-up: {trace.runner_up_score}")
    print(f"   Margin: {trace.score_margin}")
    print("   ✅ Winner and runner-up scores present")
else:
    print("   (No runner-up)")

# ============================================================================
# Summary
# ============================================================================

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

all_passed = True

# Check critical assertions
if trace.query_key != "chicken thighs":
    print("❌ Query key not normalized")
    all_passed = False

if fd_retrieved < 2:
    print("❌ FreshDirect retrieval too low (expected >1)")
    all_passed = False

if not trace.drivers:
    print("❌ Drivers not populated")
    all_passed = False

filtered = [c for c in trace.candidates if c.status == "filtered_out"]
if filtered and any(not c.elimination_explanation for c in filtered):
    print("❌ Some filtered candidates missing elimination_explanation")
    all_passed = False

if all_passed:
    print("\n✅ ALL TESTS PASSED!")
    print("\nThe scoring trace implementation is working correctly.")
    print("Frontend can now show:")
    print("  - Retrieved vs considered candidate pools by store")
    print("  - Score drivers explaining why winner won")
    print("  - Tradeoffs accepted on winner")
    print("  - Clear elimination explanations for filtered candidates")
else:
    print("\n⚠️  SOME TESTS FAILED")
    print("See output above for details.")
    sys.exit(1)
