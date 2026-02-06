# Using Product Metadata in Decision Summaries

## Overview

The product database now includes rich metadata to support better decision-making and explanations:

1. **Packaging** - Environmental impact and convenience
2. **Nutrition** - Health impact (calories, protein, carbs, fat, fiber)
3. **Labels** - Additional certifications beyond organic

## Data Structure

### source_listings.csv Columns

```csv
category,product_name,brand,price,unit,size,certifications,packaging,nutrition,labels,notes,item_type,seasonality,selected_tier,selection_reason
```

### Example: Grass-Fed Milk

```csv
milk_whole,Grassmilk Whole Milk Ultra-Pasteurized Carton,Organic Valley,$7.39,ea,59fl oz,USDA Organic + Grass-fed,Gable-top carton (paper/plastic laminate),,Grass-Fed,$0.13/fl oz - grass-fed premium,staple,year-round,conscious,Grass-fed organic - highest welfare + nutrition standards
```

### Example: Baby Spinach

```csv
produce_greens,Organic Baby Spinach,Earthbound Farm,$6.99,ea,10oz,USDA Organic,Clear plastic clamshell (recyclable #1 PET),,"Naturally Gluten-Free, Vegan",,staple,,,
```

## Using Metadata in Decision Summaries

### 1. Packaging in Explanations

**Scoring Component**: Packaging affects the packaging_score (line ~800 in component_scoring.py)

**Decision Summary Usage**:
```python
# Example decision text
if product.packaging == "Glass jar":
    reason += " Glass jar packaging reduces plastic waste."
elif "plastic clamshell" in product.packaging.lower():
    reason += " Recyclable plastic clamshell (#1 PET)."
elif "loose bulk" in product.packaging.lower():
    reason += " Minimal packaging (loose bulk)."
```

**Example Output**:
> "Selected Organic Baby Spinach ($6.99) - USDA Organic, recyclable plastic clamshell (#1 PET), naturally gluten-free and vegan."

### 2. Labels in Explanations

**Common Labels**:
- Non-GMO Project Verified
- Fair Trade Certified
- Cage-Free
- Pasture-Raised
- Grass-Fed
- Free-Range
- Gluten-Free
- Vegan
- Kosher
- Halal
- B Corp Certified
- Rainforest Alliance
- Regenerative Agriculture

**Decision Summary Usage**:
```python
labels = product.labels.split(", ")

# Highlight important labels
welfare_labels = [l for l in labels if l in ["Cage-Free", "Pasture-Raised", "Grass-Fed", "Free-Range"]]
ethical_labels = [l for l in labels if l in ["Fair Trade Certified", "B Corp Certified", "Rainforest Alliance"]]
dietary_labels = [l for l in labels if l in ["Gluten-Free", "Vegan", "Kosher", "Halal"]]

if welfare_labels:
    reason += f" Animal welfare: {', '.join(welfare_labels)}."
if ethical_labels:
    reason += f" Ethical sourcing: {', '.join(ethical_labels)}."
```

**Example Output**:
> "Selected Grassmilk Whole Milk ($7.39) - USDA Organic, grass-fed (higher omega-3s), gable-top carton (paper/plastic recyclable)."

### 3. Nutrition in Explanations

**Nutrition Format**: `"Calories: 50/100g, Protein: 3g, Carbs: 10g, Fat: 1g, Fiber: 2g"`

**Decision Summary Usage**:
```python
if product.nutrition:
    # Parse nutrition string
    nutrients = dict(n.split(": ") for n in product.nutrition.split(", "))

    # Highlight key nutrients
    if "Protein" in nutrients:
        protein_val = float(nutrients["Protein"].replace("g", ""))
        if protein_val >= 10:
            reason += f" High protein ({protein_val}g/100g)."

    if "Fiber" in nutrients:
        fiber_val = float(nutrients["Fiber"].replace("g", ""))
        if fiber_val >= 5:
            reason += f" Good fiber source ({fiber_val}g/100g)."
```

## Integration Points

### A. Product Agent (src/agents/product_agent.py)

When loading products, the new fields are automatically available:

```python
class Product:
    category: str
    title: str
    brand: str
    price: float
    certifications: str
    packaging: str          # NEW
    nutrition: str          # NEW
    labels: str             # NEW
    # ... other fields
```

### B. Component Scoring (src/scoring/component_scoring.py)

Packaging already affects scoring. We can enhance this:

```python
def calculate_packaging_score(product: Product, context: dict) -> dict:
    """
    Calculate packaging score based on environmental impact.

    Current scoring:
    - Loose/bulk/glass: +6 points
    - Paper/carton: +4 points
    - Recyclable plastic: +2 points
    - Non-recyclable/styrofoam: -4 points
    """
    # Can now use product.packaging directly
    packaging_lower = product.packaging.lower()

    if "glass" in packaging_lower or "loose" in packaging_lower:
        return {"score": 6, "reason": "Minimal/reusable packaging"}
    # ... etc
```

### C. Decision Traces (src/contracts/cart_plan.py)

Enhanced CartItem with metadata:

```python
class CartItem:
    ingredient: str
    product_title: str
    price: float
    certifications: str
    packaging: str          # Include in response
    labels: str             # Include in response
    nutrition: str          # Include in response
    reason: str             # Enhanced with metadata
    # ... other fields
```

## Example Enhanced Decision Summary

### Before (old system):
> "Organic Baby Spinach - $6.99 - Selected for organic certification (Dirty Dozen #2). Score: 78/100."

### After (with metadata):
> "Organic Baby Spinach - $6.99
> - **Certification**: USDA Organic (required for Dirty Dozen #2)
> - **Packaging**: Recyclable plastic clamshell (#1 PET)
> - **Dietary**: Naturally gluten-free, vegan
> - **Score**: 78/100 (EWG +18, Form +14, Packaging +2, Unit Value +4)"

### Example: Grass-Fed Milk

> "Grassmilk Whole Milk - $7.39
> - **Certifications**: USDA Organic, Grass-Fed
> - **Packaging**: Gable-top carton (paper/plastic laminate, recyclable)
> - **Animal Welfare**: Grass-fed (pasture access, higher omega-3s)
> - **Score**: 82/100 (EWG +2, Packaging +4, Unit Value +6)"

### Example: Pasture-Raised Eggs (hypothetical)

> "Vital Farms Pasture-Raised Eggs - $8.99
> - **Certifications**: Certified Humane, B Corp
> - **Packaging**: Recyclable paperboard carton
> - **Animal Welfare**: Pasture-raised (108 sq ft per bird vs 1 sq ft cage-free)
> - **Labels**: B Corp Certified, Non-GMO Project Verified
> - **Score**: 86/100 (EWG +2, Packaging +6, Animal Welfare bonus +8)"

## Frontend Display

### Recommended UI Enhancement

```typescript
interface CartItem {
  ingredient: string
  productTitle: string
  price: number
  certifications: string
  packaging: string        // NEW
  nutrition: string        // NEW
  labels: string[]         // NEW (parse comma-separated)
  reason: string
  scoreBreakdown: ScoreBreakdown
}

// Display in cart item card
<CartItemCard>
  <ProductName>{item.productTitle}</ProductName>
  <Price>${item.price}</Price>

  <MetadataSection>
    {item.labels.length > 0 && (
      <LabelBadges>
        {item.labels.map(label => (
          <Badge key={label} variant={getLabelVariant(label)}>
            {label}
          </Badge>
        ))}
      </LabelBadges>
    )}

    <PackagingInfo>
      <Icon name="package" />
      {item.packaging}
    </PackagingInfo>

    {item.nutrition && (
      <NutritionSummary>
        {parseNutrition(item.nutrition)}
      </NutritionSummary>
    )}
  </MetadataSection>

  <ScoreBreakdown>{item.reason}</ScoreBreakdown>
</CartItemCard>
```

### Badge Color Coding

```typescript
function getLabelVariant(label: string): BadgeVariant {
  // Animal welfare - green
  if (["Pasture-Raised", "Grass-Fed", "Cage-Free", "Free-Range"].includes(label)) {
    return "success"
  }

  // Ethical sourcing - blue
  if (["Fair Trade Certified", "B Corp Certified", "Rainforest Alliance"].includes(label)) {
    return "info"
  }

  // Dietary - purple
  if (["Gluten-Free", "Vegan", "Kosher", "Halal"].includes(label)) {
    return "secondary"
  }

  // Environmental - amber
  if (["Regenerative Agriculture", "Non-GMO Project Verified"].includes(label)) {
    return "warning"
  }

  return "default"
}
```

## Data Enrichment Pipeline

### Current Status

✅ **Completed**:
1. Added `packaging` column (736 products)
2. Added `nutrition` column (placeholder for API data)
3. Added `labels` column (168 products with inferred labels)

### Next Steps

1. **Fetch from Open Food Facts API**:
   ```bash
   python scripts/add_nutrition_and_labels.py --api
   ```
   - Fetches nutrition data for branded products
   - Enriches labels with crowdsourced certifications
   - Rate-limited (1 req/sec) - takes ~12 minutes for 736 products
   - Results cached in `openfoodfacts_cache.json`

2. **Manual Label Additions**:
   - Add cage-free/pasture-raised labels to chicken/eggs in source_listings.csv
   - Add B Corp, Fair Trade to specific brands
   - Add regenerative agriculture labels

3. **Update Product Agent**:
   - Modify `src/agents/product_agent.py` to load new columns
   - Include packaging/labels in Product dataclass

4. **Update Component Scoring**:
   - Enhance packaging score with specific material types
   - Add label bonuses (e.g., +5 for pasture-raised, +3 for B Corp)

5. **Update Decision Reasoning**:
   - Modify `src/planner/engine.py` to include labels in reason text
   - Add packaging impact to decision trace

6. **Frontend Integration**:
   - Update TypeScript types to include new fields
   - Add label badges to CartItemCard
   - Display packaging info with icons

## Testing

### Verify Data

```bash
# Check packaging distribution
cut -d',' -f8 data/alternatives/source_listings.csv | sort | uniq -c | sort -rn

# Check labels distribution
cut -d',' -f10 data/alternatives/source_listings.csv | grep -v "^$" | head -20

# Find products with multiple labels
awk -F',' 'NF > 0 && $10 != "" {print $2","$10}' data/alternatives/source_listings.csv | grep "," | head -10
```

### Test API Fetch

```bash
# Fetch nutrition for a specific product (dry run)
python -c "
from scripts.add_nutrition_and_labels import search_openfoodfacts
result = search_openfoodfacts('Organic Baby Spinach', 'Earthbound Farm', {})
print(result)
"
```

## Summary

The enhanced product metadata enables:

1. **Richer Decision Explanations** - Why was this specific product chosen?
2. **Better User Understanding** - What labels/certifications does it have?
3. **Environmental Transparency** - What packaging does it use?
4. **Nutritional Awareness** - What are the nutritional benefits?
5. **Ethical Context** - What ethical/welfare standards does it meet?

This transforms product selection from a simple "organic = good" heuristic to a nuanced, multi-dimensional decision that users can understand and trust.
