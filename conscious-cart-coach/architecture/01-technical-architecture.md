# Technical Architecture: The Brain Behind Conscious Shopping

## The Big Picture: A Shopping Cart with a Conscience

Imagine you're planning to cook chicken biryani for your family. You tell a helpful friend what you want to make, and they don't just hand you a generic shopping list. Instead, they think about:
- Which stores carry authentic Indian spices vs. fresh ingredients
- Whether you should buy the small jar or bulk size based on the recipe
- If paying extra for organic makes sense for this particular ingredient
- Whether a local co-op has better quality produce than the big chain store

That's exactly what Conscious Cart Coach does - it's like having a thoughtful friend who knows your values, understands food quality, and shops strategically across multiple stores.

## The Stack: Why We Built It This Way

### Backend: Python + FastAPI
**The Decision**: We chose Python with FastAPI because grocery shopping is fundamentally about data processing and decision-making, not real-time performance.

**The Reality**:
- **Product matching** requires fuzzy logic and ranking algorithms (think "is '365 Organic Chicken Breast' the same as what the recipe needs?")
- **Multi-store optimization** needs to evaluate hundreds of products across stores
- **Future LLM integration** works naturally with Python's AI/ML ecosystem

FastAPI specifically gives us:
- Automatic API documentation (visit `/docs` to see it)
- Type safety with Pydantic models
- Async support for when we add LLM calls

### Frontend: React + TypeScript + Vite
**The Decision**: Modern React with TypeScript because grocery carts need responsive, interactive UIs.

**The Reality**:
- Users need to **see their cart update in real-time** as they adjust quantities
- **Multi-store carts** require complex UI state (FreshDirect items vs. Pure Indian Foods items)
- TypeScript catches bugs before users see them (mixing up `price` and `quantity` would be bad)

Vite gives us instant hot-reload - change the code, see it immediately. No waiting around.

### Data Layer: CSV Files (For Now)
**The Pragmatic Choice**: We're using CSV files to store product listings.

**Why Not a Database?**
- **Speed of iteration**: Change a price, update the CSV, reload. No migrations.
- **Human-readable**: Open `source_listings.csv` and you can see exactly what products exist
- **Version control**: Git tracks every change to our inventory

**The Future**: When we hit 10,000+ products or need user accounts, we'll migrate to PostgreSQL. But right now, CSV is the right tool.

## The Architecture: How the Pieces Connect

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INTERFACE                          │
│  "I want to make chicken biryani for 4 people"              │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                          │
│  ┌──────────────────┐        ┌──────────────────┐          │
│  │  MealPlanInput   │        │  ShoppingCart    │          │
│  │  Component       │───────▶│  Component       │          │
│  └──────────────────┘        └──────────────────┘          │
│         │                              ▲                     │
│         │ POST /create-cart            │ Display results    │
└─────────┼──────────────────────────────┼─────────────────────┘
          │                              │
          ▼                              │
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND API (FastAPI)                      │
│                                                               │
│  /create-cart endpoint                                       │
│         │                                                     │
│         ▼                                                     │
│  ┌──────────────────┐                                       │
│  │  Orchestrator    │  "The Conductor"                      │
│  │                  │  Coordinates all the agents           │
│  └────────┬─────────┘                                       │
│           │                                                   │
│           ├──────────┐──────────┐──────────┐                │
│           │          │          │          │                 │
│           ▼          ▼          ▼          ▼                 │
│     ┌─────────┐ ┌────────┐ ┌────────┐ ┌────────┐           │
│     │Ingredient│ │Product │ │Quantity│ │Explain │           │
│     │ Agent   │ │ Agent  │ │ Agent  │ │ Agent  │           │
│     └─────────┘ └────────┘ └────────┘ └────────┘           │
│                                                               │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                │
│                                                               │
│  ┌──────────────────────────────────────────────┐           │
│  │  source_listings.csv                          │           │
│  │  353 products across multiple stores:        │           │
│  │  - FreshDirect (produce, proteins, pantry)   │           │
│  │  - Whole Foods (organic options)             │           │
│  │  - Pure Indian Foods (specialty spices)      │           │
│  └──────────────────────────────────────────────┘           │
│                                                               │
│  ┌──────────────────────────────────────────────┐           │
│  │  Store-exclusive brand mapping:               │           │
│  │  "365 by Whole Foods" → Only at Whole Foods  │           │
│  │  "Pure Indian Foods" → Only at Pure Indian   │           │
│  └──────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## The Agent Pattern: Divide and Conquer

### Why Agents?
Shopping involves multiple types of expertise:
1. **Understanding what ingredients you need** (Ingredient Agent)
2. **Finding which products match those ingredients** (Product Agent)
3. **Calculating how much to buy** (Quantity Agent)
4. **Explaining the choices** (Explain Agent)

Each agent is a specialist. The Orchestrator coordinates them.

### The Flow: From "Chicken Biryani" to Shopping Cart

**Step 1: Ingredient Extraction**
```
User input: "chicken biryani for 4"
Ingredient Agent:
  - Parses the meal description
  - Identifies: chicken, basmati rice, onions, tomatoes,
    ginger, garlic, cumin, coriander, cardamom, cinnamon...
  - Estimates quantities based on serving size (4 people)
```

**Step 2: Product Matching**
```
Product Agent:
  For each ingredient:
    1. Search source_listings.csv
    2. Filter by store (if target_store specified)
    3. Filter out store-exclusive brands from wrong stores
    4. Rank by quality tier (cheaper/balanced/conscious)
    5. Select best match
```

**Step 3: Quantity Optimization**
```
Quantity Agent:
  Recipe needs: 2 tsp cardamom
  Found product: Cardamom Green, 2oz jar
  Calculation:
    - 2oz = ~16 tsp of whole cardamom
    - Recipe needs 2 tsp
    - One jar covers this recipe 8x
    - Recommendation: Buy qty=1 (smallest size)
```

**Step 4: Cart Assembly**
```
Orchestrator:
  - Combines all products
  - Groups by store (multi-store splitting)
  - Adds metadata (tags, reasons, trade-offs)
  - Returns structured cart to frontend
```

## Key Technical Decisions: The "Why" Behind the "What"

### 1. No Database (Yet)
**Why**: We're in the "figure out what works" phase. CSV files let us iterate fast. When we scale to 10K+ products or add user accounts, we'll migrate to PostgreSQL.

**Trade-off**: Can't handle concurrent writes or complex queries. That's fine for now.

### 2. Agent-Based Architecture
**Why**: Each agent can be upgraded independently. When we add LLM calls, we can enhance the Ingredient Agent without touching the Product Agent.

**Trade-off**: More code complexity than a monolithic approach. Worth it for flexibility.

### 3. Store Filtering at Product Agent Level
**Why**: The Product Agent knows which products exist at which stores. It's the right place to enforce "365 brand only at Whole Foods" rules.

**Trade-off**: Can't easily answer "show me all stores that carry cardamom." We'd need a reverse index. Not needed yet.

### 4. Frontend State Management (React State)
**Why**: The cart UI is complex (multi-store, quantities, tags, modals) but doesn't need global state management yet.

**Trade-off**: If we add user authentication or shopping history, we'll need Redux/Zustand. For now, local component state is simpler.

### 5. TypeScript Everywhere
**Why**: Catching bugs at compile time saves user frustration. Mixing up `price: number` and `price: string` breaks carts.

**Trade-off**: Slightly slower development. Worth it for reliability.

## The File Structure: Where Everything Lives

```
conscious-cart-coach/
├── api/
│   └── main.py                 # FastAPI app, all HTTP endpoints
│
├── src/
│   ├── agents/
│   │   ├── ingredient_agent.py # Extracts ingredients from text
│   │   ├── product_agent.py    # Matches products to ingredients
│   │   ├── quantity_agent.py   # Calculates optimal quantities
│   │   └── explain_agent.py    # Generates explanations
│   │
│   ├── orchestrator/
│   │   └── orchestrator.py     # Coordinates all agents
│   │
│   └── utils/
│       └── store_split.py      # Multi-store cart splitting logic
│
├── data/
│   ├── alternatives/
│   │   └── source_listings.csv # Main product database (353 products)
│   │
│   └── samples/
│       ├── freshdirect_chicken_sample.tsv
│       ├── wholefoods_chicken_sample.tsv
│       └── kesar_grocery_sample.tsv
│
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── App.tsx                  # Main application component
│       │   ├── components/
│       │   │   ├── MealPlanInput.tsx    # Left panel: user input
│       │   │   ├── ShoppingCart.tsx     # Right panel: cart display
│       │   │   ├── CartItemCard.tsx     # Individual product card
│       │   │   ├── MultiStoreCart.tsx   # Multi-store cart view
│       │   │   └── ...modals & overlays
│       │   │
│       │   ├── types.ts                 # TypeScript interfaces
│       │   └── services/
│       │       └── api.ts               # Backend API calls
│       │
│       └── styles/
│           └── tailwind.css             # Styling
│
└── architecture/
    └── *.md                             # This documentation
```

## Technologies & Tools

### Backend Stack
- **Python 3.11+**: Modern Python with type hints
- **FastAPI 0.104+**: Fast, modern API framework
- **Pydantic**: Data validation using Python type annotations
- **Pandas**: CSV reading and data manipulation
- **uvicorn**: ASGI server for FastAPI

### Frontend Stack
- **React 18**: Component-based UI
- **TypeScript 5**: Type-safe JavaScript
- **Vite 5**: Build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework
- **Shadcn/ui**: Pre-built UI components
- **Lucide React**: Icon library

### Development Tools
- **Git**: Version control
- **VS Code**: Primary IDE (assumed based on Claude Code integration)
- **npm**: Package management (frontend)
- **pip**: Package management (backend)

## What's Coming Next: The LLM Integration

**Current State**: All logic is rule-based (if/else, fuzzy matching, heuristics)

**Future State**: LLM-enhanced agents
- **Ingredient Agent**: LLM parses "I want to make grandma's chicken curry" → understands regional variations
- **Product Agent**: LLM helps match ambiguous ingredients ("curry powder" → suggests specific blends)
- **Explain Agent**: LLM generates natural language explanations ("I chose this cardamom because...")

**Why Not LLM From Day 1?**
1. **Cost**: LLM calls cost money. Get the logic right first.
2. **Determinism**: Rule-based systems are predictable. Good for debugging.
3. **Speed**: Local logic is instant. LLM calls take 1-3 seconds.

**The Hybrid Approach**: Use rules for most decisions, LLM for the hard ones (ambiguous parsing, explanation generation).

## Performance Considerations

### Current Performance
- **Cart generation**: ~100-300ms (rule-based)
- **API response time**: <500ms (including network)
- **Frontend render**: <100ms (React is fast)

### Bottlenecks to Watch
1. **CSV loading**: Currently loads entire file into memory. Fine for 353 products, problematic at 10K+.
2. **Product matching**: O(n) search through products. Need indexing at scale.
3. **LLM calls** (future): Will add 1-3 seconds per agent call. Need caching & batching.

### Optimization Strategy
1. **Now**: Keep it simple. Premature optimization is evil.
2. **At 1K products**: Add in-memory indexing (dicts/sets)
3. **At 10K products**: Migrate to PostgreSQL with proper indexes
4. **With LLM**: Add Redis caching for common queries

## Error Handling Philosophy

**Frontend**: Fail gracefully with user-friendly messages
```typescript
try {
  const cart = await createCart(mealPlan);
} catch (error) {
  showError("Couldn't create your cart. Try again?");
}
```

**Backend**: Be explicit about what failed
```python
try:
  products = product_agent.get_candidates(ingredients)
except ProductNotFoundError as e:
  return {"error": f"Couldn't find product for {e.ingredient}"}
```

**Data Layer**: Validate early
```python
# Pydantic models catch bad data before it reaches agents
class CartItem(BaseModel):
  price: float  # Will fail if price is string or negative
  quantity: int  # Will fail if quantity is float or zero
```

## The Conscious Buyer Philosophy (Embedded in Code)

This isn't just a shopping cart. The code embodies values:

1. **Organic where it matters** (Dirty Dozen prioritization)
2. **Local when possible** (Lancaster Farm Fresh Cooperative preference)
3. **Authentic for specialty items** (Pure Indian Foods for spices, not FreshDirect)
4. **Economical but not cheap** (smallest appropriate size, not bulk unless needed)

These aren't just marketing - they're implemented in the Product Agent's ranking algorithm, the quantity calculations, and the store filtering logic.

---

**Next**: [LLM Integration Strategy](./02-llm-integration.md) - How AI will enhance each agent
