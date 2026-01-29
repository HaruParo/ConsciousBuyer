# Conscious Cart Coach

> **Current Version**: React + FastAPI Full-Stack Application

Make more conscious purchasing decisions with AI-powered grocery recommendations. Get personalized suggestions across three tiers (cheaper, balanced, conscious) based on safety data, seasonality, and your preferences.

## Features

- **Recipe-Based Shopping**: Tell us what you want to cook, get a complete shopping list
- **Three-Tier Recommendations**: Cheaper, balanced, or conscious options for every ingredient
- **Safety Integration**: EWG Dirty Dozen/Clean Fifteen data, FDA recall alerts
- **Seasonal Awareness**: NJ crop calendar for local/peak season produce
- **Preference Learning**: System learns your tier preferences over time
- **Evidence-Based**: Every recommendation comes with traceable sources

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR                            │
│  Gated Flow: Ingredients → Products → Enrich → Score → Export   │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ IngredientAgent│   │ ProductAgent  │    │ UserHistory   │
│ Recipe templates│  │ 3-tier match  │    │ Learn prefs   │
└───────────────┘    └───────────────┘    └───────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        ▼                                           ▼
┌───────────────┐                          ┌───────────────┐
│ SafetyAgent   │                          │ SeasonalAgent │
│ EWG + Recalls │                          │ NJ Crop Data  │
└───────────────┘                          └───────────────┘
                              │
                              ▼
                    ┌───────────────┐
                    │DecisionEngine │
                    │ Pure Scoring  │
                    └───────────────┘
```

## Project Structure

```
conscious-cart-coach/
├── Figma_files/                # React Frontend (CURRENT VERSION)
│   ├── src/                    # React components & logic
│   ├── public/                 # Static assets
│   ├── index.html              # Entry point
│   └── package.json            # Node dependencies
├── api/                        # FastAPI Backend
│   └── main.py                 # REST API endpoints
├── data/
│   ├── raw/                    # Original receipts CSV
│   ├── processed/              # Normalized data
│   ├── alternatives/           # Product alternatives seed data
│   ├── ewg/                    # EWG Dirty Dozen/Clean Fifteen
│   ├── recalls/                # FDA recall data
│   ├── seasonal/               # NJ crop calendar
│   └── stores/                 # Store and regional source data
├── outputs/                    # CSV exports for debugging
├── src/
│   ├── core/                   # AgentResult contract, types
│   ├── data/                   # FactsStore (SQLite), refresh jobs
│   ├── facts/                  # FactsGateway (single data access point)
│   ├── agents/                 # Lightweight agents
│   │   ├── ingredient_agent.py # Extract ingredients from prompts
│   │   ├── product_agent.py    # Match to inventory (3 tiers)
│   │   ├── safety_agent_v2.py  # EWG + recall checks
│   │   ├── seasonal_agent.py   # NJ seasonality
│   │   └── user_history_agent.py # Preference learning
│   ├── engine/                 # DecisionEngine (pure scoring)
│   ├── orchestrator/           # Gated flow coordinator
│   ├── exporters/              # CSV export for debugging
│   └── cli/                    # CLI tools
└── tests/
```

## Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd conscious-cart-coach

# Backend setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd Figma_files
npm install
cd ..

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run (starts both backend and frontend)
./run.sh
```

**Access the app**:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Usage

### Full Flow (from prompt to recommendations)

```python
from src.orchestrator import Orchestrator

orch = Orchestrator()
result = orch.process_prompt("chicken biryani for 4")

# Results
print(result.facts["recommendations"])  # Best tier per ingredient
print(result.facts["tier_totals"])      # {"cheaper": 45.50, "conscious": 78.20}
print(result.explain)                   # ["Processed 12 ingredients", ...]
```

### Step-by-Step Flow

```python
from src.orchestrator import Orchestrator

orch = Orchestrator()

# Step 1: Extract ingredients
ingredients = orch.step_ingredients("chicken biryani", servings=4)
print(ingredients.facts["ingredients"])  # Review extracted list

# Step 2: Confirm/modify ingredients
orch.confirm_ingredients(modified_list)  # Optional

# Step 3: Match to products
products = orch.step_products(ingredients.facts["ingredients"])

# Step 4: Enrich with safety/seasonal data
enriched = orch.step_enrich()

# Step 5: Apply user preferences
prefs = orch.step_preferences()

# Step 6: Get scored recommendations
recommendations = orch.step_recommend()
```

### Export to CSV (debugging)

```python
from src.exporters import CSVExporter

exporter = CSVExporter()
exporter.export_flow(result)  # Creates outputs/*.csv files
```

### CLI Tools

```bash
# Inspect facts store
python -m src.cli.facts_inspector status
python -m src.cli.facts_inspector ewg spinach
python -m src.cli.facts_inspector recalls --state NJ

# Refresh data
python -m src.data.refresh_jobs status
python -m src.data.refresh_jobs refresh --table recalls
```

## AgentResult Contract

All agents return a consistent format:

```python
@dataclass
class AgentResult:
    agent_name: str                    # "safety", "seasonal", etc.
    status: Literal["ok", "error"]     # Success/failure
    facts: dict[str, Any]              # Agent-specific data
    explain: list[str]                 # Max 5 bullets for UI
    evidence: list[Evidence]           # Traceable sources
    error_message: str | None          # If status == "error"
    timestamp: str                     # ISO timestamp
```

## Data Sources

| Source | Refresh | Description |
|--------|---------|-------------|
| EWG | Annual | Dirty Dozen / Clean Fifteen lists |
| FDA Recalls | Daily | Food safety recalls for NJ |
| NJ Crops | Annual | Seasonal availability calendar |
| Regional Sources | Quarterly | Local farms, co-ops, trusted vendors |
| Stores | Monthly | Stores serving Middlesex County |

## Configuration

Copy `.env.example` to `.env`:

```
ANTHROPIC_API_KEY=your-key      # For Claude LLM features
OPIK_API_KEY=your-key           # For experiment tracking
DATABASE_URL=postgresql://...    # Optional PostgreSQL
```

## Development

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src

# Type checking
mypy src/
```

## License

MIT
