#!/usr/bin/env python3
"""
Rebuild Trusted Inventory System

CRITICAL: Only use real product listings from trusted sources.
NO invented ethical scores, transparency claims, or safety ratings.

Trusted sources:
- data/samples/*.tsv (real store listings)
- data/alternatives/pure_indian_foods_products.csv
- data/alternatives/source_listings.csv

Output: Minimal, evidence-based product catalogs per store
"""

import csv
import json
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List

@dataclass
class Product:
    """Minimal product schema - evidence-based only"""
    product_id: str
    source_store_id: str
    store_name: str
    title: str
    brand: str
    price: float
    size_value: Optional[float]
    size_unit: Optional[str]
    unit_price: float
    unit_price_unit: str
    organic: bool  # Only if listing says "organic"
    category: str
    ingredient_key: str
    ingredient_form: str  # powder/seeds/leaves/whole/unknown
    is_synthetic: bool = False
    packaging: Optional[str] = None  # plastic/glass/unknown


def load_store_config(config_path: Path) -> Dict:
    """Load store catalog specification"""
    with open(config_path, 'r') as f:
        return json.load(f)


def infer_ingredient_form(title: str, config: Dict) -> str:
    """Infer ingredient form from product title keywords"""
    title_lower = title.lower()
    
    for form, keywords in config["ingredient_forms"]["inference_keywords"].items():
        if any(kw in title_lower for kw in keywords):
            return form
    
    return "unknown"


def parse_size(size_str: str) -> tuple[Optional[float], Optional[str]]:
    """Parse size string like '1 lb', '8oz', '100g'"""
    if not size_str:
        return None, None
    
    # Remove pricing parts (e.g., "$8.49/ea")
    size_str = re.sub(r'\$[\d.]+', '', size_str)
    
    # Try to extract number and unit
    match = re.search(r'([\d.]+)\s*([a-zA-Z]+)', size_str)
    if match:
        value = float(match.group(1))
        unit = match.group(2).lower()
        return value, unit
    
    return None, None


def parse_price(price_str: str) -> Optional[float]:
    """Parse price string like '$8.49', '$8.49/ea'"""
    if not price_str or price_str.lower() in ['sold out', 'n/a', '']:
        return None
    
    # Extract first number after $
    match = re.search(r'\$?([\d.]+)', price_str)
    if match:
        return float(match.group(1))
    
    return None


def compute_unit_price(price: float, size_value: Optional[float], size_unit: Optional[str]) -> tuple[float, str]:
    """Compute unit price normalized to oz"""
    if not size_value or not size_unit:
        return 0.0, "oz"
    
    # Convert to oz
    conversions = {
        'oz': 1.0,
        'lb': 16.0,
        'g': 0.035274,
        'kg': 35.274,
        'ml': 0.033814,
        'l': 33.814,
        'floz': 1.0
    }
    
    unit_lower = size_unit.lower().replace('.', '')
    multiplier = conversions.get(unit_lower, 1.0)
    
    size_in_oz = size_value * multiplier
    if size_in_oz > 0:
        return round(price / size_in_oz, 4), "oz"
    
    return 0.0, "oz"


def categorize_product(title: str, brand: str, store_config: Dict) -> tuple[str, str]:
    """Categorize product and extract ingredient key"""
    title_lower = title.lower()
    
    # Chicken/Poultry
    if any(kw in title_lower for kw in ['chicken', 'poultry', 'turkey']):
        return "protein_poultry", "chicken"
    
    # Rice
    if 'basmati' in title_lower or 'rice' in title_lower:
        return "rice", "basmati rice"
    
    # Spices
    spice_keywords = {
        'garam masala': 'garam masala',
        'turmeric': 'turmeric',
        'coriander': 'coriander',
        'cumin': 'cumin',
        'cardamom': 'cardamom',
        'bay': 'bay leaves'
    }
    for keyword, ingredient in spice_keywords.items():
        if keyword in title_lower:
            return "spices", ingredient
    
    # Ghee
    if 'ghee' in title_lower:
        return "oil", "ghee"
    
    # Produce
    produce_keywords = {
        'onion': 'onions',
        'tomato': 'tomatoes',
        'ginger': 'ginger',
        'garlic': 'garlic',
        'mint': 'mint',
        'cilantro': 'cilantro'
    }
    for keyword, ingredient in produce_keywords.items():
        if keyword in title_lower:
            return "produce", ingredient
    
    # Dairy
    if 'yogurt' in title_lower or 'yoghurt' in title_lower:
        return "dairy", "yogurt"
    
    return "pantry", "unknown"


def parse_tsv_sample(file_path: Path, store_config: Dict, config: Dict) -> List[Product]:
    """Parse TSV sample file (FreshDirect, Whole Foods, Kesar format)"""
    products = []
    store_id = store_config["store_id"]
    store_name = store_config["store_name"]
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        
        for idx, row in enumerate(reader, start=1):
            # Parse fields
            title = row.get('Product Name', '').strip('"')
            brand = row.get('Brand', '').strip('"')
            price_str = row.get('Price', '') or row.get('Sale Price', '')
            
            if not title or not brand:
                continue
            
            price = parse_price(price_str)
            if price is None:
                continue
            
            # Parse size from price string (e.g., "$8.49/ea")
            size_value, size_unit = parse_size(price_str)
            
            # Check if organic
            is_organic = 'organic' in title.lower()
            
            # Categorize
            category, ingredient_key = categorize_product(title, brand, store_config)
            
            # Infer form
            ingredient_form = infer_ingredient_form(title, config)
            
            # Compute unit price
            unit_price, unit_price_unit = compute_unit_price(price, size_value, size_unit)
            
            # Create product
            product = Product(
                product_id=f"prod_{store_id}_{idx:04d}",
                source_store_id=store_id,
                store_name=store_name,
                title=title,
                brand=brand,
                price=price,
                size_value=size_value,
                size_unit=size_unit,
                unit_price=unit_price,
                unit_price_unit=unit_price_unit,
                organic=is_organic,
                category=category,
                ingredient_key=ingredient_key,
                ingredient_form=ingredient_form,
                is_synthetic=False
            )
            
            products.append(product)
    
    return products


def parse_pure_indian_foods_csv(file_path: Path, store_config: Dict, config: Dict) -> List[Product]:
    """Parse Pure Indian Foods CSV"""
    products = []
    store_id = store_config["store_id"]
    store_name = store_config["store_name"]
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for idx, row in enumerate(reader, start=1):
            title = row.get('product_name', '').strip()
            brand = row.get('brand', 'Pure Indian Foods').strip()  # Default to store brand
            price_str = row.get('price', '')
            size_str = row.get('size', '')
            
            if not title:
                continue
            
            price = parse_price(price_str)
            if price is None:
                continue
            
            # Parse size
            size_value, size_unit = parse_size(size_str)
            
            # Check if organic
            is_organic = 'organic' in row.get('certifications', '').lower() or 'organic' in title.lower()
            
            # Categorize
            category, ingredient_key = categorize_product(title, brand, store_config)
            
            # Infer form
            ingredient_form = infer_ingredient_form(title, config)
            
            # Compute unit price
            unit_price, unit_price_unit = compute_unit_price(price, size_value, size_unit)
            
            product = Product(
                product_id=f"prod_{store_id}_{idx:04d}",
                source_store_id=store_id,
                store_name=store_name,
                title=title,
                brand=brand,
                price=price,
                size_value=size_value,
                size_unit=size_unit,
                unit_price=unit_price,
                unit_price_unit=unit_price_unit,
                organic=is_organic,
                category=category,
                ingredient_key=ingredient_key,
                ingredient_form=ingredient_form,
                is_synthetic=False
            )
            
            products.append(product)
    
    return products


def parse_alternatives_template(file_path: Path, store_config: Dict, config: Dict) -> List[Product]:
    """Parse alternatives_template.csv (detailed FreshDirect products with EWG data)"""
    products = []
    store_id = store_config["store_id"]
    store_name = store_config["store_name"]

    with open(file_path, 'r', encoding='utf-8') as f:
        # Skip first 2 lines (blank + generic column headers)
        next(f)  # Skip blank line
        next(f)  # Skip "Column 1,A,B,C..."

        # Line 3 has actual headers: 1,category,tier,brand,product_name,est_price...
        # We'll use csv.reader since the first column is a row number
        import csv as csv_module
        reader = csv_module.reader(f)

        # Read header row
        header = next(reader)
        # header = ['1', 'category', 'tier', 'brand', 'product_name', 'est_price', ...]

        # Create column index mapping
        col_map = {col: i for i, col in enumerate(header)}

        for idx, row in enumerate(reader, start=1):
            if len(row) < 5:
                continue

            # Parse fields using column indices
            category = row[col_map.get('category', 1)] if 'category' in col_map else ''
            title = row[col_map.get('product_name', 4)] if 'product_name' in col_map else ''
            brand_raw = row[col_map.get('brand', 3)] if 'brand' in col_map else ''
            price_str = row[col_map.get('est_price', 5)] if 'est_price' in col_map else ''
            certifications = row[col_map.get('certifications', 8)] if 'certifications' in col_map else ''

            if not title or not price_str:
                continue

            # Clean up brand (remove "Generic - Store Brand" prefix)
            brand = brand_raw.replace('Generic - Store Brand', 'FreshDirect').strip()
            if not brand or brand == 'Generic':
                brand = 'FreshDirect'

            price = parse_price(price_str)
            if price is None:
                continue

            # Parse size from price string (e.g., "$1.99/lb")
            size_value, size_unit = parse_size(price_str)

            # Check if organic
            is_organic = 'organic' in certifications.lower() or 'organic' in title.lower()

            # Categorize
            cat, ingredient_key = categorize_product(title, brand, store_config)

            # Infer form
            ingredient_form = infer_ingredient_form(title, config)

            # Compute unit price
            unit_price, unit_price_unit = compute_unit_price(price, size_value, size_unit)

            product = Product(
                product_id=f"prod_{store_id}_{idx:04d}",
                source_store_id=store_id,
                store_name=store_name,
                title=title,
                brand=brand,
                price=price,
                size_value=size_value,
                size_unit=size_unit,
                unit_price=unit_price,
                unit_price_unit=unit_price_unit,
                organic=is_organic,
                category=cat,
                ingredient_key=ingredient_key,
                ingredient_form=ingredient_form,
                is_synthetic=False
            )

            products.append(product)

    return products


def parse_source_listings(file_path: Path, config: Dict) -> Dict[str, List[Product]]:
    """Parse source_listings.csv (multi-store consolidated file)"""
    # Group products by inferred store based on category and brand
    store_products = {
        'freshdirect': [],
        'wholefoods': [],
        'kaiser': [],
        'pure_indian_foods': []
    }

    with open(file_path, 'r', encoding='utf-8') as f:
        # Skip first 2 comment lines
        next(f)  # Skip line 1
        next(f)  # Skip line 2
        reader = csv.DictReader(f)

        for idx, row in enumerate(reader, start=1):
            # Skip comment rows
            if row.get('category', '').startswith('#'):
                continue

            title = row.get('product_name', '').strip()
            brand = row.get('brand', '').strip()
            price_str = row.get('price', '')
            size_str = row.get('size', '')
            certifications = row.get('certifications', '')
            category_raw = row.get('category', '')

            if not title or not price_str:
                continue

            price = parse_price(price_str)
            if price is None:
                continue

            # Infer store from brand/category
            # Default to freshdirect if unclear
            store_id = 'freshdirect'

            # Check if it's a specialty Indian brand (Pure Indian Foods or Kesar)
            indian_brands = ['swad', 'laxmi', 'deep', '24 mantra', 'pure indian foods',
                           'shan', 'everest', 'mtr', 'gits', 'patak']
            if any(b in brand.lower() for b in indian_brands):
                # Could be Pure Indian Foods or Kesar - default to kesar for now
                store_id = 'kaiser'

            # If brand is "365", it's Whole Foods
            if '365' in brand:
                store_id = 'wholefoods'

            store_config = config["stores"][store_id]

            # Parse size
            size_value, size_unit = parse_size(size_str or price_str)

            # Check if organic
            is_organic = 'organic' in certifications.lower() or 'organic' in title.lower()

            # Categorize
            cat, ingredient_key = categorize_product(title, brand, store_config)

            # Infer form
            ingredient_form = infer_ingredient_form(title, config)

            # Compute unit price
            unit_price, unit_price_unit = compute_unit_price(price, size_value, size_unit)

            product = Product(
                product_id=f"prod_{store_id}_{len(store_products[store_id]) + 1:04d}",
                source_store_id=store_id,
                store_name=store_config["store_name"],
                title=title,
                brand=brand,
                price=price,
                size_value=size_value,
                size_unit=size_unit,
                unit_price=unit_price,
                unit_price_unit=unit_price_unit,
                organic=is_organic,
                category=cat,
                ingredient_key=ingredient_key,
                ingredient_form=ingredient_form,
                is_synthetic=False
            )

            store_products[store_id].append(product)

    return store_products


def write_inventory_csv(products: List[Product], output_path: Path):
    """Write products to CSV with minimal schema"""
    if not products:
        print(f"⚠️  No products to write for {output_path.stem}")
        return

    fieldnames = [
        'product_id', 'source_store_id', 'store_name', 'title', 'brand',
        'price', 'size_value', 'size_unit', 'unit_price', 'unit_price_unit',
        'organic', 'category', 'ingredient_key', 'ingredient_form',
        'is_synthetic', 'packaging'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for product in products:
            writer.writerow(asdict(product))

    print(f"✓ Wrote {len(products)} products to {output_path.name}")


def main():
    """Rebuild trusted inventories from real sources only"""
    base_dir = Path(__file__).parent.parent
    config_path = base_dir / "config" / "store_catalog_spec.json"
    samples_dir = base_dir / "data" / "samples"
    alternatives_dir = base_dir / "data" / "alternatives"
    output_dir = base_dir / "data" / "inventories_trusted"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Load config
    config = load_store_config(config_path)

    print("=" * 80)
    print("REBUILD TRUSTED INVENTORY - Evidence-Based Only")
    print("=" * 80)
    print()

    # Initialize store inventories
    all_inventories = {
        'freshdirect': [],
        'wholefoods': [],
        'kaiser': [],
        'pure_indian_foods': []
    }

    # 1. Parse source_listings.csv (multi-store consolidated)
    print("📊 Parsing source_listings.csv (consolidated multi-store data)...")
    source_listings_path = alternatives_dir / "source_listings.csv"
    if source_listings_path.exists():
        store_products = parse_source_listings(source_listings_path, config)
        for store_id, products in store_products.items():
            all_inventories[store_id].extend(products)
            print(f"  - Added {len(products)} products to {store_id}")
    else:
        print("  ⚠️  source_listings.csv not found")

    # 2. Parse Pure Indian Foods CSV
    print("\n📦 Parsing Pure Indian Foods products...")
    pif_path = alternatives_dir / "pure_indian_foods_products.csv"
    if pif_path.exists():
        pif_products = parse_pure_indian_foods_csv(
            pif_path,
            config["stores"]["pure_indian_foods"],
            config
        )
        all_inventories["pure_indian_foods"].extend(pif_products)
        print(f"  - Added {len(pif_products)} products")
    else:
        print("  ⚠️  pure_indian_foods_products.csv not found")

    # 3. Parse alternatives_template.csv (detailed FreshDirect with EWG data)
    print("\n🌟 Parsing alternatives_template.csv (FreshDirect detailed with EWG)...")
    alternatives_path = alternatives_dir / "alternatives_template.csv"
    if alternatives_path.exists():
        freshdirect_detailed = parse_alternatives_template(
            alternatives_path,
            config["stores"]["freshdirect"],
            config
        )
        # Deduplicate by title to avoid duplicates from source_listings
        existing_titles = {p.title.lower() for p in all_inventories['freshdirect']}
        new_products = [p for p in freshdirect_detailed if p.title.lower() not in existing_titles]
        all_inventories['freshdirect'].extend(new_products)
        print(f"  - Added {len(new_products)} unique FreshDirect products ({len(freshdirect_detailed) - len(new_products)} duplicates skipped)")
    else:
        print("  ⚠️  alternatives_template.csv not found")

    # 4. Parse TSV samples (if available, as supplemental)
    print("\n📁 Parsing TSV samples (supplemental)...")
    for sample_file, store_id in [
        ("freshdirect_chicken_sample.tsv", "freshdirect"),
        ("wholefoods_chicken_sample.tsv", "wholefoods"),
        ("kesar_grocery_sample.tsv", "kaiser")
    ]:
        sample_path = samples_dir / sample_file
        if sample_path.exists():
            products = parse_tsv_sample(
                sample_path,
                config["stores"][store_id],
                config
            )
            # Deduplicate
            existing_titles = {p.title.lower() for p in all_inventories[store_id]}
            new_products = [p for p in products if p.title.lower() not in existing_titles]
            all_inventories[store_id].extend(new_products)
            print(f"  - {sample_file}: Added {len(new_products)} unique products ({len(products) - len(new_products)} duplicates skipped)")

    # Write inventories
    print("\n" + "=" * 80)
    print("WRITING TRUSTED INVENTORIES")
    print("=" * 80)
    print()

    for store_id, products in all_inventories.items():
        if products:
            write_inventory_csv(products, output_dir / f"{store_id}_inventory.csv")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY - Trusted Inventories Only")
    print("=" * 80)

    total_products = sum(len(products) for products in all_inventories.values())
    print(f"\n✓ Total products from real sources: {total_products}")

    for store_id, products in all_inventories.items():
        print(f"  - {store_id}: {len(products)} products")

    # Check ingredient coverage for biryani demo
    print("\n" + "-" * 80)
    print("INGREDIENT COVERAGE CHECK (Biryani Demo)")
    print("-" * 80)

    biryani_ingredients = [
        'chicken', 'basmati rice', 'onions', 'tomatoes', 'yogurt',
        'ginger', 'garlic', 'turmeric', 'cumin', 'coriander',
        'cardamom', 'garam masala', 'bay leaves', 'mint', 'cilantro', 'ghee'
    ]

    ingredient_coverage = {}
    for ingredient in biryani_ingredients:
        count = 0
        for products in all_inventories.values():
            count += sum(1 for p in products if ingredient in p.ingredient_key.lower())
        ingredient_coverage[ingredient] = count

    print("\nIngredients with products:")
    for ingredient, count in sorted(ingredient_coverage.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"  ✓ {ingredient}: {count} products")

    print("\nMissing ingredients (need synthetic fill):")
    missing = [ing for ing, count in ingredient_coverage.items() if count == 0]
    if missing:
        for ingredient in missing:
            print(f"  ⚠️  {ingredient}: 0 products")
    else:
        print("  ✓ All ingredients have coverage!")

    print(f"\n✓ Output directory: {output_dir}")
    print("\nNOTE: Controlled synthetic fill for missing demo items will be added in next step")
    print("=" * 80)


if __name__ == "__main__":
    main()
