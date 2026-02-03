"""
ProductIndex: Product retrieval with fresh produce merge

CRITICAL FIX for P0 bug:
- Searches both ingredient-specific category AND produce category
- Ensures fresh ginger/garlic/herbs are found alongside dried/powder variants
"""

import csv
import re
from pathlib import Path
from typing import List, Dict, Set, Optional
from dataclasses import dataclass

from src.agents.product_agent import apply_form_constraints


@dataclass
class ProductCandidate:
    """Product candidate for an ingredient"""
    product_id: str
    title: str
    brand: str
    price: float
    size: str
    unit: str
    organic: bool
    category: str
    store_type: str
    available_stores: List[str]
    source_store_id: str  # MANDATORY: Which store this product comes from

    # Computed and loaded fields
    unit_price: float = 0.0  # per oz
    unit_price_unit: str = "oz"  # Unit for unit_price
    form_score: int = 0  # 0=best (fresh), higher=worse (granules)

    def __post_init__(self):
        """Compute derived fields"""
        # Only compute unit_price if not already set from CSV (default is 0.0)
        if self.unit_price == 0.0:
            self.unit_price = self._compute_unit_price()
        self.form_score = self._compute_form_score()

    def _compute_unit_price(self) -> float:
        """Convert price to price per oz"""
        # Parse size string (e.g., "1 lb", "16 oz", "1.5oz")
        size_str = self.size.lower().replace(" ", "")

        try:
            # Extract number
            num_match = re.search(r'(\d+\.?\d*)', size_str)
            if not num_match:
                return self.price  # Fallback

            amount = float(num_match.group(1))

            # Convert to oz
            if 'lb' in size_str or 'pound' in size_str:
                oz = amount * 16
            elif 'oz' in size_str:
                oz = amount
            elif 'g' in size_str:
                oz = amount / 28.35
            else:
                return self.price  # Unknown unit

            return round(self.price / oz, 4) if oz > 0 else self.price

        except (ValueError, ZeroDivisionError):
            return self.price

    def _compute_form_score(self) -> int:
        """
        Compute form preference score (lower is better)

        Form hierarchy:
        - 0: Fresh (fresh, bunch, whole produce)
        - 5: Generic match
        - 10: Dried/minced (but not powder/granules)
        - 20: Granules/powder (avoid for fresh ingredients)

        IMPORTANT: Check for processed forms FIRST before checking for "root"
        because "Ginger Root Powder" contains both "root" and "powder"
        """
        title_lower = self.title.lower()

        # Granules/powder/minced/dried WORST for fresh ingredients (check FIRST)
        if any(word in title_lower for word in ["granules", "powder", "minced", "dried", "ground"]):
            return 20

        # Fresh is best (check AFTER processed forms)
        if any(word in title_lower for word in ["fresh", "bunch", "organic whole"]):
            return 0

        # Root/whole (but not if already caught by processed check above)
        if "root" in title_lower or "whole" in title_lower:
            return 0

        # Generic match (neither explicitly fresh nor processed)
        return 5


# ============================================================================
# Fresh Produce Ingredients (P0 FIX)
# ============================================================================

FRESH_PRODUCE_INGREDIENTS = {
    "ginger", "garlic", "mint", "cilantro", "basil", "parsley",
    "scallions", "green onions", "chives", "dill", "thyme", "rosemary",
    "oregano", "sage", "tarragon"
}

INGREDIENT_SYNONYMS = {
    "green onions": ["scallions", "spring onions"],
    "scallions": ["green onions", "spring onions"],
    "cilantro": ["coriander leaves"],
    "ginger": ["ginger root"],
}


# ============================================================================
# ProductIndex
# ============================================================================

class ProductIndex:
    """
    Product retrieval index with fresh produce merge

    Key feature: For ingredients like ginger/garlic/herbs, searches BOTH:
    1. The ingredient-specific category (e.g., inventory["ginger"])
    2. The produce category (e.g., inventory["produce"])

    This ensures fresh variants are never missed.
    """

    def __init__(self, inventory_path: Optional[Path] = None, use_synthetic: bool = True):
        """
        Initialize product index from CSV inventory

        Args:
            inventory_path: Path to source_listings.csv (or None for default)
            use_synthetic: If True, load from trusted inventories (recommended)
        """
        self.inventory_path = inventory_path
        self.inventory: Dict[str, List[ProductCandidate]] = {}
        self.all_products: List[ProductCandidate] = []
        self.use_synthetic = use_synthetic

        if use_synthetic:
            self._load_trusted_inventories()
        else:
            if inventory_path is None:
                # Fallback to old inventory
                inventory_path = Path(__file__).parent.parent.parent / "data" / "alternatives" / "source_listings.csv"
                self.inventory_path = inventory_path
            self._load_inventory()

    def _load_trusted_inventories(self):
        """Load trusted inventory from multiple store CSV files (evidence-based only)"""
        inventories_dir = Path(__file__).parent.parent.parent / "data" / "inventories_trusted"

        if not inventories_dir.exists():
            print(f"⚠️  Trusted inventories directory not found at {inventories_dir}")
            print(f"    Run: python scripts/rebuild_trusted_inventory.py")
            # Fallback to old inventory
            self.use_synthetic = False
            inventory_path = Path(__file__).parent.parent.parent / "data" / "alternatives" / "source_listings.csv"
            self.inventory_path = inventory_path
            self._load_inventory()
            return

        # Load all store inventory files
        store_files = list(inventories_dir.glob("*_inventory.csv"))

        if not store_files:
            print(f"⚠️  No inventory files found in {inventories_dir}")
            return

        total_products = 0

        for store_file in store_files:
            with open(store_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    # Use new CSV format (already has source_store_id)
                    product_id = row['product_id']
                    source_store_id = row['source_store_id']
                    category = row['category'].strip().lower()
                    brand = row['brand'].strip()
                    title = row['title'].strip()
                    price = float(row['price'])
                    size_value = row['size_value']
                    size_unit = row['size_unit']
                    size = f"{size_value} {size_unit}"
                    unit = size_unit
                    unit_price = float(row['unit_price'])
                    unit_price_unit = row['unit_price_unit']
                    organic = row['organic'].lower() == 'true'
                    store_type = "specialty" if source_store_id == "pure_indian_foods" else "primary"
                    available_stores = [row['store_name']]
                    ingredient_key = row.get('ingredient_key', '').strip().lower()

                    candidate = ProductCandidate(
                        product_id=product_id,
                        title=title,
                        brand=brand,
                        price=price,
                        size=size,
                        unit=unit,
                        unit_price=unit_price,
                        unit_price_unit=unit_price_unit,
                        organic=organic,
                        category=category,
                        store_type=store_type,
                        available_stores=available_stores,
                        source_store_id=source_store_id
                    )

                    self.all_products.append(candidate)

                    # Index by category
                    if category not in self.inventory:
                        self.inventory[category] = []
                    self.inventory[category].append(candidate)

                    # Also index by ingredient_key for easier lookup
                    if ingredient_key and ingredient_key not in self.inventory:
                        self.inventory[ingredient_key] = []
                    if ingredient_key:
                        self.inventory[ingredient_key].append(candidate)

                    total_products += 1

        print(f"✓ Loaded {total_products} products from {len(store_files)} store inventories")
        print(f"✓ Indexed into {len(self.inventory)} categories")

    def _load_synthetic_inventories(self):
        """Compatibility alias for _load_trusted_inventories"""
        return self._load_trusted_inventories()

    def _load_inventory(self):
        """Load inventory from CSV (OLD FORMAT - fallback)"""
        if not self.inventory_path.exists():
            print(f"⚠️  Inventory not found at {self.inventory_path}")
            return

        with open(self.inventory_path, 'r', encoding='utf-8') as f:
            # Skip comment lines
            lines = [line for line in f if not line.strip().startswith('#')]

        reader = csv.DictReader(lines)
        product_counter = 0

        for row in reader:
            if not row.get('category') or not row.get('category').strip():
                continue

            category = row['category'].strip().lower()
            product_name = row.get('product_name', '').strip()
            brand = row.get('brand', '').strip()
            price_str = row.get('price', '').strip()

            # Skip sold out items
            if price_str.lower() == 'sold out':
                continue

            # Parse price
            try:
                price = float(price_str.replace('$', '').replace(',', '').strip())
            except (ValueError, TypeError):
                continue

            # Determine organic status
            certifications = row.get('certifications', '')
            organic = 'USDA Organic' in certifications or 'Organic' in certifications

            # Determine store type, available stores, and source_store_id
            if "Pure Indian Foods" in brand:
                store_type = "specialty"
                available_stores = ["Pure Indian Foods"]
                source_store_id = "pure_indian_foods"
            elif "365 by Whole Foods" in brand or "365" in brand:
                store_type = "primary"
                available_stores = ["Whole Foods", "Whole Foods Market"]
                source_store_id = "wholefoods"
            elif "Bowl & Basket" in brand:
                store_type = "primary"
                available_stores = ["ShopRite"]
                source_store_id = "shoprite"
            else:
                store_type = "primary"
                available_stores = ["FreshDirect"]  # Default
                source_store_id = "freshdirect"

            product_counter += 1
            candidate = ProductCandidate(
                product_id=f"prod{product_counter:04d}",
                title=product_name,
                brand=brand,
                price=price,
                size=row.get('size', '').strip(),
                unit=row.get('unit', 'ea').strip(),
                organic=organic,
                category=category,
                store_type=store_type,
                available_stores=available_stores,
                source_store_id=source_store_id
            )

            self.all_products.append(candidate)

            # Index by category
            if category not in self.inventory:
                self.inventory[category] = []
            self.inventory[category].append(candidate)

        print(f"✓ Loaded {product_counter} products into {len(self.inventory)} categories")

    def retrieve(self, ingredient_name: str, max_candidates: int = 6) -> List[ProductCandidate]:
        """
        Retrieve product candidates for an ingredient

        CRITICAL: For fresh produce ingredients (ginger, garlic, herbs),
        this searches ACROSS multiple related categories:
        - The ingredient-specific category
        - All produce* categories
        - The spices category (for dried/powder variants)

        Args:
            ingredient_name: Ingredient to search for
            max_candidates: Maximum number of candidates to return

        Returns:
            List of ProductCandidate, sorted by form_score (fresh first)
        """
        ingredient_lower = ingredient_name.lower().strip()
        candidates = []
        seen_ids: Set[str] = set()

        # Normalize ingredient name
        normalized = self._normalize_ingredient(ingredient_lower)

        # 1. Search by original ingredient name first (for synthetic inventory with ingredient_key)
        if ingredient_lower in self.inventory:
            for product in self.inventory[ingredient_lower]:
                if product.product_id not in seen_ids:
                    candidates.append(product)
                    seen_ids.add(product.product_id)

        # 2. Search ingredient-specific category (for legacy inventory)
        if normalized in self.inventory and normalized != ingredient_lower:
            for product in self.inventory[normalized]:
                if product.product_id not in seen_ids:
                    candidates.append(product)
                    seen_ids.add(product.product_id)

        # 2. CRITICAL FIX: For fresh produce ingredients, search multiple categories
        if normalized in FRESH_PRODUCE_INGREDIENTS:
            # Search all produce categories (produce, produce_roots, produce_greens, etc.)
            for category_name in self.inventory.keys():
                if category_name.startswith('produce'):
                    for product in self.inventory[category_name]:
                        if self._matches_ingredient(product.title, normalized):
                            if product.product_id not in seen_ids:
                                candidates.append(product)
                                seen_ids.add(product.product_id)

            # Also search spices category for dried/powder variants
            if 'spices' in self.inventory:
                for product in self.inventory['spices']:
                    if self._matches_ingredient(product.title, normalized):
                        if product.product_id not in seen_ids:
                            candidates.append(product)
                            seen_ids.add(product.product_id)

        # 3. Apply hard form constraints to filter out incompatible products
        # Convert ProductCandidate objects to dict format for constraint filtering
        candidates_as_dicts = [
            {"title": c.title, "brand": c.brand, "product_id": c.product_id}
            for c in candidates
        ]

        # Apply constraints using the original ingredient_name (which may include form like "fresh ginger")
        filtered_dicts = apply_form_constraints(candidates_as_dicts, ingredient_name)

        # Get filtered product IDs
        filtered_ids = {d["product_id"] for d in filtered_dicts}

        # Filter original candidates to only those that passed constraints
        candidates = [c for c in candidates if c.product_id in filtered_ids]

        # 4. Sort by form preference (fresh > dried > powder > granules)
        candidates.sort(key=lambda c: (c.form_score, c.organic == False, c.unit_price))

        return candidates[:max_candidates]

    def _matches_ingredient(self, product_title: str, ingredient_name: str) -> bool:
        """Check if product title matches ingredient name"""
        title_lower = product_title.lower()
        ingredient_lower = ingredient_name.lower()

        # Direct match
        if ingredient_lower in title_lower:
            return True

        # Check synonyms
        if ingredient_lower in INGREDIENT_SYNONYMS:
            for synonym in INGREDIENT_SYNONYMS[ingredient_lower]:
                if synonym in title_lower:
                    return True

        # Check with common variants
        variants = [
            ingredient_lower + " root",
            "fresh " + ingredient_lower,
            ingredient_lower + " powder",
            ingredient_lower + " granules",
        ]
        return any(variant in title_lower for variant in variants)

    def _search_produce_category(self, ingredient_name: str) -> List[ProductCandidate]:
        """
        Search produce category for fresh variants of an ingredient

        Example: ingredient_name="ginger"
        Finds: "Fresh Organic Ginger Root", "Ginger Root", etc.
        """
        if "produce" not in self.inventory:
            return []

        matches = []
        search_terms = [ingredient_name]

        # Add synonyms
        if ingredient_name in INGREDIENT_SYNONYMS:
            search_terms.extend(INGREDIENT_SYNONYMS[ingredient_name])

        # Add common produce variants
        search_terms.extend([
            f"{ingredient_name} root",
            f"fresh {ingredient_name}",
            f"{ingredient_name} bunch"
        ])

        for product in self.inventory["produce"]:
            title_lower = product.title.lower()

            # Check if any search term matches
            if any(term in title_lower for term in search_terms):
                matches.append(product)

        return matches

    def _normalize_ingredient(self, ingredient_name: str) -> str:
        """Normalize ingredient name to category key"""
        # Handle common variations
        ingredient_name = ingredient_name.lower().strip()

        # Map common ingredient names to categories
        category_map = {
            "chicken breast": "protein_poultry",
            "chicken thigh": "protein_poultry",
            "chicken": "protein_poultry",
            "basmati rice": "rice",
            "rice": "rice",
            "onion": "onions",
            "onions": "onions",
            "tomato": "tomatoes",
            "tomatoes": "tomatoes",
            "yogurt": "dairy",
            "ghee": "oil",
            "cooking oil": "oil",
            "olive oil": "oil",
        }

        # Check direct mapping first
        if ingredient_name in category_map:
            return category_map[ingredient_name]

        # Check if ingredient name matches a category directly
        if ingredient_name in self.inventory:
            return ingredient_name

        # Try partial matches
        for category in self.inventory.keys():
            if ingredient_name in category or category in ingredient_name:
                return category

        # Return original if no match
        return ingredient_name

    def get_statistics(self) -> Dict:
        """Get index statistics"""
        return {
            "total_products": len(self.all_products),
            "categories": len(self.inventory),
            "organic_products": sum(1 for p in self.all_products if p.organic),
            "fresh_produce_categories": len([c for c in self.inventory.keys() if c in FRESH_PRODUCE_INGREDIENTS])
        }


# ============================================================================
# CLI Test
# ============================================================================

if __name__ == "__main__":
    print("=== Testing ProductIndex ===\n")

    index = ProductIndex()
    print(f"Index stats: {index.get_statistics()}\n")

    # TEST P0 FIX: Ginger must include fresh + dried
    print("TEST: Ginger retrieval (P0 fix)")
    print("-" * 60)
    ginger_candidates = index.retrieve("ginger")

    has_fresh = any("fresh" in c.title.lower() or "root" in c.title.lower() for c in ginger_candidates)
    has_dried = any("granules" in c.title.lower() or "powder" in c.title.lower() for c in ginger_candidates)

    for i, candidate in enumerate(ginger_candidates):
        print(f"{i+1}. {candidate.title} ({candidate.brand})")
        print(f"   Form score: {candidate.form_score}, Organic: {candidate.organic}, Price: ${candidate.price}")

    print(f"\n✓ Has fresh: {has_fresh}")
    print(f"✓ Has dried: {has_dried}")

    if has_fresh and has_dried:
        print("\n✅ P0 FIX VERIFIED: Fresh ginger found alongside dried variants")
    else:
        print("\n❌ P0 FIX FAILED: Missing fresh or dried variants")

    # Test other fresh ingredients
    print("\n" + "="*60)
    print("TEST: Other fresh produce ingredients")
    print("-" * 60)

    for ingredient in ["garlic", "mint", "cilantro"]:
        candidates = index.retrieve(ingredient, max_candidates=3)
        print(f"\n{ingredient.upper()}: {len(candidates)} candidates")
        for c in candidates:
            print(f"  - {c.title} (form_score: {c.form_score})")
