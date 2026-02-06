"""
EWG Dirty Dozen / Clean Fifteen categorization for produce.

Based on EWG's Shopper's Guide to Pesticides in Produce.
These lists determine how strongly organic is recommended for each ingredient.
"""

# EWG Dirty Dozen - highest pesticide residues, organic strongly recommended
DIRTY_DOZEN = {
    "strawberries",
    "strawberry",
    "spinach",
    "kale",
    "collard greens",
    "collards",
    "nectarines",
    "nectarine",
    "apples",
    "apple",
    "grapes",
    "grape",
    "peaches",
    "peach",
    "cherries",
    "cherry",
    "pears",
    "pear",
    "tomatoes",
    "tomato",
    "celery",
    "bell peppers",
    "bell pepper",
    "peppers",
    "pepper",
    "hot peppers",
    "hot pepper",
    "blueberries",
    "blueberry",
    "green beans",
}

# EWG Clean Fifteen - lowest pesticide residues, organic optional
CLEAN_FIFTEEN = {
    "avocados",
    "avocado",
    "sweet corn",
    "corn",
    "pineapple",
    "onions",
    "onion",
    "papaya",
    "sweet peas",
    "peas",
    "eggplant",
    "asparagus",
    "broccoli",
    "cabbage",
    "kiwi",
    "cauliflower",
    "mushrooms",
    "mushroom",
    "honeydew melon",
    "honeydew",
    "cantaloupe",
    "mango",
}

# Middle category - wash/peel recommended
MIDDLE_CATEGORY = {
    "cucumbers",
    "cucumber",
    "zucchini",
    "squash",
    "carrots",
    "carrot",
    "potatoes",
    "potato",
    "sweet potatoes",
    "sweet potato",
    "lettuce",
    "arugula",
}


def get_ewg_category(ingredient_name: str) -> str:
    """
    Determine EWG category for an ingredient.

    Returns:
        "dirty_dozen": Organic strongly recommended
        "clean_fifteen": Organic optional
        "middle": Wash/peel recommended
        "non_produce": Not produce (organic minor benefit)
    """
    name_lower = ingredient_name.lower().strip()

    # Check each category
    if any(name_lower.startswith(item) or item in name_lower for item in DIRTY_DOZEN):
        return "dirty_dozen"

    if any(name_lower.startswith(item) or item in name_lower for item in CLEAN_FIFTEEN):
        return "clean_fifteen"

    if any(name_lower.startswith(item) or item in name_lower for item in MIDDLE_CATEGORY):
        return "middle"

    return "non_produce"
