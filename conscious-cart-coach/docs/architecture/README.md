# Architecture Documentation

> **📌 Current Version: React + FastAPI Full-Stack (v2.0)**
> Historical references to Streamlit are from v1.0. The current production version uses React frontend with FastAPI backend.

This directory contains comprehensive documentation for the Conscious Cart Coach project.

---

## 🚀 Getting Started

### [architecture-overview.md](architecture-overview.md) - Complete Architecture Guide ⭐ START HERE
**Your comprehensive walkthrough** from high-level concepts to technical implementation.

- Problem statement and solution overview
- System architecture and data flows
- Agent breakdown and decision logic
- Code structure and setup guide
- Perfect for onboarding developers

---

## 📚 Core Technical Docs

### [technical-stack.md](technical-stack.md) - Technical Architecture
**The restaurant kitchen analogy.** Deep dive into how the system is built.

- Full-stack architecture (React + FastAPI)
- Multi-agent system breakdown
- Technology choices and rationale
- Hybrid LLM strategy (AI for UX, deterministic for scoring)
- Data layer design (FactsStore + FactsGateway)
- Error handling and performance

### [ui-user-flows.md](ui-user-flows.md) - UI Flows & User Journeys
**Walk through actual user experiences** with different interaction patterns.

- Deterministic flow (fast, no LLM)
- LLM-enhanced flow (natural language)
- React/HTML demo flow (hackathon edition)
- Screen-by-screen walkthroughs
- Edge cases and error states
- UI design principles

### [data-pipeline.md](data-pipeline.md) - Data Pipeline
**Following the journey of data** from user input to shopping cart.

- The river metaphor (6-stage pipeline)
- Data transformations at each stage
- Timing breakdowns and bottlenecks
- Database schema and indexes
- Performance optimizations

---

## 🤖 LLM Integration

### [llm-integration.md](llm-integration.md) - LLM Deep Dive
**Why we chose a hybrid approach** and how AI is strategically integrated.

- The great LLM debate (not full AI)
- Two strategic touchpoints (extraction, explanations)
- What we DON'T use LLM for (scoring stays deterministic)
- Failure modes and fallbacks
- API implementation details
- Future improvements

### [llm-monitoring-opik.md](llm-monitoring-opik.md) - Opik LLM Evaluation
**Tracing and debugging LLM calls** with Opik observability.

- The black box problem
- Opik integration strategy
- Trace analysis and debugging workflows
- Cost monitoring
- Troubleshooting guide

---

## 🛒 Feature Specifications

### [DATA_SOURCE_STRATEGY.md](DATA_SOURCE_STRATEGY.md) - Data Source Strategy
**Where our data comes from** and how we maintain it.

- EWG Dirty Dozen/Clean Fifteen
- FDA recall integration
- NJ crop calendar (seasonality)
- Store and regional data
- Refresh schedules and automation

### [MULTI_STORE_CART_SYSTEM.md](MULTI_STORE_CART_SYSTEM.md) - Multi-Store Carts
**Shopping across multiple stores** feature specification.

- Store availability by region
- Cart splitting logic
- Price comparison across stores
- User preferences per store

### [STORE_CLASSIFICATION_SYSTEM.md](STORE_CLASSIFICATION_SYSTEM.md) - Store Classification (v2.0)
**Dynamic ingredient classification** for multi-store routing.

- Pattern-based classification (no static fields)
- 1-item efficiency rule
- Urgency-aware store selection
- Clean product data approach

---

## 🏗️ Current Stack (v2.0)

**Frontend**: React + Vite + Tailwind CSS
**Backend**: FastAPI + Python
**Database**: SQLite (FactsStore)
**LLM**: Claude (Anthropic) - Optional
**Observability**: Opik - Optional

**Default Mode**: Deterministic (no LLM, no API calls)
- Free, fast (<100ms), reliable
- Template-based ingredient extraction
- Rule-based decision scoring

**Optional LLM Features**:
- Natural language ingredient extraction
- Detailed decision explanations
- Both disabled by default

---

## 📁 Project Structure

```
ConsciousBuyer/
└── conscious-cart-coach/          # Main application (CONSOLIDATED)
    ├── Figma_files/              # React Frontend (v2.0 - CURRENT)
    ├── api/                      # FastAPI Backend
    ├── src/
    │   ├── agents/               # Product, Safety, Seasonal agents
    │   ├── engine/               # DecisionEngine (scoring)
    │   ├── orchestrator/         # Flow coordinator
    │   ├── llm/                  # Optional LLM integration
    │   └── data/                 # FactsStore, FactsGateway
    ├── data/                     # CSV data (EWG, recalls, etc.)
    ├── tests/                    # Integration tests
    └── docs/                     # All documentation
        ├── architecture/         # THIS FOLDER - Architecture docs
        ├── project-history/      # Development history (archived)
        ├── CLAUDE.md
        ├── IMPLEMENTATION_COMPLETE.md
        └── *.md                  # Other project docs
```

---

## 🚀 Quick Start

- **Run demo**: `python demo_api.py` from project root
- **Access demo**: http://localhost:8000
- **Run tests**: `python tests/test_store_split_demo.py`
- **Read overview**: Start with [architecture-overview.md](architecture-overview.md)

---

Last updated: 2026-01-29
