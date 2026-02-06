# The Technical Architecture: Building a Grocery Shopping Assistant

**Updated**: 2026-01-29
**Current Version**: React + FastAPI Full-Stack (v2.0)

> ⚠️ **Note**: Historical Streamlit references are from v1.0. Current production version uses React frontend with FastAPI backend.

---

## The Restaurant Kitchen Analogy

Imagine Conscious Cart Coach as a restaurant kitchen. When a customer (user) orders "chicken biryani for 4," their request doesn't go straight to the chef. Instead, it flows through a well-orchestrated kitchen hierarchy:

1. **The Host (UI)** takes the order
2. **The Expediter (Orchestrator)** breaks it down into tasks
3. **Multiple Stations (Agents)** each handle their specialty
4. **The Head Chef (DecisionEngine)** makes the final call
5. **The Plating Team (UI again)** presents the result beautifully

This isn't just a metaphor—it's exactly how our system works. Let's tour the kitchen.

---

## The Two-Building Architecture: Why We Have Two Codebases

Here's something unusual about our project: **we have two parallel `/src/` directories**.

```
ConsciousBuyer/
├── src/                           ← Building #1: The Frontend Office
│   └── data_processing/
└── conscious-cart-coach/
    └── src/                       ← Building #2: The Backend Factory
        ├── agents/
        ├── engine/
        ├── orchestrator/
        ├── ui/
        └── ...
```

**Why two buildings?**

Think of it like a restaurant group that owns both:
- **Building #1** (root `/src/`): The corporate office where they handle marketing, data analysis, and customer-facing stuff
- **Building #2** (`/conscious-cart-coach/src/`): The actual restaurant kitchen where all the food prep happens

In our case:
- **Root `/src/`**: Originally meant for data preprocessing and frontend integrations
- **`/conscious-cart-coach/src/`**: The **core engine**—this is where the magic happens

**The active Streamlit UI lives in Building #2** (`conscious-cart-coach/src/ui/app.py`). When you run `./run.sh`, you're launching the factory kitchen, not the corporate office.

**Why keep them separate?**
1. **Clean separation of concerns**: The core engine doesn't care about frontend details
2. **Reusability**: Tomorrow we could build a mobile app that uses the same engine
3. **Testing**: We can test the core logic without worrying about UI state
4. **Historical reasons**: The project evolved from separating data work from business logic

It's like keeping your recipe development separate from your catering business. Same food, different contexts.

---

## The Multi-Agent System: Everyone Has a Job

### Why Agents?

In 2024, everyone talks about "AI agents." But here's what agents *really* mean in software: **specialized workers, each doing one thing well**.

Think about a hospital:
- The receptionist doesn't do surgery
- The radiologist doesn't write prescriptions
- The nurse doesn't handle billing

Each person has a clear job, and they communicate through a standardized system (patient charts, forms, etc.).

Our agents work the same way. Here's the roster:

### The Agent Lineup

**1. IngredientAgent** - The Translator
```python
User says: "chicken biryani for 4"
IngredientAgent returns: [
    {name: "basmati_rice", quantity: "2 cups"},
    {name: "chicken", quantity: "1.5 lbs"},
    {name: "onions", quantity: "2 medium"},
    ...
]
```

**Job**: Turn vague human requests into structured grocery lists.

**Two modes**:
- **Template mode (default)**: "I've seen this recipe before! Here's the list." (Fast, free, works for 4 recipes)
- **LLM mode (optional)**: "Let me think about what 'healthy and seasonal' means..." (Slower, costs money, works for anything)

Think of template mode as ordering off the menu vs LLM mode as asking the chef to improvise based on your dietary restrictions.

---

**2. ProductAgent** - The Inventory Manager

**Job**: "You need spinach? Let me check what we have in stock."

```python
Input: "spinach"
Output: [
    ProductCandidate(brand="Earthbound", organic=True, price=3.99, size="5oz"),
    ProductCandidate(brand="Store Brand", organic=False, price=1.99, size="10oz"),
    ProductCandidate(brand="Local Farm", organic=True, price=4.99, size="6oz"),
    ...
]
```

ProductAgent searches the inventory database (ShopRite, Whole Foods, etc.) and returns **all matching products**. It doesn't pick winners—that's not its job. It's like a warehouse worker pulling all the spinach options off the shelf for the chef to choose.

**Why not assign tiers here?** Because tiers depend on *context*:
- If you're on a budget, the $1.99 spinach might be "balanced"
- If spinach is on the EWG Dirty Dozen, organic becomes essential
- If it's peak season, local matters more

ProductAgent doesn't know these rules. It just finds products. Separation of concerns.

---

**3. SafetyAgent** - The Food Inspector

**Job**: Check if products are safe, using two data sources:

**EWG Dirty Dozen** (Pesticide concerns)
```
Dirty Dozen (high pesticides) → Recommend organic
Clean Fifteen (low pesticides) → Conventional is fine
```

**FDA Recalls** (Product recalls)
```
"Romaine lettuce - E. coli outbreak - 2024-01-15"
→ Flag all romaine products
```

Think of SafetyAgent as the health inspector who walks through before service and puts warning stickers on certain ingredients.

---

**4. SeasonalAgent** - The Farmer's Market Expert

**Job**: Know what's in season in New Jersey (our launch region).

```python
January: {
    "spinach": "out-of-season",
    "kale": "in-season",
    "tomatoes": "greenhouse-only"
}

June: {
    "spinach": "in-season",
    "tomatoes": "peak-season",
    "strawberries": "local-available"
}
```

SeasonalAgent uses a crop calendar to score products. It's like having a farmer on staff who knows exactly when to buy local.

**Why does this matter?**
- **Taste**: In-season produce tastes better
- **Price**: Supply/demand affects cost
- **Environment**: Local seasonal = less transportation
- **Freshness**: Peak season = picked ripe

---

**5. UserHistoryAgent** - The Regular Customer Memory

**Job**: "Oh, you're back! I remember you always go for organic and avoid Nestle brands."

This agent (currently basic) tracks:
- Preferred brands ("I always buy Organic Valley")
- Avoided brands ("I'm boycotting Nestle")
- Tier preferences ("I usually pick the balanced option")

Think of it as the bartender who remembers your usual order.

---

**6. DecisionEngine** - The Head Chef

**Not technically an "agent," but the final decision maker.**

**Job**: Take all the intelligence gathered by other agents and make the call:
- Which product to recommend
- What tier it belongs to (cheaper/balanced/conscious)
- What the cheaper alternative is
- What the premium alternative is

**Two-stage process**:

**Stage 1: Hard Constraints (Binary Pass/Fail)**
```python
if product.recalled:
    DISQUALIFY ❌

if "Nestle" in user_prefs.avoided_brands and product.brand == "Nestle":
    DISQUALIFY ❌

if strict_safety and dirty_dozen and not product.organic:
    DISQUALIFY ❌
```

Think of this as the health code. You either pass or you're shut down. No gray area.

**Stage 2: Soft Scoring (0-100 points)**
```python
score = 50  # Start neutral

# EWG factors
if dirty_dozen and organic:
    score += 20  # "Smart choice for this ingredient"
if dirty_dozen and not organic:
    score -= 20  # "Risky for pesticides"

# Seasonality
if peak_season:
    score += 15  # "Perfect timing!"
if out_of_season:
    score -= 5   # "Long journey from warehouse"

# Price efficiency
if best_unit_price:
    score += 10  # "Great value per ounce"

# Brand trust
if preferred_brand:
    score += 5   # "You know you like this"
```

This is where the magic happens. Every product gets a score, and that score determines its tier:
- **Cheaper tier**: Lowest price in the top 3
- **Conscious tier**: Highest score for ethics/health
- **Balanced tier**: The recommended middle ground

**Key insight**: Scoring is **100% deterministic**. Same inputs = same outputs. No randomness. This is crucial for trust and debugging.

---

## The Orchestrator: The Expediter

If agents are kitchen stations, the **Orchestrator** is the expediter who coordinates everything.

```python
class Orchestrator:
    """
    I don't cook. I don't plate.
    I just make sure everyone does their job in the right order.
    """
```

The Orchestrator runs a **5-stage pipeline**:

```
1. EXTRACT INGREDIENTS
   User: "biryani for 4"
   → IngredientAgent
   → [rice, chicken, onions, ...]

2. FETCH PRODUCTS
   → ProductAgent
   → candidates_by_ingredient = {"rice": [product1, product2, ...]}

3. ENRICH WITH DATA
   → SafetyAgent + SeasonalAgent (parallel)
   → safety_signals, seasonality_scores

4. MAKE DECISIONS
   → DecisionEngine
   → DecisionBundle (recommended products + alternatives)

5. DISPLAY
   → Streamlit UI
   → Beautiful 3-tier cart
```

**The Gating Pattern**

Here's something clever: the Orchestrator uses **gates** between stages.

```python
# Stage 1: Extract
result = orch.step_ingredients(prompt)

# GATE: User must confirm ingredients
orch.confirm_ingredients(modified_list)

# Stage 2: Continue only after gate passes
orch.step_candidates()
```

**Why gates?** Because users might want to edit the ingredient list before we spend time fetching products. It's like confirming your order before the kitchen starts cooking.

Think of gates as:
- Restaurant: "Is this order correct?"
- Airport: "Do you have your boarding pass?"
- Our app: "Are these the ingredients you want?"

---

## The Data Layer: FactsStore & FactsGateway

### The Problem

Our agents need data:
- EWG Dirty Dozen lists
- FDA recall notices
- Seasonal crop calendars
- Store inventories

But agents shouldn't query databases directly. **Agents are workers, not DBAs.**

### The Solution: The Two-Tier Data Layer

**FactsStore** (Raw Storage)
```python
class FactsStore:
    """
    I'm just SQLite with a simple interface.
    I store facts. I don't interpret them.
    """

    def get_ewg_classification(ingredient: str) -> str:
        # Query: SELECT classification FROM ewg WHERE ingredient = ?
```

Think of FactsStore as the **filing cabinet**. It holds papers, but doesn't care what's written on them.

**FactsGateway** (Smart Retrieval)
```python
class FactsGateway:
    """
    I know how to ask the right questions.
    I also know when data is stale and needs refreshing.
    """

    def get_safety_signals(ingredient: str) -> SafetySignals:
        # 1. Check if data is fresh (< 24 hours old)
        # 2. If stale, re-import from CSV
        # 3. Combine EWG + recall data
        # 4. Return structured SafetySignals object
```

FactsGateway is the **librarian** who knows:
- Where things are
- When they were last updated
- How to combine multiple sources
- When to refresh cached data

**Auto-Refresh Pattern**

```python
class FactsGateway:
    REFRESH_WINDOWS = {
        "ewg": 365 * 24 * 60 * 60,      # Annual
        "recalls": 24 * 60 * 60,         # Daily
        "seasonal": 30 * 24 * 60 * 60,  # Monthly
    }
```

FactsGateway checks timestamps and auto-imports from CSV when data goes stale. Users never think about it. It just works.

Like your phone auto-updating apps in the background.

---

## Technology Choices: Why We Picked What We Picked

### Python 3.10+
**Why**: Type hints, match statements, improved error messages.

**Trade-off**: Requires newer Python, but worth it for developer experience.

Think of it like using a modern car with automatic transmission vs a manual from the 90s. Sure, the old one works, but why suffer?

---

### SQLite for Data Storage
**Why**:
- No server setup
- File-based (easy to backup/share)
- Fast for read-heavy workloads
- Built into Python

**When to upgrade to PostgreSQL**: When you have multiple concurrent writers or need advanced features.

SQLite is like a local coffee shop. It's perfect until you need to serve 500 customers at once.

---

### Streamlit for UI
**Why**:
- Python-native (no JavaScript)
- Rapid prototyping
- Built-in components (text, buttons, expanders)
- Hot reload during development

**Trade-offs**:
- Less control than React
- State management can be tricky
- Not ideal for mobile

Streamlit is like IKEA furniture. Limited customization, but you can set it up in an afternoon and it looks pretty good.

---

### Anthropic Claude for LLM
**Why Claude over GPT-4**:
1. **Better at following instructions** (critical for structured output)
2. **Longer context windows** (useful for product comparisons)
3. **More conservative** (less hallucination)
4. **API design** (cleaner, easier to use)

Think of Claude as the sous chef who follows recipes exactly vs the creative chef who improvises (and sometimes makes mistakes).

---

### Pandas for Data Processing
**Why**: Industry standard for tabular data, excellent CSV handling, powerful transformations.

**Trade-off**: Memory-heavy for large datasets, but we're dealing with grocery data, not big data.

Pandas is like Excel on steroids. If you can think it, you can do it (but it'll use all your RAM).

---

## The Hybrid LLM Strategy: Why We Don't Use LLM for Everything

**The Big Decision**: LLM for input/output UX, deterministic for scoring.

### What LLM Does (Optional)

**1. Ingredient Extraction**
```
User: "I want something healthy and seasonal"
Claude: "Here's a structured list of ingredients based on that request"
```

**Why LLM here?** Natural language understanding is hard. Claude is trained on millions of recipe variations.

**2. Explanations**
```
Deterministic system: score=68, tier=BALANCED, reason="Organic recommended (EWG)"
Claude: "The Earthbound Farm option at $3.99 offers organic certification..."
```

**Why LLM here?** Humans prefer natural language over code-like outputs.

### What LLM Doesn't Do (Never)

**3. Scoring Products**
```python
# ❌ NOPE - Not using LLM here
score = claude.score_this_product(...)

# ✅ YES - Deterministic rules
score = 50
if dirty_dozen and organic:
    score += 20
```

**Why deterministic?**
1. **Trust**: Users can audit the logic
2. **Consistency**: Same inputs → same outputs
3. **Speed**: No API latency for core logic
4. **Cost**: Scoring 1000 products costs $0 vs $$$ with LLM
5. **Reliability**: No hallucinations affecting recommendations

**The Analogy**:

LLM is like a friendly tour guide explaining a museum. They make the experience richer and more accessible. But **the museum's security system** (which items are on loan, which are fragile, which room to prioritize) is hardcoded rules. You don't want your security system "hallucinating" that a $10M painting is actually in the gift shop.

Scoring is our security system. Explanations are our tour guide.

---

## The Contracts: How Components Talk to Each Other

Every agent and service communicates through **standardized data structures** (contracts).

```python
@dataclass
class ProductCandidate:
    """Everyone agrees this is what a 'product' looks like."""
    product_id: str
    title: str
    brand: str
    price: float
    size: str
    unit_price: float
    unit_price_unit: str
    organic: bool
    in_stock: bool
```

**Why contracts?**

Imagine if every restaurant had its own definition of "medium rare." Chaos.

Contracts are like:
- **USB-C**: Every device knows what to expect
- **LEGO blocks**: Different pieces, same connection points
- **Sheet music**: Musicians read the same notation

In our system:
- ProductAgent outputs `List[ProductCandidate]`
- SafetyAgent expects `ProductCandidate` input
- DecisionEngine returns `DecisionBundle`

If someone changes ProductCandidate, **Python type hints will catch errors immediately**. This is huge for team collaboration.

---

## Error Handling: The Graceful Fallback Philosophy

Software fails. APIs timeout. Databases go down. Users input garbage.

**Our philosophy**: **Degrade gracefully. Never crash.**

### Example 1: LLM Ingredient Extraction

```python
# Try LLM first
if self.use_llm:
    llm_result = self._extract_with_llm(prompt)
    if llm_result:
        return llm_result  # Success!

# Fallback to templates
return self._extract_with_templates(prompt)
```

**What happens**:
1. LLM enabled but API key missing? → Use templates
2. LLM times out? → Use templates
3. LLM returns invalid JSON? → Use templates
4. Templates don't match? → Return empty list + helpful error

**User experience**: "I tried Claude but it's not available, so I used recipe templates instead."

Like a restaurant running out of salmon and automatically offering the sea bass special.

---

### Example 2: Missing Data

```python
def get_safety_signals(ingredient: str) -> SafetySignals:
    ewg = self._get_ewg(ingredient) or EWGClassification.UNKNOWN
    recall = self._get_recalls(ingredient) or RecallSignal.NONE

    return SafetySignals(
        ewg=ewg,
        recall=recall,
        data_gap=(ewg == UNKNOWN or recall.data_gap)
    )
```

**What happens**:
- EWG data missing? → Default to UNKNOWN, flag as data gap
- Recalls DB down? → Warn user but continue
- Both missing? → Product still shows up, just with a disclaimer

**User experience**: "We don't have full safety data for this item, but here's what we know."

Like a nutritionist saying "I don't know the sodium content, but I know it's high in protein."

---

### Example 3: Empty Search Results

```python
if not candidates:
    return DecisionBundle(
        items=[],
        constraint_notes=["No products found for spinach (out of stock)"]
    )
```

**What happens**: Empty cart with explanation, not a crash.

**User experience**: "We couldn't find X at ShopRite. Try another store?"

Like calling a pizza place and hearing "We're out of pepperoni, want mushrooms?"

---

## Testing Strategy: The 32 Integration Tests

We have **32+ integration tests** in `tests/test_pipeline.py`. Here's why:

### Unit Tests vs Integration Tests

**Unit test**: "Does the addition function work?"
```python
def test_add():
    assert add(2, 3) == 5
```

**Integration test**: "If I order biryani, do I get rice, chicken, and the right prices?"
```python
def test_biryani_full_flow():
    orch = Orchestrator()
    bundle = orch.process_prompt("biryani for 4")

    assert "basmati_rice" in bundle.items
    assert bundle.recommended_total > 0
    assert len(bundle.items) >= 10
```

**Why integration tests matter more here**:
- Our value is in the **orchestration**, not individual functions
- A bug in ProductAgent might not show up until DecisionEngine tries to score
- Real user flows involve 5+ agents working together

Think of it like testing a car:
- Unit test: "Does the brake pedal press?"
- Integration test: "Does the car actually stop when I press the brake?"

You need both, but integration tests catch the scary bugs.

---

## Performance Considerations

### The Fast Path (Deterministic Mode)

```
User input → Template extraction (10ms)
          → Product fetch (50ms, SQLite)
          → Safety/Seasonal lookup (20ms, cached)
          → Decision engine (15ms, pure Python)
          → UI render (5ms, Streamlit)
═══════════════════════════════════════════════
Total: ~100ms
```

**Why so fast?**
- No network calls (SQLite is local)
- No LLM (pure computation)
- Cached data (FactsGateway)
- Simple queries (indexed SQLite tables)

Like a fast-food restaurant. Everything's pre-prepped and ready to assemble.

---

### The LLM Path (Optional Enhanced Mode)

```
User input → LLM extraction (1-3 sec, API call)
          → Product fetch (50ms)
          → Safety/Seasonal (20ms)
          → Decision engine (15ms)
          → LLM explanations (1-2 sec, API calls, 10 items)
          → UI render (5ms)
═══════════════════════════════════════════════
Total: ~2-4 seconds
```

**Why slower?**
- Network round trips to Anthropic
- Claude processing time
- Multiple API calls (1 for extraction, N for explanations)

Like fine dining. Takes longer, but the experience is richer.

**Optimization opportunities**:
1. Batch explanation requests (1 API call instead of N)
2. Cache common ingredient extractions
3. Use cheaper model (Haiku) for simple cases

---

## Security & Privacy Considerations

### Data Storage
- **User preferences**: Stored locally in `facts_store.db`
- **Shopping history**: Local only (never sent to cloud)
- **LLM queries**: Sent to Anthropic if LLM enabled

### API Key Management
```bash
# .env file (never committed to git)
ANTHROPIC_API_KEY=sk-ant-api03-...
```

If someone gets your API key:
- They can't access your shopping data (local SQLite)
- They can run up your API bill (standard risk)
- Rotate keys immediately if compromised

Like losing your credit card: cancel it, but your bank account is still safe.

---

### PII (Personally Identifiable Information)

**What we store**:
- Ingredient preferences (generic)
- Brand preferences (generic)
- Tier choices (generic)

**What we don't store**:
- Names
- Addresses
- Payment info
- Social graphs

The system is **privacy-first by design**. Even if the database leaked, there's no way to identify individuals.

---

## Scalability: What Happens When We Grow

**Current design**: Single-user desktop app (Streamlit)

**What breaks first when scaling**:
1. **SQLite** (concurrent writes)
2. **Streamlit** (not designed for 1000s of users)
3. **Local storage** (each user needs their own database)

**Migration path to production**:

```
Phase 1 (Now): Local Streamlit + SQLite
Phase 2 (100 users): Web app + PostgreSQL
Phase 3 (10K users): API backend + React frontend + Redis cache
Phase 4 (1M users): Microservices + event streaming + CDN
```

Think of it like:
- Phase 1: Food truck (works great!)
- Phase 2: Single restaurant
- Phase 3: Restaurant chain
- Phase 4: Franchise operation

We're intentionally starting small. Premature optimization is the root of all evil.

---

## Key Architectural Patterns We Use

### 1. Separation of Concerns
Each agent has **one job**. ProductAgent doesn't care about safety. SafetyAgent doesn't care about pricing.

### 2. Dependency Injection
```python
def __init__(self, anthropic_client: Optional[Anthropic] = None):
```
Orchestrator creates the client once, shares it with agents. Easier to test, more efficient.

### 3. Lazy Loading
```python
if self.use_llm:
    from ..llm.ingredient_extractor import extract_ingredients
```
Don't import LLM modules unless needed. Faster startup, smaller footprint.

### 4. Strategy Pattern
```python
# Template strategy
result = self._extract_with_templates(prompt)

# LLM strategy
result = self._extract_with_llm(prompt)
```
Swap strategies at runtime based on user preference.

### 5. Gateway Pattern
```python
# Don't do this
agent.query_db("SELECT * FROM ewg WHERE...")

# Do this
facts = gateway.get_ewg_classification(ingredient)
```
FactsGateway hides database complexity. Agents just ask for facts.

---

## What Makes This Architecture Good

### 1. **Testable**
Every component has clear inputs/outputs. Easy to mock and test.

### 2. **Maintainable**
Change one agent without breaking others. Clear boundaries.

### 3. **Debuggable**
Deterministic scoring means you can trace every decision.

### 4. **Extendable**
Want to add a new agent (e.g., NutritionAgent)? Just follow the pattern. Orchestrator doesn't change.

### 5. **Cost-Effective**
LLM is optional. You can use the full system for $0/month or enhance it for ~$5/month.

### 6. **User-Friendly**
Fast default experience (100ms) with optional richness (4 sec with LLM).

---

## What Could Be Better (Honest Assessment)

### 1. **Two Codebases**
Having root `/src/` and `/conscious-cart-coach/src/` is confusing for newcomers.

**Why we haven't merged**: Historical reasons + separation of concerns.

**Future**: Probably merge into single structure.

---

### 2. **Streamlit State Management**
Streamlit's state management is... quirky. Widgets rerun on every interaction.

**Workarounds**: We use session state + callbacks carefully.

**Future**: Consider migrating to FastAPI + React for more control.

---

### 3. **Agent Communication**
Agents are currently called sequentially by Orchestrator. No inter-agent communication.

**Future**: Could use event-driven architecture (agents publish events, others subscribe).

---

### 4. **Limited Store Coverage**
Currently only a few stores. Adding new stores requires manual data import.

**Future**: Real-time API integration with store inventories.

---

### 5. **Caching Strategy**
Basic caching in FactsGateway. Could be more sophisticated.

**Future**: Redis layer for multi-user deployment, smarter cache invalidation.

---

## The Bottom Line

**This architecture is intentionally pragmatic.**

We didn't build for 1 million users on day one. We built for:
- **Fast iteration** (change things easily)
- **Low cost** (free tier works great)
- **Clear debugging** (deterministic = predictable)
- **Optional enhancement** (LLM when you want it)

It's like building a house:
- Strong foundation (clean separation, tested)
- Flexible walls (easy to add rooms/agents)
- Good plumbing (data flows cleanly)
- Optional luxury features (LLM enhancements)

**Could it scale to 1M users?** Not as-is. But that's okay. When we get to 10K users, we'll have the resources and knowledge to rebuild the parts that matter.

**Perfect is the enemy of good. This architecture is good.**

---

## The Full-Stack Evolution: From Streamlit to FastAPI + React

**When we started**: Streamlit was perfect for prototyping. Python end-to-end, fast iteration, built-in components.

**When we needed to deploy**: We realized Streamlit has limitations for production hackathon demos:
- CSS customization is tricky
- State management can be quirky
- Harder to match exact Figma designs
- Not ideal for mobile responsiveness

**The solution**: We didn't abandon our core engine. We just gave it a better front door.

---

### The New Architecture: Separation of Church and State

Think of it like a restaurant that started as a food truck (Streamlit) and then opened a brick-and-mortar location (React) while keeping the same kitchen (Orchestrator).

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Streamlit  │    │  React App   │    │  HTML Demo   │  │
│  │   (Local)    │    │  (Vite Dev)  │    │  (Static)    │  │
│  │  Port: 8501  │    │ Port: 5173   │    │  Standalone  │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                    │           │
│         └───────────────────┼────────────────────┘           │
│                             │                                │
│                    ┌────────▼────────┐                       │
│                    │  FastAPI Server │                       │
│                    │   Port: 8000    │                       │
│                    │  CORS Enabled   │                       │
│                    └────────┬────────┘                       │
│                             │                                │
└─────────────────────────────┼────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   BUSINESS LOGIC   │
                    │    Orchestrator    │
                    │  ├─ Agents         │
                    │  ├─ DecisionEngine │
                    │  └─ FactsGateway   │
                    └────────┬───────────┘
                             │
                    ┌────────▼───────────┐
                    │    DATA LAYER      │
                    │  SQLite FactsStore │
                    │  Product Catalog   │
                    └────────────────────┘
```

**Key insight**: The Orchestrator doesn't care who's calling it. Streamlit, React, HTML, mobile app—doesn't matter. It just processes meal plans and returns shopping carts.

---

### The FastAPI Backend: The Translator

**Location**: `/conscious-cart-coach/api/main.py`

**Job**: Translate between HTTP requests and Orchestrator calls.

```python
@app.post("/api/create-cart", response_model=CreateCartResponse)
def create_cart(request: CreateCartRequest):
    """
    HTTP endpoint that wraps the Orchestrator pipeline.

    Takes: {"meal_plan": "chicken biryani for 4"}
    Returns: {"items": [...], "total": 67.80, "store": "FreshDirect"}
    """

    # Initialize orchestrator (same as Streamlit)
    orch = Orchestrator(
        use_llm_extraction=False,  # Template mode for demo
        use_llm_explanations=False
    )

    # Run the 5-stage pipeline
    result = orch.step_ingredients(request.meal_plan)
    ingredients = result.facts.get("ingredients", [])

    orch.confirm_ingredients(ingredients)
    orch.step_candidates()
    orch.step_enrich()
    bundle = orch.step_decide()

    # Map internal format to React-friendly format
    cart_items = [
        map_decision_to_cart_item(item, product_lookup, idx)
        for idx, item in enumerate(bundle.items)
    ]

    return CreateCartResponse(
        items=cart_items,
        total=sum(item.price for item in cart_items),
        store="FreshDirect",
        location="NJ"
    )
```

**What this does**:
1. Receives HTTP POST with meal plan text
2. Calls the exact same Orchestrator we use in Streamlit
3. Maps DecisionBundle → CartItem[] (React format)
4. Returns JSON

**CORS Configuration**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative React port
        "https://*.vercel.app",   # Production deployments
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Why CORS?** React runs on port 5173, API runs on port 8000. Browser needs permission for cross-origin requests.

Like getting a passport to travel between countries.

---

### The React Frontend: Pixel-Perfect Figma Implementation

**Location**: `/conscious-cart-coach/Figma_files/`

**Tech Stack**:
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Fast dev server and build tool
- **Tailwind CSS** - Utility-first styling
- **Figma design system** - Color palette, spacing, typography

**Key Files**:

**1. API Service** (`src/app/services/api.ts`)
```typescript
export async function createCart(mealPlan: string): Promise<CreateCartResponse> {
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const response = await fetch(`${API_BASE_URL}/api/create-cart`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ meal_plan: mealPlan }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create cart');
  }

  return response.json();
}
```

**2. Main App** (`src/app/App.tsx`)
```typescript
const [cartItems, setCartItems] = useState<CartItem[]>([]);
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState<string | null>(null);

const handleCreateCart = async () => {
  setIsLoading(true);
  setError(null);

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

**3. Components**:
- `MealPlanInput.tsx` - Text input + create button
- `Cart.tsx` - Shopping cart display
- `CartItem.tsx` - Individual product card
- `Preferences.tsx` - User settings modal

**Design System Colors** (from Figma):
```css
--primary-brown: #6b5f3a      /* Header background */
--cream: #fef9f5              /* Main background */
--beige-border: #e5d5b8       /* Card borders */
--text-dark: #2c2c2c          /* Primary text */
--accent-green: #4a7c59       /* Success/organic tags */
```

**Why React?**
- Full control over HTML/CSS
- Component reusability
- Strong TypeScript support
- Easier to match Figma pixel-perfect
- Better for production deployment

Like upgrading from IKEA furniture (Streamlit) to custom-built pieces (React).

---

### The HTML Demo: No Build Step Required

**Location**: `/conscious-cart-coach/demo.html`

**Purpose**: Standalone demo for hackathon judges who don't have Node.js installed.

**Features**:
- **Single file** - No npm install, no build step
- **Vanilla JavaScript** - No framework dependencies
- **Tailwind CDN** - Styling without build tools
- **Same API** - Calls the FastAPI backend
- **Full functionality** - Preferences modal, cart display, etc.

**Why this exists**:

Imagine you're at a hackathon demo table. A judge walks up. You have 2 minutes.

**Bad scenario**:
```bash
"Let me just npm install... wait, Node version... oh hold on..."
*5 minutes later*
"Okay, now npm run dev..."
*Judge has walked away*
```

**Good scenario**:
```bash
*Opens demo.html in browser*
*Works immediately*
"Here's how it works..."
*Judge is impressed*
```

**Implementation Snippet**:
```javascript
// Same API call, vanilla JS
async function createCart() {
  const mealPlan = document.getElementById('meal-plan-input').value;

  try {
    const response = await fetch('http://localhost:8000/api/create-cart', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ meal_plan: mealPlan }),
    });

    const data = await response.json();
    displayCart(data.items);
  } catch (error) {
    alert('Error: ' + error.message);
  }
}

// Preferences stored in localStorage
function savePreferences() {
  const prefs = {
    store: document.getElementById('store-select').value,
    servings: parseInt(document.getElementById('servings').value),
    complexity: document.querySelector('input[name="complexity"]:checked').value,
    // ... more preferences
  };

  localStorage.setItem('userPreferences', JSON.stringify(prefs));
}
```

**Design Fidelity**: Matches Figma prototype exactly
- Same color palette
- Same spacing/padding
- Same component layouts
- Same interaction patterns

Like having a printed menu (HTML) vs a tablet menu (React). Same content, different mediums.

---

### Deployment Strategy: Hackathon Production

**Frontend: Vercel**

```bash
cd Figma_files
vercel
```

**Why Vercel?**
- Free tier for demos
- Automatic HTTPS
- Git integration
- Instant deployments
- CDN for fast loading

**Backend: Railway**

```bash
railway login
railway init
railway up
```

**Why Railway?**
- Free tier with $5 credit
- Auto-detects Python + FastAPI
- Environment variable management
- Auto-scaling
- Built-in logging

**Environment Configuration**:

**Frontend** (`.env.local`):
```bash
VITE_API_URL=https://your-railway-app.railway.app
```

**Backend** (Railway environment variables):
```bash
ANTHROPIC_API_KEY=sk-ant-api03-...  # Optional, for LLM features
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app
```

**The Flow**:
```
User browser
  ↓
Vercel CDN (React app)
  ↓
Railway server (FastAPI)
  ↓
Orchestrator (business logic)
  ↓
SQLite (local to Railway instance)
```

**Cost Breakdown**:
- Vercel: $0 (free tier, plenty for demos)
- Railway: $0-5 (free tier + $5 credit)
- Anthropic: $0 if LLM disabled, ~$0.045/cart if enabled

**Total monthly cost for hackathon**: ~$5 max

Like running a pop-up restaurant. Low overhead, high impact.

---

### Data Mapping: Orchestrator → React

**Challenge**: The Orchestrator returns `DecisionItem` objects. React expects `CartItem` objects matching the Figma design.

**Solution**: Mapping function in FastAPI

```python
def map_decision_to_cart_item(
    item: DecisionItem,
    product_lookup: dict[str, dict],
    index: int
) -> CartItem:
    """
    Convert internal DecisionItem to React-friendly CartItem.
    """

    # Get product details
    product = product_lookup.get(item.selected_product_id, {})

    # Generate UI tags
    why_pick_tags = []
    trade_off_tags = []

    # Product attributes → why pick tags
    if product.get("organic"):
        why_pick_tags.append("Organic")
    if product.get("local"):
        why_pick_tags.append("Local")
    if "in season" in " ".join(item.attributes).lower():
        why_pick_tags.append("In Season")

    # Safety concerns → trade-off tags
    for note in item.safety_notes or []:
        if "dirty dozen" in note.lower():
            trade_off_tags.append("EWG Dirty Dozen")
        elif "recall" in note.lower():
            trade_off_tags.append("Recent recalls")

    return CartItem(
        id=f"item-{index}",
        name=product.get("title", item.ingredient_name),
        brand=product.get("brand", ""),
        price=product.get("price", 0),
        size=product.get("size", ""),
        image="https://images.unsplash.com/photo-...",  # Placeholder
        tags=CartItemTag(
            whyPick=why_pick_tags[:5],      # Max 5 tags
            tradeOffs=trade_off_tags[:4]    # Max 4 tags
        ),
        store="FreshDirect",
        location="NJ"
    )
```

**Why this mapping layer?**
1. **Separation of concerns**: Orchestrator doesn't know about UI needs
2. **Flexibility**: Can create different mappings for mobile vs web
3. **Evolution**: UI can change without touching core logic

Like a translator at the UN. Same content, different languages.

---

### The Benefits of This Architecture

**1. Multiple Frontends, One Engine**

```
Streamlit (for internal tools)
     │
     ├──► Orchestrator ◄──── FastAPI ◄──── React (for production)
     │                                │
     │                                └──── Mobile app (future)
     │
     └──► Jupyter notebooks (for data analysis)
```

Write the business logic once. Use it everywhere.

**2. Technology Flexibility**

Don't like React? Swap it for Vue or Svelte. The API contract stays the same.

Don't like Streamlit? Use Gradio or Dash. The Orchestrator doesn't care.

**3. Easier Testing**

```python
# Test the API endpoint
def test_create_cart_endpoint():
    response = client.post("/api/create-cart", json={"meal_plan": "biryani"})
    assert response.status_code == 200
    assert len(response.json()["items"]) > 0

# Test the Orchestrator directly
def test_orchestrator():
    orch = Orchestrator()
    bundle = orch.process_prompt("biryani")
    assert len(bundle.items) > 0
```

Can test API and business logic separately.

**4. Performance Optimization**

- React: Lazy load components, code splitting
- FastAPI: Async endpoints, connection pooling
- Orchestrator: Unchanged (already optimized)

Each layer can be optimized independently.

**5. Deployment Flexibility**

- **Dev**: Run everything locally (FastAPI + Vite + Streamlit)
- **Staging**: Deploy API to Railway, frontend to Vercel
- **Prod**: Add CDN, database replication, load balancers

Start simple, scale when needed.

---

### What We Learned

**1. Don't throw away working code**

We didn't rewrite the Orchestrator. We just added an API layer. All the agent logic, decision engine, facts store—unchanged.

**2. Start with the simplest thing that works**

Streamlit got us to MVP fast. When we needed more control, we added React. Incremental evolution.

**3. Separation of concerns pays off**

Because the Orchestrator was decoupled from the UI, switching from Streamlit to React was straightforward. No business logic changes needed.

**4. Demo-first architecture**

The HTML demo was an afterthought that became crucial. Always think about "How would someone demo this in 2 minutes?"

**5. Cost matters**

By making LLM optional and using free tiers (Vercel, Railway), we can run a full production demo for ~$0-5/month. This matters for hackathons and MVPs.

---

## Further Reading

- [LLM Integration Deep Dive](6-llm-integration-deep-dive.md) - How we blend AI and rules
- [UI Flows](7-ui-flows.md) - What the user sees and clicks
- [Data Flows](8-data-flows.md) - Follow the data through the system
- [Opik LLM Evaluation](9-opik-llm-evaluation.md) - Testing and improving LLM features

---

*"Architecture is the decisions you wish you could make at the beginning of a project, but usually only learn by the end." - Unknown*

*"Fortunately, we got most of them right. And the ones we got wrong are easy to fix." - Us, being honest*

*"The best code is the code you don't have to rewrite. The second best code is the code that's easy to rewrite." - Us, after building three UIs*
