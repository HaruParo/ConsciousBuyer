#!/usr/bin/env python3
"""Debug inventory loading"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Check CSV file
csv_path = PROJECT_ROOT / "data/alternatives/source_listings.csv"
print(f"CSV path: {csv_path}")
print(f"CSV exists: {csv_path.exists()}")

if csv_path.exists():
    with open(csv_path, 'r') as f:
        lines = f.readlines()
    print(f"CSV lines: {len(lines)}")

    # Count mushroom lines
    mushroom_lines = [l for l in lines if 'produce_mushrooms' in l.lower()]
    print(f"Mushroom lines in CSV: {len(mushroom_lines)}")
    print(f"\nFirst few mushroom lines:")
    for i, line in enumerate(mushroom_lines[:3], 1):
        print(f"{i}. {line.strip()[:100]}")

print("\n" + "="*80)
print("Now loading via ProductAgent...")
print("="*80 + "\n")

from src.agents.product_agent import ProductAgent, LOADED_INVENTORY, SIMULATED_INVENTORY

print(f"LOADED_INVENTORY keys: {list(LOADED_INVENTORY.keys())[:10]}")
print(f"LOADED_INVENTORY total items: {sum(len(v) for v in LOADED_INVENTORY.values())}")
print(f"\nSIMULATED_INVENTORY keys: {list(SIMULATED_INVENTORY.keys())[:10]}")
print(f"SIMULATED_INVENTORY total items: {sum(len(v) for v in SIMULATED_INVENTORY.values())}")

# Check if mushrooms are loaded
if "mushrooms" in LOADED_INVENTORY:
    print(f"\n✅ 'mushrooms' found in LOADED_INVENTORY: {len(LOADED_INVENTORY['mushrooms'])} products")
    for i, p in enumerate(LOADED_INVENTORY['mushrooms'][:3], 1):
        print(f"  {i}. {p['title']} - ${p['price']}")
elif "produce_mushrooms" in LOADED_INVENTORY:
    print(f"\n⚠️  'produce_mushrooms' found in LOADED_INVENTORY: {len(LOADED_INVENTORY['produce_mushrooms'])} products")
else:
    print("\n❌ No mushrooms found in LOADED_INVENTORY")

# Test ProductAgent
agent = ProductAgent()
print(f"\nProductAgent inventory keys: {list(agent.inventory.keys())[:10]}")
print(f"ProductAgent using: {'LOADED' if agent.inventory is LOADED_INVENTORY else 'SIMULATED'}")
