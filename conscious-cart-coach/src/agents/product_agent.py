"""
Product Agent - Returns candidate products per ingredient.

Does NOT assign tiers. Returns all viable candidates with normalized
unit pricing. DecisionEngine handles tier assignment.

Usage:
    from src.agents.product_agent import ProductAgent

    agent = ProductAgent()
    result = agent.get_candidates([
        IngredientSpec(name="spinach", quantity="1 bunch"),
    ])
"""

import re
from typing import Any

from ..contracts.models import IngredientSpec, ProductCandidate
from ..core.types import AgentResult, Evidence, make_result, make_error
from ..facts import get_facts, FactsGateway


# Simulated inventory for hackathon demo.
# Each product has: id, title, brand, size, price, organic flag.
# No tier labels - DecisionEngine assigns tiers.
SIMULATED_INVENTORY: dict[str, list[dict]] = {
    "spinach": [
        {"id": "sp001", "title": "Organic Baby Spinach", "brand": "Earthbound Farm", "size": "5oz", "price": 5.99, "organic": True},
        {"id": "sp002", "title": "Baby Spinach", "brand": "Fresh Express", "size": "5oz", "price": 3.99, "organic": False},
        {"id": "sp003", "title": "Spinach Bunch", "brand": "Store Brand", "size": "8oz", "price": 1.99, "organic": False},
    ],
    "kale": [
        {"id": "ka001", "title": "Organic Lacinato Kale", "brand": "Local Farm", "size": "6oz", "price": 4.49, "organic": True},
        {"id": "ka002", "title": "Curly Kale", "brand": "Store Brand", "size": "6oz", "price": 2.49, "organic": False},
    ],
    "lettuce": [
        {"id": "le001", "title": "Organic Romaine Hearts", "brand": "Earthbound Farm", "size": "18oz", "price": 5.49, "organic": True},
        {"id": "le002", "title": "Romaine Hearts", "brand": "Fresh Express", "size": "18oz", "price": 3.49, "organic": False},
        {"id": "le003", "title": "Iceberg Lettuce", "brand": "Store Brand", "size": "24oz", "price": 1.79, "organic": False},
    ],
    "tomatoes": [
        {"id": "to001", "title": "Organic Heirloom Tomatoes", "brand": "Local Farm", "size": "16oz", "price": 6.99, "organic": True},
        {"id": "to002", "title": "Roma Tomatoes", "brand": "Store Brand", "size": "16oz", "price": 2.99, "organic": False},
        {"id": "to003", "title": "Tomatoes on Vine", "brand": "Store Brand", "size": "16oz", "price": 3.49, "organic": False},
    ],
    "cherry_tomatoes": [
        {"id": "ct001", "title": "Organic Cherry Tomatoes", "brand": "NatureSweet", "size": "10oz", "price": 5.99, "organic": True},
        {"id": "ct002", "title": "Cherry Tomatoes", "brand": "Store Brand", "size": "16oz", "price": 3.49, "organic": False},
    ],
    "strawberries": [
        {"id": "st001", "title": "Organic Strawberries", "brand": "Driscoll's", "size": "16oz", "price": 7.99, "organic": True},
        {"id": "st002", "title": "Strawberries", "brand": "Driscoll's", "size": "16oz", "price": 4.99, "organic": False},
    ],
    "blueberries": [
        {"id": "bl001", "title": "Organic Blueberries", "brand": "Driscoll's", "size": "6oz", "price": 6.99, "organic": True},
        {"id": "bl002", "title": "Blueberries", "brand": "Store Brand", "size": "16oz", "price": 4.49, "organic": False},
    ],
    "onion": [
        {"id": "on001", "title": "Organic Yellow Onions", "brand": "Local Farm", "size": "32oz", "price": 3.99, "organic": True},
        {"id": "on002", "title": "Yellow Onions", "brand": "Store Brand", "size": "48oz", "price": 1.99, "organic": False},
    ],
    "garlic": [
        {"id": "ga001", "title": "Organic Garlic", "brand": "Local Farm", "size": "2oz", "price": 1.99, "organic": True},
        {"id": "ga002", "title": "Garlic", "brand": "Store Brand", "size": "2oz", "price": 0.79, "organic": False},
    ],
    "ginger": [
        {"id": "gi001", "title": "Organic Ginger Root", "brand": "Store Brand", "size": "4oz", "price": 3.49, "organic": True},
        {"id": "gi002", "title": "Ginger Root", "brand": "Store Brand", "size": "4oz", "price": 2.49, "organic": False},
    ],
    "chicken": [
        {"id": "ch001", "title": "Organic Free-Range Chicken Thighs", "brand": "Bell & Evans", "size": "16oz", "price": 9.99, "organic": True},
        {"id": "ch002", "title": "Chicken Thighs", "brand": "Perdue", "size": "16oz", "price": 5.99, "organic": False},
        {"id": "ch003", "title": "Chicken Thighs Value Pack", "brand": "Store Brand", "size": "32oz", "price": 7.49, "organic": False},
    ],
    "eggs": [
        {"id": "eg001", "title": "Pasture-Raised Eggs", "brand": "Vital Farms", "size": "dozen", "price": 8.99, "organic": True},
        {"id": "eg002", "title": "Free-Range Eggs", "brand": "Pete and Gerry's", "size": "dozen", "price": 5.99, "organic": True},
        {"id": "eg003", "title": "Large Eggs", "brand": "Store Brand", "size": "dozen", "price": 3.49, "organic": False},
    ],
    "salmon": [
        {"id": "sa001", "title": "Wild-Caught Sockeye Salmon", "brand": "Wild Planet", "size": "16oz", "price": 14.99, "organic": False},
        {"id": "sa002", "title": "Atlantic Salmon Fillet", "brand": "Store Brand", "size": "16oz", "price": 9.99, "organic": False},
    ],
    "milk": [
        {"id": "mi001", "title": "Organic Whole Milk", "brand": "Organic Valley", "size": "64oz", "price": 7.49, "organic": True},
        {"id": "mi002", "title": "Whole Milk", "brand": "Store Brand", "size": "128oz", "price": 4.29, "organic": False},
    ],
    "yogurt": [
        {"id": "yo001", "title": "Organic Greek Yogurt", "brand": "Stonyfield", "size": "32oz", "price": 6.99, "organic": True},
        {"id": "yo002", "title": "Greek Yogurt", "brand": "Fage", "size": "32oz", "price": 5.49, "organic": False},
        {"id": "yo003", "title": "Greek Yogurt", "brand": "Store Brand", "size": "32oz", "price": 3.99, "organic": False},
    ],
    "ghee": [
        {"id": "gh001", "title": "Organic Grass-Fed Ghee", "brand": "4th & Heart", "size": "9oz", "price": 12.99, "organic": True},
        {"id": "gh002", "title": "Ghee", "brand": "Deep", "size": "8oz", "price": 7.99, "organic": False},
    ],
    "cumin": [
        {"id": "cu001", "title": "Organic Ground Cumin", "brand": "Simply Organic", "size": "2.31oz", "price": 5.99, "organic": True},
        {"id": "cu002", "title": "Ground Cumin", "brand": "McCormick", "size": "1.5oz", "price": 4.49, "organic": False},
    ],
    "turmeric": [
        {"id": "tu001", "title": "Organic Ground Turmeric", "brand": "Simply Organic", "size": "2.38oz", "price": 6.49, "organic": True},
        {"id": "tu002", "title": "Ground Turmeric", "brand": "McCormick", "size": "1.37oz", "price": 4.99, "organic": False},
    ],
    "coriander": [
        {"id": "co001", "title": "Organic Ground Coriander", "brand": "Simply Organic", "size": "2.29oz", "price": 5.49, "organic": True},
        {"id": "co002", "title": "Ground Coriander", "brand": "McCormick", "size": "1.5oz", "price": 4.29, "organic": False},
    ],
    "rice": [
        {"id": "ri001", "title": "Organic Basmati Rice", "brand": "Lundberg", "size": "32oz", "price": 8.99, "organic": True},
        {"id": "ri002", "title": "Basmati Rice", "brand": "Tilda", "size": "32oz", "price": 5.99, "organic": False},
        {"id": "ri003", "title": "Long Grain Rice", "brand": "Store Brand", "size": "32oz", "price": 2.99, "organic": False},
    ],
    "bell_pepper": [
        {"id": "bp001", "title": "Organic Bell Peppers", "brand": "Local Farm", "size": "24oz", "price": 5.99, "organic": True},
        {"id": "bp002", "title": "Bell Peppers", "brand": "Store Brand", "size": "24oz", "price": 3.99, "organic": False},
    ],
    "hot_peppers": [
        {"id": "hp001", "title": "Serrano Peppers", "brand": "Store Brand", "size": "4oz", "price": 1.99, "organic": False},
        {"id": "hp002", "title": "Jalapeno Peppers", "brand": "Store Brand", "size": "4oz", "price": 1.49, "organic": False},
    ],
    "cilantro": [
        {"id": "ci001", "title": "Organic Cilantro", "brand": "Local Farm", "size": "1oz", "price": 2.99, "organic": True},
        {"id": "ci002", "title": "Cilantro", "brand": "Store Brand", "size": "1oz", "price": 1.49, "organic": False},
    ],
    "mint": [
        {"id": "mt001", "title": "Organic Fresh Mint", "brand": "Local Farm", "size": "1oz", "price": 3.49, "organic": True},
        {"id": "mt002", "title": "Fresh Mint", "brand": "Store Brand", "size": "0.75oz", "price": 1.99, "organic": False},
    ],
    "potatoes": [
        {"id": "po001", "title": "Organic Russet Potatoes", "brand": "Local Farm", "size": "80oz", "price": 6.99, "organic": True},
        {"id": "po002", "title": "Russet Potatoes", "brand": "Store Brand", "size": "80oz", "price": 3.99, "organic": False},
    ],
    "broccoli": [
        {"id": "br001", "title": "Organic Broccoli Crowns", "brand": "Local Farm", "size": "12oz", "price": 4.49, "organic": True},
        {"id": "br002", "title": "Broccoli Crowns", "brand": "Store Brand", "size": "12oz", "price": 2.49, "organic": False},
    ],
}

# Aliases for ingredient normalization
INGREDIENT_ALIASES: dict[str, str] = {
    "baby spinach": "spinach", "fresh spinach": "spinach",
    "lacinato kale": "kale", "dinosaur kale": "kale",
    "romaine": "lettuce",
    "roma tomatoes": "tomatoes", "plum tomatoes": "tomatoes",
    "grape tomatoes": "cherry_tomatoes",
    "yellow onion": "onion", "white onion": "onion", "red onion": "onion", "onions": "onion",
    "fresh ginger": "ginger", "ginger root": "ginger",
    "chicken thighs": "chicken", "chicken breast": "chicken",
    "chicken drumsticks": "chicken", "whole chicken": "chicken",
    "basmati rice": "rice", "jasmine rice": "rice", "long grain rice": "rice",
    "fresh cilantro": "cilantro", "coriander leaves": "cilantro",
    "fresh mint": "mint", "mint leaves": "mint",
    "green bell pepper": "bell_pepper", "red bell pepper": "bell_pepper",
    "serrano": "hot_peppers", "jalapeno": "hot_peppers", "green chili": "hot_peppers",
    "potato": "potatoes",
}


def parse_size_oz(size_str: str) -> float:
    """
    Parse a size string to ounces for unit price normalization.

    Handles: "5oz", "16oz", "1 lb", "32oz", "dozen", "2.31oz"
    """
    s = size_str.lower().strip()
    if s == "dozen":
        return 12.0
    match = re.match(r"([\d.]+)\s*(oz|lb|lbs|g|kg)?", s)
    if not match:
        return 1.0
    amount = float(match.group(1))
    unit = match.group(2) or "oz"
    if unit in ("lb", "lbs"):
        return amount * 16.0
    elif unit == "g":
        return amount / 28.35
    elif unit == "kg":
        return amount * 35.27
    return amount


class ProductAgent:
    """
    Product agent that returns candidate products per ingredient.

    Does NOT assign tiers. Returns candidates sorted by unit_price.
    DecisionEngine handles tier assignment and neighbor selection.
    """

    AGENT_NAME = "product"

    def __init__(self, facts: FactsGateway | None = None):
        self.facts = facts or get_facts()
        self.inventory = SIMULATED_INVENTORY
        self.aliases = INGREDIENT_ALIASES

    def get_candidates(
        self,
        ingredients: list[IngredientSpec] | list[dict],
    ) -> AgentResult:
        """
        Return candidate products for each ingredient.

        Args:
            ingredients: List of IngredientSpec or dicts with {name, quantity}

        Returns:
            AgentResult with candidates_by_ingredient: dict[str, list[candidate_dict]]
            Each candidate has: product_id, title, brand, size, price,
            unit_price, unit_price_unit, organic, in_stock
        """
        try:
            candidates_by_ingredient: dict[str, list[dict]] = {}
            not_found: list[str] = []
            evidence: list[Evidence] = []

            for ing in ingredients:
                if isinstance(ing, IngredientSpec):
                    name = ing.name
                else:
                    name = ing.get("name", "")

                name_lower = name.lower().strip()
                normalized = self._normalize(name_lower)

                if normalized and normalized in self.inventory:
                    raw_products = self.inventory[normalized]
                    candidates = []

                    for p in raw_products:
                        size_oz = parse_size_oz(p["size"])
                        unit_price = round(p["price"] / size_oz, 4) if size_oz > 0 else p["price"]

                        candidates.append({
                            "product_id": p["id"],
                            "ingredient_name": name_lower,
                            "title": p["title"],
                            "brand": p["brand"],
                            "size": p["size"],
                            "price": p["price"],
                            "unit_price": unit_price,
                            "unit_price_unit": "oz",
                            "organic": p.get("organic", False),
                            "in_stock": True,
                        })

                    # Sort by unit_price ascending (cheapest first)
                    candidates.sort(key=lambda c: c["unit_price"])
                    candidates_by_ingredient[name_lower] = candidates

                    evidence.append(Evidence(
                        source="Product Inventory",
                        key=name_lower,
                        value=f"{len(candidates)} candidates",
                    ))
                else:
                    not_found.append(name_lower)

            matched = len(candidates_by_ingredient)
            total = len(ingredients)
            explain = []

            if matched == total:
                explain.append(f"Found candidates for all {matched} ingredients")
            else:
                explain.append(f"Found candidates for {matched}/{total} ingredients")
            if not_found:
                explain.append(f"No inventory match: {', '.join(not_found[:3])}")

            return make_result(
                agent_name=self.AGENT_NAME,
                facts={
                    "candidates_by_ingredient": candidates_by_ingredient,
                    "not_found": not_found,
                    "matched_count": matched,
                    "total_count": total,
                },
                explain=explain,
                evidence=evidence,
            )

        except Exception as e:
            return make_error(self.AGENT_NAME, str(e))

    def _normalize(self, name: str) -> str | None:
        """Normalize ingredient name to inventory key."""
        if name in self.inventory:
            return name
        if name in self.aliases:
            return self.aliases[name]
        for key in self.inventory:
            if key in name:
                return key
        for alias, canonical in self.aliases.items():
            if alias in name:
                return canonical
        return None

    def search(self, query: str) -> AgentResult:
        """Search inventory by keyword."""
        try:
            results = []
            q = query.lower()
            for category, products in self.inventory.items():
                for p in products:
                    if q in p["title"].lower() or q in p["brand"].lower() or q in category:
                        size_oz = parse_size_oz(p["size"])
                        results.append({
                            "category": category,
                            "product_id": p["id"],
                            "title": p["title"],
                            "brand": p["brand"],
                            "price": p["price"],
                            "unit_price": round(p["price"] / size_oz, 4) if size_oz > 0 else p["price"],
                        })
            return make_result(
                agent_name=self.AGENT_NAME,
                facts={"results": results, "count": len(results), "query": query},
                explain=[f"Found {len(results)} products matching '{query}'"],
                evidence=[],
            )
        except Exception as e:
            return make_error(self.AGENT_NAME, str(e))


def get_product_agent() -> ProductAgent:
    """Get default product agent instance."""
    return ProductAgent()
