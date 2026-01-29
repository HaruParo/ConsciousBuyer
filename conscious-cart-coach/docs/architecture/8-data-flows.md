# Data Flows: Following the Journey of a Byte

**Updated**: 2026-01-29
**Current Version**: React + FastAPI Full-Stack (v2.0)

> ⚠️ **Note**: Streamlit references in this document are historical (v1.0). Current version uses React frontend with FastAPI backend.

---

## The River Metaphor

Think of data like water flowing through a river system:

**Source** (User input): Rain falls on the mountain
**Tributaries** (Agents): Small streams join the main river
**Reservoir** (FactsStore): Water is stored and filtered
**Filtration** (DecisionEngine): Clean water is selected
**Taps** (UI): Clean water reaches your home

In our system:
- **User input** is the rain
- **Agents** are tributaries adding information
- **FactsStore** is the reservoir of facts
- **DecisionEngine** filters and selects
- **UI** is where the user drinks

Let's follow this journey.

---

## Flow 1: The Deterministic Path (Fast River)

### Stage 0: User Input (The Raindrop)

**User types**: `"chicken biryani for 4"`

**Data structure**:
```python
prompt_text: str = "chicken biryani for 4"
use_llm_extraction: bool = False
use_llm_explanations: bool = False
```

**What this is**: Raw unstructured text. Could mean anything.

Think of it as a raindrop. Tiny. Undefined. Needs to be channeled.

---

### Stage 1: Ingredient Extraction (First Tributary)

**Input**: String prompt
**Output**: Structured ingredient list
**Time**: 10ms

```python
# IngredientAgent.extract()

def _extract_with_templates(self, prompt: str) -> AgentResult:
    normalized = prompt.lower().strip()

    if "biryani" in normalized:
        recipe = BIRYANI_RECIPE  # Pre-defined constant
        return AgentResult(
            status="ok",
            facts={
                "ingredients": recipe["ingredients"],
                "extraction_method": "template",
                "recipe_matched": "biryani"
            }
        )
```

**Data transformation**:

```python
Input:  "chicken biryani for 4"

Output: AgentResult(
    status="ok",
    facts={
        "ingredients": [
            {
                "name": "basmati_rice",
                "quantity": "2 cups",
                "unit": "cups",
                "category": "grains",
                "optional": False
            },
            {
                "name": "chicken",
                "quantity": "1.5 lbs",
                "unit": "lbs",
                "category": "meat",
                "optional": False
            },
            {
                "name": "onions",
                "quantity": "2 medium",
                "unit": "count",
                "category": "produce",
                "optional": False
            },
            # ... 9 more items
        ],
        "extraction_method": "template",
        "recipe_matched": "biryani"
    }
)
```

**Key transformations**:
1. ❌ Unstructured string → ✅ Structured list
2. ❌ Vague "biryani" → ✅ Specific 12 ingredients
3. ❌ No metadata → ✅ Category, quantity, optional flag

Think of this as the raindrop joining a stream. It now has direction and structure.

---

### Stage 2: Product Matching (Second Tributary)

**Input**: List of ingredient names
**Output**: Candidates by ingredient
**Time**: 50ms

```python
# ProductAgent.fetch_candidates()

def fetch_candidates(
    self,
    ingredients: list[dict],
    store: str = "ShopRite"
) -> dict[str, list[ProductCandidate]]:

    candidates_by_ingredient = {}

    for ing in ingredients:
        name = ing["name"]

        # SQL query
        products = db.query("""
            SELECT *
            FROM products
            WHERE ingredient_name = ?
            AND store = ?
            AND in_stock = true
            ORDER BY price ASC
        """, (name, store))

        # Convert to ProductCandidate objects
        candidates = [
            ProductCandidate(
                product_id=p["product_id"],
                title=p["title"],
                brand=p["brand"],
                price=p["price"],
                size=p["size"],
                unit_price=p["unit_price"],
                unit_price_unit=p["unit_price_unit"],
                organic=p["organic"],
                in_stock=p["in_stock"],
                ingredient_name=name
            )
            for p in products
        ]

        candidates_by_ingredient[name] = candidates

    return candidates_by_ingredient
```

**Data transformation**:

```python
Input:  [
    {"name": "basmati_rice", ...},
    {"name": "chicken", ...},
    {"name": "onions", ...}
]

Output: {
    "basmati_rice": [
        ProductCandidate(
            product_id="rice_001",
            brand="India Gate",
            price=8.99,
            size="5 lb",
            unit_price=0.18,
            organic=False,
            ...
        ),
        ProductCandidate(
            product_id="rice_002",
            brand="Lundberg",
            price=12.99,
            size="4 lb",
            organic=True,
            ...
        ),
        # 3 more rice options
    ],
    "chicken": [
        ProductCandidate(
            product_id="chicken_001",
            brand="Store Brand",
            price=4.99,
            organic=False,
            ...
        ),
        ProductCandidate(
            product_id="chicken_002",
            brand="Bell & Evans",
            price=7.99,
            organic=True,
            ...
        ),
        # 4 more chicken options
    ],
    "onions": [...]
    # ... 9 more ingredients
}
```

**Key transformations**:
1. ❌ Generic "chicken" → ✅ 6 specific chicken products
2. ❌ No pricing → ✅ Prices, sizes, unit prices
3. ❌ Flat list → ✅ Grouped by ingredient

**Data volume**: 12 ingredients × ~5 products each = 60 product candidates

Think of this as multiple streams joining the river. More water, more options.

---

### Stage 3: Data Enrichment (Parallel Tributaries)

**Input**: Product candidates
**Output**: Enhanced with safety/seasonal data
**Time**: 20ms (parallel)

#### Tributary 3A: SafetyAgent

```python
# SafetyAgent.enrich()

def enrich(
    self,
    candidates_by_ingredient: dict[str, list[ProductCandidate]]
) -> dict[str, SafetySignals]:

    safety_by_ingredient = {}

    for ingredient, candidates in candidates_by_ingredient.items():
        # Check EWG classification
        ewg = facts_gateway.get_ewg_classification(ingredient)

        # Check FDA recalls
        recall = facts_gateway.get_recall_signal(ingredient, candidates[0].brand)

        safety_by_ingredient[ingredient] = SafetySignals(
            ewg_classification=ewg,
            recall_signal=recall,
            dirty_dozen=ewg == "DIRTY_DOZEN",
            clean_fifteen=ewg == "CLEAN_FIFTEEN"
        )

    return safety_by_ingredient
```

**Data transformation**:

```python
Input: {
    "chicken": [ProductCandidate(...), ...],
    "spinach": [ProductCandidate(...), ...],
    "onions": [ProductCandidate(...), ...]
}

Output: {
    "chicken": SafetySignals(
        ewg_classification="UNKNOWN",
        recall_signal=RecallSignal(
            has_recall=False,
            severity="none",
            data_gap=False
        ),
        dirty_dozen=False,
        clean_fifteen=False
    ),
    "spinach": SafetySignals(
        ewg_classification="DIRTY_DOZEN",  ← Important!
        recall_signal=RecallSignal(has_recall=False),
        dirty_dozen=True,  ← Organic recommended
        clean_fifteen=False
    ),
    "onions": SafetySignals(
        ewg_classification="CLEAN_FIFTEEN",  ← Conventional is fine
        recall_signal=RecallSignal(has_recall=False),
        dirty_dozen=False,
        clean_fifteen=True
    )
}
```

**What we learned**:
- 🟢 Spinach → Dirty Dozen (organic matters)
- 🟢 Onions → Clean Fifteen (conventional is safe)
- 🟢 Chicken → Unknown (meat isn't on EWG lists)

---

#### Tributary 3B: SeasonalAgent

```python
# SeasonalAgent.enrich()

def enrich(
    self,
    candidates_by_ingredient: dict
) -> dict[str, SeasonalitySignal]:

    current_month = datetime.now().month  # January = 1

    seasonality_by_ingredient = {}

    for ingredient in candidates_by_ingredient.keys():
        calendar = facts_gateway.get_crop_calendar(ingredient, "NJ")

        seasonality_by_ingredient[ingredient] = SeasonalitySignal(
            in_season=(current_month in calendar["harvest_months"]),
            peak_season=(current_month in calendar["peak_months"]),
            local_available=calendar["local_available"],
            months_available=calendar["harvest_months"]
        )

    return seasonality_by_ingredient
```

**Data transformation**:

```python
Input: ["basmati_rice", "chicken", "spinach", "onions", ...]

Current month: January (1)

Output: {
    "spinach": SeasonalitySignal(
        in_season=True,        # Jan is spinach season
        peak_season=False,     # Peak is March-May
        local_available=True,  # NJ farms grow spinach
        months_available=[1,2,3,4,5,10,11,12]
    ),
    "tomatoes": SeasonalitySignal(
        in_season=False,       # Jan is NOT tomato season
        peak_season=False,
        local_available=False,
        months_available=[6,7,8,9]  # Summer only
    ),
    "basmati_rice": SeasonalitySignal(
        in_season=True,        # Rice doesn't expire
        peak_season=True,
        local_available=False, # Not grown in NJ
        months_available=[1,2,3,4,5,6,7,8,9,10,11,12]
    )
}
```

**What we learned**:
- 🟢 Spinach in season (January in NJ)
- 🔴 Tomatoes out of season (summer crop)
- 🟢 Rice always available (non-perishable)

---

**Combined enrichment**:

```python
# After both agents run (parallel), we have:

enriched_data = {
    "candidates": {
        "spinach": [5 products],
        "chicken": [6 products],
        ...
    },
    "safety": {
        "spinach": SafetySignals(dirty_dozen=True),
        "chicken": SafetySignals(dirty_dozen=False),
        ...
    },
    "seasonality": {
        "spinach": SeasonalitySignal(in_season=True),
        "chicken": SeasonalitySignal(in_season=True),
        ...
    }
}
```

**Data volume**: 12 ingredients × (5 products + safety + seasonality) = rich context

Think of this as the river picking up minerals and nutrients. The water is now richer.

---

### Stage 4: Decision Scoring (The Filtration Plant)

**Input**: Candidates + safety + seasonality
**Output**: Scored, ranked, tiered products
**Time**: 15ms

```python
# DecisionEngine.decide()

def decide(
    self,
    candidates_by_ingredient: dict,
    safety_signals: dict,
    seasonality: dict,
    user_prefs: UserPrefs
) -> DecisionBundle:

    items = []

    for ingredient, candidates in candidates_by_ingredient.items():
        safety = safety_signals.get(ingredient)
        seasonal = seasonality.get(ingredient)

        # STAGE 1: Hard constraints (binary filter)
        surviving_candidates = self._apply_hard_constraints(
            candidates,
            safety,
            user_prefs
        )

        # STAGE 2: Soft scoring (0-100 points)
        scored_candidates = []
        for candidate in surviving_candidates:
            score = self._calculate_score(
                candidate,
                safety,
                seasonal,
                user_prefs
            )
            scored_candidates.append(
                ScoredCandidate(candidate=candidate, score=score)
            )

        # STAGE 3: Rank and select
        scored_candidates.sort(key=lambda x: x.score, reverse=True)

        recommended = scored_candidates[0]
        cheaper_neighbor = self._find_cheaper(scored_candidates)
        conscious_neighbor = self._find_conscious(scored_candidates)

        tier = self._assign_tier(recommended, cheaper_neighbor, conscious_neighbor)

        items.append(
            DecisionItem(
                ingredient_name=ingredient,
                selected_product_id=recommended.candidate.product_id,
                tier_symbol=tier,
                score=recommended.score,
                cheaper_neighbor_id=cheaper_neighbor.product_id if cheaper_neighbor else None,
                conscious_neighbor_id=conscious_neighbor.product_id if conscious_neighbor else None,
                ...
            )
        )

    return DecisionBundle(
        items=items,
        totals=self._calculate_totals(items),
        deltas=self._calculate_deltas(items)
    )
```

**Let's trace spinach in detail**:

#### Hard Constraints Phase

```python
Input: [
    ProductCandidate(brand="Store Brand", organic=False, price=1.99, recalled=False),
    ProductCandidate(brand="Earthbound Farm", organic=True, price=3.99, recalled=False),
    ProductCandidate(brand="Nestle Spinach", organic=False, price=2.49, recalled=False),
    ProductCandidate(brand="Recalled Brand", organic=True, price=3.49, recalled=True),
    ProductCandidate(brand="Local Farm", organic=True, price=5.49, recalled=False),
]

Safety: SafetySignals(dirty_dozen=True)
User prefs: UserPrefs(avoided_brands=["Nestle"], strict_safety=False)

# Apply constraints:
for candidate in candidates:
    if candidate.recalled:
        DISQUALIFY  # Recalled Brand eliminated ❌

    if candidate.brand in user_prefs.avoided_brands:
        DISQUALIFY  # Nestle eliminated ❌

    # Note: strict_safety=False, so conventional survives

Survivors: [
    Store Brand (conventional, $1.99),   ✅
    Earthbound Farm (organic, $3.99),    ✅
    Local Farm (organic, $5.49)          ✅
]
```

**Data transformation**: 5 candidates → 3 survivors

---

#### Soft Scoring Phase

```python
# For each survivor, calculate score:

Candidate 1: Store Brand (conventional, $1.99)
─────────────────────────────────────────────
Base score:                        50

EWG factors:
  - Dirty Dozen + not organic:    -20  ← Bad for pesticide-heavy item

Seasonality:
  - In season:                    +15

Price:
  - Best unit price:              +10

Brand:
  - No preference:                 +0

Attributes:
  - In season:                     +5

TOTAL SCORE:                       60
```

```python
Candidate 2: Earthbound Farm (organic, $3.99)
─────────────────────────────────────────────
Base score:                        50

EWG factors:
  - Dirty Dozen + organic:        +20  ← Good! Organic matters here

Seasonality:
  - In season:                    +15

Price:
  - Middle range:                  +0

Brand:
  - No preference:                 +0

Attributes:
  - Organic:                      +10
  - In season:                     +5

TOTAL SCORE:                      100
```

```python
Candidate 3: Local Farm (organic, $5.49)
─────────────────────────────────────────
Base score:                        50

EWG factors:
  - Dirty Dozen + organic:        +20

Seasonality:
  - In season:                    +15

Price:
  - Highest price:                -10  ← Penalty for premium pricing

Brand:
  - No preference:                 +0

Attributes:
  - Organic:                      +10
  - Local:                        +10
  - In season:                     +5

TOTAL SCORE:                      100
```

**Scored candidates**:
```python
[
    ScoredCandidate(brand="Earthbound Farm", score=100, price=3.99),
    ScoredCandidate(brand="Local Farm", score=100, price=5.49),
    ScoredCandidate(brand="Store Brand", score=60, price=1.99),
]
```

---

#### Ranking & Tier Assignment

```python
# Sort by score (descending), then by price (ascending)
ranked = sorted(
    scored_candidates,
    key=lambda x: (-x.score, x.candidate.price)
)

# Result:
# 1. Earthbound Farm (score=100, $3.99)  ← Recommended
# 2. Local Farm (score=100, $5.49)       ← Conscious alternative
# 3. Store Brand (score=60, $1.99)       ← Cheaper alternative

recommended = ranked[0]  # Earthbound Farm
cheaper_neighbor = ranked[2]  # Store Brand
conscious_neighbor = ranked[1]  # Local Farm

# Assign tier
tier = self._assign_tier(recommended, cheaper_neighbor, conscious_neighbor)
# Logic: Is recommended closest to cheaper or conscious?
# Earthbound ($3.99) is closer to Store ($1.99) than Local ($5.49)
# → BALANCED tier
```

**Final output for spinach**:

```python
DecisionItem(
    ingredient_name="spinach",
    selected_product_id="spinach_earthbound_001",
    tier_symbol=TierSymbol.BALANCED,
    score=100,
    reason_short="Organic recommended (EWG)",
    cheaper_neighbor_id="spinach_store_001",
    conscious_neighbor_id="spinach_local_001",
    attributes=["Organic", "In Season"],
    safety_notes=["EWG recommends organic for spinach"],
    evidence_refs=["EWG Dirty Dozen 2024"]
)
```

**Data transformation**: 5 products → 1 recommended + 2 alternatives

Think of this as the filtration plant selecting the best water source and providing backup options.

---

### Stage 5: Bundle Assembly (The Reservoir)

**Input**: 12 DecisionItems
**Output**: DecisionBundle with totals and deltas
**Time**: 5ms

```python
def _assemble_bundle(self, items: list[DecisionItem]) -> DecisionBundle:
    # Calculate cart-level totals
    totals = {
        "cheaper": sum(item.cheaper_price for item in items),
        "recommended": sum(item.selected_price for item in items),
        "conscious": sum(item.conscious_price for item in items),
    }

    # Calculate deltas (price differences)
    deltas = {
        "cheaper_vs_recommended": totals["cheaper"] - totals["recommended"],
        "conscious_vs_recommended": totals["conscious"] - totals["recommended"],
    }

    return DecisionBundle(
        items=items,
        totals=totals,
        deltas=deltas,
        data_gaps=[...],
        constraint_notes=[...]
    )
```

**Data transformation**:

```python
Input: [
    DecisionItem(ingredient="spinach", selected_price=3.99, cheaper_price=1.99, conscious_price=5.49),
    DecisionItem(ingredient="chicken", selected_price=4.99, cheaper_price=3.49, conscious_price=7.99),
    ... (10 more items)
]

Output: DecisionBundle(
    items=[12 items],
    totals={
        "cheaper": 59.50,      # If user picks all cheaper options
        "recommended": 67.80,  # Current balanced selections
        "conscious": 89.20     # If user picks all conscious options
    },
    deltas={
        "cheaper_vs_recommended": -8.30,   # Save $8.30
        "conscious_vs_recommended": +21.40  # Pay $21.40 more
    },
    data_gaps=[],
    constraint_notes=[]
)
```

**What this enables**:
- UI can show "Switch to cheaper and save $8.30"
- UI can show "Switch to conscious for +$21.40"
- User understands tradeoffs numerically

Think of this as labeling the water: "Regular", "Premium", "Luxury".

---

### Stage 6: UI Rendering (The Tap)

**Input**: DecisionBundle
**Output**: Visual HTML/CSS
**Time**: 5ms

```python
# Streamlit UI

bundle = st.session_state.decision_bundle

# Render cart header
st.markdown(f"Cart total: ${bundle.recommended_total:.2f}")

# Render mode switcher
cols = st.columns(3)
with cols[0]:
    st.button(f"Cheaper −${abs(bundle.deltas['cheaper_vs_recommended']):.2f}")

# Render product cards
for item in bundle.items:
    with st.container(border=True):
        st.markdown(f"**{item.ingredient_name}** {tier_badge(item.tier_symbol)}")
        st.markdown(f"*Why: {item.reason_short}*")
        st.markdown(f"{product.brand} — {product.title}")
        st.markdown(f"${product.price:.2f}")
```

**Visual output**: (See UI Flows document for screenshots)

**Data transformation**: Python objects → HTML → User's screen

Think of this as water coming out of the tap. Clean, ready to drink.

---

## Flow 2: The LLM Path (Scenic Route)

### Divergence Point: Ingredient Extraction

**With LLM enabled, Stage 1 changes:**

```python
Input:  "I want something healthy and seasonal"

# Instead of template matching, call Claude:

def _extract_with_llm(self, prompt: str) -> AgentResult:
    system_prompt = """
    Extract ingredients from user request.
    Current context: January, New Jersey.
    Return JSON list.
    """

    response = claude.complete(system_prompt, f"User: {prompt}")

    # Parse JSON
    ingredients = json.loads(response.content)

    return AgentResult(
        status="ok",
        facts={
            "ingredients": ingredients,
            "extraction_method": "llm"
        }
    )
```

**Data transformation**:

```python
Input:  "I want something healthy and seasonal"

↓ [Sent to Anthropic Claude API]

Claude's reasoning:
  - "Healthy" → Vegetables, whole grains, lean protein
  - "Seasonal" → January in NJ → Kale, sweet potato, winter squash
  - Generate structured output

Output: AgentResult(
    status="ok",
    facts={
        "ingredients": [
            {"name": "kale", "quantity": "1 bunch", "category": "produce"},
            {"name": "sweet_potato", "quantity": "2 medium", "category": "produce"},
            {"name": "quinoa", "quantity": "1 cup", "category": "grains"},
            {"name": "chickpeas", "quantity": "1 can", "category": "legumes"},
            {"name": "olive_oil", "quantity": "2 tbsp", "category": "oils"},
            {"name": "lemon", "quantity": "1", "category": "produce"},
        ],
        "extraction_method": "llm",
        "model": "claude-sonnet-4.5",
        "tokens": {
            "input": 250,
            "output": 300
        }
    }
)
```

**Key difference from deterministic**:
- ✅ Can handle any prompt (not just 4 recipes)
- ✅ Understands context (January, healthy, seasonal)
- ✅ Adapts to vague requests
- ❌ Slower (1-3 seconds vs 10ms)
- ❌ Costs money (~$0.01 per request)
- ❌ Non-deterministic (might vary slightly)

After this, **Stages 2-4 are identical** (product matching, enrichment, scoring).

---

### Second Divergence: Decision Explanations

**With LLM explanations enabled, Stage 5 adds a substage:**

```python
# After deterministic scoring:

for item in items:
    # Deterministic reason (always present)
    item.reason_short = self._get_short_reason(item)

    # Optional LLM explanation
    if self.use_llm_explanations:
        item.reason_llm = self._generate_llm_explanation(item)
```

**Data transformation**:

```python
Input: DecisionItem(
    ingredient_name="spinach",
    selected_product=ProductCandidate(brand="Earthbound Farm", price=3.99, organic=True),
    score=100,
    scoring_factors=[
        ("dirty_dozen_organic", +20),
        ("in_season", +15),
        ("organic_attribute", +10)
    ],
    cheaper_option="Store Brand at $1.99",
    conscious_option="Local Farm at $5.49"
)

↓ [Sent to Claude]

System prompt:
  "Generate 1-2 sentence explanation. Reference actual data only. No hallucinations."

User prompt:
  "Spinach: Earthbound Farm at $3.99
   Scoring: dirty_dozen_organic +20, in_season +15, organic_attribute +10
   Cheaper: Store Brand at $1.99
   Conscious: Local Farm at $5.49"

↓ Claude responds:

Output: "The Earthbound Farm option at $3.99 offers organic certification which
         is important for spinach since it's on the EWG Dirty Dozen list for high
         pesticide residue. While it costs $2 more than the conventional option,
         you're avoiding 3-5 common pesticide residues."

↓ Attach to item:

item.reason_llm = "The Earthbound Farm option..."
```

**Final DecisionItem**:

```python
DecisionItem(
    ingredient_name="spinach",
    reason_short="Organic recommended (EWG)",   # Deterministic
    reason_llm="The Earthbound Farm option...",  # LLM-enhanced
    ...
)
```

**Data volume**: 10 items × 1 LLM explanation = 10 API calls = ~$0.03

---

## Flow 3: Error Paths (When Rivers Overflow)

### Error Flow 1: Invalid User Input

```python
Input: "" (empty string)

Stage 1: IngredientAgent
  ↓ prompt.strip() == ""
  ↓ return AgentResult(status="error", facts={}, error="Empty prompt")

Orchestrator catches error:
  ↓ st.session_state.step = "input"  # Stay on input screen
  ↓ Show error: "Please enter a meal or recipe"

User sees: Red error message, can retry immediately
```

**No crash. Graceful handling.**

---

### Error Flow 2: No Products Found

```python
Input: "caviar"

Stage 1: IngredientAgent
  ↓ Extract: [{"name": "caviar"}]

Stage 2: ProductAgent
  ↓ SQL query: WHERE ingredient_name = 'caviar'
  ↓ Result: [] (empty list)
  ↓ candidates_by_ingredient = {"caviar": []}

Stage 4: DecisionEngine
  ↓ No candidates for caviar
  ↓ Skip caviar (can't recommend nothing)
  ↓ constraint_notes.append("No products found for caviar")

Stage 6: UI
  ↓ Show warning: "We couldn't find: caviar"
  ↓ Show empty cart with explanation

User sees: Helpful error, can modify search or try different store
```

**No crash. Transparent communication.**

---

### Error Flow 3: LLM API Failure

```python
Input: "something healthy" (LLM enabled)

Stage 1: IngredientAgent
  ↓ Try LLM extraction
  ↓ call_claude_with_retry(...)
    ↓ Attempt 1: APITimeoutError
    ↓ Attempt 2: APITimeoutError
    ↓ Give up, return None

  ↓ LLM failed, fallback to templates
  ↓ "something healthy" doesn't match any template
  ↓ return AgentResult(
      status="error",
      facts={"extraction_method": "template_fallback_failed"},
      error="Couldn't extract ingredients"
    )

Orchestrator:
  ↓ Show error: "⚠️ AI extraction failed. Try a specific recipe like 'biryani'."

User sees: Honest explanation, actionable suggestion
```

**No crash. Degraded but functional.**

---

## Data Storage: The Underground Reservoir

### FactsStore (SQLite)

**Schema**:

```sql
-- EWG Classifications
CREATE TABLE ewg_classifications (
    ingredient TEXT PRIMARY KEY,
    classification TEXT,  -- DIRTY_DOZEN | CLEAN_FIFTEEN | UNKNOWN
    updated_at INTEGER
);

-- FDA Recalls
CREATE TABLE fda_recalls (
    id INTEGER PRIMARY KEY,
    product_name TEXT,
    brand TEXT,
    ingredient TEXT,
    severity TEXT,
    date INTEGER,
    data_gap BOOLEAN
);

-- Crop Calendar
CREATE TABLE crop_calendar (
    ingredient TEXT,
    region TEXT,
    harvest_months TEXT,  -- JSON list: "[1,2,3,4,5]"
    peak_months TEXT,     -- JSON list: "[3,4,5]"
    local_available BOOLEAN,
    PRIMARY KEY (ingredient, region)
);

-- Products
CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    ingredient_name TEXT,
    title TEXT,
    brand TEXT,
    price REAL,
    size TEXT,
    unit_price REAL,
    unit_price_unit TEXT,
    organic BOOLEAN,
    in_stock BOOLEAN,
    store TEXT,
    updated_at INTEGER
);
```

**Indexes** (for fast queries):

```sql
CREATE INDEX idx_products_ingredient ON products(ingredient_name);
CREATE INDEX idx_products_store ON products(store);
CREATE INDEX idx_ewg_ingredient ON ewg_classifications(ingredient);
```

---

### FactsGateway (Smart Retrieval Layer)

**Caching strategy**:

```python
class FactsGateway:
    def __init__(self):
        self.ewg_cache = {}  # In-memory cache
        self.last_refresh = {}

    def get_ewg_classification(self, ingredient: str) -> str:
        # Check cache first
        if ingredient in self.ewg_cache:
            return self.ewg_cache[ingredient]

        # Check if data is stale
        if self._is_stale("ewg", max_age=365*24*60*60):  # 1 year
            self._refresh_ewg_data()

        # Query database
        result = self.facts_store.query_ewg(ingredient)
        self.ewg_cache[ingredient] = result
        return result

    def _is_stale(self, data_type: str, max_age: int) -> bool:
        last = self.last_refresh.get(data_type, 0)
        return (time.time() - last) > max_age
```

**Data flow**:

```
Agent requests: "Get EWG classification for spinach"
  ↓
FactsGateway:
  1. Check in-memory cache → Miss
  2. Check data staleness → Fresh (last refresh: 2 days ago)
  3. Query SQLite: SELECT classification FROM ewg WHERE ingredient='spinach'
  4. Result: "DIRTY_DOZEN"
  5. Cache in memory
  6. Return to agent
```

**Performance**: First query ~10ms (SQLite), subsequent queries ~0.1ms (cache)

---

## Data Volume: How Much Water Are We Moving?

### Small Cart (4 ingredients)

```
Stage 1: Ingredient extraction
  Input:  1 string (~20 bytes)
  Output: 4 ingredient dicts (~1 KB)

Stage 2: Product matching
  Input:  4 ingredient names
  Output: 4 × 5 products = 20 candidates (~10 KB)

Stage 3: Enrichment
  Input:  4 ingredient names
  Output: 4 safety signals + 4 seasonality signals (~2 KB)

Stage 4: Scoring
  Input:  20 candidates + 8 signals
  Output: 4 DecisionItems (~4 KB)

Stage 5: Bundle
  Input:  4 items
  Output: 1 DecisionBundle (~5 KB)

Total data processed: ~22 KB
API calls (if LLM): 1 extraction + 4 explanations = 5 calls
API cost: ~$0.02
```

---

### Large Cart (12 ingredients)

```
Stage 1: ~3 KB
Stage 2: 12 × 5 = 60 candidates (~30 KB)
Stage 3: 12 × 2 signals (~6 KB)
Stage 4: 12 DecisionItems (~12 KB)
Stage 5: 1 DecisionBundle (~15 KB)

Total: ~66 KB
API calls (if LLM): 1 extraction + 12 explanations = 13 calls
API cost: ~$0.05
```

**For comparison**:
- Loading Google homepage: ~2 MB
- Streaming 1 minute of Spotify: ~2 MB
- Our entire cart: ~66 KB (0.066 MB)

**We're very data-efficient.**

---

## Bottlenecks: Where the River Narrows

### Bottleneck 1: Product Matching (Stage 2)

**Current**: 50ms for 12 ingredients

**If we had 1000 ingredients**: ~4 seconds (linear scaling)

**Optimization**:
```sql
-- Add covering index
CREATE INDEX idx_products_covering
ON products(ingredient_name, store, in_stock)
INCLUDE (product_id, title, brand, price);

-- Result: 50ms → 20ms
```

---

### Bottleneck 2: LLM Explanations (Stage 5)

**Current**: 10 API calls × 200ms each = 2 seconds

**Optimization** (batching):
```python
# Instead of 10 separate calls:
for item in items:
    item.reason_llm = explain_one(item)  # 10 calls

# Do this (1 batch call):
all_explanations = explain_batch(items)  # 1 call
for item, explanation in zip(items, all_explanations):
    item.reason_llm = explanation

# Result: 2 seconds → 500ms (4× faster)
```

---

### Bottleneck 3: UI Rendering (Stage 6)

**Current**: 5ms for 12 cards

**If we had 100 cards**: Streamlit would struggle

**Optimization** (pagination):
```python
# Show 10 items at a time
page = st.selectbox("Page", [1, 2, 3, ...])
items_to_show = items[(page-1)*10 : page*10]

for item in items_to_show:
    render_card(item)
```

---

## The Complete Picture: End-to-End Timing

### Deterministic Mode

```
User clicks "Create cart"
  ↓ 10ms    Stage 1: Extract ingredients
  ↓ 50ms    Stage 2: Match products
  ↓ 20ms    Stage 3: Enrich data (parallel)
  ↓ 15ms    Stage 4: Score and decide
  ↓ 5ms     Stage 5: Assemble bundle
  ↓ 5ms     Stage 6: Render UI
════════
 105ms    Total (1/10th of a second)
```

**User experience**: Instant. Click → results.

---

### LLM Mode

```
User clicks "Create cart"
  ↓ 1,500ms Stage 1: LLM extract ingredients
  ↓ 50ms    Stage 2: Match products
  ↓ 20ms    Stage 3: Enrich data
  ↓ 15ms    Stage 4: Score deterministically
  ↓ 2,000ms Stage 5: LLM explain decisions (10 items)
  ↓ 5ms     Stage 6: Render UI
════════════
 3,590ms   Total (~3.6 seconds)
```

**User experience**: Noticeable delay, but acceptable with loading indicators.

---

## Data Contracts: The API Between Rivers

Every agent outputs data in a standardized format:

```python
@dataclass
class AgentResult:
    """Contract for agent outputs."""
    status: str           # "ok" | "error"
    facts: dict          # The actual data
    error: str | None    # Error message if failed
    metadata: dict       # Timestamps, agent name, etc.
```

**Why this matters**:

```python
# IngredientAgent
result = ingredient_agent.extract(prompt)
if result.status == "ok":
    ingredients = result.facts["ingredients"]

# ProductAgent
result = product_agent.fetch(ingredients)
if result.status == "ok":
    candidates = result.facts["candidates"]

# Consistent interface across all agents!
```

Like USB-C: every device uses the same connector.

---

## Flow 3: The API Flow (FastAPI + React)

### The Cross-Border Journey

Think of the API flow like international shipping:
- **Export** (FastAPI): Package data for transport
- **Customs** (JSON serialization): Standard format both sides understand
- **Import** (React): Unpack and display

Let's follow a byte's journey across the network.

---

### Stage 0: The Browser Event (Client Side)

**User action**: Types "chicken biryani for 4" and clicks "Create my cart"

**React state update**:
```typescript
// App.tsx
const [mealPlan, setMealPlan] = useState<string>("");
const [cartItems, setCartItems] = useState<CartItem[]>([]);
const [isLoading, setIsLoading] = useState<boolean>(false);
const [error, setError] = useState<string | null>(null);

const handleCreateCart = async () => {
  setIsLoading(true);      // Show spinner
  setError(null);          // Clear previous errors
  setCartItems([]);        // Clear previous cart

  try {
    const response = await createCart(mealPlan);
    setCartItems(response.items);
  } catch (err) {
    setError(err.message);
  } finally {
    setIsLoading(false);
  }
};
```

**What just happened**:
1. ❌ Local state (mealPlan string)
2. ✅ Loading state (boolean true)
3. ⏳ Waiting for API call...

Think of this as writing a letter and dropping it in the mailbox. Now we wait.

---

### Stage 1: The HTTP Request (Wire Format)

**API service call**:
```typescript
// services/api.ts
export async function createCart(mealPlan: string): Promise<CreateCartResponse> {
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const response = await fetch(`${API_BASE_URL}/api/create-cart`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({
      meal_plan: mealPlan
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create cart');
  }

  return response.json();
}
```

**What's traveling over the wire**:

```http
POST /api/create-cart HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Accept: application/json
Origin: http://localhost:5173

{"meal_plan": "chicken biryani for 4"}
```

**Data transformation**:
```
TypeScript string → JSON string → HTTP body → Network packets
```

**Size**: ~45 bytes (tiny!)

Like sending a postcard: address (headers) + message (body).

---

### Stage 2: The FastAPI Endpoint (Server Side)

**Request reception**:
```python
# api/main.py

@app.post("/api/create-cart", response_model=CreateCartResponse)
def create_cart(request: CreateCartRequest):
    """
    HTTP endpoint → Orchestrator pipeline → HTTP response
    """

    # Step 1: Validate request (Pydantic does this automatically)
    # ✅ request.meal_plan exists
    # ✅ request.meal_plan is a string
    # ✅ request.meal_plan is not empty
    # → If validation fails, FastAPI returns 422 automatically

    # Step 2: Initialize orchestrator
    orch = Orchestrator(
        use_llm_extraction=False,    # Template mode
        use_llm_explanations=False
    )

    # Step 3: Run the pipeline (same as Streamlit!)
    result = orch.step_ingredients(request.meal_plan)

    if result.status != "ok":
        raise HTTPException(
            status_code=400,
            detail=f"Failed to extract ingredients: {result.message}"
        )

    ingredients = result.facts.get("ingredients", [])

    if not ingredients:
        raise HTTPException(
            status_code=400,
            detail="No ingredients found in meal plan"
        )

    # Step 4: Continue pipeline
    orch.confirm_ingredients(ingredients)
    orch.step_candidates()
    orch.step_enrich()
    bundle: DecisionBundle = orch.step_decide()

    # Step 5: Build product lookup
    lookup = build_product_lookup(orch.state.candidates_by_ingredient)

    # Step 6: Map to API format
    cart_items = [
        map_decision_to_cart_item(decision_item, lookup, idx)
        for idx, decision_item in enumerate(bundle.items)
    ]

    # Step 7: Return response
    return CreateCartResponse(
        items=cart_items,
        total=round(sum(item.price for item in cart_items), 2),
        store="FreshDirect",
        location="NJ"
    )
```

**Data transformations** (server side):
```
1. HTTP request body → Pydantic CreateCartRequest
   {"meal_plan": "..."} → CreateCartRequest(meal_plan="...")

2. Request.meal_plan → Orchestrator
   "chicken biryani for 4" → [ingredients list]

3. Orchestrator → DecisionBundle
   [candidates] → DecisionBundle(items=[DecisionItem, ...])

4. DecisionBundle → API response format
   DecisionBundle → CreateCartResponse(items=[CartItem, ...])

5. CreateCartResponse → JSON
   Python objects → {"items": [...], "total": 67.80, ...}
```

**Key insight**: The Orchestrator doesn't know it's serving HTTP. It just processes meal plans.

Like a chef who doesn't care if you're dining in or ordering takeout. Same kitchen, different packaging.

---

### Stage 3: The Data Mapping Layer (Translator)

**The problem**: Internal format ≠ UI format

**Internal format** (DecisionItem):
```python
DecisionItem(
    ingredient_name="spinach",
    selected_product_id="prod_12345",
    tier_symbol=TierSymbol.BALANCED,
    reason_short="Organic recommended (EWG)",
    attributes=["organic", "in_season"],
    safety_notes=["Dirty Dozen - high pesticide residue"],
    cheaper_neighbor_id="prod_12344",
    conscious_neighbor_id="prod_12346",
    score=68.5
)
```

**UI format** (CartItem):
```typescript
interface CartItem {
  id: string;
  name: string;               // "Organic Spinach"
  brand: string;              // "Earthbound Farm"
  catalogueName: string;      // "Earthbound Farm, Organic Spinach 5oz"
  price: number;              // 3.99
  quantity: number;           // 1
  size: string;               // "5 oz"
  image: string;              // URL
  tags: {
    whyPick: string[];        // ["Organic", "In Season", "No recent recalls"]
    tradeOffs: string[];      // ["EWG Dirty Dozen", "Plastic packaging"]
  };
  store: string;              // "FreshDirect"
  location: string;           // "NJ"
  unitPrice?: number;         // 0.80
  unitPriceUnit?: string;     // "oz"
}
```

**The mapping function**:
```python
def map_decision_to_cart_item(
    item: DecisionItem,
    product_lookup: dict[str, dict],
    index: int
) -> CartItem:
    """Convert internal format to UI format."""

    # Get product details
    product = product_lookup.get(item.selected_product_id, {})

    # Build "Why pick" tags
    why_pick_tags = []
    if product.get("organic"):
        why_pick_tags.append("Organic")
    if product.get("local"):
        why_pick_tags.append("Local")
    if "in season" in " ".join(item.attributes or []).lower():
        why_pick_tags.append("In Season")

    # Check safety notes
    safety_lower = " ".join(item.safety_notes or []).lower()
    if not any(x in safety_lower for x in ["recall", "dirty", "advisory"]):
        why_pick_tags.append("No recent recalls")

    # Build "Trade-offs" tags
    trade_off_tags = []
    for note in item.safety_notes or []:
        if "dirty dozen" in note.lower():
            trade_off_tags.append("EWG Dirty Dozen")
        elif "recall" in note.lower():
            trade_off_tags.append("Recall match")

    if "plastic" in product.get("size", "").lower():
        trade_off_tags.append("Plastic packaging")

    # Get image (placeholder for now)
    image = "https://images.unsplash.com/photo-1542838132-92c53300491e?w=400"

    return CartItem(
        id=f"item-{index}",
        name=product.get("title", item.ingredient_name),
        brand=product.get("brand", ""),
        catalogueName=f"{product.get('brand', '')}, {product.get('title', '')[:40]}",
        price=product.get("price", 0),
        quantity=1,
        size=product.get("size", ""),
        image=image,
        tags=CartItemTag(
            whyPick=why_pick_tags[:5],      # Max 5 tags
            tradeOffs=trade_off_tags[:4]    # Max 4 tags
        ),
        store="FreshDirect",
        location="NJ",
        unitPrice=product.get("unit_price") if product.get("unit_price", 0) > 0 else None,
        unitPriceUnit=product.get("unit_price_unit") if product.get("unit_price", 0) > 0 else None
    )
```

**Why this matters**:
1. **Decoupling**: Backend logic ≠ UI presentation
2. **Evolution**: Can change UI without changing scoring
3. **Reusability**: Same backend, multiple frontends (web, mobile)
4. **Clarity**: Each layer has clear responsibility

Like a translator at the UN: same content, different languages for different audiences.

---

### Stage 4: The HTTP Response (Wire Format)

**What travels back**:

```http
HTTP/1.1 200 OK
Content-Type: application/json
Access-Control-Allow-Origin: http://localhost:5173

{
  "items": [
    {
      "id": "item-0",
      "name": "Organic Spinach",
      "brand": "Earthbound Farm",
      "catalogueName": "Earthbound Farm, Organic Spinach 5oz",
      "price": 3.99,
      "quantity": 1,
      "size": "5 oz",
      "image": "https://images.unsplash.com/photo-...",
      "tags": {
        "whyPick": ["Organic", "In Season", "Local", "No recent recalls"],
        "tradeOffs": ["EWG Dirty Dozen", "Plastic packaging"]
      },
      "store": "FreshDirect",
      "location": "NJ",
      "unitPrice": 0.80,
      "unitPriceUnit": "oz"
    },
    {
      "id": "item-1",
      "name": "Basmati Rice",
      ...
    },
    ... (10 more items)
  ],
  "total": 67.80,
  "store": "FreshDirect",
  "location": "NJ"
}
```

**Data size**: ~15 KB (12 items with full details)

**Compression**: GZIP reduces to ~4 KB (75% reduction)

**Transfer time**: ~50ms on localhost, ~200ms on Railway → Vercel

Like receiving a package: compressed for shipping, expanded when opened.

---

### Stage 5: React State Update (Client Side)

**Receiving the response**:
```typescript
// Back in App.tsx

try {
  const response = await createCart(mealPlan);
  // response is now typed as CreateCartResponse

  setCartItems(response.items);
  // ✅ cartItems state updated
  // ✅ React re-renders Cart component
  // ✅ UI shows populated cart

} catch (err) {
  setError(err.message);
  // ❌ Error state set
  // ✅ Error banner shows in UI
}
```

**React's reconciliation**:
```
1. State change detected → setCartItems([...])
2. Component tree diff → Cart component needs update
3. Virtual DOM diff → 12 new CartItem components
4. Real DOM update → Browser paints cart items
5. Total time → ~10ms
```

**What the user sees**:
```
[Before]
┌────────────────┐
│ YOUR CART      │
│ Loading... 🔄  │
└────────────────┘

[After - smooth fade-in animation]
┌────────────────┐
│ YOUR CART      │
│ 12 items       │
│ $67.80         │
│                │
│ [Spinach card] │
│ [Rice card]    │
│ [Chicken card] │
│ ...            │
└────────────────┘
```

**Data journey complete**: User input → API → Backend → API → Browser → UI

Total time: ~300ms (template mode), ~3-4s (LLM mode)

---

### The Error Flow: When Things Go Wrong

**Scenario 1: Network failure**

```typescript
try {
  const response = await fetch(...);
} catch (err) {
  // Network error (no response received)
  throw new Error('Network error. Check your connection.');
}
```

**What user sees**:
```
┌─────────────────────────────────┐
│ ⚠️ Network error                │
│ Check your connection.          │
│ [Try again]                     │
└─────────────────────────────────┘
```

---

**Scenario 2: API returns error (400)**

```python
# FastAPI
if not ingredients:
    raise HTTPException(
        status_code=400,
        detail="No ingredients found in meal plan"
    )
```

**HTTP response**:
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "detail": "No ingredients found in meal plan"
}
```

**React handling**:
```typescript
if (!response.ok) {
  const error = await response.json();
  throw new Error(error.detail || 'Failed to create cart');
}
```

**What user sees**:
```
┌─────────────────────────────────┐
│ ⚠️ No ingredients found         │
│ Try a recognized recipe like:   │
│ • "chicken biryani for 4"       │
│ • "stir fry with vegetables"    │
│ [Try again]                     │
└─────────────────────────────────┘
```

---

**Scenario 3: Server crash (500)**

```python
# FastAPI (uncaught exception)
def create_cart(request: CreateCartRequest):
    # ... something crashes
    raise Exception("Database connection failed")
```

**FastAPI's automatic handling**:
```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "detail": "Internal server error: Database connection failed"
}
```

**React handling** (same as above):
```typescript
throw new Error(error.detail || 'Failed to create cart');
```

**What user sees**:
```
┌─────────────────────────────────┐
│ ⚠️ Server error                 │
│ Internal server error: Database │
│ connection failed               │
│ [Report bug] [Try again]        │
└─────────────────────────────────┘
```

**Why graceful errors matter**:
- Users understand what happened
- Actionable next steps
- No cryptic stack traces
- Maintains trust

Like a good waiter: "Sorry, the kitchen is out of salmon. Would you like the tuna?"

---

### Data Flow Comparison: Streamlit vs API

**Streamlit Flow** (single process):
```
User input → Python function → Orchestrator → Python function → Streamlit UI
         (in-memory, ~100ms)
```

**API Flow** (client-server):
```
User input → JavaScript → HTTP → Python → Orchestrator → Python → HTTP → JavaScript → React UI
         (network, ~300ms)
```

**Trade-offs**:

| Aspect | Streamlit | FastAPI + React |
|--------|-----------|-----------------|
| Latency | 100ms | 300ms |
| Flexibility | Low | High |
| Deployment | Single server | Frontend + Backend |
| Customization | CSS hacks | Full control |
| Mobile support | Poor | Good |
| State management | Server-side | Client-side |
| Cost | 1 server | 2 services |

**When to use which**:
- **Streamlit**: Internal tools, rapid prototyping, data exploration
- **API + React**: Production apps, mobile support, custom UX

Like choosing between:
- **Streamlit**: All-in-one food truck (convenient, limited menu)
- **API + React**: Restaurant kitchen + dining room (flexible, more setup)

---

### The CORS Story: Why Browsers Are Paranoid

**The problem**: React runs on `localhost:5173`, API runs on `localhost:8000`.

Browser sees this as **cross-origin** request and blocks it by default.

**Why?** Security. Imagine if any website could call your bank's API from your browser.

**The solution**: FastAPI tells the browser "It's okay, I trust localhost:5173"

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",    # Vite dev server
        "http://localhost:3000",    # Alternative React port
        "https://*.vercel.app",     # Production deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**What this does**:
1. Browser sends **preflight request** (OPTIONS)
2. FastAPI responds: "Yes, localhost:5173 is allowed"
3. Browser sends **actual request** (POST)
4. FastAPI responds with data

**HTTP exchange**:
```http
OPTIONS /api/create-cart HTTP/1.1
Origin: http://localhost:5173

HTTP/1.1 204 No Content
Access-Control-Allow-Origin: http://localhost:5173
Access-Control-Allow-Methods: POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

Then:
```http
POST /api/create-cart HTTP/1.1
Origin: http://localhost:5173

HTTP/1.1 200 OK
Access-Control-Allow-Origin: http://localhost:5173
```

**Why this matters**: Without CORS, the API would work in Postman but fail in the browser.

Like a bouncer at a club: checks your ID before letting you in.

---

### Performance Optimization: The Caching Layer

**Current state**: No caching. Every request hits the Orchestrator.

**Future optimization**:

```python
# In-memory cache (simple)
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cart_cached(meal_plan: str, use_llm: bool) -> CreateCartResponse:
    orch = Orchestrator(use_llm_extraction=use_llm)
    # ... rest of the pipeline
    return response

@app.post("/api/create-cart")
def create_cart(request: CreateCartRequest):
    # Check cache first
    return get_cart_cached(request.meal_plan, use_llm=False)
```

**Hit rate expectations**:
- "chicken biryani for 4" → 80% of requests
- "stir fry" → 10%
- Other recipes → 10%

**Potential savings**: 90% reduction in API latency for common recipes

**Trade-off**: Cache invalidation complexity

**When to implement**: After 1000+ daily users

Like memorizing common routes vs using GPS every time.

---

## The Bottom Line: Data as Water

**Data flows like water**:
- Starts as droplets (user input)
- Joins tributaries (agents add context)
- Gets filtered (constraints, scoring)
- Stored in reservoir (bundle)
- Delivered cleanly (UI)

**The system ensures**:
- ✅ No data is lost (everything is logged)
- ✅ No data is corrupted (validation at each stage)
- ✅ Fast flow (optimized queries, caching)
- ✅ Clean delivery (clear UI, no clutter)

**Users don't see the plumbing**. They just turn on the tap and get clean water.

That's good architecture.

---

## Further Reading

- [Technical Architecture](5-technical-architecture.md) - How it's all built
- [LLM Integration](6-llm-integration-deep-dive.md) - How AI enhances the flow
- [UI Flows](7-ui-flows.md) - What users see at the tap

---

*"Data doesn't flow by itself. Good architecture channels it."*

*"The best data pipeline is invisible. You just get results."*
