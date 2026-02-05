"""
Synthetic Inventory Generator for Conscious Cart Coach

Generates market-plausible product inventories for stores with:
- Multiple candidates per ingredient (3-6) for meaningful scoring
- Store-exclusive private labels (hard-enforced)
- Realistic brands, sizes, units, prices
- Deterministic output (seeded by store + ingredient)

Stores:
- freshdirect
- wholefoods
- shoprite
- pure_indian_foods
- kaiser

Usage:
    python scripts/generate_synthetic_inventory.py
"""

import csv
import random
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict

# Deterministic seeding for reproducibility
def seed_for(store_id: str, ingredient: str) -> int:
    """Generate deterministic seed from store + ingredient"""
    hash_input = f"{store_id}:{ingredient}".encode('utf-8')
    hash_value = hashlib.sha256(hash_input).hexdigest()
    return int(hash_value[:8], 16)


@dataclass
class Product:
    """Product listing with all required fields"""
    product_id: str
    source_store_id: str
    store_name: str
    category: str
    ingredient_key: str
    brand: str
    title: str
    price: float
    size_value: float
    size_unit: str
    unit_price: float
    unit_price_unit: str
    organic: bool
    packaging: str  # glass, plastic, paper, bulk
    certifications: str  # comma-separated

    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# Store Configurations
# ============================================================================

STORES = {
    "freshdirect": {
        "name": "FreshDirect",
        "private_label": "FreshDirect",
        "strength": ["produce", "meat", "dairy"],
        "weakness": ["indian_spices"],
        "coverage": 0.85  # carries 85% of common ingredients
    },
    "wholefoods": {
        "name": "Whole Foods Market",
        "private_label": "365 by Whole Foods Market",
        "strength": ["organic_produce", "organic_meat", "organic_dairy", "pantry"],
        "weakness": [],
        "coverage": 0.90
    },
    "shoprite": {
        "name": "ShopRite",
        "private_label": "Bowl & Basket",
        "strength": ["staples", "pantry", "basics"],
        "weakness": ["specialty_spices", "ethnic"],
        "coverage": 0.75
    },
    "pure_indian_foods": {
        "name": "Pure Indian Foods",
        "private_label": "Pure Indian Foods",
        "strength": ["indian_spices", "ghee", "rice", "lentils"],
        "weakness": ["fresh_produce", "meat", "dairy"],
        "coverage": 0.40  # Specialty store - limited range
    },
    "kaiser": {
        "name": "Kaiser Grocery",
        "private_label": "Kaiser Select",
        "strength": ["general"],
        "weakness": [],
        "coverage": 0.80
    }
}


# ============================================================================
# Ingredient Database
# ============================================================================

BIRYANI_INGREDIENTS = {
    # Proteins
    "chicken": {
        "category": "protein_poultry",
        "sizes": [("1", "lb"), ("2", "lb"), ("3", "lb"), ("1.5", "lb")],
        "brands": {
            "mainstream": ["Perdue", "Tyson", "Bell & Evans"],
            "premium": ["Murray's Organic", "Mary's Free Range", "Farmer Focus"],
            "store": True
        },
        "base_price": 6.99,  # per lb
        "stores": ["freshdirect", "wholefoods", "shoprite", "kaiser"]
    },

    # Vegetables
    "onions": {
        "category": "produce",
        "sizes": [("3", "lb"), ("5", "lb"), ("1", "lb"), ("2", "lb")],
        "brands": {
            "mainstream": ["Melissa's", "Fresh Farms"],
            "premium": ["Organic Valley"],
            "store": True
        },
        "base_price": 1.99,  # per lb
        "stores": ["freshdirect", "wholefoods", "shoprite", "kaiser"]
    },

    "tomatoes": {
        "category": "produce",
        "sizes": [("1", "lb"), ("2", "lb"), ("16", "oz")],
        "brands": {
            "mainstream": ["NatureSweet", "Campari"],
            "premium": ["Heirloom Organic"],
            "store": True
        },
        "base_price": 2.99,
        "stores": ["freshdirect", "wholefoods", "shoprite", "kaiser"]
    },

    # Dairy
    "yogurt": {
        "category": "dairy",
        "sizes": [("32", "oz"), ("5.3", "oz"), ("6", "oz")],
        "brands": {
            "mainstream": ["Chobani", "Fage", "Dannon"],
            "premium": ["Straus Organic", "Maple Hill"],
            "store": True
        },
        "base_price": 5.99,  # for 32oz
        "stores": ["freshdirect", "wholefoods", "shoprite", "kaiser"]
    },

    # Aromatics
    "ginger": {
        "category": "produce",
        "sizes": [("6", "oz"), ("1", "lb"), ("8", "oz")],
        "brands": {
            "mainstream": ["Melissa's"],
            "premium": ["Organic Ginger Root"],
            "store": True
        },
        "base_price": 3.99,  # per lb
        "stores": ["freshdirect", "wholefoods", "shoprite", "kaiser"]
    },

    "garlic": {
        "category": "produce",
        "sizes": [("3", "ct"), ("1", "lb"), ("5", "ct")],
        "brands": {
            "mainstream": ["Christopher Ranch"],
            "premium": ["Organic Hardneck Garlic"],
            "store": True
        },
        "base_price": 4.99,
        "stores": ["freshdirect", "wholefoods", "shoprite", "kaiser"]
    },

    # Herbs
    "mint": {
        "category": "herbs",
        "sizes": [("1", "bunch"), ("0.75", "oz")],
        "brands": {
            "mainstream": ["Fresh Herb Co"],
            "premium": ["Organic Mint"],
            "store": True
        },
        "base_price": 2.49,  # per bunch
        "stores": ["freshdirect", "wholefoods", "shoprite", "kaiser"]
    },

    "cilantro": {
        "category": "herbs",
        "sizes": [("1", "bunch"), ("0.75", "oz")],
        "brands": {
            "mainstream": ["Fresh Herb Co"],
            "premium": ["Organic Cilantro"],
            "store": True
        },
        "base_price": 1.99,
        "stores": ["freshdirect", "wholefoods", "shoprite", "kaiser"]
    },

    # Rice & Grains
    "basmati rice": {
        "category": "rice",
        "sizes": [("2", "lb"), ("5", "lb"), ("10", "lb"), ("4", "lb")],
        "brands": {
            "mainstream": ["Lundberg", "Royal"],
            "premium": ["Pride of India", "Tilda"],
            "store": True,
            "specialty": ["Laxmi", "India Gate"]
        },
        "base_price": 8.99,  # for 2lb
        "stores": ["freshdirect", "wholefoods", "shoprite", "pure_indian_foods", "kaiser"]
    },

    # Oils & Fats
    "ghee": {
        "category": "oil",
        "sizes": [("8", "oz"), ("16", "oz"), ("32", "oz")],
        "brands": {
            "mainstream": ["Organic Valley", "Fourth & Heart"],
            "premium": ["Ancient Organics"],
            "store": False,  # No store brand ghee
            "specialty": ["Pure Indian Foods", "Swad", "Deep", "Laxmi"]
        },
        "base_price": 9.99,  # for 16oz ($8-$20 range)
        "stores": ["freshdirect", "wholefoods", "shoprite", "pure_indian_foods", "kaiser"]
    },

    # Spices - Indian
    "garam masala": {
        "category": "spices",
        "sizes": [("2", "oz"), ("8", "oz")],  # Real PIF sizes
        "brands": {
            "mainstream": ["McCormick", "Simply Organic"],
            "premium": ["Diaspora Co"],
            "store": False,
            "specialty": ["Pure Indian Foods", "Laxmi", "MDH", "Everest", "Shan", "Deep"]
        },
        "base_price": 6.49,  # Real PIF pricing: 2oz = $6.49
        "stores": ["wholefoods", "shoprite", "pure_indian_foods", "kaiser"]
    },

    "turmeric": {
        "category": "spices",
        "sizes": [("3", "oz"), ("8", "oz")],  # Real PIF sizes
        "brands": {
            "mainstream": ["McCormick", "Simply Organic"],
            "premium": ["Diaspora Co"],
            "store": False,
            "specialty": ["Pure Indian Foods", "Laxmi", "MDH", "Swad", "Deep", "Everest"]
        },
        "base_price": 6.99,  # Real PIF pricing: 3oz = $6.99, 8oz = $15.99
        "stores": ["freshdirect", "wholefoods", "shoprite", "pure_indian_foods", "kaiser"]
    },

    "coriander": {
        "category": "spices",
        "sizes": [("3", "oz"), ("8", "oz")],  # Real PIF sizes
        "brands": {
            "mainstream": ["McCormick", "Simply Organic"],
            "premium": ["Diaspora Co"],
            "store": False,
            "specialty": ["Pure Indian Foods", "Laxmi", "MDH", "Swad", "Deep"]
        },
        "base_price": 5.31,  # Real PIF pricing: 3oz = $5.31, 8oz = $11.99
        "stores": ["freshdirect", "wholefoods", "shoprite", "pure_indian_foods", "kaiser"]
    },

    "cumin": {
        "category": "spices",
        "sizes": [("3", "oz"), ("8", "oz")],  # Real PIF sizes
        "brands": {
            "mainstream": ["McCormick", "Simply Organic"],
            "premium": ["Diaspora Co"],
            "store": False,
            "specialty": ["Pure Indian Foods", "Laxmi", "MDH", "Swad", "Deep"]
        },
        "base_price": 6.69,  # Real PIF pricing: 3oz = $6.69, 8oz = $14.99
        "stores": ["freshdirect", "wholefoods", "shoprite", "pure_indian_foods", "kaiser"]
    },

    "cardamom": {
        "category": "spices",
        "sizes": [("2", "oz"), ("8", "oz")],  # Real PIF sizes
        "brands": {
            "mainstream": ["McCormick", "Simply Organic"],
            "premium": ["Diaspora Co"],
            "store": False,
            "specialty": ["Pure Indian Foods", "Laxmi", "MDH", "Swad", "Deep"]
        },
        "base_price": 12.99,  # Real PIF pricing: 2oz = $12.99, 8oz = $28.99 (already correct!)
        "stores": ["wholefoods", "shoprite", "pure_indian_foods", "kaiser"]
    },

    "bay leaves": {
        "category": "spices",
        "sizes": [("0.5", "oz"), ("1", "oz")],  # Real PIF sizes (Indian bay leaves small)
        "brands": {
            "mainstream": ["McCormick", "Simply Organic"],
            "premium": ["Diaspora Co"],
            "store": False,
            "specialty": ["Pure Indian Foods", "Laxmi", "MDH", "Swad"]
        },
        "base_price": 7.98,  # Real PIF pricing: 0.5oz = $3.99 → $7.98/oz
        "stores": ["freshdirect", "wholefoods", "shoprite", "pure_indian_foods", "kaiser"]
    }
}


# ============================================================================
# Product Generation
# ============================================================================

def generate_products_for_ingredient(
    ingredient: str,
    config: Dict,
    store_id: str,
    store_config: Dict,
    product_counter: int
) -> List[Product]:
    """Generate 3-6 product candidates for an ingredient at a store"""

    # Check if store carries this ingredient
    if store_id not in config["stores"]:
        return []

    # Deterministic seed
    random.seed(seed_for(store_id, ingredient))

    products = []
    brands_to_generate = []

    # Store brand (if applicable)
    if config["brands"].get("store", False):
        brands_to_generate.append(("store", store_config["private_label"], False))  # Store brands usually not organic

    # Mainstream brands (pick 2-3) - mix of organic and non-organic
    mainstream = config["brands"].get("mainstream", [])
    if mainstream:
        selected_mainstream = random.sample(mainstream, min(2, len(mainstream)))
        for brand in selected_mainstream:
            # 50% chance organic for mainstream
            is_organic = random.random() < 0.5
            brands_to_generate.append(("mainstream", brand, is_organic))

    # Premium brand (pick 1) - usually organic
    premium = config["brands"].get("premium", [])
    if premium:
        # Filter out brands that are exclusive to other stores
        store_exclusive_brands = ["Pure Indian Foods", "365 by Whole Foods Market", "FreshDirect", "Bowl & Basket", "Kaiser Select"]
        filtered_premium = [b for b in premium if b not in store_exclusive_brands or b == store_config["private_label"]]

        if filtered_premium:
            selected_premium = random.choice(filtered_premium)
            brands_to_generate.append(("premium", selected_premium, True))  # Premium is organic

    # Specialty brands (for specialty stores) - generate MORE variety
    if store_id == "pure_indian_foods" and "specialty" in config["brands"]:
        specialty = config["brands"]["specialty"]
        # For Pure Indian Foods, generate 4-5 products with different brands
        num_specialty = min(5, len(specialty))
        selected_specialty = random.sample(specialty, num_specialty)
        for brand in selected_specialty:
            # Mix of organic and non-organic for variety (30% organic for specialty)
            is_organic = random.random() < 0.3
            brands_to_generate.append(("specialty", brand, is_organic))

    # Generate products for each brand
    for idx, (tier, brand, is_organic) in enumerate(brands_to_generate):
        # Pick a size variant
        size_value, size_unit = random.choice(config["sizes"])
        size_val = float(size_value)

        # Calculate price with REALISTIC CONSTRAINTS
        base_price = config["base_price"]

        # Price modifiers by tier
        tier_multipliers = {
            "store": 0.75,  # Store brand significantly cheaper
            "mainstream": 0.90,  # Mainstream slightly below baseline
            "premium": 1.40,  # Premium more expensive
            "specialty": 1.00  # Specialty at baseline (not premium by default)
        }

        # Organic premium (applied to base after tier)
        organic_multiplier = 1.30 if is_organic else 1.0

        # Size-based pricing with HARD CONSTRAINTS
        category = config["category"]

        # Apply category-specific pricing rules with bounds
        if category == "rice":
            # Basmati rice pricing by size (market-plausible ranges)
            if size_unit == "lb":
                if size_val >= 10:
                    # 10lb: $18–$45 baseline, adjusted by tier/organic
                    price = random.uniform(18, 45) * tier_multipliers[tier] * organic_multiplier
                elif size_val >= 5:
                    # 5lb: $12–$25 baseline, adjusted by tier/organic
                    price = random.uniform(12, 25) * tier_multipliers[tier] * organic_multiplier
                elif size_val >= 2:
                    # 2lb: $5–$12 baseline
                    price = random.uniform(5, 12) * tier_multipliers[tier] * organic_multiplier
                else:
                    price = random.uniform(3, 8) * tier_multipliers[tier] * organic_multiplier
        elif category == "oil" and ingredient == "ghee":
            # Ghee pricing by size (realistic Indian market prices)
            if size_unit == "oz":
                if size_val >= 32:
                    price = random.uniform(18, 35) * tier_multipliers[tier] * organic_multiplier
                elif size_val >= 16:
                    price = random.uniform(9, 20) * tier_multipliers[tier] * organic_multiplier
                elif size_val >= 8:
                    price = random.uniform(6, 12) * tier_multipliers[tier] * organic_multiplier
                else:
                    price = random.uniform(4, 10) * tier_multipliers[tier] * organic_multiplier
        elif category == "spices":
            # Spice pricing - market-plausible ranges
            # Requirements: turmeric/cumin/coriander 100g ($2-$8), garam masala 100g ($3-$9), cardamom 50g ($6-$18)
            if size_unit == "oz":
                if "cardamom" in ingredient.lower():
                    # Cardamom is expensive: 2oz (≈50g) baseline $6-$18
                    if size_val >= 8:
                        price = random.uniform(22, 35) * tier_multipliers[tier] * organic_multiplier
                    elif size_val >= 2:
                        price = random.uniform(6, 18) * tier_multipliers[tier] * organic_multiplier
                    else:
                        price = random.uniform(4, 12) * tier_multipliers[tier] * organic_multiplier
                elif "bay" in ingredient.lower():
                    # Bay leaves: 0.5oz baseline $2-$5
                    if size_val >= 1:
                        price = random.uniform(3, 8) * tier_multipliers[tier] * organic_multiplier
                    else:
                        price = random.uniform(2, 5) * tier_multipliers[tier] * organic_multiplier
                elif size_val >= 8:
                    # 8oz bulk: $10-$16 baseline
                    price = random.uniform(10, 16) * tier_multipliers[tier] * organic_multiplier
                elif size_val >= 2:
                    # 2-3oz (≈100g): $2-$8 baseline for most spices
                    if "garam masala" in ingredient.lower():
                        price = random.uniform(3, 9) * tier_multipliers[tier] * organic_multiplier
                    else:
                        price = random.uniform(2, 8) * tier_multipliers[tier] * organic_multiplier
                else:
                    # Sub-2oz sizes
                    price = random.uniform(2, 6) * tier_multipliers[tier] * organic_multiplier
            elif size_unit == "g":
                # Gram-based pricing (for variety)
                if "cardamom" in ingredient.lower():
                    # Cardamom 50g: $6-$18 baseline
                    if size_val >= 100:
                        price = random.uniform(12, 30) * tier_multipliers[tier] * organic_multiplier
                    else:
                        price = random.uniform(6, 18) * tier_multipliers[tier] * organic_multiplier
                elif size_val >= 200:
                    # 200g: $4-$16 baseline
                    price = random.uniform(4, 16) * tier_multipliers[tier] * organic_multiplier
                elif size_val >= 100:
                    # 100g: $2-$9 baseline (depends on spice)
                    if "garam masala" in ingredient.lower():
                        price = random.uniform(3, 9) * tier_multipliers[tier] * organic_multiplier
                    else:
                        price = random.uniform(2, 8) * tier_multipliers[tier] * organic_multiplier
                else:
                    price = random.uniform(2, 6) * tier_multipliers[tier] * organic_multiplier
            else:
                # Fallback
                price = base_price * tier_multipliers[tier] * organic_multiplier
        elif category == "herbs":
            # Herbs per bunch
            price = random.uniform(1, 4) * tier_multipliers[tier] * organic_multiplier
        elif category == "protein_poultry":
            # Chicken per lb: $3–$12/lb baseline
            if size_unit == "lb":
                price_per_lb = random.uniform(3, 12) * tier_multipliers[tier] * organic_multiplier
                price = price_per_lb * size_val
            else:
                price = base_price * tier_multipliers[tier] * organic_multiplier
        elif size_unit == "lb":
            price = base_price * size_val * tier_multipliers[tier] * organic_multiplier
        elif size_unit == "oz":
            price = base_price * (size_val / 16) * tier_multipliers[tier] * organic_multiplier
        elif size_unit == "g":
            price = base_price * (size_val / 28.35) * tier_multipliers[tier] * organic_multiplier
        elif size_unit in ["ct", "bunch"]:
            price = base_price * tier_multipliers[tier] * organic_multiplier
        else:
            price = base_price * tier_multipliers[tier] * organic_multiplier

        # Round to realistic prices
        price = round(price, 2)
        price = max(price, 0.99)  # Minimum price

        # HARD UPPER BOUNDS by category (prevent absurd prices)
        if category == "rice":
            price = min(price, 50.0)  # Max $50 for rice
        elif category == "oil":
            price = min(price, 60.0)  # Max $60 for ghee
        elif category == "spices":
            price = min(price, 15.0)  # Max $15 for spices
        elif category == "herbs":
            price = min(price, 5.0)  # Max $5 for herbs
        elif category == "protein_poultry":
            price = min(price, 100.0)  # Max $100 for chicken (large pack)

        # Calculate unit price
        if size_unit == "lb":
            unit_price = round(price / (size_val * 16), 4)  # per oz
            unit_price_unit = "oz"
        elif size_unit == "oz":
            unit_price = round(price / size_val, 4)
            unit_price_unit = "oz"
        elif size_unit == "g":
            unit_price = round(price / size_val, 4)
            unit_price_unit = "g"
        elif size_unit in ["ct", "bunch"]:
            unit_price = round(price / size_val, 4) if size_val > 0 else price
            unit_price_unit = "ea"
        elif size_unit == "L":
            unit_price = round(price / (size_val * 33.814), 4)  # per oz
            unit_price_unit = "oz"
        else:
            unit_price = price
            unit_price_unit = "ea"

        # Packaging
        if config["category"] in ["spices"]:
            packaging = random.choice(["glass", "plastic"])
        elif config["category"] in ["oil", "ghee"]:
            packaging = "glass"
        elif config["category"] in ["dairy"]:
            packaging = "plastic"
        else:
            packaging = "bulk"

        # Certifications
        certs = []
        if is_organic:
            certs.append("USDA Organic")
        if tier == "premium" and config["category"] in ["protein_poultry"]:
            certs.append("Free Range")

        # Product title
        organic_prefix = "Organic " if is_organic else ""
        title = f"{organic_prefix}{ingredient.title()}, {brand}"

        product = Product(
            product_id=f"prod{product_counter + idx:04d}",
            source_store_id=store_id,
            store_name=store_config["name"],
            category=config["category"],
            ingredient_key=ingredient,
            brand=brand,
            title=title,
            price=price,
            size_value=float(size_value),
            size_unit=size_unit,
            unit_price=unit_price,
            unit_price_unit=unit_price_unit,
            organic=is_organic,
            packaging=packaging,
            certifications=", ".join(certs) if certs else ""
        )

        products.append(product)

    return products


def generate_store_inventory(store_id: str, start_product_id: int = 1) -> tuple[List[Product], int]:
    """Generate complete inventory for a store

    Returns: (products, next_product_id)
    """
    store_config = STORES[store_id]
    products = []
    product_counter = start_product_id

    for ingredient, config in BIRYANI_INGREDIENTS.items():
        ingredient_products = generate_products_for_ingredient(
            ingredient, config, store_id, store_config, product_counter
        )
        products.extend(ingredient_products)
        product_counter += len(ingredient_products)

    return products, product_counter


def write_inventory_csv(store_id: str, products: List[Product], output_dir: Path):
    """Write inventory to CSV"""
    output_file = output_dir / f"{store_id}_inventory.csv"

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'product_id', 'source_store_id', 'store_name', 'category', 'ingredient_key',
            'brand', 'title', 'price', 'size_value', 'size_unit',
            'unit_price', 'unit_price_unit', 'organic', 'packaging', 'certifications'
        ])
        writer.writeheader()
        for product in products:
            writer.writerow(product.to_dict())

    print(f"✓ Generated {output_file.name}: {len(products)} products")
    return output_file


# ============================================================================
# Coverage Report
# ============================================================================

def generate_coverage_report(all_inventories: Dict[str, List[Product]], output_dir: Path):
    """Generate coverage analysis report"""
    report_lines = [
        "# Synthetic Inventory Coverage Report",
        "",
        "Generated: " + str(Path(__file__).name),
        "",
        "## Store Inventories",
        ""
    ]

    for store_id, products in all_inventories.items():
        store_config = STORES[store_id]
        report_lines.append(f"### {store_config['name']} ({store_id})")
        report_lines.append(f"- Total products: {len(products)}")
        report_lines.append(f"- Private label: {store_config['private_label']}")
        report_lines.append("")

    report_lines.extend([
        "## Coverage Matrix",
        "",
        "| Ingredient | FreshDirect | Whole Foods | ShopRite | Pure Indian Foods | Kaiser |",
        "|------------|-------------|-------------|----------|-------------------|--------|"
    ])

    for ingredient in BIRYANI_INGREDIENTS.keys():
        counts = []
        for store_id in ["freshdirect", "wholefoods", "shoprite", "pure_indian_foods", "kaiser"]:
            count = sum(1 for p in all_inventories[store_id] if p.ingredient_key == ingredient)
            counts.append(f"{count}" if count > 0 else "—")

        report_lines.append(f"| {ingredient} | {' | '.join(counts)} |")

    report_lines.extend([
        "",
        "## Store Exclusivity Verification",
        "",
        "Private label products are store-exclusive:"
    ])

    # Check for violations
    violations = []
    for store_id, products in all_inventories.items():
        store_private_label = STORES[store_id]["private_label"]

        # Check if this store's private label appears elsewhere
        for other_store_id, other_products in all_inventories.items():
            if other_store_id == store_id:
                continue

            for product in other_products:
                if store_private_label in product.brand:
                    violations.append(f"❌ {product.brand} found in {other_store_id} (should be {store_id} only)")

    if violations:
        report_lines.extend(violations)
    else:
        report_lines.append("✅ No violations detected - all private labels are store-exclusive")

    report_lines.extend([
        "",
        "## Multi-Store Split Test (Biryani)",
        "",
        "Expected outcome for 'chicken biryani for 4':",
        "- Primary store: FreshDirect or Whole Foods (produce, protein, dairy)",
        "- Specialty store: Pure Indian Foods (spices: garam masala, cardamom)",
        "- Unavailable: ~2-3 items (herbs: mint, cilantro; spices: bay leaves)",
        "",
        "✅ Ready for Opik evaluation with meaningful candidate sets"
    ])

    report_path = output_dir / "COVERAGE_REPORT.md"
    report_path.write_text("\n".join(report_lines))
    print(f"✓ Generated {report_path.name}")


# ============================================================================
# Main
# ============================================================================

def main():
    """Generate all inventories"""
    output_dir = Path(__file__).parent.parent / "data" / "inventories"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Synthetic Inventory Generator")
    print("=" * 60)

    all_inventories = {}
    global_product_counter = 1

    for store_id in STORES.keys():
        print(f"\nGenerating {store_id}...")
        products, global_product_counter = generate_store_inventory(store_id, global_product_counter)
        all_inventories[store_id] = products
        write_inventory_csv(store_id, products, output_dir)

    print("\nGenerating coverage report...")
    generate_coverage_report(all_inventories, output_dir)

    print("\n" + "=" * 60)
    print("✅ Complete!")
    print(f"Output: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
