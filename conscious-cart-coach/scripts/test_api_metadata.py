#!/usr/bin/env python3
"""Test that API returns metadata fields"""

import requests
import json

def test_api_metadata():
    """Test if /api/plan-v2 returns packaging, nutrition, labels"""

    url = "http://localhost:8000/api/plan-v2"

    payload = {
        "prompt": "chicken biryani",
        "servings": 4
    }

    print("=" * 80)
    print("Testing API metadata flow")
    print("=" * 80)

    print(f"\nSending request: {payload}")

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()

        data = response.json()

        print(f"\n✓ API responded successfully")
        print(f"  Items in cart: {len(data.get('items', []))}")

        # Check first few items for metadata
        items = data.get('items', [])

        if not items:
            print("\n❌ No items in response!")
            return

        print(f"\n{'=' * 80}")
        print("Checking metadata for first 3 items:")
        print(f"{'=' * 80}\n")

        metadata_found = False

        for i, item in enumerate(items[:3]):
            ethical_default = item.get('ethical_default', {})
            product = ethical_default.get('product', {})

            title = product.get('title', 'Unknown')
            packaging = product.get('packaging', '')
            nutrition = product.get('nutrition', '')
            labels = product.get('labels', '')

            print(f"{i+1}. {title}")
            print(f"   Packaging: {packaging or '(empty)'}")
            print(f"   Nutrition: {nutrition or '(empty)'}")
            print(f"   Labels: {labels or '(empty)'}")

            if packaging or nutrition or labels:
                print(f"   ✅ Has metadata!")
                metadata_found = True
            else:
                print(f"   ⚠️  No metadata")
            print()

        if metadata_found:
            print("✅ Metadata is flowing through the API!")
        else:
            print("❌ No metadata found in any items")

    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to backend at http://localhost:8000")
        print("   Make sure the backend is running!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_api_metadata()
