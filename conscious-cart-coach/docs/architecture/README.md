# Architecture Documentation

> **📌 Current Version: React + FastAPI Full-Stack (v2.0)**
> Historical references to Streamlit are from v1.0. The current production version uses React frontend with FastAPI backend.

This directory contains comprehensive documentation for the Conscious Cart Coach project.

---

## 🚀 Getting Started

### [0-step.md](0-step.md) - Complete Architecture Guide ⭐ START HERE
**Your comprehensive walkthrough** from high-level concepts to technical implementation.

- Problem statement and solution overview
- System architecture and data flows
- Agent breakdown and decision logic
- Code structure and setup guide
- Perfect for onboarding developers

---

## 📚 Core Technical Docs

### [5-technical-architecture.md](5-technical-architecture.md) - Technical Architecture
**The restaurant kitchen analogy.** Deep dive into how the system is built.

- Full-stack architecture (React + FastAPI)
- Multi-agent system breakdown
- Technology choices and rationale
- Hybrid LLM strategy (AI for UX, deterministic for scoring)
- Data layer design (FactsStore + FactsGateway)
- Error handling and performance

### [7-ui-flows.md](7-ui-flows.md) - UI Flows & User Journeys
**Walk through actual user experiences** with different interaction patterns.

- Deterministic flow (fast, no LLM)
- LLM-enhanced flow (natural language)
- React/HTML demo flow (hackathon edition)
- Screen-by-screen walkthroughs
- Edge cases and error states
- UI design principles

### [8-data-flows.md](8-data-flows.md) - Data Flows
**Following the journey of data** from user input to shopping cart.

- The river metaphor (6-stage pipeline)
- Data transformations at each stage
- Timing breakdowns and bottlenecks
- Database schema and indexes
- Performance optimizations

---

## 🤖 LLM Integration

### [2-llm-integration-summary.md](2-llm-integration-summary.md) - LLM Integration Summary
Quick reference for optional LLM features.

- Implementation plan and status
- Design principles (deterministic-first)
- Cost analysis (~$0.045 per cart)
- Performance implications (1-4s latency)

### [6-llm-integration-deep-dive.md](6-llm-integration-deep-dive.md) - LLM Deep Dive
**Why we chose a hybrid approach** and how AI is strategically integrated.

- The great LLM debate (not full AI)
- Two strategic touchpoints (extraction, explanations)
- What we DON'T use LLM for (scoring stays deterministic)
- Failure modes and fallbacks
- API implementation details
- Future improvements

### [9-opik-llm-evaluation.md](9-opik-llm-evaluation.md) - Opik LLM Evaluation
**Tracing and debugging LLM calls** with Opik observability.

- The black box problem
- Opik integration strategy
- Trace analysis and debugging workflows
- Cost monitoring
- Troubleshooting guide

---

## 🛒 Feature Specifications

### [CONSCIOUS_BUYING_PHILOSOPHY.md](CONSCIOUS_BUYING_PHILOSOPHY.md) - Buying Philosophy
**Core principles** behind the conscious buying system.

- What makes a purchase "conscious"
- Ethical sourcing principles
- Safety and seasonality priorities
- Three-tier recommendation logic

### [CONSCIOUS_BUYING_SYSTEM.md](CONSCIOUS_BUYING_SYSTEM.md) - Buying System
**How the recommendation engine works** under the hood.

- Scoring algorithm details
- Safety data integration (EWG, FDA recalls)
- Seasonal preference logic
- Tier assignment rules

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

---

## 📖 Usage & Setup

### [3-usage-guide.md](3-usage-guide.md) - Usage Guide
**Practical guide** with code examples and workflows.

- Quick start and installation
- Three usage modes (deterministic, LLM extraction, full LLM)
- Step-by-step API workflows
- Cost/performance comparison
- Troubleshooting

### [4-ui-expectations.md](4-ui-expectations.md) - UI Expectations
**Visual guide** showing UI changes with LLM features.

- Before/after comparisons
- Ingredient extraction differences
- Explanation style examples
- Loading states and error handling
- Frontend implementation checklist

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

## 🔗 Quick Links

- **Start developing**: See [project README.md](../../README.md)
- **Run the app**: `./run.sh` from project root (starts React + FastAPI)
- **Access frontend**: http://localhost:5173
- **Access API**: http://localhost:8000/docs

---

Last updated: 2026-01-29
