# CONSCIOUS CART COACH - COMPREHENSIVE GUIDE

> **Updated**: 2026-01-29
> **Current Version**: React + FastAPI Full-Stack (v2.0)
> **Note**: Optional LLM features available. See [2-llm-integration-summary.md](2-llm-integration-summary.md) and [4-ui-expectations.md](4-ui-expectations.md).
> **Architecture**: Deterministic by default, optional LLM enhancement (Claude for natural language and explanations).
>
> ⚠️ **Historical Note**: References to Streamlit in this document are from v1.0. Current version uses React frontend.

## 🎯 HIGH LEVEL OVERVIEW

### What Problem Does This Solve?

You're standing in a grocery store with a shopping list. You want to make healthier, more ethical choices, but:
- Which produce has pesticide residues? (EWG Dirty Dozen)
- Are there any recalls on this lettuce brand?
- Is this fruit even in season?
- What's the best value between organic vs conventional?
- Should I spend $4 or $7 on this ingredient?

**Conscious Cart Coach** is a rule-based shopping assistant that helps you make informed grocery decisions across three tiers:

- 💸 **Cheaper**: Budget-focused options
- ⚖️ **Balanced**: Middle ground - value + quality
- 🌍 **Conscious**: Premium/ethical choices (organic, local, sustainable)

### Who Is This For?

- Health-conscious shoppers who want to avoid pesticide-heavy produce
- Budget-aware families who want to optimize spending
- Environmentally conscious consumers preferring local/seasonal options
- Anyone who wants to make informed tradeoffs (price vs health vs ethics)

### How Does It Work?

1. **Input**: "I want to make chicken biryani for 4 people" (or with LLM: "I want something healthy and seasonal")
2. **Extract**: Template-based OR LLM-powered ingredient extraction (optional)
3. **Match**: System finds products from local stores (ShopRite, Whole Foods, etc.)
4. **Enrich**: Adds safety data (EWG, FDA recalls), seasonality info
5. **Decide**: Deterministic scoring engine recommends tiers (cheaper/balanced/conscious)
6. **Explain**: Optional LLM-generated explanations (why this pick, what are tradeoffs)
7. **Output**: 3 shopping carts side-by-side with price comparisons

**Key Features**:
- Every recommendation comes with **traceable reasoning** - why this tier? What are the tradeoffs?
- **Two modes**: Deterministic (free, fast) or LLM-enhanced (natural language + detailed explanations, ~$0.045/cart)

---

## 🏗️ MIDDLE LEVEL - ARCHITECTURE

### System Architecture (Two-Layer Design)

The project has **two parallel codebases** that work together:

```
Root Level (/src/)                  Backend (/conscious-cart-coach/src/)
─────────────────                   ─────────────────────────────────────
Frontend Integration                Core Orchestration Engine
↓                                   ↓
data_processing/                    orchestrator/orchestrator.py
  seasonal_regional.py              agents/ (12 agent types)
                                    engine/decision_engine.py (deterministic)
                                    contracts/models.py
                                    facts/facts_gateway.py
                                    ui/app.py (ACTIVE Streamlit UI)
```

### Data Flow Pipeline (6 Stages)

```
1. INGREDIENT EXTRACTION
   User: "chicken biryani for 4" OR "I want something healthy" (natural language)
   ↓ [IngredientAgent]
   - Deterministic: Template matching (4 hardcoded recipes)
   - Optional LLM: Claude extracts ingredients from any prompt
   Output: [{name: "miso_paste", category: "miso_paste", quantity: "3 tbsp"}]

2. PRODUCT MATCHING
   ↓ [ProductAgent]
   Searches inventory for "miso_paste" alternatives
   Output: [ProductCandidate(title="Organic White Miso", price=6.99, unit_price=0.87/oz)]

3. ENRICHMENT (Parallel)
   ↓ [SafetyAgent + SeasonalAgent]
   - EWG classification (Dirty Dozen? Clean Fifteen?)
   - FDA recall status (any recent recalls?)
   - Seasonality (in-season? local availability?)

4. DECISION ENGINE (Deterministic Scoring)
   ↓ [DecisionEngine]
   Two-stage: Hard constraints → Soft scoring (100% deterministic)
   Output: DecisionBundle with scores, tiers, and deterministic reasons

5. EXPLANATION GENERATION (Optional)
   ↓ [LLM Decision Explainer]
   - If enabled: Claude generates 1-2 sentence natural language explanations
   - If disabled: Uses deterministic reason_short (3-5 words)
   Output: reason_llm populated for each item

6. DISPLAY
   ↓ [Streamlit UI]
   - 3-tier cart view (cheaper/balanced/conscious)
   - Expandable AI explanations (if LLM enabled)
   - LLM indicators and toggles
```

### Key Agents (Multi-Agent System)

| Agent | Purpose | Output |
|-------|---------|--------|
| **IngredientAgent** | Extracts ingredients (template or LLM) | `List[IngredientSpec]` with extraction method |
| **ProductAgent** | Matches ingredients to store inventory | `Dict[ingredient, List[ProductCandidate]]` |
| **SafetyAgent** | Checks EWG lists, FDA recalls | `RecallSignal` per product |
| **SeasonalAgent** | Checks NJ crop calendar, local sourcing | Seasonality score |
| **UserHistoryAgent** | Learns user's tier preferences over time | Preference weights |
| **DecisionEngine** | Scores products deterministically, optionally adds LLM explanations | `DecisionBundle` with reason_short + reason_llm |
| **DecisionEngine** | Scores products, assigns tiers | `DecisionBundle` |

### Decision Logic (Deterministic Engine)

**Two-Stage Scoring System** (100-point scale)

- **Stage 1 (Hard Constraints)**: Disqualifies products with:
  - Active recalls (`product_match = true`)
  - User's avoided brands
  - Dirty Dozen without organic (in strict mode)

- **Stage 2 (Soft Scoring)**:
  ```
  Base: 50 points
  + EWG Dirty Dozen (organic): +5
  - EWG Dirty Dozen (no organic): -20
  + Seasonality (peak): +15
  + Organic: +8
  + Local brand: +6
  - Recall advisory: -5 to -10
  + Best value efficiency: +12
  + Matches preferred brand: +10
  ```

**Tier Assignment**: Based on final scores, the engine selects:
- `recommended` = highest-scoring product
- `cheaper_neighbor` = best product with lower unit price (min score 30)
- `conscious_neighbor` = best product with higher unit price or organic status

### Data Sources (Auto-Refreshing)

| Source | Refresh Frequency | Location |
|--------|-------------------|----------|
| EWG Dirty Dozen/Clean 15 | Annual | `data/flags/ewg_lists.csv` |
| FDA Recalls | Daily | `data/flags/fda_recalls.csv` |
| NJ Crop Calendar | Annual | `data/seasonal/nj_crop_calendar.csv` |
| Store Inventory | Monthly | `data/stores/nj_middlesex_stores.csv` |
| Product Alternatives | As needed | `data/alternatives/` |

The system checks staleness on startup and auto-refreshes from CSV files.

---

## 🔧 TECHNICAL LEVEL - IMPLEMENTATION DETAILS

### Project Structure

```
ConsciousBuyer/
├── .env                              # API keys (ANTHROPIC_API_KEY)
├── README.md                         # Root-level README
│
├── src/                              # Root-level utilities
│   └── data_processing/
│       └── seasonal_regional.py      # Regional/seasonal utilities
│
├── conscious-cart-coach/             # Core Backend Engine
│   ├── run.sh                        # Startup script (sets PYTHONPATH, runs Streamlit)
│   ├── requirements.txt              # Python dependencies
│   ├── environments.yml              # Conda environment config
│   ├── DEV_NOTE.md                   # Architecture decisions (MUST READ)
│   ├── README.md                     # Backend documentation
│   │
│   ├── data/                         # All data sources
│   │   ├── facts_store.db            # SQLite database (auto-generated)
│   │   ├── processed/                # Normalized purchase history
│   │   │   ├── items.csv
│   │   │   ├── purchases.csv
│   │   │   └── categories.csv
│   │   ├── flags/                    # Safety data
│   │   │   ├── ewg_lists.csv         # Dirty Dozen/Clean Fifteen
│   │   │   └── fda_recalls.csv       # Recall data
│   │   ├── seasonal/                 # Seasonality data
│   │   │   ├── nj_crop_calendar.csv
│   │   │   └── trusted_regional_sources.csv
│   │   └── stores/
│   │       └── nj_middlesex_stores.csv
│   │
│   ├── outputs/                      # CSV exports for debugging
│   │
│   ├── src/
│   │   ├── contracts/
│   │   │   └── models.py             # Typed dataclasses (CRITICAL)
│   │   │       # ProductCandidate, DecisionBundle, IngredientSpec, RecallSignal
│   │   │
│   │   ├── orchestrator/
│   │   │   └── orchestrator.py       # State machine coordinator
│   │   │
│   │   ├── agents/                   # Multi-agent system
│   │   │   ├── ingredient_agent.py   # NLP extraction
│   │   │   ├── product_agent.py      # Inventory matching (tier-free)
│   │   │   ├── safety_agent_v2.py    # EWG + recall checks
│   │   │   ├── seasonal_agent.py     # Seasonality scoring
│   │   │   └── user_history_agent.py # Preference learning
│   │   │
│   │   ├── engine/
│   │   │   └── decision_engine.py    # Deterministic scoring engine
│   │   │
│   │   ├── facts/
│   │   │   └── facts_gateway.py      # Single data access point
│   │   │
│   │   ├── data/
│   │   │   ├── facts_store.py        # SQLite wrapper
│   │   │   └── refresh_jobs.py       # Auto-refresh logic
│   │   │
│   │   ├── exporters/
│   │   │   └── csv_exporter.py       # Debug exports
│   │   │
│   │   └── ui/
│   │       └── app.py                # STUB (42 lines) - use root-level instead
│   │
│   └── tests/
│       ├── test_pipeline.py          # 32 integration tests
│       ├── test_decision_engine.py
│       └── test_categorize.py
│
├── PromptsResponses/                 # Design docs & specs
│   ├── 1_AppStructure.md
│   ├── 10_DecisionUI.md              # DecisionUI specifications
│   └── [2-9].md                      # Feature design docs
│
└── tests/                            # Root-level tests
```

### Key Files You MUST Understand

| File Path | Lines | Purpose | When to Touch |
|-----------|-------|---------|---------------|
| `conscious-cart-coach/src/contracts/models.py` | ~300 | All typed contracts | Adding new data fields |
| `conscious-cart-coach/src/orchestrator/orchestrator.py` | ~400 | Flow coordination | Changing pipeline stages |
| `conscious-cart-coach/src/engine/decision_engine.py` | ~500 | Deterministic scoring | Tweaking scoring rules |
| `conscious-cart-coach/src/ui/app.py` | 563 | Main Streamlit UI | UI changes |
| `conscious-cart-coach/src/ui/components.py` | ~200 | Reusable UI components | Adding new UI elements |
| `conscious-cart-coach/DEV_NOTE.md` | 94 | Architecture decisions | Understanding "why" |

### Core Data Models (TypeScript-Style)

```python
@dataclass
class ProductCandidate:
    """A product that could fulfill an ingredient (tier-agnostic)"""
    product_id: str
    ingredient_name: str
    title: str                    # "Organic Baby Spinach"
    brand: str                    # "Earthbound Farm"
    size: str                     # "5oz"
    price: float                  # 3.99
    unit_price: float             # 0.80 (per oz)
    organic: bool
    in_stock: bool
    metadata: dict

@dataclass
class RecallSignal:
    """Nuanced recall assessment (not binary)"""
    product_match: bool           # Direct recall (disqualify)
    category_advisory: "none" | "recent" | "elevated"  # Soft penalty
    confidence: "high" | "medium" | "low"
    data_gap: bool                # Insufficient data

@dataclass
class DecisionItem:
    """A single tier recommendation for an ingredient"""
    ingredient_name: str
    recommended: ProductCandidate
    cheaper_neighbor: ProductCandidate | None
    conscious_neighbor: ProductCandidate | None
    reason_short: str             # Why this tier?
    safety_flags: list[str]
    seasonal_status: str

@dataclass
class DecisionBundle:
    """Complete recommendations for all ingredients"""
    items: list[DecisionItem]
    tier_totals: dict             # {"cheaper": 45.50, "balanced": 67.80}
    cart_delta: float             # How much more/less than balanced
    timestamp: str
```

### Dependencies (Python 3.10+)

**Core:**
- `pandas` (data processing)
- `sqlalchemy` + `psycopg2-binary` (database)
- `anthropic` (Claude API)
- `streamlit` (web UI)

**Observability:**
- `opik` (LLM tracing, evaluation, and cost monitoring - see [9-opik-llm-evaluation.md](9-opik-llm-evaluation.md))

**Testing:**
- `pytest` + `pytest-cov`

### Design Patterns

1. **Agent Result Contract** - All agents return:
   ```python
   AgentResult(
       agent_name="safety",
       status="ok",
       facts={...},            # Agent-specific data
       explain=["...", ...],   # Max 5 bullets for UI
       evidence=[Evidence()],  # Traceable sources
       timestamp="2025-01-24T..."
   )
   ```

2. **Gated Orchestrator** - State machine with explicit gates:
   ```python
   IDLE → INGREDIENTS_EXTRACTED → [GATE] → PRODUCTS_MATCHED →
   ENRICHED → DECIDED → [GATE] → EXPORTED
   ```

3. **Tier-Free Candidates** - ProductAgent doesn't assign tiers
   - Returns candidates sorted by `unit_price`
   - DecisionEngine assigns tiers dynamically
   - Decouples data fetching from decision logic

4. **Two-Stage Scoring** - Hard constraints then soft scoring
   - Stage 1: Binary filters (recalls, avoided brands)
   - Stage 2: Continuous scoring (0-100 scale)

5. **Neighbor Selection** - Always shows 3 tiers per ingredient:
   - `recommended` = highest score
   - `cheaper_neighbor` = best option with lower `unit_price` (min score 30)
   - `conscious_neighbor` = best option with higher `unit_price` or organic

### Testing Strategy

```bash
# Run all tests
cd conscious-cart-coach
python -m pytest tests/ -v

# Test coverage
pytest --cov=src

# Specific test suites
pytest tests/test_pipeline.py -v          # 32 integration tests
pytest tests/test_decision_engine.py -v   # Scoring logic tests
```

**Test Coverage:**
- Unit price normalization (oz, lb, g, kg, dozen)
- ProductAgent (candidates, sorting, no tier labels)
- DecisionEngine constraints (recalls, avoided brands, strict safety)
- DecisionEngine scoring (EWG penalties, seasonality)
- Orchestrator gating (state transitions)
- Bundle generation (cart totals, deltas)

---

## 🚀 SETUP GUIDE - NEW COMPUTER

### Prerequisites

- Python 3.10 or higher
- Git
- Anthropic API key (optional - only for LLM features)

### Option 1: pip (Recommended)

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd ConsciousBuyer

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
cd conscious-cart-coach
pip install -r requirements.txt

# 4. Configure environment (optional for LLM features)
cp ../.env.example ../.env  # Or create new
# Edit .env and add your API key if using LLM:
# ANTHROPIC_API_KEY=sk-ant-api03-...
# Note: System works without API key in deterministic mode

# 5. Verify setup
python -m pytest tests/ -v

# 6. Run the application
./run.sh
```

### Option 2: conda

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd ConsciousBuyer/conscious-cart-coach

# 2. Create conda environment
conda env create -f environments.yml
conda activate consciousbuyer

# 3. Configure .env (see step 4 above)

# 4. Run
./run.sh
```

### What `run.sh` Does

```bash
#!/bin/bash
export PYTHONPATH="${PYTHONPATH}:$(dirname "$0")/src"
export $(cat .env | grep -v '^#' | xargs)
streamlit run src/ui/app.py "$@"
```

- Sets Python path to include `src/` directory
- Loads environment variables from `.env`
- Launches Streamlit UI

### First Run

1. **Database Initialization**: On first run, `facts_store.db` will be created automatically
2. **Data Refresh**: System auto-imports CSV data from `data/` directory
3. **UI Launch**: Streamlit opens at `http://localhost:8501`

### Troubleshooting

**Issue: ModuleNotFoundError**
```bash
# Ensure you're in the right directory
cd conscious-cart-coach
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

**Issue: SQLite errors**
```bash
# Delete and regenerate database
rm data/facts_store.db
python -c "from src.data.facts_store import FactsStore; FactsStore()"
```

**Issue: Anthropic API errors (only if using LLM features)**
```bash
# Check .env file exists and has valid key
cat ../.env  # Should show ANTHROPIC_API_KEY=sk-ant-...

# Or disable LLM features in UI:
# Go to Preferences → Uncheck "Enable AI ingredient extraction" and "Enable detailed explanations"
```

### Development Workflow

```bash
# Run with auto-reload (Streamlit watches for changes)
./run.sh

# Run tests in watch mode
pytest-watch tests/

# Type checking (if using mypy)
mypy src/

# Export debug CSVs
python -m src.cli.facts_inspector status
python -m src.cli.facts_inspector ewg spinach
```

---

## 🎨 UI FEATURES AND LLM INTEGRATION

### Using the Streamlit UI

The UI has two modes, controlled by toggles in the **Preferences** popover:

#### Deterministic Mode (Default)
- **Free, fast, no API calls**
- Template-based ingredient extraction (4 hardcoded recipes)
- Rule-based scoring (100% deterministic)
- Terse explanations (3-5 words: "Best value per oz")

**How to use:**
1. Enter a known recipe: "chicken biryani for 4", "spinach salad", "stir fry"
2. Click "Create cart"
3. Review and confirm ingredients
4. See 3-tier recommendations with price comparisons

#### LLM-Enhanced Mode (Optional)
- **~$0.045 per cart, adds 2-4 seconds**
- Natural language ingredient extraction
- Detailed AI-powered explanations (1-2 sentences)
- Scoring still 100% deterministic

**How to enable:**
1. Click "⚙️ Preferences" in the top-left
2. Scroll to **🤖 AI Features** section
3. Check "Enable AI ingredient extraction" (for natural language prompts)
4. Check "Enable detailed explanations" (for rich reasoning)
5. Close preferences

**Now you can use:**
- "I want something healthy and seasonal for dinner"
- "Quick weeknight meal for 2"
- "Budget-friendly vegetarian options"

### UI Components for LLM

When LLM features are enabled, you'll see:

**In Ingredient Modal:**
- 🤖 AI badge: "AI extracted from your request"
- Shows extraction method used

**In Product Cards:**
- Quick reason (deterministic): "Organic recommended (EWG)"
- "🤖 Show AI explanation" expander (when available)
- Clicking expander reveals 1-2 sentence natural language explanation

**Example Product Card with LLM:**
```
Spinach
⚖️ Your pick

Why this pick: Organic recommended (EWG)

[🤖 Show AI explanation ▼]

"The Earthbound Farm option at $3.99 offers organic
 certification which is important for spinach since it's
 on the EWG Dirty Dozen list for high pesticide residue.
 While it costs $2 more than the conventional option,
 you're avoiding 3-5 common pesticide residues."

Earthbound Farm — Organic Baby Spinach
$3.99 · 5oz · $0.80/oz
Organic · In Season · EWG recommends organic
```

### Cost and Performance

| Mode | Cost | Latency | Prompts Supported |
|------|------|---------|-------------------|
| Deterministic | $0 | <100ms | 4 recipes (biryani, salad, stir fry, tikka) |
| LLM Extraction Only | ~$0.01 | +1-3 sec | Unlimited natural language |
| Full LLM | ~$0.045 | +2-4 sec | Unlimited + detailed explanations |

**Recommended approach**: Start with deterministic mode. Enable LLM only when you need natural language prompts or detailed explanations.

---

## 📋 KEY CONCEPTS TO REMEMBER

### 1. Two Codebases, One System
- **Root `/src/`**: Frontend, LLM integration, validation
- **`/conscious-cart-coach/src/`**: Core engine, agents, orchestration

### 2. Tier-Free Until Decision Time
- ProductAgent doesn't assign tiers anymore
- DecisionEngine dynamically computes tiers from candidate pool
- This decouples data fetching from decision logic

### 3. Hard Constraints → Soft Scoring
- Stage 1: Binary filters (recalls, avoided brands, strict safety)
- Stage 2: Continuous scoring (EWG, seasonality, organic, brand)

### 4. Optional LLM Enhancement
- **Default**: Deterministic (template extraction, rule-based scoring, terse explanations)
- **Optional**: LLM ingredient extraction (natural language understanding)
- **Optional**: LLM explanations (detailed reasoning for recommendations)
- Scoring is ALWAYS deterministic - LLM only enhances input/output UX

### 5. Evidence-Based Everything
- Every recommendation has `evidence` field
- Traceable to source (EWG, FDA, crop calendar)
- UI displays reasoning + validation results

### 6. Auto-Refreshing Data
- FactsGateway checks staleness on init
- Auto-imports from CSV if data is stale
- Configurable refresh windows (24h for recalls, annual for EWG)

---

## 🎓 NEXT STEPS FOR YOU

1. **Read** `conscious-cart-coach/DEV_NOTE.md` - Explains key architectural decisions
2. **Run** `./run.sh` - Get hands-on with the UI
3. **Explore** `conscious-cart-coach/src/contracts/models.py` - Understand data structures
4. **Test** `pytest tests/test_pipeline.py -v` - See how it all works together
5. **Trace** a full flow: Start from `conscious-cart-coach/src/ui/app.py` → follow to orchestrator → agents → decision engine

### Current Branch Context

You're on `DecisionUI-1` branch. Recent commits:
- `decisionui` - Latest DecisionUI work
- `Validator` - LLM output validation
- `LLMReasoning` - Claude integration
- `Rules` - Rule-based fallback

Main branch is `main` (use for PRs).

### Questions to Ask Yourself

1. How does a user input flow from Streamlit to final recommendations?
2. How are EWG Dirty Dozen items handled differently in the scoring system?
3. What's the difference between a "recall" and a "category advisory"?
4. Why doesn't ProductAgent assign tiers anymore?
5. How does the two-stage scoring system (hard constraints → soft scoring) work?

**You now have everything you need to continue development!** 🚀
