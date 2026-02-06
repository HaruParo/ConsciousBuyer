# Test the UI - Quick Guide

**Last Updated**: 2026-01-29

---

## 🎯 Two Ways to Test

### 1️⃣ Simple Demo (Store Classification Only)

**Fastest way to see the store classification system:**

```bash
cd /Users/hash/Documents/ConsciousBuyer/conscious-cart-coach
python demo_api.py
```

**Open in browser:**
- **Interactive Demo**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

**Try these test cases:**
- `turmeric, ghee, basmati rice` → Should split to Pure Indian Foods
- `tomatoes, lettuce, chicken` → Should stay at FreshDirect (primary)
- `turmeric` alone → Should merge to primary (1-item rule)
- Toggle **Urgency** to see Kesar Grocery vs Pure Indian Foods

---

### 2️⃣ Full React UI (Complete Experience)

**Full production UI with all features:**

```bash
# Option A: Use run script
./run.sh

# Option B: Manual start
# Terminal 1: Backend
python -m uvicorn api.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

**Open in browser:**
- **React App**: http://localhost:5173
- **Backend API**: http://localhost:8000

---

## 🧪 Test Scenarios

### Store Classification Tests

**Primary Store Only** (all items from FreshDirect):
```
Ingredients: tomatoes, lettuce, chicken, olive oil
Expected: 1 store (FreshDirect)
```

**Specialty Store Split** (multiple specialty items):
```
Ingredients: turmeric, ghee, cardamom, cumin
Expected: 2 stores (FreshDirect + Pure Indian Foods/Kesar Grocery)
```

**1-Item Rule** (single specialty item merges to primary):
```
Ingredients: tomatoes, lettuce, turmeric
Expected: 1 store (FreshDirect) with note about turmeric
```

**Urgency Test**:
```
Planning mode: Uses Pure Indian Foods (slow shipping, high transparency)
Urgent mode: Uses Kesar Grocery (fast delivery)
```

### Full App Tests

**Template Matching** (no LLM needed):
- "chicken biryani for 4"
- "stir fry with vegetables"
- "fresh salad"

**Natural Language** (requires LLM):
- "I want something healthy for dinner"
- "seasonal vegetables for a week"

---

## 🎨 What to Look For

### Design System Colors
- **Primary Store (FreshDirect)**: Orange (`#d4976c`)
- **Specialty Store**: Purple (`#8b7ba8`)
- **Unavailable**: Beige (`#e5d5b8`)

### UI Features
- ✅ Interactive ingredient input
- ✅ Urgency toggle (Planning/Urgent)
- ✅ Real-time store split calculation
- ✅ Visual color coding
- ✅ Clear store reasoning

---

## 🐛 Troubleshooting

**Demo won't start?**
```bash
# Check Python version
python --version  # Should be 3.8+

# Check if port 8000 is in use
lsof -ti:8000 | xargs kill -9

# Restart demo
python demo_api.py
```

**React UI won't start?**
```bash
# Check Node version
node --version  # Should be 16+

# Reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

**Backend API not responding?**
```bash
# Check FastAPI is running
curl http://localhost:8000/

# Check logs
python demo_api.py  # Look for error messages
```

---

## 📸 Expected Output

### Demo UI (http://localhost:8000)
```
┌────────────────────────────────────┐
│ Conscious Cart Coach               │
│ Store Classification Demo          │
│                                    │
│ Ingredients:                       │
│ [turmeric, ghee, basmati rice]    │
│                                    │
│ Urgency: ⚪ Planning ⚫ Urgent     │
│                                    │
│ [Split by Store]                   │
│                                    │
│ Results:                           │
│ 🟠 FreshDirect (Primary): 0 items │
│ 🟣 Pure Indian Foods: 3 items      │
└────────────────────────────────────┘
```

### API Response
```json
{
  "stores": [
    {
      "store_name": "Pure Indian Foods",
      "items": ["turmeric", "ghee", "basmati rice"],
      "color": "#8b7ba8",
      "reason": "Specialty ingredients"
    }
  ]
}
```

---

## ✅ Success Criteria

You've successfully tested the UI when:
- [x] Demo loads at http://localhost:8000
- [x] Ingredient input works
- [x] Store split logic works correctly
- [x] Colors match design system
- [x] Urgency toggle changes specialty store
- [x] 1-item rule works (merges to primary)

---

**Quick Links**:
- [Architecture Overview](docs/architecture/architecture-overview.md)
- [Store Classification System](docs/architecture/STORE_CLASSIFICATION_SYSTEM.md)
- [Implementation Status](docs/architecture/implementation-status.md)
