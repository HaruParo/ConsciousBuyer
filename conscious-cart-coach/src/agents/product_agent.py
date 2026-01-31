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
# Each ingredient has 5-6 products spanning a realistic price/quality range:
#   1. Store brand value (cheapest, large pack, non-organic)
#   2. Store brand standard (mid-cheap, normal size, non-organic)
#   3. Mid-tier national brand (conventional but reputable)
#   4. Premium national brand (higher quality, may be organic)
#   5. Premium organic/ethical (highest price, organic/local/fair-trade)
#   6. (optional) Specialty/artisan option
# No tier labels - DecisionEngine assigns tiers.
#
# Store types:
#   - "primary": FreshDirect, Whole Foods, ShopRite (fresh items, common groceries)
#   - "specialty": Pure Indian Foods, Patel Brothers (ethnic spices, specialty items)
#   - "both": Available at both store types
SIMULATED_INVENTORY: dict[str, list[dict]] = {
    "spinach": [
        {"id": "sp001", "title": "Spinach Bunch Value", "brand": "ShopRite", "size": "10oz", "price": 1.99, "organic": False, "store_type": "primary"},
        {"id": "sp002", "title": "Baby Spinach", "brand": "ShopRite", "size": "5oz", "price": 2.99, "organic": False, "store_type": "primary"},
        {"id": "sp003", "title": "Baby Spinach", "brand": "Fresh Express", "size": "5oz", "price": 3.99, "organic": False, "store_type": "primary"},
        {"id": "sp004", "title": "Organic Baby Spinach", "brand": "Fresh Express", "size": "5oz", "price": 4.99, "organic": True, "store_type": "primary"},
        {"id": "sp005", "title": "Organic Baby Spinach", "brand": "Earthbound Farm", "size": "5oz", "price": 5.99, "organic": True, "store_type": "primary"},
        {"id": "sp006", "title": "Local Organic Spinach", "brand": "Lancaster Farm", "size": "6oz", "price": 6.49, "organic": True, "store_type": "primary"},
    ],
    "kale": [
        {"id": "ka001", "title": "Curly Kale Bunch", "brand": "ShopRite", "size": "8oz", "price": 1.99, "organic": False, "store_type": "primary"},
        {"id": "ka002", "title": "Curly Kale", "brand": "ShopRite", "size": "6oz", "price": 2.49, "organic": False, "store_type": "primary"},
        {"id": "ka003", "title": "Lacinato Kale", "brand": "Fresh Express", "size": "6oz", "price": 3.49, "organic": False, "store_type": "primary"},
        {"id": "ka004", "title": "Organic Curly Kale", "brand": "Earthbound Farm", "size": "6oz", "price": 4.49, "organic": True, "store_type": "primary"},
        {"id": "ka005", "title": "Organic Lacinato Kale", "brand": "Lancaster Farm", "size": "6oz", "price": 4.99, "organic": True, "store_type": "primary"},
    ],
    "lettuce": [
        {"id": "le001", "title": "Iceberg Lettuce Head", "brand": "ShopRite", "size": "24oz", "price": 1.79, "organic": False},
        {"id": "le002", "title": "Romaine Hearts", "brand": "ShopRite", "size": "18oz", "price": 2.99, "organic": False},
        {"id": "le003", "title": "Romaine Hearts", "brand": "Fresh Express", "size": "18oz", "price": 3.49, "organic": False},
        {"id": "le004", "title": "Organic Romaine Hearts", "brand": "Fresh Express", "size": "18oz", "price": 4.49, "organic": True},
        {"id": "le005", "title": "Organic Romaine Hearts", "brand": "Earthbound Farm", "size": "18oz", "price": 5.49, "organic": True},
    ],
    "tomatoes": [
        {"id": "to001", "title": "Roma Tomatoes Value", "brand": "ShopRite", "size": "32oz", "price": 2.99, "organic": False},
        {"id": "to002", "title": "Roma Tomatoes", "brand": "ShopRite", "size": "16oz", "price": 2.49, "organic": False},
        {"id": "to003", "title": "Tomatoes on Vine", "brand": "Sunset", "size": "16oz", "price": 3.49, "organic": False},
        {"id": "to004", "title": "Organic Tomatoes on Vine", "brand": "Sunset", "size": "16oz", "price": 4.99, "organic": True},
        {"id": "to005", "title": "Organic Heirloom Tomatoes", "brand": "Lancaster Farm", "size": "16oz", "price": 6.99, "organic": True},
    ],
    "cherry_tomatoes": [
        {"id": "ct001", "title": "Cherry Tomatoes", "brand": "ShopRite", "size": "16oz", "price": 2.99, "organic": False},
        {"id": "ct002", "title": "Grape Tomatoes", "brand": "ShopRite", "size": "10oz", "price": 2.99, "organic": False},
        {"id": "ct003", "title": "Cherry Tomatoes", "brand": "NatureSweet", "size": "10oz", "price": 3.99, "organic": False},
        {"id": "ct004", "title": "Organic Cherry Tomatoes", "brand": "NatureSweet", "size": "10oz", "price": 5.49, "organic": True},
        {"id": "ct005", "title": "Organic Medley Tomatoes", "brand": "Lancaster Farm", "size": "12oz", "price": 5.99, "organic": True},
    ],
    "strawberries": [
        {"id": "st001", "title": "Strawberries", "brand": "ShopRite", "size": "16oz", "price": 3.49, "organic": False},
        {"id": "st002", "title": "Strawberries", "brand": "Driscoll's", "size": "16oz", "price": 4.99, "organic": False},
        {"id": "st003", "title": "Organic Strawberries", "brand": "ShopRite", "size": "16oz", "price": 5.99, "organic": True},
        {"id": "st004", "title": "Organic Strawberries", "brand": "Driscoll's", "size": "16oz", "price": 7.49, "organic": True},
        {"id": "st005", "title": "Local Organic Strawberries", "brand": "Lancaster Farm", "size": "12oz", "price": 7.99, "organic": True},
    ],
    "blueberries": [
        {"id": "bl001", "title": "Blueberries", "brand": "ShopRite", "size": "18oz", "price": 3.99, "organic": False},
        {"id": "bl002", "title": "Blueberries", "brand": "Driscoll's", "size": "6oz", "price": 3.99, "organic": False},
        {"id": "bl003", "title": "Organic Blueberries", "brand": "ShopRite", "size": "6oz", "price": 4.99, "organic": True},
        {"id": "bl004", "title": "Organic Blueberries", "brand": "Driscoll's", "size": "6oz", "price": 6.49, "organic": True},
        {"id": "bl005", "title": "Wild Organic Blueberries", "brand": "Wyman's", "size": "6oz", "price": 6.99, "organic": True},
    ],
    "onion": [
        {"id": "on001", "title": "Yellow Onions Bag", "brand": "ShopRite", "size": "48oz", "price": 1.99, "organic": False},
        {"id": "on002", "title": "Yellow Onions", "brand": "ShopRite", "size": "32oz", "price": 1.99, "organic": False},
        {"id": "on003", "title": "Yellow Onions", "brand": "Vidalia", "size": "32oz", "price": 2.99, "organic": False},
        {"id": "on004", "title": "Organic Yellow Onions", "brand": "ShopRite", "size": "32oz", "price": 3.49, "organic": True},
        {"id": "on005", "title": "Organic Yellow Onions", "brand": "Lancaster Farm", "size": "32oz", "price": 3.99, "organic": True},
    ],
    "garlic": [
        {"id": "ga001", "title": "Garlic Bulb", "brand": "ShopRite", "size": "2oz", "price": 0.59, "organic": False},
        {"id": "ga002", "title": "Garlic 3-Pack", "brand": "ShopRite", "size": "6oz", "price": 1.49, "organic": False},
        {"id": "ga003", "title": "Garlic", "brand": "Christopher Ranch", "size": "3oz", "price": 1.29, "organic": False},
        {"id": "ga004", "title": "Organic Garlic", "brand": "Christopher Ranch", "size": "2oz", "price": 1.79, "organic": True},
        {"id": "ga005", "title": "Organic Garlic", "brand": "Lancaster Farm", "size": "2oz", "price": 1.99, "organic": True},
    ],
    "ginger": [
        {"id": "gi001", "title": "Ginger Root", "brand": "ShopRite", "size": "4oz", "price": 1.99, "organic": False},
        {"id": "gi002", "title": "Ginger Root", "brand": "ShopRite", "size": "6oz", "price": 2.79, "organic": False},
        {"id": "gi003", "title": "Organic Ginger Root", "brand": "ShopRite", "size": "4oz", "price": 2.99, "organic": True},
        {"id": "gi004", "title": "Organic Ginger Root", "brand": "Wholesome Pantry", "size": "4oz", "price": 3.49, "organic": True},
        {"id": "gi005", "title": "Local Organic Ginger", "brand": "Lancaster Farm", "size": "3oz", "price": 3.99, "organic": True},
    ],
    "chicken": [
        {"id": "ch001", "title": "Chicken Thighs Value Pack", "brand": "ShopRite", "size": "48oz", "price": 6.99, "organic": False},
        {"id": "ch002", "title": "Chicken Thighs", "brand": "ShopRite", "size": "16oz", "price": 4.49, "organic": False},
        {"id": "ch003", "title": "Chicken Thighs", "brand": "Perdue", "size": "20oz", "price": 6.99, "organic": False},
        {"id": "ch004", "title": "Free-Range Chicken Thighs", "brand": "Perdue Harvestland", "size": "16oz", "price": 7.99, "organic": False},
        {"id": "ch005", "title": "Organic Free-Range Thighs", "brand": "Bell & Evans", "size": "16oz", "price": 9.99, "organic": True},
        {"id": "ch006", "title": "Pasture-Raised Thighs", "brand": "Applegate", "size": "16oz", "price": 11.99, "organic": True},
    ],
    "eggs": [
        {"id": "eg001", "title": "Large Eggs 18ct", "brand": "ShopRite", "size": "18ct", "price": 3.99, "organic": False},
        {"id": "eg002", "title": "Large Eggs", "brand": "ShopRite", "size": "dozen", "price": 3.49, "organic": False},
        {"id": "eg003", "title": "Cage-Free Eggs", "brand": "Eggland's Best", "size": "dozen", "price": 4.99, "organic": False},
        {"id": "eg004", "title": "Free-Range Eggs", "brand": "Pete and Gerry's", "size": "dozen", "price": 5.99, "organic": True},
        {"id": "eg005", "title": "Pasture-Raised Eggs", "brand": "Vital Farms", "size": "dozen", "price": 8.99, "organic": True},
    ],
    "salmon": [
        {"id": "sa001", "title": "Atlantic Salmon Fillet", "brand": "ShopRite", "size": "16oz", "price": 7.99, "organic": False},
        {"id": "sa002", "title": "Atlantic Salmon Fillet", "brand": "Verlasso", "size": "12oz", "price": 8.99, "organic": False},
        {"id": "sa003", "title": "Wild-Caught Pink Salmon", "brand": "ShopRite", "size": "16oz", "price": 9.99, "organic": False},
        {"id": "sa004", "title": "Wild-Caught Sockeye Salmon", "brand": "Wild Planet", "size": "12oz", "price": 12.99, "organic": False},
        {"id": "sa005", "title": "Wild-Caught King Salmon", "brand": "Sitka Salmon", "size": "12oz", "price": 16.99, "organic": False},
    ],
    "milk": [
        {"id": "mi001", "title": "Whole Milk", "brand": "ShopRite", "size": "128oz", "price": 3.99, "organic": False},
        {"id": "mi002", "title": "Whole Milk", "brand": "ShopRite", "size": "64oz", "price": 3.49, "organic": False},
        {"id": "mi003", "title": "Whole Milk", "brand": "Horizon", "size": "64oz", "price": 5.49, "organic": True},
        {"id": "mi004", "title": "Organic Whole Milk", "brand": "Organic Valley", "size": "64oz", "price": 6.99, "organic": True},
        {"id": "mi005", "title": "Grass-Fed Organic Milk", "brand": "Maple Hill", "size": "64oz", "price": 7.99, "organic": True},
    ],
    "yogurt": [
        {"id": "yo001", "title": "Greek Yogurt Plain", "brand": "ShopRite", "size": "32oz", "price": 3.49, "organic": False},
        {"id": "yo002", "title": "Greek Yogurt", "brand": "Fage", "size": "32oz", "price": 5.49, "organic": False},
        {"id": "yo003", "title": "Greek Yogurt", "brand": "Chobani", "size": "32oz", "price": 5.29, "organic": False},
        {"id": "yo004", "title": "Organic Greek Yogurt", "brand": "Stonyfield", "size": "32oz", "price": 6.99, "organic": True},
        {"id": "yo005", "title": "Grass-Fed Greek Yogurt", "brand": "Maple Hill", "size": "24oz", "price": 7.49, "organic": True},
    ],
    "ghee": [
        {"id": "gh001", "title": "Clarified Butter", "brand": "ShopRite", "size": "8oz", "price": 5.99, "organic": False},
        {"id": "gh002", "title": "Ghee", "brand": "Deep", "size": "8oz", "price": 6.99, "organic": False},
        {"id": "gh003", "title": "Ghee", "brand": "Organic Valley", "size": "7.5oz", "price": 9.49, "organic": True},
        {"id": "gh004", "title": "Grass-Fed Ghee", "brand": "4th & Heart", "size": "9oz", "price": 10.99, "organic": True},
        {"id": "gh005", "title": "Organic Grass-Fed Ghee", "brand": "Ancient Organics", "size": "8oz", "price": 14.99, "organic": True},
    ],
    "cumin": [
        {"id": "cu001", "title": "Ground Cumin", "brand": "ShopRite", "size": "2oz", "price": 1.99, "organic": False},
        {"id": "cu002", "title": "Ground Cumin", "brand": "McCormick", "size": "1.5oz", "price": 3.99, "organic": False},
        {"id": "cu003", "title": "Ground Cumin", "brand": "Badia", "size": "2oz", "price": 2.49, "organic": False},
        {"id": "cu004", "title": "Organic Ground Cumin", "brand": "Simply Organic", "size": "2.31oz", "price": 5.49, "organic": True},
        {"id": "cu005", "title": "Organic Ground Cumin", "brand": "Frontier Co-op", "size": "1.87oz", "price": 5.99, "organic": True},
    ],
    "turmeric": [
        {"id": "tu001", "title": "Ground Turmeric", "brand": "ShopRite", "size": "2oz", "price": 1.99, "organic": False},
        {"id": "tu002", "title": "Ground Turmeric", "brand": "McCormick", "size": "1.37oz", "price": 4.49, "organic": False},
        {"id": "tu003", "title": "Ground Turmeric", "brand": "Badia", "size": "2oz", "price": 2.29, "organic": False},
        {"id": "tu004", "title": "Organic Ground Turmeric", "brand": "Simply Organic", "size": "2.38oz", "price": 5.99, "organic": True},
        {"id": "tu005", "title": "Organic Ground Turmeric", "brand": "Frontier Co-op", "size": "1.92oz", "price": 6.49, "organic": True},
    ],
    "coriander": [
        {"id": "co001", "title": "Ground Coriander", "brand": "ShopRite", "size": "1.75oz", "price": 1.79, "organic": False},
        {"id": "co002", "title": "Ground Coriander", "brand": "McCormick", "size": "1.5oz", "price": 3.99, "organic": False},
        {"id": "co003", "title": "Ground Coriander", "brand": "Badia", "size": "2oz", "price": 2.29, "organic": False},
        {"id": "co004", "title": "Organic Ground Coriander", "brand": "Simply Organic", "size": "2.29oz", "price": 5.49, "organic": True},
        {"id": "co005", "title": "Organic Ground Coriander", "brand": "Frontier Co-op", "size": "1.6oz", "price": 5.99, "organic": True},
    ],
    "rice": [
        {"id": "ri001", "title": "Long Grain Rice", "brand": "ShopRite", "size": "32oz", "price": 2.49, "organic": False},
        {"id": "ri002", "title": "Basmati Rice", "brand": "ShopRite", "size": "32oz", "price": 3.49, "organic": False},
        {"id": "ri003", "title": "Basmati Rice", "brand": "Tilda", "size": "32oz", "price": 5.99, "organic": False},
        {"id": "ri004", "title": "Organic Basmati Rice", "brand": "Lundberg", "size": "32oz", "price": 7.99, "organic": True},
        {"id": "ri005", "title": "Organic Brown Basmati Rice", "brand": "Lundberg", "size": "32oz", "price": 8.99, "organic": True},
    ],
    "bell_pepper": [
        {"id": "bp001", "title": "Green Bell Peppers", "brand": "ShopRite", "size": "16oz", "price": 1.99, "organic": False},
        {"id": "bp002", "title": "Bell Peppers Multi", "brand": "ShopRite", "size": "24oz", "price": 3.49, "organic": False},
        {"id": "bp003", "title": "Red Bell Peppers", "brand": "Sunset", "size": "16oz", "price": 3.99, "organic": False},
        {"id": "bp004", "title": "Organic Bell Peppers", "brand": "Wholesome Pantry", "size": "16oz", "price": 4.99, "organic": True},
        {"id": "bp005", "title": "Organic Bell Peppers", "brand": "Lancaster Farm", "size": "16oz", "price": 5.99, "organic": True},
    ],
    "hot_peppers": [
        {"id": "hp001", "title": "Jalapeno Peppers", "brand": "ShopRite", "size": "4oz", "price": 0.99, "organic": False},
        {"id": "hp002", "title": "Serrano Peppers", "brand": "ShopRite", "size": "4oz", "price": 1.29, "organic": False},
        {"id": "hp003", "title": "Mixed Hot Peppers", "brand": "Sunset", "size": "8oz", "price": 2.99, "organic": False},
        {"id": "hp004", "title": "Organic Jalapeno Peppers", "brand": "Wholesome Pantry", "size": "4oz", "price": 2.49, "organic": True},
        {"id": "hp005", "title": "Organic Serrano Peppers", "brand": "Lancaster Farm", "size": "4oz", "price": 2.99, "organic": True},
    ],
    "cilantro": [
        {"id": "ci001", "title": "Cilantro Bunch", "brand": "ShopRite", "size": "1oz", "price": 0.99, "organic": False},
        {"id": "ci002", "title": "Cilantro", "brand": "ShopRite", "size": "1.5oz", "price": 1.49, "organic": False},
        {"id": "ci003", "title": "Living Cilantro", "brand": "Shenandoah Growers", "size": "2oz", "price": 2.49, "organic": False},
        {"id": "ci004", "title": "Organic Cilantro", "brand": "Wholesome Pantry", "size": "1oz", "price": 2.49, "organic": True},
        {"id": "ci005", "title": "Organic Cilantro", "brand": "Lancaster Farm", "size": "1oz", "price": 2.99, "organic": True},
    ],
    "mint": [
        {"id": "mt001", "title": "Fresh Mint", "brand": "ShopRite", "size": "0.75oz", "price": 1.49, "organic": False},
        {"id": "mt002", "title": "Fresh Mint", "brand": "ShopRite", "size": "1oz", "price": 1.99, "organic": False},
        {"id": "mt003", "title": "Living Mint", "brand": "Shenandoah Growers", "size": "2oz", "price": 2.99, "organic": False},
        {"id": "mt004", "title": "Organic Fresh Mint", "brand": "Wholesome Pantry", "size": "1oz", "price": 2.99, "organic": True},
        {"id": "mt005", "title": "Organic Fresh Mint", "brand": "Lancaster Farm", "size": "1oz", "price": 3.49, "organic": True},
    ],
    "potatoes": [
        {"id": "po001", "title": "Russet Potatoes Bag", "brand": "ShopRite", "size": "80oz", "price": 3.49, "organic": False},
        {"id": "po002", "title": "Russet Potatoes", "brand": "ShopRite", "size": "48oz", "price": 2.99, "organic": False},
        {"id": "po003", "title": "Gold Potatoes", "brand": "Green Giant", "size": "48oz", "price": 3.99, "organic": False},
        {"id": "po004", "title": "Organic Russet Potatoes", "brand": "Wholesome Pantry", "size": "48oz", "price": 4.99, "organic": True},
        {"id": "po005", "title": "Organic Yukon Gold", "brand": "Lancaster Farm", "size": "48oz", "price": 5.99, "organic": True},
    ],
    "broccoli": [
        {"id": "br001", "title": "Broccoli Crowns", "brand": "ShopRite", "size": "16oz", "price": 1.99, "organic": False},
        {"id": "br002", "title": "Broccoli Crowns", "brand": "ShopRite", "size": "12oz", "price": 2.29, "organic": False},
        {"id": "br003", "title": "Broccoli Florets", "brand": "Green Giant", "size": "12oz", "price": 2.99, "organic": False},
        {"id": "br004", "title": "Organic Broccoli Crowns", "brand": "Wholesome Pantry", "size": "12oz", "price": 3.99, "organic": True},
        {"id": "br005", "title": "Organic Broccoli", "brand": "Lancaster Farm", "size": "12oz", "price": 4.49, "organic": True},
    ],
    "butter": [
        {"id": "bu001", "title": "Salted Butter", "brand": "ShopRite", "size": "16oz", "price": 3.99, "organic": False},
        {"id": "bu002", "title": "Unsalted Butter", "brand": "Land O'Lakes", "size": "16oz", "price": 4.99, "organic": False},
        {"id": "bu003", "title": "Butter", "brand": "Kerrygold", "size": "8oz", "price": 4.49, "organic": False},
        {"id": "bu004", "title": "Organic Butter", "brand": "Organic Valley", "size": "16oz", "price": 6.99, "organic": True},
        {"id": "bu005", "title": "Grass-Fed Organic Butter", "brand": "Vital Farms", "size": "8oz", "price": 5.99, "organic": True},
    ],
    "olive_oil": [
        {"id": "oo001", "title": "Extra Virgin Olive Oil", "brand": "ShopRite", "size": "16oz", "price": 4.99, "organic": False},
        {"id": "oo002", "title": "Extra Virgin Olive Oil", "brand": "Bertolli", "size": "16oz", "price": 6.99, "organic": False},
        {"id": "oo003", "title": "Extra Virgin Olive Oil", "brand": "Colavita", "size": "16oz", "price": 7.99, "organic": False},
        {"id": "oo004", "title": "Organic Extra Virgin Olive Oil", "brand": "California Olive Ranch", "size": "16oz", "price": 9.99, "organic": True},
        {"id": "oo005", "title": "Organic EVOO", "brand": "Lucini", "size": "16oz", "price": 12.99, "organic": True},
    ],
    "salt": [
        {"id": "sl001", "title": "Iodized Salt", "brand": "ShopRite", "size": "26oz", "price": 0.99, "organic": False},
        {"id": "sl002", "title": "Sea Salt", "brand": "Morton", "size": "26oz", "price": 2.49, "organic": False},
        {"id": "sl003", "title": "Pink Himalayan Salt", "brand": "McCormick", "size": "13oz", "price": 4.99, "organic": False},
        {"id": "sl004", "title": "Sea Salt Fine", "brand": "Redmond Real Salt", "size": "10oz", "price": 6.99, "organic": False},
        {"id": "sl005", "title": "Fleur de Sel", "brand": "Le Saunier de Camargue", "size": "4.4oz", "price": 7.99, "organic": False},
    ],
    "black_pepper": [
        {"id": "bk001", "title": "Ground Black Pepper", "brand": "ShopRite", "size": "4oz", "price": 2.49, "organic": False},
        {"id": "bk002", "title": "Ground Black Pepper", "brand": "McCormick", "size": "3oz", "price": 4.99, "organic": False},
        {"id": "bk003", "title": "Peppercorn Grinder", "brand": "McCormick", "size": "1oz", "price": 3.99, "organic": False},
        {"id": "bk004", "title": "Organic Ground Pepper", "brand": "Simply Organic", "size": "2.31oz", "price": 5.99, "organic": True},
        {"id": "bk005", "title": "Organic Tellicherry Pepper", "brand": "Frontier Co-op", "size": "1.76oz", "price": 6.49, "organic": True},
    ],
    "lemon": [
        {"id": "lm001", "title": "Lemons", "brand": "ShopRite", "size": "8oz", "price": 0.69, "organic": False},
        {"id": "lm002", "title": "Lemons Bag", "brand": "ShopRite", "size": "32oz", "price": 3.99, "organic": False},
        {"id": "lm003", "title": "Meyer Lemons", "brand": "Sunkist", "size": "16oz", "price": 3.99, "organic": False},
        {"id": "lm004", "title": "Organic Lemons", "brand": "Wholesome Pantry", "size": "8oz", "price": 1.29, "organic": True},
        {"id": "lm005", "title": "Organic Lemons Bag", "brand": "Lancaster Farm", "size": "24oz", "price": 4.99, "organic": True},
    ],
    "avocado": [
        {"id": "av001", "title": "Avocado", "brand": "ShopRite", "size": "6oz", "price": 1.29, "organic": False},
        {"id": "av002", "title": "Avocados Bag", "brand": "ShopRite", "size": "24oz", "price": 4.49, "organic": False},
        {"id": "av003", "title": "Hass Avocado", "brand": "Mission", "size": "6oz", "price": 1.69, "organic": False},
        {"id": "av004", "title": "Organic Avocado", "brand": "Wholesome Pantry", "size": "6oz", "price": 1.99, "organic": True},
        {"id": "av005", "title": "Organic Avocados", "brand": "Mission", "size": "12oz", "price": 4.99, "organic": True},
    ],
    "cucumber": [
        {"id": "cc001", "title": "Cucumber", "brand": "ShopRite", "size": "12oz", "price": 0.99, "organic": False},
        {"id": "cc002", "title": "English Cucumber", "brand": "ShopRite", "size": "14oz", "price": 1.79, "organic": False},
        {"id": "cc003", "title": "Persian Cucumbers", "brand": "Sunset", "size": "16oz", "price": 2.99, "organic": False},
        {"id": "cc004", "title": "Organic Cucumber", "brand": "Wholesome Pantry", "size": "12oz", "price": 1.99, "organic": True},
        {"id": "cc005", "title": "Organic Persian Cucumbers", "brand": "Lancaster Farm", "size": "12oz", "price": 3.49, "organic": True},
    ],
    "carrots": [
        {"id": "cr001", "title": "Carrots Bag", "brand": "ShopRite", "size": "32oz", "price": 1.49, "organic": False},
        {"id": "cr002", "title": "Baby Carrots", "brand": "ShopRite", "size": "16oz", "price": 1.79, "organic": False},
        {"id": "cr003", "title": "Baby Carrots", "brand": "Bolthouse Farms", "size": "16oz", "price": 2.49, "organic": False},
        {"id": "cr004", "title": "Organic Carrots", "brand": "Wholesome Pantry", "size": "32oz", "price": 2.99, "organic": True},
        {"id": "cr005", "title": "Organic Rainbow Carrots", "brand": "Lancaster Farm", "size": "16oz", "price": 3.49, "organic": True},
    ],
    "celery": [
        {"id": "cy001", "title": "Celery Stalk", "brand": "ShopRite", "size": "16oz", "price": 1.49, "organic": False},
        {"id": "cy002", "title": "Celery Hearts", "brand": "ShopRite", "size": "16oz", "price": 2.49, "organic": False},
        {"id": "cy003", "title": "Celery Hearts", "brand": "Dole", "size": "16oz", "price": 2.99, "organic": False},
        {"id": "cy004", "title": "Organic Celery", "brand": "Wholesome Pantry", "size": "16oz", "price": 3.49, "organic": True},
        {"id": "cy005", "title": "Organic Celery Hearts", "brand": "Lancaster Farm", "size": "16oz", "price": 3.99, "organic": True},
    ],
    "mushrooms": [
        {"id": "mu001", "title": "White Mushrooms", "brand": "ShopRite", "size": "8oz", "price": 1.99, "organic": False},
        {"id": "mu002", "title": "Baby Bella Mushrooms", "brand": "ShopRite", "size": "8oz", "price": 2.49, "organic": False},
        {"id": "mu003", "title": "Baby Bella Mushrooms", "brand": "Giorgio", "size": "8oz", "price": 3.29, "organic": False},
        {"id": "mu004", "title": "Organic Baby Bella", "brand": "Wholesome Pantry", "size": "8oz", "price": 3.99, "organic": True},
        {"id": "mu005", "title": "Organic Shiitake Mushrooms", "brand": "Lancaster Farm", "size": "4oz", "price": 4.99, "organic": True},
    ],
    "ground_beef": [
        {"id": "gb001", "title": "Ground Beef 80/20", "brand": "ShopRite", "size": "16oz", "price": 4.99, "organic": False},
        {"id": "gb002", "title": "Ground Beef 85/15", "brand": "ShopRite", "size": "16oz", "price": 5.99, "organic": False},
        {"id": "gb003", "title": "Ground Beef 90/10", "brand": "Certified Angus", "size": "16oz", "price": 7.99, "organic": False},
        {"id": "gb004", "title": "Organic Ground Beef", "brand": "Organic Prairie", "size": "16oz", "price": 9.99, "organic": True},
        {"id": "gb005", "title": "Grass-Fed Ground Beef", "brand": "Applegate", "size": "16oz", "price": 11.99, "organic": True},
    ],
    "pasta": [
        {"id": "pa001", "title": "Spaghetti", "brand": "ShopRite", "size": "16oz", "price": 1.29, "organic": False},
        {"id": "pa002", "title": "Spaghetti", "brand": "Barilla", "size": "16oz", "price": 1.99, "organic": False},
        {"id": "pa003", "title": "Spaghetti", "brand": "De Cecco", "size": "16oz", "price": 3.29, "organic": False},
        {"id": "pa004", "title": "Organic Spaghetti", "brand": "Bionaturae", "size": "16oz", "price": 3.99, "organic": True},
        {"id": "pa005", "title": "Organic Artisan Pasta", "brand": "Jovial", "size": "12oz", "price": 4.99, "organic": True},
    ],
    "canned_tomatoes": [
        {"id": "cnt001", "title": "Crushed Tomatoes", "brand": "ShopRite", "size": "28oz", "price": 1.49, "organic": False},
        {"id": "cnt002", "title": "Crushed Tomatoes", "brand": "Tuttorosso", "size": "28oz", "price": 2.29, "organic": False},
        {"id": "cnt003", "title": "San Marzano Tomatoes", "brand": "Cento", "size": "28oz", "price": 3.99, "organic": False},
        {"id": "cnt004", "title": "Organic Crushed Tomatoes", "brand": "Muir Glen", "size": "28oz", "price": 3.49, "organic": True},
        {"id": "cnt005", "title": "Organic San Marzano", "brand": "Bionaturae", "size": "28oz", "price": 4.99, "organic": True},
    ],
    "coconut_milk": [
        {"id": "cm001", "title": "Coconut Milk", "brand": "ShopRite", "size": "13.5oz", "price": 1.49, "organic": False},
        {"id": "cm002", "title": "Coconut Milk", "brand": "Thai Kitchen", "size": "13.5oz", "price": 2.49, "organic": False},
        {"id": "cm003", "title": "Coconut Milk", "brand": "Aroy-D", "size": "13.5oz", "price": 2.29, "organic": False},
        {"id": "cm004", "title": "Organic Coconut Milk", "brand": "Thai Kitchen", "size": "13.5oz", "price": 3.29, "organic": True},
        {"id": "cm005", "title": "Organic Coconut Milk", "brand": "Native Forest", "size": "13.5oz", "price": 3.99, "organic": True},
    ],
    "tofu": [
        {"id": "tf001", "title": "Extra Firm Tofu", "brand": "ShopRite", "size": "14oz", "price": 1.79, "organic": False},
        {"id": "tf002", "title": "Extra Firm Tofu", "brand": "Nasoya", "size": "14oz", "price": 2.49, "organic": False},
        {"id": "tf003", "title": "Organic Extra Firm Tofu", "brand": "Nasoya", "size": "14oz", "price": 2.99, "organic": True},
        {"id": "tf004", "title": "Organic Tofu", "brand": "Wildwood", "size": "14oz", "price": 3.29, "organic": True},
        {"id": "tf005", "title": "Sprouted Organic Tofu", "brand": "Hodo", "size": "10oz", "price": 4.49, "organic": True},
    ],
    "soy_sauce": [
        {"id": "ss001", "title": "Soy Sauce", "brand": "ShopRite", "size": "10oz", "price": 1.49, "organic": False},
        {"id": "ss002", "title": "Soy Sauce", "brand": "Kikkoman", "size": "10oz", "price": 2.99, "organic": False},
        {"id": "ss003", "title": "Tamari Soy Sauce", "brand": "Kikkoman", "size": "10oz", "price": 3.99, "organic": False},
        {"id": "ss004", "title": "Organic Tamari", "brand": "San-J", "size": "10oz", "price": 4.99, "organic": True},
        {"id": "ss005", "title": "Organic Shoyu", "brand": "Eden", "size": "10oz", "price": 5.49, "organic": True},
    ],
    "garam_masala": [
        {"id": "gm001", "title": "Garam Masala", "brand": "ShopRite", "size": "2oz", "price": 2.49, "organic": False},
        {"id": "gm002", "title": "Garam Masala", "brand": "McCormick", "size": "1.75oz", "price": 4.99, "organic": False},
        {"id": "gm003", "title": "Garam Masala", "brand": "Deep", "size": "3.5oz", "price": 3.99, "organic": False},
        {"id": "gm004", "title": "Organic Garam Masala", "brand": "Simply Organic", "size": "2.01oz", "price": 5.99, "organic": True},
        {"id": "gm005", "title": "Organic Garam Masala", "brand": "Frontier Co-op", "size": "1.9oz", "price": 6.49, "organic": True},
    ],
    "cardamom": [
        {"id": "cd001", "title": "Ground Cardamom", "brand": "ShopRite", "size": "1oz", "price": 4.99, "organic": False},
        {"id": "cd002", "title": "Ground Cardamom", "brand": "McCormick", "size": "0.95oz", "price": 7.99, "organic": False},
        {"id": "cd003", "title": "Cardamom Pods", "brand": "Deep", "size": "1.76oz", "price": 5.99, "organic": False},
        {"id": "cd004", "title": "Organic Cardamom", "brand": "Simply Organic", "size": "0.53oz", "price": 8.99, "organic": True},
        {"id": "cd005", "title": "Organic Cardamom Pods", "brand": "Frontier Co-op", "size": "0.95oz", "price": 9.49, "organic": True},
    ],
    "cinnamon": [
        {"id": "cn001", "title": "Ground Cinnamon", "brand": "ShopRite", "size": "2.37oz", "price": 1.99, "organic": False},
        {"id": "cn002", "title": "Ground Cinnamon", "brand": "McCormick", "size": "2.37oz", "price": 4.49, "organic": False},
        {"id": "cn003", "title": "Cinnamon Sticks", "brand": "McCormick", "size": "1.25oz", "price": 5.99, "organic": False},
        {"id": "cn004", "title": "Organic Ground Cinnamon", "brand": "Simply Organic", "size": "2.45oz", "price": 5.49, "organic": True},
        {"id": "cn005", "title": "Organic Cinnamon Sticks", "brand": "Frontier Co-op", "size": "1.28oz", "price": 6.99, "organic": True},
    ],
    "cloves": [
        {"id": "cl001", "title": "Ground Cloves", "brand": "ShopRite", "size": "1.62oz", "price": 2.99, "organic": False},
        {"id": "cl002", "title": "Ground Cloves", "brand": "McCormick", "size": "0.9oz", "price": 4.99, "organic": False},
        {"id": "cl003", "title": "Whole Cloves", "brand": "McCormick", "size": "0.62oz", "price": 5.49, "organic": False},
        {"id": "cl004", "title": "Organic Ground Cloves", "brand": "Simply Organic", "size": "2.82oz", "price": 6.49, "organic": True},
        {"id": "cl005", "title": "Organic Whole Cloves", "brand": "Frontier Co-op", "size": "1.36oz", "price": 6.99, "organic": True},
    ],
    "bay_leaves": [
        {"id": "bl101", "title": "Bay Leaves", "brand": "ShopRite", "size": "0.12oz", "price": 1.99, "organic": False},
        {"id": "bl102", "title": "Bay Leaves", "brand": "McCormick", "size": "0.12oz", "price": 3.49, "organic": False},
        {"id": "bl103", "title": "Turkish Bay Leaves", "brand": "Badia", "size": "0.25oz", "price": 2.99, "organic": False},
        {"id": "bl104", "title": "Organic Bay Leaves", "brand": "Simply Organic", "size": "0.14oz", "price": 4.49, "organic": True},
        {"id": "bl105", "title": "Organic Bay Leaves", "brand": "Frontier Co-op", "size": "0.14oz", "price": 4.99, "organic": True},
    ],
    "saffron": [
        {"id": "sf001", "title": "Saffron Threads", "brand": "Badia", "size": "0.4g", "price": 12.99, "organic": False},
        {"id": "sf002", "title": "Saffron", "brand": "McCormick", "size": "0.06oz", "price": 16.99, "organic": False},
        {"id": "sf003", "title": "Spanish Saffron", "brand": "La Mancha", "size": "1g", "price": 14.99, "organic": False},
        {"id": "sf004", "title": "Organic Saffron", "brand": "Frontier Co-op", "size": "0.036oz", "price": 18.99, "organic": True},
        {"id": "sf005", "title": "Persian Saffron", "brand": "Zaran", "size": "1g", "price": 19.99, "organic": False},
    ],
}

# Aliases for ingredient normalization
INGREDIENT_ALIASES: dict[str, str] = {
    "baby spinach": "spinach", "fresh spinach": "spinach",
    "lacinato kale": "kale", "dinosaur kale": "kale", "tuscan kale": "kale",
    "romaine": "lettuce", "romaine lettuce": "lettuce", "iceberg": "lettuce",
    "roma tomatoes": "tomatoes", "plum tomatoes": "tomatoes", "tomato": "tomatoes",
    "grape tomatoes": "cherry_tomatoes",
    "yellow onion": "onion", "white onion": "onion", "red onion": "onion", "onions": "onion",
    "fresh ginger": "ginger", "ginger root": "ginger",
    "chicken thighs": "chicken", "chicken breast": "chicken",
    "chicken drumsticks": "chicken", "whole chicken": "chicken", "chicken thigh": "chicken",
    "basmati rice": "rice", "jasmine rice": "rice", "long grain rice": "rice", "brown rice": "rice",
    "fresh cilantro": "cilantro", "coriander leaves": "cilantro",
    "fresh mint": "mint", "mint leaves": "mint",
    "green bell pepper": "bell_pepper", "red bell pepper": "bell_pepper",
    "bell peppers": "bell_pepper", "green pepper": "bell_pepper",
    "serrano": "hot_peppers", "jalapeno": "hot_peppers", "green chili": "hot_peppers",
    "green chilies": "hot_peppers", "chili pepper": "hot_peppers",
    "potato": "potatoes", "russet potatoes": "potatoes", "yukon gold": "potatoes",
    "unsalted butter": "butter", "salted butter": "butter",
    "olive oil": "olive_oil", "extra virgin olive oil": "olive_oil", "evoo": "olive_oil",
    "kosher salt": "salt", "sea salt": "salt", "table salt": "salt",
    "pepper": "black_pepper", "ground pepper": "black_pepper", "peppercorn": "black_pepper",
    "lemons": "lemon", "lemon juice": "lemon", "meyer lemon": "lemon",
    "avocados": "avocado", "hass avocado": "avocado",
    "cucumbers": "cucumber", "english cucumber": "cucumber", "persian cucumber": "cucumber",
    "carrot": "carrots", "baby carrots": "carrots",
    "celery stalks": "celery", "celery hearts": "celery",
    "mushroom": "mushrooms", "baby bella": "mushrooms", "shiitake": "mushrooms",
    "white mushrooms": "mushrooms", "cremini": "mushrooms",
    "ground beef": "ground_beef", "beef": "ground_beef", "minced beef": "ground_beef",
    "spaghetti": "pasta", "penne": "pasta", "noodles": "pasta",
    "crushed tomatoes": "canned_tomatoes", "diced tomatoes": "canned_tomatoes",
    "san marzano": "canned_tomatoes", "tomato sauce": "canned_tomatoes",
    "coconut milk": "coconut_milk", "coconut cream": "coconut_milk",
    "firm tofu": "tofu", "extra firm tofu": "tofu", "silken tofu": "tofu",
    "biryani masala": "garam_masala", "garam masala": "garam_masala",
    "cardamom pods": "cardamom", "green cardamom": "cardamom",
    "cinnamon stick": "cinnamon", "cinnamon sticks": "cinnamon", "ground cinnamon": "cinnamon",
    "whole cloves": "cloves", "ground cloves": "cloves", "clove": "cloves",
    "bay leaf": "bay_leaves",
    "soy sauce": "soy_sauce", "tamari": "soy_sauce", "shoyu": "soy_sauce",
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
