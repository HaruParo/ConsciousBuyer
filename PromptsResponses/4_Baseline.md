Create src/data_processing/baseline.py that computes statistics per category.

For each category:

SELECT 
  category_name,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median_price,
  MIN(price) as min_price,
  MAX(price) as max_price,
  STDDEV(price) as price_volatility,
  MODE() WITHIN GROUP (ORDER BY brand_name) as usual_brand,
  MODE() WITHIN GROUP (ORDER BY packaging_type) as common_packaging,
  COUNT(*) as purchase_count,
  AVG(quantity) as avg_quantity
FROM purchases p
JOIN items i ON p.item_id = i.item_id
JOIN item_categories ic ON i.item_id = ic.item_id
JOIN categories c ON ic.category_id = c.category_id
GROUP BY category_name

Save to data/processed/baseline_stats.json

Structure:
{
  "miso_paste": {
    "median_price": 7.99,
    "price_range": [7.99, 7.99],
    "usual_brand": "Miso Master Organic",
    "common_packaging": "glass jar",
    "volatility": 0.0,
    "purchase_count": 1,
    "avg_quantity": 1.0
  },
  ...
}

Function: get_baseline(category_name) -> dict

Add summary stats at top (total categories, total spend, date range)

----------------Response----------------


Created: src/data_processing/baseline.py
Output: data/processed/baseline_stats.json

{
  "summary": {
    "total_categories": 39,
    "total_items": 182,
    "total_purchases": 372,
    "total_spend": 2996.60,
    "avg_price": 6.06,
    "date_range": {"start": "2025-01-18", "end": "2026-01-10"}
  },
  "categories": {
    "fermented": {
      "median_price": 10.39,
      "price_range": [7.99, 10.39],
      "usual_brand": "Mama O's",
      "common_packaging": null,
      "volatility": 1.39,
      "purchase_count": 3,
      "avg_quantity": 1.0
    },
    ...
  }
}
Top Categories by Spend
Category	Total Spend	Purchases
produce_onions	$426.64	40
produce_tomatoes	$264.87	18
produce_root_veg	$211.38	39
produce_greens	$203.15	43
fruit_tropical	$194.82	33
Functions
get_baseline(category_name) → dict with category stats
calculate_baseline() → full baseline with summary + all categories
get_category_breakdown() → spending breakdown by category
get_top_categories(n, by) → top N by spend or count
get_price_comparison(category, price) → compare price to baseline
Usage

# Generate full baseline
python -m src.data_processing.baseline

# Get specific category
python -m src.data_processing.baseline --category milk

# Top 5 categories
python -m src.data_processing.baseline --top 5
