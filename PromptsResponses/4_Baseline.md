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
