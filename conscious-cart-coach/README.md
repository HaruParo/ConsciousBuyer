# Conscious Cart Coach

AI-powered grocery shopping assistant that helps you make conscious purchasing decisions. Get personalized recommendations across three tiers (cheaper, balanced, conscious) based on safety data, seasonality, and your preferences.

## Features

- **Natural Language Input**: "chicken biryani for 4" → complete shopping list
- **LLM-Powered**: Claude extracts ingredients and explains recommendations
- **Three-Tier Options**: Cheaper, balanced, or conscious choice for every ingredient
- **Safety Integration**: EWG Dirty Dozen/Clean Fifteen, FDA recall alerts
- **Multi-Store Support**: Splits cart across stores for best selection

## Quick Start

### Local Development

```bash
# Clone and setup
git clone <repo-url>
cd conscious-cart-coach

# Install dependencies (conda recommended)
conda env create -f environments.yml
conda activate consciousbuyer

# Configure
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# Run (starts backend + frontend)
./run.sh
```

**Access**:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/docs

### Vercel Deployment

The app is configured for Vercel deployment:
- Frontend: Static build from `frontend/`
- Backend: Python serverless function via `index.py`

```bash
vercel deploy
```

## Environment Variables

```bash
# Required for LLM features
ANTHROPIC_API_KEY=sk-ant-...

# Optional
ANTHROPIC_MODEL=claude-3-haiku-20240307  # Default model
LLM_PROVIDER=anthropic                    # or "ollama" for local

# Observability (optional)
OPIK_API_KEY=...
OPIK_PROJECT_NAME=consciousbuyer
```

## Project Structure

```
conscious-cart-coach/
├── api/main.py           # FastAPI backend (/api/plan-v2)
├── frontend/             # React/TypeScript UI
├── src/
│   ├── llm/              # LLM modules (ingredient extraction, explanations)
│   ├── planner/          # Core planning engine
│   ├── agents/           # Ingredient, product, safety agents
│   └── utils/            # Unified LLM client
├── data/                 # Product inventories (CSV)
├── architecture/         # Documentation (see below)
├── index.py              # Vercel serverless entry
└── vercel.json           # Deployment config
```

## Documentation

All detailed documentation lives in the `architecture/` folder:

| Document | Description |
|----------|-------------|
| [01-technical-architecture.md](architecture/01-technical-architecture.md) | Tech stack, component connections, file structure |
| [02-llm-integration.md](architecture/02-llm-integration.md) | LLM modules, prompts, cost optimization |
| [03-ui-flows.md](architecture/03-ui-flows.md) | User journey, modals, loading states |
| [04-data-flows.md](architecture/04-data-flows.md) | CSV → Cart data pipeline, scoring |
| [05-mental-models.md](architecture/05-mental-models.md) | Design philosophy, decisions |
| [06-llm-skills.md](architecture/06-llm-skills.md) | LLM module usage guide |

**Start here**: [architecture/README.md](architecture/README.md)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/plan-v2` | POST | Create shopping cart from meal description |
| `/api/health` | GET | Health check |
| `/api/debug-env` | GET | Check environment configuration |

### Example Request

```bash
curl -X POST http://localhost:8000/api/plan-v2 \
  -H "Content-Type: application/json" \
  -d '{"prompt": "chicken biryani for 4", "servings": 4}'
```

## Development

```bash
# Run tests
pytest

# Type checking
mypy src/

# Frontend dev
cd frontend && npm run dev
```

## License

MIT
