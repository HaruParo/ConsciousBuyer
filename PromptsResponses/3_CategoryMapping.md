Prompt 1.2: Create Category Mapping
Create src/data_processing/categorize.py that analyzes items table and groups into categories.

Categories to create (15-20):
- miso_paste
- milk (all dairy milk)
- chicken
- eggs
- bread
- nuts_almonds
- nuts_cashews
- produce_onions
- produce_tomatoes
- produce_cucumbers
- produce_greens
- produce_root_veg
- oils
- vinegar
- spices
- etc.

Logic:
1. Use fuzzy matching on item name
2. Group by brand families where obvious
3. Manual overrides for edge cases

Output:
- Insert into categories and item_categories tables
- Generate data/processed/category_mapping.json for reference

Function: assign_category(item_id) -> category_name

Include pytest tests with example items



----------------Response----------------

Created: src/data_processing/categorize.py
39 Categories Created
Category	Items	Category	Items
produce_root_veg	23	produce_greens	21
produce_squash	13	fruit_tropical	13
produce_onions	11	fruit_berries	8
produce_beans	8	fruit_citrus	6
produce_cucumbers	5	milk	5
ice_cream	5	bread	5
spices	5	fruit_other	5
chicken	4	chocolate	3
vinegar	3	oils_olive	3
produce_tomatoes	3	fermented	3
yogurt	3	cheese	3
... and more			
Features
Pattern-based matching with regex for 30+ category definitions
Brand-based hints for 20+ brands (Driscoll's → berries, Vital Farms → eggs, etc.)
Manual overrides for edge cases (10 items)
Priority system to resolve conflicts
Output Files
data/processed/category_mapping.json - Full mapping reference
Database tables: categories (39 rows), item_categories (183 mappings)
Tests
tests/test_categorize.py - 50 tests passing
Usage

# Run categorization
python -m src.data_processing.categorize --clear

# View summary only
python -m src.data_processing.categorize --summary

# Programmatic usage
from src.data_processing.categorize import assign_category, get_items_by_category
category = assign_category(item_id=107)  # Returns "milk"
items = get_items_by_category("fruit_berries")