# Conscious Cart Coach - Project Structure Guide

> **Last Updated**: 2026-01-29
> **Current Version**: v2.0 (React + FastAPI)
> **Purpose**: Quick reference for navigating the codebase

---

## 📁 Directory Overview

```
conscious-cart-coach/
├── src/                          # Core backend engine (Python)
│   ├── orchestrator/             # ✨ NEW: Store classification system
│   │   ├── ingredient_classifier.py  # Dynamic ingredient classification
│   │   ├── store_split.py            # Multi-store cart splitting logic
│   │   └── orchestrator.py           # Main orchestration engine
│   ├── agents/                   # Multi-agent system
│   │   ├── product_agent.py      # Inventory matching
│   │   ├── safety_agent_v2.py    # EWG + FDA recall checks
│   │   └── seasonal_agent.py     # Seasonality scoring
│   ├── engine/                   # Scoring & decision logic
│   │   └── decision_engine.py
│   ├── contracts/                # Data models & types
│   │   └── models.py
│   └── ui/                       # (Empty - old Streamlit removed)
│
├── tests/                        # Test suite
│   └── test_store_split_demo.py  # ✨ Store classification tests
│
├── frontend/                     # ✨ React UI (was: Figma_files)
│   ├── dist/                     # Built React app (served at localhost:5173)
│   └── node_modules/             # NPM dependencies
│
├── docs/                         # Documentation
│   └── architecture/             # ✨ Architecture docs
│       ├── STORE_CLASSIFICATION_SYSTEM.md          # v2.0 system docs
│       ├── STORE_CLASSIFICATION_VERSION_HISTORY.md # Evolution tracking
│       ├── MULTI_STORE_CART_SYSTEM.md              # Original design doc
│       └── 0-step.md                                # Overview
│
├── archive/                      # ✨ Archived old code
│   ├── v1.0-streamlit/          # Old Streamlit UI (deprecated)
│   │   ├── app.py
│   │   ├── components.py
│   │   └── styles.py
│   └── unused-scripts/          # v1.0 static classification scripts
│       ├── add_store_types.py
│       └── add_store_types_bulk.py
│
├── data/                        # Data sources
│   ├── flags/                   # Safety data (EWG, FDA)
│   ├── seasonal/                # Crop calendars
│   └── stores/                  # Store inventory
│
├── demo_api.py                  # ✨ Interactive demo (http://localhost:8000)
├── run.sh                       # Startup script
└── requirements.txt             # Python dependencies
```

---

## 🎯 Key Files - What & Where

### Store Classification (NEW - v2.0)

| File | Purpose | When to Use |
|------|---------|-------------|
| `src/orchestrator/ingredient_classifier.py` | Classifies ingredients as primary/specialty/both | Add new ingredient patterns |
| `src/orchestrator/store_split.py` | Splits cart by stores, implements 1-item rule | Modify store routing logic |
| `tests/test_store_split_demo.py` | Test suite with 4 test scenarios | Run tests, see examples |
| `demo_api.py` | FastAPI demo with web UI | Demo the system visually |

### Documentation

| File | Purpose | Audience |
|------|---------|----------|
| `docs/architecture/STORE_CLASSIFICATION_SYSTEM.md` | v2.0 system documentation | Developers integrating the system |
| `docs/architecture/STORE_CLASSIFICATION_VERSION_HISTORY.md` | Why we made v2.0, what changed | Understanding design decisions |
| `docs/architecture/MULTI_STORE_CART_SYSTEM.md` | Original multi-store vision | Product/design context |
| `PROJECT_STRUCTURE.md` | This file | Quick navigation |

### Core Backend

| File | Lines | Purpose |
|------|-------|---------|
| `src/contracts/models.py` | ~300 | All typed contracts (ProductCandidate, DecisionBundle) |
| `src/orchestrator/orchestrator.py` | ~400 | Main orchestration engine |
| `src/engine/decision_engine.py` | ~500 | Deterministic scoring logic |
| `src/agents/product_agent.py` | ~500 | Simulated inventory (40+ ingredients) |

---

## 🚀 Quick Start Commands

### Run Tests
```bash
# Store classification tests
python tests/test_store_split_demo.py

# All tests
pytest tests/ -v
```

### Run Demo
```bash
# Interactive web demo
python demo_api.py

# Then visit: http://localhost:8000
```

### Run Frontend (if source exists)
```bash
cd frontend
npm run dev  # Would run at localhost:5173
```

---

## 🗂️ What Got Archived

### v1.0 Streamlit UI → `archive/v1.0-streamlit/`
- Old Streamlit-based UI
- Deprecated when moved to React + FastAPI
- Kept for reference only

### Unused Scripts → `archive/unused-scripts/`
- `add_store_types.py` - Static store_type field approach (abandoned)
- `add_store_types_bulk.py` - Bulk version (abandoned)
- Why archived: v1.0 approach didn't handle new ingredients dynamically

---

## 📊 System Architecture (High-Level)

```
User Input → Ingredient Extraction → Product Matching → Store Classification
                                                                ↓
                                                        ┌───────────────────┐
                                                        │ Store Split Logic │
                                                        │  (v2.0 Dynamic)   │
                                                        └───────────────────┘
                                                                ↓
                                           ┌────────────────────┴────────────────────┐
                                           │                                         │
                                    Primary Store                            Specialty Store
                                   (FreshDirect)                        (Pure Indian Foods /
                                  Fresh + Common                            Kesar Grocery)
                                                                         Spices + Specialty
```

---

## 🎨 Design System Colors

Used in UI components for store display:

```css
--primary-brown: #6b5f3a;    /* Headers, primary text */
--cream: #fef9f5;            /* Background */
--beige-border: #e5d5b8;     /* Borders */

/* Store-specific colors */
--accent-orange: #d4976c;    /* Primary Store tab */
--accent-purple: #8b7ba8;    /* Specialty Store tab */
--unavailable: #a89968;      /* Unavailable items */
```

---

## 🔄 Version History

### v2.0 (Current) - Dynamic Rule-Based Classification
- **Date**: 2026-01-29
- **Status**: ✅ Active
- **Approach**: Dynamic pattern matching, no static fields
- **Handles**: New ingredients without manual intervention
- **Tests**: All passing ✅

### v1.0 (Archived) - Static store_type Fields
- **Date**: 2026-01-29 (proposed, never deployed)
- **Status**: ❌ Archived
- **Why Abandoned**: Couldn't handle new ingredients dynamically

### v0.0 (Baseline) - No Classification
- **Date**: 2026-01-14 to 2026-01-28
- **Status**: 📦 Still used for product data structure

---

## 🤝 Contributing

### Adding New Ingredients

1. **No code changes needed!** The system handles new ingredients automatically
2. Classification is pattern-based (fresh keywords, spice suffixes, etc.)
3. See `src/orchestrator/ingredient_classifier.py` for patterns

### Adding New Stores

1. Update `_select_primary_store()` in `store_split.py`
2. Update `_select_specialty_store()` in `store_split.py`
3. Add to documentation

### Modifying Classification Rules

1. Edit pattern lists in `ingredient_classifier.py`:
   - `FRESH_CATEGORIES` - Fresh produce, meat, dairy
   - `ETHNIC_SPECIALTY` - Spices, specialty items
   - `COMMON_SHELF_STABLE` - Available everywhere
2. Run tests to verify: `python tests/test_store_split_demo.py`

---

## 📝 Common Tasks

### "I want to see the store classification in action"
```bash
python demo_api.py
# Visit http://localhost:8000
```

### "I want to understand how classification works"
```bash
# Read the documentation
cat docs/architecture/STORE_CLASSIFICATION_SYSTEM.md

# See test examples
python tests/test_store_split_demo.py
```

### "I want to integrate this into my UI"
```python
from orchestrator.store_split import split_ingredients_by_store, format_store_split_for_ui

# Get store split
result = split_ingredients_by_store(ingredients, candidates)
ui_data = format_store_split_for_ui(result)

# ui_data = {
#   "primary_store": {"store": "FreshDirect", "count": 5},
#   "specialty_store": {"store": "Pure Indian Foods", "count": 3},
#   "unavailable": []
# }
```

---

## 🐛 Troubleshooting

### Import Errors
The store classification modules use standalone imports to avoid package issues:
```python
# If you see ImportError, use direct module loading:
import importlib.util
spec = importlib.util.spec_from_file_location("store_split", "path/to/store_split.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
```

### Tests Failing
```bash
# Check Python version (requires 3.10+)
python --version

# Re-run tests with verbose output
python tests/test_store_split_demo.py -v
```

---

## 📞 Quick Reference

- **Demo**: http://localhost:8000
- **Frontend** (if running): http://localhost:5173
- **API Docs**: http://localhost:8000/docs (when demo_api.py is running)
- **Tests**: `python tests/test_store_split_demo.py`
- **Main Docs**: `docs/architecture/STORE_CLASSIFICATION_SYSTEM.md`

---

**Last Updated**: 2026-01-29
**Maintainer**: Claude (Sonnet 4.5)
**Questions?** Check `/docs/architecture/` or run the demo!
