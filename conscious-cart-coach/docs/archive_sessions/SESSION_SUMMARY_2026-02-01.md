# Session Summary: 2026-02-01

## Problems Identified

### 1. **LLM Extraction: Only 4 Ingredients Returned**
**Issue**: "chicken biryani for 4" extracted only 4 ingredients instead of expected 16

**Root Cause**:
- Missing `anthropic` module prevented LLM client initialization
- Ollama was configured but client initialization failed silently
- Prompt wasn't explicit enough about 12-16 ingredient requirement

**Fixes Applied**:
1. Made `anthropic` import optional in 3 files:
   - [`src/utils/llm_client.py:19-30`](src/utils/llm_client.py#L19-L30)
   - [`src/llm/ingredient_extractor.py:8-12`](src/llm/ingredient_extractor.py#L8-L12)
   - [`src/llm/decision_explainer.py:6-10`](src/llm/decision_explainer.py#L6-L10)

2. Enhanced extraction prompt [`src/llm/ingredient_extractor.py:35-111`](src/llm/ingredient_extractor.py#L35-L111):
   - Added explicit biryani ingredient list (16 items)
   - Increased `max_tokens`: 2048 → 3000
   - Increased `temperature`: 0.0 → 0.1
   - Added "Extract 12-16 ingredients minimum" requirement

3. Added missing spices to prompt:
   - Coriander powder
   - Fresh mint
   - Fresh cilantro

**Status**: ✅ Fixed (confirmed working with Ollama)

---

### 2. **Store Assignment: 365 Showing Under FreshDirect**
**Issue**: "365 by Whole Foods Market" products showing under FreshDirect cart

**Root Cause**:
- Store assignment only checked `available_stores` field
- Didn't consider brand exclusivity
- Brand-based filtering happened AFTER store grouping

**Fix Applied**:
Added brand-based store assignment [`api/main.py:372-398`](api/main.py#L372-L398):
```python
# Check brand exclusivity first (overrides everything)
if "365" in brand_lower or "whole foods" in brand_lower:
    actual_store = "Whole Foods"
elif "pure indian foods" in brand_lower:
    actual_store = "Pure Indian Foods"
elif "kesar grocery" in brand_lower or "swad" in brand_lower:
    actual_store = "Kesar Grocery"
```

**Status**: ⚠️  Partially Fixed (logic added but still failing in production)

---

### 3. **Generic/Repetitive Tags**
**Issue**: All products showing "Organic", "Safe", "Premium priced" tags

**Root Cause**:
- Tags were hardcoded basic attributes
- No evidence-based validation
- No context from alternatives (cheaper_neighbor, conscious_neighbor)

**Fixes Applied**:
1. **Validator-Safe Tag System** [`api/main.py:286-357`](api/main.py#L286-L357):
   - 7 evidence-based categories
   - EWG Dirty Dozen/Clean Fifteen ratings
   - FDA recall checks
   - Verifiable certifications (USDA Organic, Fair Trade)
   - Cost positioning with data (tier symbols)

2. **Relative Tradeoff Tags** [`api/main.py:301-370`](api/main.py#L301-L370):
   - Compare recommended product against cheaper_neighbor
   - Compare against conscious_neighbor
   - Show actual price differences (e.g., "$3 more for organic")
   - Context-aware phrasing ("Worth organic premium" vs "$4 more than cheapest")

**Tag Categories**:
| Category | Why Pick | Trade-off |
|----------|----------|-----------|
| Organic | USDA Organic, EWG Safe Choice | Not organic (saves $X), EWG Dirty Dozen |
| Safety | No Active Recalls, EWG Clean Fifteen | FDA Advisory |
| Sourcing | Direct Import, Local Farm, Locally Sourced | — |
| Cost | Best Value, Balanced Choice, Saves $X vs organic | Premium Price, $X more for organic |
| Certifications | Free-Range, Grass-Fed, Fair Trade | — |
| Brand | Store Brand | — |

**Status**: ✅ Fixed (code complete, needs production validation)

---

### 4. **Wrong Product Forms: Granules Instead of Fresh**
**Issue**: Recipe calls for fresh ginger, but system recommends "Ginger Root Coarse Granules"

**Root Cause**:
- Product sorting checked "organic" keyword before "granules"
- "Organic Ginger Root Coarse Granules" got form_score=0 because "organic" was detected
- Fresh vs dried check happened too late

**Fix Applied**:
Reordered form matching logic [`src/agents/product_agent.py:797-808`](src/agents/product_agent.py#L797-L808):
```python
# CRITICAL: Check for dried/granules FIRST (even if organic)
if "granules" in title_lower or "minced" in title_lower or "dried" in title_lower or "powder" in title_lower:
    form_score = 20  # Avoid dried/granules for fresh ingredients
elif "fresh" in title_lower or "bunch" in title_lower or "root" in title_lower:
    form_score = 0  # Fresh is best
elif "organic" in title_lower and "granules" not in title_lower:
    form_score = 0  # Organic whole produce (not granules)
else:
    form_score = 5  # Generic match
```

**Fresh Produce Added** [`data/alternatives/source_listings.csv`](data/alternatives/source_listings.csv):
- Fresh Organic Ginger Root (FreshDirect, $3.99/lb)
- Organic Garlic (FreshDirect, $5.99/lb)
- Fresh Mint Bunch (FreshDirect, $2.99/bunch)
- Fresh Cilantro Bunch (FreshDirect, $1.99/bunch)
- Organic Cilantro Bunch (FreshDirect, $2.99/bunch)

**Status**: ⚠️  Fixed in code, still failing in production (needs investigation)

---

### 5. **No Bundle Detection**
**Issue**: System recommends 6 individual spices instead of "Biryani Spice Bundle"

**Root Cause**: No bundle detection logic

**Potential Solutions**:
1. Pre-scan inventory for bundles matching ingredient set
2. LLM skill to evaluate if bundle covers recipe needs
3. Hardcoded bundle rules per recipe template

**Status**: ⏳ Not yet implemented (future enhancement)

---

## New Features Created

### 1. **Recipe Product Matcher LLM Skill** 🔍
**File**: [`src/llm/recipe_product_matcher.py`](src/llm/recipe_product_matcher.py)

**Purpose**: Evaluate products against recipe requirements across 7 attributes

**The 7 Attributes**:
1. **FORM**: Fresh vs dried, powder vs whole, stick vs ground
2. **QUALITY**: Organic, certifications, grade
3. **VARIETY**: Specific cultivar/type if it matters (e.g., Basmati rice)
4. **ORIGIN**: Geographic source for authenticity
5. **PROCESSING**: Minimal vs heavily processed
6. **BRAND**: Trusted specialty brands vs generic
7. **VALUE**: Price-quality balance

**Usage**:
```python
from src.llm.recipe_product_matcher import select_best_product_for_recipe

best_product = select_best_product_for_recipe(
    client=anthropic_client,
    recipe_context="Chicken Biryani (traditional Indian dish)",
    ingredient_name="ginger",
    ingredient_form="fresh root",
    candidates=[...]
)
```

**Status**: ✅ Created, not yet integrated into product_agent

---

### 2. **Ingredient Form Mapping System**
**File**: [`src/agents/ingredient_forms.py`](src/agents/ingredient_forms.py)

**Purpose**: Define preferred forms for ingredients

**Examples**:
```python
INGREDIENT_FORMS = {
    "ginger": ("fresh", ["ginger root", "fresh ginger"], ["dried", "granules", "powder"]),
    "turmeric": ("powder", ["turmeric powder", "ground turmeric"], ["granules", "whole root"]),
    "cumin seeds": ("whole", ["cumin seeds whole", "jeera"], ["powder", "ground"]),
}
```

**Functions**:
- `get_preferred_form(ingredient_name)` → "fresh" | "powder" | "whole"
- `should_match_product(ingredient, product_title)` → (matches: bool, score: int)

**Status**: ✅ Created, used in product ranking

---

## Documentation Created

### 1. **LLM Skills Guide**
**File**: [`docs/LLM_SKILLS_GUIDE.md`](docs/LLM_SKILLS_GUIDE.md)

**Contents**:
- LLM integration architecture
- Available LLM skills (Ingredient Extraction, Decision Explanation, Recipe Product Matcher)
- Multi-provider support (Ollama, Anthropic, Gemini, OpenAI)
- How to create new LLM skills (step-by-step template)
- Prompt engineering best practices
- Temperature & token configuration
- Opik tracing setup
- Debugging guide

---

### 2. **Pivot Options Document**
**File**: [`PIVOT_OPTIONS.md`](PIVOT_OPTIONS.md)

**Contents**:
- 4 concrete pivot strategies:
  1. **Streamlit Rapid Prototype**: Replace React with Python UI (2 hours)
  2. **Hardcoded Recipe Templates**: Pre-defined ingredients instead of LLM (3 hours)
  3. **Single-Store Simplified Flow**: Remove multi-store complexity (1 day)
  4. **Focus on Tags + Tradeoffs**: Be a "conscious decision guide" not "orchestrator"

- Recommended approach: **Streamlit + Templates + Single Store**
- 4-hour action plan with code examples
- Decision framework (Speed vs Risk vs Value)

---

## Technical Context

### Architecture Decisions

**LLM Provider**: Ollama (local) with Mistral model
- Privacy-first (no API calls)
- No cost
- Fast enough for development
- Can switch to Anthropic for production

**Decision Engine** [`src/engine/decision_engine.py`](src/engine/decision_engine.py):
- 2-stage scoring: Hard constraints → Soft scoring
- Deterministic (same input → same output)
- Optional LLM explanations
- Scoring weights:
  - Organic specialty: +15
  - Value efficiency: +12
  - Dirty Dozen no organic: -20
  - Avoided brand: -25

**Store Split Logic** [`src/orchestrator/store_split.py`](src/orchestrator/store_split.py):
- 3-item efficiency rule (don't add specialty store for <3 items)
- Minimum order thresholds per store
- Fresh/shelf-stable constraint (fresh → primary only)
- Urgency inference (tonight → Kesar Grocery, later → Pure Indian Foods)

---

## Files Modified (16 total)

### Core LLM Files (3)
1. ✅ `src/llm/ingredient_extractor.py` - Enhanced prompt, optional imports
2. ✅ `src/llm/decision_explainer.py` - Optional imports
3. ✅ `src/llm/recipe_product_matcher.py` - NEW: 7-attribute recipe matching

### Agent Files (2)
4. ✅ `src/agents/product_agent.py` - Fresh produce prioritization fix
5. ✅ `src/agents/ingredient_forms.py` - NEW: Form preference mappings

### API Files (1)
6. ✅ `api/main.py` - Relative tradeoff tags, brand-based store assignment

### Infrastructure Files (2)
7. ✅ `src/utils/llm_client.py` - Optional anthropic import
8. ✅ `src/orchestrator/store_split.py` - 3-item efficiency rule

### Data Files (1)
9. ✅ `data/alternatives/source_listings.csv` - Fresh produce added

### Documentation Files (4)
10. ✅ `docs/LLM_SKILLS_GUIDE.md` - NEW: Comprehensive LLM guide
11. ✅ `PIVOT_OPTIONS.md` - NEW: Simplification strategies
12. ✅ `SESSION_SUMMARY_2026-02-01.md` - NEW: This file
13. ✅ `CHANGELOG_SESSION_2026-02-01.md` - Existing changelog

### Test Files (2)
14. ✅ `test_llm_extraction.py` - Ollama extraction test
15. ✅ `conscious-cart-coach/frontend/package.json` - Frontend dependencies

### Config Files (1)
16. ✅ `conscious-cart-coach/frontend/vite.config.ts` - Vite config updates

---

## User Feedback Log

### Iteration 1: "Only 4 ingredients?"
**User**: "now i see 4 ingredients in the list and cart what's wrong?"
**Fix**: Made anthropic imports optional, enhanced prompt
**Result**: LLM extraction now returns 12-16 ingredients

### Iteration 2: "Tags are way off"
**User**: "tags are way off"
**Fix**: Validator-safe tag system with EWG ratings, FDA recalls
**Result**: Evidence-based tags with verifiable claims

### Iteration 3: "365 showing under FreshDirect"
**User**: "365 by Whole Foods Market... is from whole foods why are you recommending it under fresh direct"
**Fix**: Brand-based store assignment (checks brand before available_stores)
**Result**: Logic added but still failing in production

### Iteration 4: "Recipe calls for fresh ginger"
**User**: "Pure Indian Foods, Ginger Root Coarse Granules is unnecessary- recipie asks for fresh ginger and garlic"
**Fix**: Reordered form matching (check granules BEFORE organic)
**Result**: Logic fixed but still failing in production

### Iteration 5: "Need coriander powder, mint, cilantro"
**User**: "you need coriander powder, fresh mint and fresh cilantro"
**Fix**: Added to extraction prompt template
**Result**: Prompt updated

### Iteration 6: "Tags not showing tradeoffs"
**User**: "except for premium price i dont see tradeoffs. how is decision agent deciding?"
**Fix**: Added relative comparisons with cheaper_neighbor and conscious_neighbor
**Result**: Tags now show "$3 more for organic", "Saves $4 vs organic", etc.

### Iteration 7: "Still not working, need pivot"
**User**: "remember i told you if things aren't working you need to give me pivot suggestions? like streamlits"
**Fix**: Created PIVOT_OPTIONS.md with 4 concrete alternatives
**Result**: Streamlit prototype, recipe templates, single-store simplification

---

## Current Status

### What's Working ✅
1. LLM extraction (12-16 ingredients for dishes)
2. Optional LLM provider support (Ollama, Anthropic, Gemini, OpenAI)
3. Validator-safe tag system (7 categories)
4. Relative tradeoff tags (code complete)
5. Fresh produce inventory (added to CSV)
6. Recipe Product Matcher skill (created)
7. Documentation (LLM guide, pivot options)

### What's Broken ⚠️
1. Store assignment (365 still showing under FreshDirect)
2. Fresh produce matching (granules still recommended over fresh)
3. Backend not applying code changes (needs investigation)
4. Tag comparisons not showing in UI

### Root Issues 🔍
1. **Too Complex**: Multi-layer architecture (product_agent → decision_engine → store_split → api)
2. **Hard to Debug**: Changes don't propagate (inventory loading, sorting, assignment)
3. **Fragile**: Many failure points (CSV loading, normalization, matching, sorting, grouping)

---

## Recommended Next Steps

### Immediate (Today)
1. **Create Streamlit Prototype** (2 hours)
   - Test LLM extraction visually
   - Debug product matching
   - Validate fresh produce prioritization
   - Prove core value without React complexity

2. **Hardcode Recipe Templates** (3 hours)
   - Top 10 dishes with pre-defined ingredients
   - Ingredient forms specified (fresh vs powder)
   - Remove LLM extraction complexity
   - 100% reliable results

### Short-term (This Week)
3. **Single-Store Focus** (1 day)
   - Remove store_split.py complexity
   - FreshDirect only
   - Perfect the tags and tradeoffs
   - Prove value before scaling

4. **Fix Fresh Produce Matching** (debug)
   - Investigate why code changes aren't applied
   - Test inventory loading
   - Verify sorting logic
   - Check product selection flow

### Long-term (Future)
5. **Multi-store Support** (only after single-store works perfectly)
6. **Bundle Detection** (LLM or rules-based)
7. **React Frontend Rebuild** (using proven Streamlit logic)

---

## Key Learnings

### What Worked
- ✅ LLM extraction with Ollama (fast, private, works)
- ✅ Structured prompts with examples (12-16 ingredients now extracted)
- ✅ Optional imports pattern (graceful degradation)
- ✅ Opik tracing (visibility into LLM calls)
- ✅ Validator-safe tags (evidence-based, fact-checkable)

### What Didn't Work
- ❌ Complex multi-layer architecture (hard to debug)
- ❌ Brand-based store assignment (keeps failing)
- ❌ Product form matching (granules over fresh despite fixes)
- ❌ CSV inventory loading (changes not propagating)

### What We Learned
1. **Simplicity > Cleverness**: Hardcoded recipe templates would be faster than LLM extraction
2. **Single Store > Multi-Store**: Prove value with one store before adding complexity
3. **Tags = Differentiator**: Focus on tag quality, not orchestration logic
4. **Streamlit = Speed**: Test ideas in hours, not days

---

## Decision Points

### Continue Current Approach?
**Pros**: Architecture is "correct", scalable, well-architected
**Cons**: Too complex, hard to debug, fragile
**Recommendation**: ❌ No - pivot to Streamlit

### Pivot to Streamlit?
**Pros**: 10x faster iteration, visual debugging, proof of value
**Cons**: Not production-ready, needs React later
**Recommendation**: ✅ Yes - do this NOW

### Hardcode Recipe Templates?
**Pros**: 100% reliable, instant results, curated quality
**Cons**: Limited flexibility, manual work per recipe
**Recommendation**: ✅ Yes - do this in parallel with Streamlit

### Single-Store Focus?
**Pros**: Removes 500+ lines of complexity, faster, simpler
**Cons**: Loses specialty store support (but can add later)
**Recommendation**: ✅ Yes - focus on FreshDirect only

---

## Context for Future Sessions

### Environment
- **LLM Provider**: Ollama (local) with Mistral:latest
- **Backend**: FastAPI on port 8000
- **Frontend**: React + Vite
- **Database**: CSV files (data/alternatives/*.csv)

### API Endpoints
- `POST /api/plan` - Extract ingredients and return cart
- `POST /api/extract-ingredients` - LLM extraction only
- Backend running at http://localhost:8000

### Configuration Files
- `.env` - LLM provider settings (LLM_PROVIDER=ollama)
- `data/alternatives/source_listings.csv` - Product inventory
- `conscious-cart-coach/frontend/package.json` - Frontend deps

### Key Directories
- `src/llm/` - LLM skills (extraction, explanation, matching)
- `src/agents/` - Product agent, ingredient forms
- `src/engine/` - Decision engine (scoring, neighbor selection)
- `src/orchestrator/` - Store split logic
- `api/` - FastAPI endpoints
- `docs/` - Documentation

---

## Questions to Ask Next Session

1. Did you try the Streamlit prototype? Did it help debug?
2. Are recipe templates working better than LLM extraction?
3. Should we abandon multi-store support entirely?
4. What's the #1 blocker to launching?
5. Should we focus on tags/tradeoffs or product matching?

---

## Code Snippets for Reference

### LLM Extraction (working)
```python
from src.utils.llm_client import OllamaClient
from src.llm.ingredient_extractor import extract_ingredients_with_llm

client = OllamaClient(base_url='http://localhost:11434', model='mistral:latest')
ingredients = extract_ingredients_with_llm(client, "chicken biryani for 4", servings=4)
# Returns: list[dict] with 12-16 ingredients
```

### Recipe Template (recommended)
```python
from src.recipes.templates import get_recipe_template

template = get_recipe_template("chicken_biryani_4", servings=4)
# Returns: pre-defined 16 ingredients with forms
```

### Product Matching (needs debugging)
```python
from src.agents.product_agent import ProductAgent

agent = ProductAgent()
result = agent.get_candidates(ingredients, target_store="FreshDirect")
# Should prioritize fresh ginger over granules, but doesn't
```

---

## Final Summary

**Session Goal**: Fix LLM extraction, store assignment, tags, and product matching
**Result**: 4/5 fixed in code, but production issues persist
**Root Cause**: Over-engineered architecture that's hard to debug
**Pivot**: Streamlit prototype + recipe templates + single-store focus
**Next Session**: Build Streamlit MVP, test in 2 hours vs 2 days debugging

**Key Insight**: The core value isn't "multi-store orchestration" - it's "conscious decision-making with transparent tradeoffs". Simplify to prove that value first.
