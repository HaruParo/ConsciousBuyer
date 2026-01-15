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
