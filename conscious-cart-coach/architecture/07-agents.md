# Agents Architecture

> **Purpose**: Document all agents in Conscious Cart Coach, their responsibilities, and how they work together.

## Overview

Conscious Cart Coach uses a multi-agent architecture where each agent has a specific responsibility. Agents communicate through a shared contract system (`AgentResult`) and are orchestrated by the `Orchestrator`.

## Agent Pipeline

```
User Prompt: "chicken biryani for 4"
         │
         ▼
┌─────────────────────┐
│   IngredientAgent   │  Extract: chicken, basmati rice, onion, yogurt, ginger, garlic...
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│    ProductAgent     │  Find candidates: Bell & Evans Chicken, Tilda Basmati Rice...
└─────────────────────┘
         │
         ├──────────────────────┐
         ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│   SafetyAgent   │    │  SeasonalAgent  │   (parallel enrichment)
└─────────────────┘    └─────────────────┘
         │                      │
         └──────────┬───────────┘
                    ▼
         ┌─────────────────────┐
         │   DecisionEngine    │  Score, rank, select best products
         └─────────────────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │  UserHistoryAgent   │  Record selections, learn preferences
         └─────────────────────┘
                    │
                    ▼
              DecisionBundle (final cart)
```

## Core Agents

### 1. IngredientAgent

**Location**: `src/agents/ingredient_agent.py`

**Purpose**: Extract ingredients from natural language meal requests.

**Key Methods**:
- `extract(prompt, servings)` - Main extraction method
- `_extract_with_llm()` - LLM-powered extraction (Claude, Ollama, Gemini)
- `_extract_with_templates()` - Template-based fallback

**Features**:
- Supports both LLM-powered and template-based extraction
- Cuisine-aware ingredient parsing (Indian, Italian, Mexican, etc.)
- Handles cooking forms (fresh ginger, coriander powder, cumin seeds)
- Scales quantities based on servings

**Example**:
```python
from src.agents.ingredient_agent import IngredientAgent

agent = IngredientAgent(use_llm=True)
result = agent.extract("chicken biryani for 4", servings=4)

# result.facts["ingredients"]:
# [
#   {"name": "chicken", "form": "thighs", "quantity": 2, "unit": "lb"},
#   {"name": "basmati rice", "form": "basmati", "quantity": 2, "unit": "cups"},
#   {"name": "onion", "form": "whole", "quantity": 3, "unit": "large"},
#   ...
# ]
```

---

### 2. ProductAgent

**Location**: `src/agents/product_agent.py`

**Purpose**: Find product candidates for each ingredient from inventory.

**Key Methods**:
- `get_candidates(ingredients)` - Get product candidates for ingredient list
- `search(keyword)` - Search inventory by keyword
- `filter_by_store(store)` - Filter by target store

**Features**:
- Loads CSV inventory from `data/source_listings.csv`
- Unit price normalization ($/oz)
- Store-specific brand mapping (Whole Foods, Trader Joe's, etc.)
- Form-aware matching (handles spices, herbs, produce)
- Smart sorting by form match, freshness, organic status, price

**Example**:
```python
from src.agents.product_agent import ProductAgent

agent = ProductAgent()
result = agent.get_candidates([
    {"name": "spinach"},
    {"name": "chicken", "form": "thighs"}
])

# result.facts["candidates_by_ingredient"]:
# {
#   "spinach": [
#     {"product_id": "sp1", "title": "Organic Baby Spinach", "brand": "365", "price": 4.99, ...},
#     {"product_id": "sp2", "title": "Fresh Spinach", "brand": "Earthbound", "price": 3.49, ...},
#   ],
#   "chicken": [
#     {"product_id": "ch1", "title": "Chicken Thighs", "brand": "Bell & Evans", "price": 8.99, ...},
#     ...
#   ]
# }
```

---

### 3. SafetyAgent

**Location**: `src/agents/safety_agent_v2.py`

**Purpose**: Check products for safety signals (EWG classification, FDA recalls).

**Key Methods**:
- `check_products(products)` - Check safety for multiple products
- `check_single_product(product)` - Check single product
- `get_ewg_info(ingredient)` - Get EWG Dirty Dozen/Clean Fifteen status
- `get_recall_summary(region)` - Get active recalls by region

**Features**:
- EWG Dirty Dozen/Clean Fifteen classification
- FDA recall status checking
- Pesticide scoring
- Red flags for critical recalls (Class I, II, III)

**Example**:
```python
from src.agents.safety_agent_v2 import SafetyAgent

agent = SafetyAgent()
result = agent.check_products(["spinach", "avocado", "strawberries"])

# result.facts:
# {
#   "spinach": {"ewg_bucket": "dirty_dozen", "organic_recommended": True, "pesticide_score": 8},
#   "avocado": {"ewg_bucket": "clean_fifteen", "organic_recommended": False, "pesticide_score": 1},
#   "strawberries": {"ewg_bucket": "dirty_dozen", "organic_recommended": True, "pesticide_score": 9},
# }
```

---

### 4. SeasonalAgent

**Location**: `src/agents/seasonal_agent.py`

**Purpose**: Check products for seasonality and regional availability.

**Key Methods**:
- `check_products(products)` - Check seasonality for multiple products
- `check_single_product(product)` - Check single product
- `get_in_season_now()` - Get items currently in season
- `get_regional_sources()` - Get trusted regional sources

**Features**:
- NJ crop calendar integration (Rutgers NJAES)
- Peak season status
- Local vs. imported classification
- Regional source trust levels

**Example**:
```python
from src.agents.seasonal_agent import SeasonalAgent

agent = SeasonalAgent()
result = agent.check_products(["tomatoes", "asparagus", "blueberries"])

# result.facts:
# {
#   "tomatoes": {"status": "peak", "is_local": True, "source": "NJ farms"},
#   "asparagus": {"status": "out_of_season", "is_local": False, "source": "imported"},
#   "blueberries": {"status": "peak", "is_local": True, "source": "NJ farms"},
# }
```

---

### 5. UserHistoryAgent

**Location**: `src/agents/user_history_agent.py`

**Purpose**: Track user preferences and past selections for personalization.

**Key Methods**:
- `record_selection(ingredient, tier, product_id)` - Record tier selection
- `get_preferences()` - Get learned preferences
- `set_preference(key, value)` - Set user preference
- `get_tier_for_ingredient(ingredient)` - Get recommended tier
- `apply_preferences_to_matches(products)` - Apply preferences to candidates

**Features**:
- In-memory storage (demo mode)
- Tier preference learning (cheaper, balanced, conscious)
- Ingredient-specific overrides
- Pattern detection (3+ selections with same tier)

**Example**:
```python
from src.agents.user_history_agent import UserHistoryAgent

agent = UserHistoryAgent(user_id="user123")

# Record selections
agent.record_selection("spinach", "conscious", "sp1")
agent.record_selection("spinach", "conscious", "sp1")
agent.record_selection("spinach", "conscious", "sp1")

# Now agent recommends conscious tier for spinach
tier = agent.get_tier_for_ingredient("spinach")  # Returns "conscious"
```

---

## Orchestration

### Orchestrator

**Location**: `src/orchestrator/orchestrator.py`

**Purpose**: Coordinate all agents in a gated flow.

**Stages**:
1. `step_ingredients()` - Extract ingredients via IngredientAgent
2. `confirm_ingredients()` - Gate: wait for user confirmation
3. `step_candidates()` - Get products via ProductAgent
4. `step_enrich()` - Run SafetyAgent + SeasonalAgent in parallel
5. `step_decide()` - DecisionEngine: constraints → scoring → neighbors → bundle
6. `record_selection()` - Record via UserHistoryAgent

**Example - Full Flow**:
```python
from src.orchestrator.orchestrator import Orchestrator

# Initialize with LLM extraction enabled
orch = Orchestrator(use_llm_extraction=True, use_llm_explanations=False)

# One-shot processing
bundle = orch.process_prompt("chicken biryani for 4")

# bundle.items: [DecisionItem, DecisionItem, ...]
# bundle.totals: {"recommended": 45.99, "cheaper": 32.50, "conscious": 52.00}
```

**Example - Step-by-Step with User Confirmation**:
```python
from src.orchestrator.orchestrator import Orchestrator

orch = Orchestrator(use_llm_extraction=True)

# Step 1: Extract ingredients
result = orch.step_ingredients("chicken biryani for 4", servings=4)
ingredients = result.facts["ingredients"]
# [{"name": "chicken", ...}, {"name": "basmati rice", ...}, ...]

# Step 2: User confirms/edits ingredients (UI interaction)
# User removes "mint", adds "saffron"
modified_ingredients = [...]
orch.confirm_ingredients(modified_ingredients)

# Step 3: Get product candidates
orch.step_candidates()

# Step 4: Enrich with safety + seasonality
orch.step_enrich()

# Step 5: Make decisions
bundle = orch.step_decide()

# bundle contains final cart with products, scores, alternatives
```

---

## Contract System

All agents return `AgentResult` containing:

```python
@dataclass
class AgentResult:
    status: str           # "ok" or "error"
    facts: dict           # Structured data payload
    explain: list[str]    # Human-readable explanations
    evidence: list[dict]  # Source citations with timestamps
    error_message: str    # Error details if status is "error"
```

**Example**:
```python
result = ingredient_agent.extract("biryani for 4")

if result.status == "ok":
    ingredients = result.facts["ingredients"]
    print(result.explain)  # ["Extracted 12 ingredients for Indian biryani"]
else:
    print(result.error_message)
```

---

## LLM Integration

### LLM Client Factory

**Location**: `src/utils/llm_client.py`

**Supported Providers**:
- `AnthropicClient` - Claude API (default for cloud)
- `OllamaClient` - Local models (default for local)
- `GeminiClient` - Google Gemini
- `OpenAIClient` - GPT models

**Configuration**:
```bash
# Cloud deployment (uses Anthropic)
export DEPLOYMENT_ENV=cloud
export ANTHROPIC_API_KEY=sk-ant-...

# Local development (uses Ollama)
export DEPLOYMENT_ENV=local
```

**Usage**:
```python
from src.utils.llm_client import get_llm_client

client = get_llm_client()
response = client.generate_sync(
    prompt="Extract ingredients from: chicken biryani for 4",
    system="You are an ingredient extraction assistant.",
    max_tokens=1000,
    temperature=0.2,
)
print(response.text)
```

---

## API Integration

The agents are exposed through FastAPI endpoints:

### `/api/extract-ingredients` (POST)
Runs IngredientAgent + ProductAgent to extract ingredients and determine store split.

### `/api/create-multi-cart` (POST)
Runs full pipeline with confirmed ingredients, returns multi-store carts.

### `/api/plan-v2` (POST)
V2 architecture using PlannerEngine (deterministic, faster).

**Example API Call**:
```bash
curl -X POST http://localhost:8000/api/plan-v2 \
  -H "Content-Type: application/json" \
  -d '{"prompt": "chicken biryani for 4", "servings": 4}'
```

---

## Testing

Run agent tests:
```bash
python -m pytest tests/test_pipeline.py -v
```

**Key Test Classes**:
- `TestProductAgent` - Product matching and unit price tests
- `TestDecisionEngineConstraints` - Hard constraint tests (recalls, avoided brands)
- `TestDecisionEngineDeterminism` - Same input → same output
- `TestOrchestratorGating` - State machine and gating tests

---

## File Locations

| Component | Path |
|-----------|------|
| IngredientAgent | `src/agents/ingredient_agent.py` |
| ProductAgent | `src/agents/product_agent.py` |
| SafetyAgent | `src/agents/safety_agent_v2.py` |
| SeasonalAgent | `src/agents/seasonal_agent.py` |
| UserHistoryAgent | `src/agents/user_history_agent.py` |
| Orchestrator | `src/orchestrator/orchestrator.py` |
| DecisionEngine | `src/decision/decision_engine.py` |
| LLM Clients | `src/utils/llm_client.py` |
| Ingredient Extractor | `src/llm/ingredient_extractor.py` |
| Decision Explainer | `src/llm/decision_explainer.py` |

---

## Last Updated

**Created**: February 7, 2026
**Version**: 1.0
