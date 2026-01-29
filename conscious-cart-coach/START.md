# Conscious Cart Coach - Full Stack Setup

> **⚡ CURRENT VERSION: React + FastAPI (v2.0)**
> This is the production-ready full-stack application.

## Quick Start

### Option 1: Use the Run Script (Recommended)

```bash
./run.sh
```

This starts both backend and frontend automatically.

### Option 2: Manual Start

The FastAPI backend is already running on http://localhost:8000

### Start the React Frontend:

```bash
# Install Node.js dependencies (first time only)
cd Figma_files
npm install

# Start the Vite dev server
npm run dev
```

The frontend will be available at http://localhost:5173

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

## Deployment

### Frontend (Vercel)
```bash
cd Figma_files
vercel
```

### Backend (Railway)
```bash
railway login
railway init
railway up
```

Update VITE_API_URL in .env.local to point to your Railway URL.

## Current Status

✅ FastAPI backend running on port 8000
✅ React app configured with API integration
✅ Loading states and error handling
✅ Design system implemented
⏳ Waiting for Node.js to start frontend
