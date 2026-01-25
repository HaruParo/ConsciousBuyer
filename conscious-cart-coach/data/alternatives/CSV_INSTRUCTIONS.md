# CSV Template Instructions

## File: `alternatives_template.csv`

Fill in the CSV with alternative product recommendations for each category.

## Column Definitions

| Column | Description | Example |
|--------|-------------|---------|
| `category` | Product category (pre-filled, don't modify) | `milk` |
| `tier` | Price/sustainability tier (pre-filled) | `cheaper`, `balanced`, `conscious` |
| `brand` | Brand or product name | `Organic Valley` |
| `est_price` | Estimated price in USD | `6.99` |
| `packaging` | Packaging type | `glass bottle`, `plastic jug`, `carton` |
| `why_this_tier` | Reason for tier placement | `Local farm, pasture-raised, glass returnable` |
| `certifications` | Certifications (comma-separated) | `USDA Organic, Non-GMO Project, B-Corp` |
| `trade_offs` | Downsides or compromises (for cheaper tier) | `Not organic, plastic packaging` |
| `source_url` | Link to product or brand website | `https://example.com/product` |

## Tier Guidelines

### Cheaper
- Budget-friendly options
- Fill: `brand`, `est_price`, `packaging`, `why_this_tier`, `trade_offs`
- Leave `certifications` empty or minimal

### Balanced
- Mid-range with some sustainability
- Fill: `brand`, `est_price`, `packaging`, `why_this_tier`, `certifications`
- `trade_offs` optional

### Conscious
- Premium sustainable choice
- Fill ALL columns
- List all certifications
- `trade_offs` = higher price (implicit)

## Example Entry

```csv
category,tier,brand,est_price,packaging,why_this_tier,certifications,trade_offs,source_url
milk,cheaper,Store Brand Organic,4.99,plastic jug,Affordable organic option,USDA Organic,Plastic packaging,https://freshdirect.com
milk,balanced,Ronnybrook Farm,8.99,glass bottle,Local NY farm with returnable bottles,Non-GMO,Higher price than conventional,https://ronnybrook.com
milk,conscious,Alexandre Family Farm,12.99,glass bottle,Regenerative A2/A2 pasture-raised,"USDA Organic, Regenerative Organic Certified, A2",Premium price,https://alexandrefamilyfarm.com
```

## Tips

1. **Use quotes** for fields containing commas: `"USDA Organic, Fair Trade"`
2. **Prices** should be numeric only: `7.99` not `$7.99`
3. **URLs** should be full links starting with `https://`
4. **Leave empty** any field you don't have data for (don't put "N/A")

## Opening in Excel/Google Sheets

- Excel: File > Open > Select CSV
- Google Sheets: File > Import > Upload > Select CSV
- Numbers: File > Open > Select CSV

Save back as CSV (not .xlsx) when done.
