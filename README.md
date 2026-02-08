# Conscious Cart Coach

**Shop with your values, not just your wallet.**

An AI-powered grocery assistant that turns meal ideas into smart shopping carts. Tell it what you want to cook, and it builds a cart that balances quality, ethics, and budget across multiple stores.

```
"chicken biryani for 4" → Complete shopping list with organic produce,
                          authentic spices from specialty stores,
                          and transparent explanations for every choice.
```

---

## Why Conscious Cart Coach?

Traditional grocery apps make you browse aisles and search for products. We flipped that:

| Old Way | Our Way |
|---------|---------|
| Search "chicken breast" → filter → add to cart → repeat 20x | "chicken biryani for 4" → complete cart appears |
| Everything from one store | Smart multi-store: FreshDirect for proteins, Pure Indian Foods for authentic spices |
| No guidance on organic | EWG Dirty Dozen prioritization: organic spinach, conventional onions |
| Black box recommendations | "We chose this cardamom because whole pods = better flavor for biryani" |

---

## Features

### Natural Language Input
Just describe what you want to cook:
- "Chicken biryani for 4"
- "Quick weeknight pasta, vegetarian"
- "Meal prep for the week, I have chicken and rice"

### LLM-Powered Intelligence
- **Ingredient Extraction**: Claude understands recipes, cuisines, and dietary needs
- **Decision Explanations**: Natural language reasons for every product choice
- **Batched Processing**: 2 LLM calls per cart (optimized from 22)

### Three-Tier Options
Every ingredient gets scored across dimensions:

| Tier | Philosophy | Example |
|------|------------|---------|
| **Cheaper** | Maximize value | Yellow onions $0.99/lb (conventional) |
| **Balanced** | Quality where it matters | Bell & Evans chicken $6.99/lb (no antibiotics) |
| **Conscious** | Values over price | Lancaster Co-op onions $1.99/lb (local + organic) |

### Multi-Store Cart Splitting
Products route to their natural home:
- **FreshDirect**: Produce, proteins, pantry staples
- **Pure Indian Foods**: Authentic Indian spices
- **Local Co-ops**: Seasonal, local produce

### Safety Integration
- **EWG Dirty Dozen/Clean Fifteen**: Organic prioritization for high-pesticide items
- **Component Scoring**: 7-factor algorithm (EWG, form fit, packaging, delivery, value, outlier penalty)

---

## Quick Start

### Local Development

```bash
# Clone and setup
git clone <repo-url>
cd conscious-cart-coach

# Install dependencies
conda env create -f environments.yml
conda activate consciousbuyer

# Start Ollama (local LLM)
ollama serve
ollama pull mistral

# Configure
cp .env.example .env
# DEPLOYMENT_ENV=local uses Ollama by default

# Run (starts backend + frontend)
./run.sh
```

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/docs

### Cloud Deployment (Vercel)

```bash
# Set environment variables in Vercel dashboard:
# DEPLOYMENT_ENV=cloud
# ANTHROPIC_API_KEY=sk-ant-...
# LLM_PROVIDER=gemini (optional, for faster inference)
# GOOGLE_API_KEY=... (if using Gemini)

vercel deploy
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INTERFACE                          │
│  "I want to make chicken biryani for 4 people"              │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   FRONTEND (React + TypeScript)              │
│  MealPlanInput → API Call → ShoppingCart Display            │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                          │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  LLM: Ingredient Extraction                          │    │
│  │  "chicken biryani" → [chicken, rice, cardamom, ...]  │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                  │
│                            ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Planner Engine: Product Matching & Scoring          │    │
│  │  7-component scoring (EWG, form, packaging, ...)     │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                  │
│                            ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  LLM: Decision Explanations (Batched)                │    │
│  │  Returns JSON with all explanations in 1 call        │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                │
│  source_listings.csv: 353 products across stores            │
│  Metadata: packaging, nutrition, labels                      │
└─────────────────────────────────────────────────────────────┘
```

---

## LLM Integration

### Hybrid Approach
- **Rules** for deterministic scoring (reproducible, fast, free)
- **LLM** for understanding and explaining (flexible, natural)

### Providers Supported
| Provider | Use Case | Speed |
|----------|----------|-------|
| Gemini (gemini-2.0-flash-lite) | Development | ~200ms |
| Anthropic (claude-3-haiku) | Production | ~2-4s |
| Ollama (mistral) | Local dev | ~3-5s |

### Cost Optimization
| Metric | Before | After |
|--------|--------|-------|
| Token usage | ~2,353/call | ~500-600/call |
| API calls/cart | 22 (N+1) | 2 (batched) |
| Cost per cart | ~$0.05 | ~$0.01 |

---

## LLM Observability with Opik

We use [Opik](https://www.comet.com/opik) for LLM observability and evaluation.

### What We Track
- Every LLM call with inputs, outputs, latency
- Token usage and costs
- Quality metrics via experiments

### Key Optimizations Discovered

| Feature | Impact |
|---------|--------|
| **Opik Assist** | Reduced prompts from 2,353 → 500 tokens (75%) |
| **Batching** | Reduced API calls from 22 → 2 (91%) |
| **LLM-as-Judge** | Automated quality scoring |
| **Annotation Queues** | Human review for edge cases |

### Experiment Results

| Experiment | Latency | Quality Score |
|------------|---------|---------------|
| Ingredient Extractor | 4.6s | 0.8 coverage |
| Decision Explainer | 1.3s | 0.6 quality, 0.7 length |

---

## Project Structure

```
conscious-cart-coach/
├── api/main.py              # FastAPI backend
├── frontend/                 # React + TypeScript UI
│   └── src/
│       ├── components/       # MealPlanInput, ShoppingCart, CartItemCard
│       └── services/api.ts   # Backend API calls
├── src/
│   ├── llm/
│   │   ├── ingredient_extractor.py   # LLM: recipe → ingredients
│   │   └── decision_explainer.py     # LLM: batched explanations
│   ├── planner/
│   │   └── engine.py                 # Core scoring & cart building
│   ├── scoring/
│   │   └── component_scoring.py      # 7-component scoring system
│   └── utils/
│       └── llm_client.py             # Unified LLM client (Anthropic/Gemini/Ollama)
├── data/
│   └── alternatives/
│       └── source_listings.csv       # 353 products with metadata
├── architecture/                      # Detailed documentation
├── index.py                          # Vercel serverless entry
└── vercel.json                       # Deployment config
```

---

## API Reference

### Create Shopping Cart

```bash
POST /api/plan-v2

curl -X POST http://localhost:8000/api/plan-v2 \
  -H "Content-Type: application/json" \
  -d '{"prompt": "chicken biryani for 4", "servings": 4}'
```

**Response:**
```json
{
  "stores": {
    "FreshDirect": {
      "items": [
        {
          "ingredient_name": "chicken",
          "brand": "Bell & Evans",
          "price": 8.99,
          "quantity": 1,
          "reason_line": "Air-chilled chicken at $8.99 offers superior texture..."
        }
      ],
      "total": 42.96
    },
    "Pure Indian Foods": {
      "items": [...],
      "total": 25.67
    }
  },
  "grand_total": 68.63
}
```

### Health Check

```bash
GET /api/health
```

### Debug Environment

```bash
GET /api/debug-env
# Returns which env vars are set (useful for Vercel debugging)
```

---

## Environment Variables

```bash
# Required
DEPLOYMENT_ENV=local          # local | cloud

# Local Development (DEPLOYMENT_ENV=local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# Cloud Deployment (DEPLOYMENT_ENV=cloud)
LLM_PROVIDER=gemini           # gemini | anthropic
GOOGLE_API_KEY=...            # For Gemini
ANTHROPIC_API_KEY=sk-ant-...  # For Anthropic
ANTHROPIC_MODEL=claude-3-haiku-20240307

# Observability (optional)
OPIK_API_KEY=...
OPIK_WORKSPACE=...
OPIK_PROJECT_NAME=consciousbuyer
```

---

## The Scoring System

Products are scored on a 0-100 scale across 7 components:

| Component | Points | Description |
|-----------|--------|-------------|
| **EWG** | -12 to +18 | Dirty Dozen organic bonus, Clean Fifteen flexibility |
| **Form Fit** | 0-14 | Fresh ginger vs powder, whole spices vs ground |
| **Packaging** | -4 to +6 | Glass jar (+4), plastic clamshell (-4) |
| **Delivery** | -10 to 0 | Penalty for slow delivery when cooking tonight |
| **Unit Value** | 0-8 | Best $/oz gets bonus |
| **Outlier** | -20 or 0 | Penalty for items >2x median price |
| **Base** | 50 | Starting score |

**Example:**
```
Pure Indian Foods Cumin Seeds, 3oz, $6.69, Organic
  Base: 50
  EWG: +2 (organic spice)
  Form Fit: +14 (seeds requested, seeds found)
  Packaging: +4 (glass jar)
  Unit Value: +6
  Total: 76/100 → SELECTED
```

---

## Documentation

Detailed architecture docs in `architecture/`:

| Document | Description |
|----------|-------------|
| [01-technical-architecture.md](architecture/01-technical-architecture.md) | Tech stack, components, file structure |
| [02-llm-integration.md](architecture/02-llm-integration.md) | LLM modules, prompts, cost optimization |
| [03-ui-flows.md](architecture/03-ui-flows.md) | User journey, modals, loading states |
| [04-data-flows.md](architecture/04-data-flows.md) | CSV → Cart pipeline, scoring details |
| [05-mental-models.md](architecture/05-mental-models.md) | Design philosophy, why we built it this way |
| [opik-integration-journey.md](architecture/opik-integration-journey.md) | LLM observability story |

---

## Development

```bash
# Run tests
pytest

# Type checking
mypy src/

# Frontend development
cd frontend && npm run dev

# Backend only
uvicorn api.main:app --reload
```

---

## The Philosophy

> **Conscious Cart Coach helps people shop according to their values, not just their wallets or convenience.**

Every technical decision flows back to: *Does this help users make value-aligned choices?*

- **Organic where it matters**: Dirty Dozen prioritization
- **Authentic for specialty items**: Pure Indian Foods for biryani spices
- **Local when possible**: Lancaster Farm Fresh Co-op preference
- **Transparent trade-offs**: "Costs $2 more but organic and local"

---

## License

MIT

---

*Built with Claude, Gemini, FastAPI, React, and Opik*
