Prompt 1.1: Ingest Receipts to Postgres
I have a receipts CSV with columns:
price_id, item_id, ts, price, qty, size, source_file, raw_product_line, brand_name, attributes

Location for csv file: /Users/hash/Documents/ConsciousBuyer/conscious-cart-coach/data/raw/Golden_dataset.csv

Create src/data_processing/ingest.py that:

1. Connects to Postgres (use DATABASE_URL from .env)
2. Creates tables:
   - purchases (price_id PK, item_id, timestamp, price, quantity)
   - items (item_id PK, name, brand, size, packaging_type)
   - categories (category_id PK, category_name)
   - item_categories (item_id, category_id)

3. Parses CSV and inserts into tables:
   - Extract packaging type from 'size' column (e.g., "plastic clamshell", "glass jar")
   - Normalize brand names
   - Handle missing data gracefully

4. Add function: get_purchase_history() -> DataFrame

Include:
- Error handling
- Logging
- Data validation

Run with: python -m src.data_processing.ingest data/raw/receipts.csv
