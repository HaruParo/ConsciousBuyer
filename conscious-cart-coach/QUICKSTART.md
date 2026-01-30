# Conscious Cart Coach - Quick Start

> **⚡ CURRENT VERSION: React + FastAPI (v2.0)**
> Two ways to test: Simple demo or full-stack app

---

## 🚀 Option 1: Simple Demo (Fastest)

**Test store classification system with interactive web UI:**

```bash
python demo_api.py
```

**Then open in browser:**
- 🌐 **Demo UI**: http://localhost:8000
- 📖 **API Docs**: http://localhost:8000/docs

**Try these ingredients:**
- `turmeric, ghee, basmati rice, chicken` (specialty items)
- `tomatoes, lettuce, chicken` (primary store only)
- Toggle between Planning/Urgent modes

---

## 🎨 Option 2: Full React UI (Production)

### Using the Run Script (Recommended):

```bash
./run.sh
```

This starts both backend and frontend automatically.

### Manual Start:

**1. Start Backend:**
```bash
# Backend runs on port 8000
python -m uvicorn api.main:app --reload
```

**2. Start Frontend:**
```bash
# Install dependencies (first time only)
cd frontend
npm install

# Start dev server
npm run dev
```

**Then open:**
- 🎨 **React UI**: http://localhost:5173
- 🔌 **Backend API**: http://localhost:8000/docs

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/
```

### Create Shopping Cart
```bash
curl -X POST http://localhost:8000/api/create-cart \
  -H "Content-Type: application/json" \
  -d '{"meal_plan": "stir fry for 4 with chicken"}'
```

## Supported Meal Plans (Template Mode)

When LLM is disabled, these keywords work best:
- **"biryani"** - Full Indian rice dish with spices
- **"stir fry"** - Asian vegetable stir fry (add protein: chicken/beef/tofu)
- **"salad"** - Fresh mixed greens salad
- **"chicken tikka"** - Grilled chicken with Indian spices

Or use specific produce names:
- "spinach kale tomatoes onions"
- "apple banana strawberries"
- "carrots broccoli cauliflower"

## Architecture

```
┌─────────────────┐         ┌──────────────────┐
│  React Frontend │────────▶│  FastAPI Backend │
│  (Vite/Tailwind)│  POST   │  (Port 8000)     │
│  Port 5173      │◀────────│                  │
└─────────────────┘   JSON  └──────────────────┘
                                     │
                                     ▼
                             ┌──────────────────┐
                             │   Orchestrator   │
                             │   • Ingredients  │
                             │   • Products     │
                             │   • Safety Data  │
                             │   • Decisions    │
                             └──────────────────┘
```

## Enable LLM Features

To use natural language extraction (e.g., "seasonal veggies for a week"):

1. Set your Claude API key:
```bash
export ANTHROPIC_API_KEY=your_key_here
```

2. Update api/main.py:
```python
orch = Orchestrator(
    use_llm_extraction=True,    # Enable this
    use_llm_explanations=True   # Enable this
)
```

3. Restart the FastAPI server

---

## 🧪 Testing

### Quick Test (Demo API)
```bash
# Start demo
python demo_api.py

# Test API directly
curl -X POST http://localhost:8000/api/split \
  -H "Content-Type: application/json" \
  -d '{"ingredients": ["turmeric", "tomatoes"], "urgency": "planning"}'
```

### Test Full App
1. Start backend: `./run.sh` or manual start
2. Open React UI: http://localhost:5173
3. Try creating a cart with different meal plans

---

## 📦 Deployment

### Frontend (Vercel)
```bash
cd frontend
vercel
```

### Backend (Railway)
```bash
railway login
railway init
railway up
```

Update `VITE_API_URL` in `.env.local` to point to your Railway URL.

---

## 🔗 Quick Links

| What | URL |
|------|-----|
| **Demo UI** | http://localhost:8000 |
| **React UI** | http://localhost:5173 |
| **API Docs** | http://localhost:8000/docs |
| **Test Store Split** | http://localhost:8000 (interactive form) |

---

## 📚 Documentation

- [Architecture Overview](docs/architecture/architecture-overview.md) - Start here
- [Implementation Status](docs/architecture/implementation-status.md) - What's built
- [Store Classification](docs/architecture/STORE_CLASSIFICATION_SYSTEM.md) - How it works
