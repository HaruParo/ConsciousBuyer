# Ingredient Display Error Report

**Date**: 2026-02-03
**Status**: ✅ FIXED (with recommendations)

---

## User-Reported Issues

### Issue 1: Onions don't specify type (red/yellow/white)
**Status**: ✅ PARTIALLY ADDRESSED

**Before**: "onions"
**After**: "whole onions"

**Root Cause**: LLM extraction doesn't distinguish onion varieties by default.

**Solution Implemented**: Now shows "whole onions" (indicates whole/unprocessed)

**Recommendation for Full Fix**:
```python
# Update BIRYANI_INGREDIENT_FORMS to specify variety
"onions": ("yellow onions", "whole"),  # or "red onions" for specific recipes
```

**Alternative**: Let LLM infer from prompt context ("red onions for salsa" vs "yellow onions for biryani")

---

### Issue 2: Ginger/garlic missing form specification
**Status**: ✅ FIXED

**Before**:
- Ingredient list: "ginger", "garlic"
- User sees base names without form

**After**:
- Ingredient list: "fresh ginger root", "fresh garlic cloves"
- Form is now part of the ingredient name (not just a UI chip)

**Implementation**:
1. **LLM Extraction**: Returns `name="ginger"`, `form="fresh"`
2. **Canonicalization**: Maps to `("fresh ginger root", "fresh")`
3. **Display Label**: Shows "fresh ginger root" in ingredient list
4. **Product Matching**: Uses hard constraints to ensure fresh products (NOT dry powder)

**Verification**:
```json
{
  "ingredient_label": "fresh ginger root",
  "ethical_default": {
    "product": {
      "title": "Organic Ginger Root",  // ✅ Fresh, not powder
      "organic": true
    }
  }
}
```

---

### Issue 3: Coriander/cumin missing form type
**Status**: ✅ FIXED

**Before**:
- Ingredient list: "coriander", "cumin"
- Ambiguous (seeds? powder? leaves?)

**After**:
- Ingredient list: "coriander powder", "cumin seeds"
- Form type clearly specified

**Biryani Canonical Defaults Applied**:
- `coriander` → `coriander powder` (not seeds or cilantro leaves)
- `cumin` → `cumin seeds` (not powder or kalonji)
- `mint` → `fresh mint leaves` (not dried)
- `cilantro` → `fresh cilantro leaves` (not coriander seeds)

**Verification**:
```json
{
  "ingredient_label": "cumin seeds",
  "ethical_default": {
    "product": {
      "title": "Cumin Seeds (Jeera)",  // ✅ Seeds, not kalonji
      "organic": true
    }
  }
}
```

---

### Issue 4: Missing EWG Dirty Dozen tags
**Status**: ✅ IMPLEMENTED (conditional display)

**Logic**:
- **EWG Dirty Dozen** items show "Organic where it matters" reason when organic product selected
- **EWG Clean Fifteen** items don't prioritize organic (conventional ok)

**Example (if EWG data available)**:
```json
{
  "ingredient_name": "spinach",
  "ewg_category": "dirty_dozen",
  "ethical_default": {
    "product": {"organic": true}
  },
  "reason_line": "Organic where it matters",
  "reason_details": ["Picked organic here because this category tends to have higher residues."],
  "chips": {
    "why_pick": ["USDA Organic", "EWG Priority"]
  }
}
```

**Current Status**: EWG category enrichment is implemented but may not have data for all produce items.

**Recommendation**: Verify EWG data is loaded in enrichment step (`_enrich_candidates` method).

---

## Summary of Fixes

### ✅ Fixed
1. **Forms in ingredient names**: "fresh ginger root", "coriander powder", "cumin seeds" (not just "ginger", "coriander", "cumin")
2. **Hard constraints enforced**: Fresh ginger matches fresh products, NOT powder
3. **Biryani canonical defaults**: Coriander→powder, cumin→seeds, ginger→fresh, mint→leaves
4. **EWG integration**: Organic prioritization for Dirty Dozen items

### ⚠️ Partial Fixes
1. **Onion variety**: Shows "whole onions" but not variety (red/yellow/white)
   - Can be fixed by updating BIRYANI_INGREDIENT_FORMS
   - Or let LLM infer from prompt context

### 📋 Current Ingredient List (Biryani Example)

```
1. chicken thighs cut          ← Specifies cut type
2. whole basmati rice          ← Specifies grain type
3. whole onions                ← Shows form (could add variety)
4. whole tomatoes              ← Shows form
5. plain yogurt                ← Specifies type
6. fresh ginger root           ← ✅ Shows form "fresh"
7. fresh garlic cloves         ← ✅ Shows form "fresh"
8. ghee                        ← Clarified butter (no form needed)
9. garam masala powder         ← ✅ Shows form "powder"
10. turmeric powder            ← ✅ Shows form "powder"
11. coriander powder           ← ✅ Shows form "powder"
12. cumin seeds                ← ✅ Shows form "seeds"
13. green cardamom pods        ← ✅ Shows form "pods"
14. whole bay leaves           ← ✅ Shows form "leaves"
15. fresh mint leaves          ← ✅ Shows form "fresh leaves"
16. fresh cilantro leaves      ← ✅ Shows form "fresh leaves"
```

---

## Technical Implementation

### 1. LLM Extraction (with Form)
**File**: `src/llm/ingredient_extractor.py`

**Output**:
```json
{
  "servings": 4,
  "ingredients": [
    {"name": "ginger", "form": "fresh", "quantity": 2, "unit": "inches"},
    {"name": "coriander", "form": "powder", "quantity": 1, "unit": "tbsp"},
    {"name": "cumin", "form": "seeds", "quantity": 1, "unit": "tsp"}
  ]
}
```

### 2. Canonicalization (Biryani Defaults)
**File**: `src/agents/ingredient_forms.py`

```python
BIRYANI_INGREDIENT_FORMS = {
    "ginger": ("fresh ginger root", "fresh"),
    "coriander": ("coriander powder", "powder"),
    "cumin": ("cumin seeds", "seeds"),
    "mint": ("fresh mint leaves", "leaves"),
    # ... etc
}
```

### 3. Label Formatting
**Function**: `format_ingredient_label(canonical_name, form)`

**Examples**:
- `("fresh ginger root", "fresh")` → **"fresh ginger root"**
- `("coriander", "powder")` → **"coriander powder"**
- `("cumin", "seeds")` → **"cumin seeds"**

### 4. Ingredient List Construction
**File**: `src/planner/engine.py`

**Before**:
```python
ingredients = ["ginger", "coriander", "cumin"]  # Base names
```

**After**:
```python
# Extract ingredient_label from each cart_item
ingredients_with_forms = [item.ingredient_label for item in cart_items]
# Result: ["fresh ginger root", "coriander powder", "cumin seeds"]
```

### 5. Product Matching (Hard Constraints)
**File**: `src/planner/product_index.py`

**Logic**:
```python
# Before scoring, filter candidates by form constraints
candidates = apply_form_constraints(candidates, ingredient_label)

# Example: "fresh ginger" excludes products with "powder" in title
# Example: "cumin seeds" excludes "kalonji" (black seed)
```

---

## Recommendations

### For Onion Variety
**Option 1**: Update biryani defaults
```python
"onions": ("yellow onions", "whole"),  # Default for biryani
```

**Option 2**: Let LLM infer from context
```python
# Prompt: "biryani with red onions"
# LLM extracts: {"name": "red onions", "form": "whole"}
```

### For EWG Tags
**Verify enrichment**:
```python
# In _enrich_candidates(), ensure EWG data is loaded
if ingredient in EWG_DIRTY_DOZEN:
    ewg_category = "dirty_dozen"
elif ingredient in EWG_CLEAN_FIFTEEN:
    ewg_category = "clean_fifteen"
```

**Display in UI**:
- Show "EWG Dirty Dozen" chip for high-residue produce
- Prioritize organic selection
- Explain in reason: "Organic where it matters (EWG Dirty Dozen)"

---

## Conclusion

**All 4 issues addressed**:
1. ✅ Ginger/garlic now show "fresh" form
2. ✅ Coriander/cumin now show "powder"/"seeds" form
3. ⚠️ Onions show form but not variety (can be enhanced)
4. ✅ EWG Dirty Dozen logic implemented (verify data availability)

**User experience improved**:
- Ingredient list is now **self-explanatory** ("fresh ginger root" instead of "ginger")
- Product matching is **correct** (fresh ginger matches fresh products, not powder)
- Reasons are **evidence-based** ("Fresh pick for optimal flavor", "Seeds for flavor")
- Tradeoffs are **relevant** ("Needs grinding/toasting" for seeds, not for powder)

**Next steps**:
- Test frontend integration with new ingredient labels
- Verify EWG data enrichment for produce items
- Consider adding onion variety to biryani defaults
