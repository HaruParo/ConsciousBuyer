# Architecture Documentation

**Last Updated**: 2026-01-25

This directory contains comprehensive documentation for the Conscious Cart Coach project. All project documentation is organized here.

## Quick Links

- 🚀 **[0-step.md](0-step.md)** - Start here! Main architecture guide
- 🎬 **[13-ideal-ui-workflow.md](13-ideal-ui-workflow.md)** - Demo guide & perfect user journey
- 🤖 **[6-llm-integration-deep-dive.md](6-llm-integration-deep-dive.md)** - Why hybrid AI approach
- 📊 **[9-opik-llm-evaluation.md](9-opik-llm-evaluation.md)** - Monitoring & evaluation
- 🚢 **[10-deployment-guide.md](10-deployment-guide.md)** - Deploy to production
- ✅ **[11-implementation-changelog.md](11-implementation-changelog.md)** - What's been built
- 🔧 **[12-troubleshooting-guide.md](12-troubleshooting-guide.md)** - Fix common issues

---

## Core Documentation

### [0-step.md](0-step.md) - Main Architecture Guide
**Start here!** Comprehensive walkthrough from high-level to technical implementation.

- High-level overview (problem, solution, users)
- Mid-level architecture (data flow, agents, decision logic)
- Technical details (code structure, data models, setup guide)
- Perfect for onboarding new developers

### [2-llm-integration-summary.md](2-llm-integration-summary.md) - LLM Integration
Technical implementation details for optional LLM features.

- Implementation plan and progress
- Design principles (deterministic scoring, graceful fallbacks)
- Cost considerations (~$0.045 per cart)
- Performance implications (1-4 sec latency)

### [3-usage-guide.md](3-usage-guide.md) - Usage Guide
Practical guide for using the system with code examples.

- Quick start and installation
- Three usage modes (deterministic, LLM extraction, full LLM)
- Step-by-step workflows
- API reference
- Cost/performance comparison
- Troubleshooting

### [4-ui-expectations.md](4-ui-expectations.md) - UI Expectations
Visual guide showing exactly what changes in the UI when LLM is enabled.

- Before/after comparisons
- Ingredient extraction differences
- Explanation style examples
- UI component recommendations
- Loading states and error handling
- Implementation checklist for frontend

---

## Deep Dive Documentation (Story-Driven)

### [5-technical-architecture.md](5-technical-architecture.md) - Technical Architecture
**The restaurant kitchen analogy.** How the system is built, why we made these choices, and what makes it work.

- Two-codebase structure explained
- Multi-agent system breakdown (each agent's job)
- Technology choices (Python, SQLite, Streamlit, Claude)
- The hybrid LLM strategy (AI for UX, deterministic for scoring)
- Data layer design (FactsStore + FactsGateway)
- Error handling philosophy (graceful degradation)
- Performance considerations
- What could be better (honest assessment)

### [6-llm-integration-deep-dive.md](6-llm-integration-deep-dive.md) - LLM Integration Deep Dive
**The AI that knows its place.** Why we chose a hybrid approach and how LLM is strategically integrated.

- The great LLM debate (why we didn't go full AI)
- Two strategic touchpoints (ingredient extraction, explanations)
- What we explicitly DON'T use LLM for (scoring, matching, totals)
- Cost analysis (~$0.045 per cart)
- Latency story (100ms vs 3.6 seconds)
- Failure modes and fallbacks
- API client implementation details
- Design principles (enhancement not requirement, deterministic is sacred)
- Future improvements (batching, caching, model selection)

### [7-ui-flows.md](7-ui-flows.md) - UI Flows
**The user's journey.** Walk through actual user experiences with screenshots and interactions.

- Journey 1: Quick recipe (Sarah's deterministic flow)
- Journey 2: Creative request (Alex's LLM-enhanced flow)
- Journey 3: Power user (Priya mixing modes)
- Screen-by-screen walkthrough
- What happens when you click buttons
- Edge cases and error states
- UI design principles (progressive disclosure, reversible actions, graceful degradation)
- Performance optimization in UI

### [8-data-flows.md](8-data-flows.md) - Data Flows
**Following the journey of a byte.** Trace data through the system from input to output.

- The river metaphor (user input as rain, agents as tributaries)
- Flow 1: Deterministic path (fast river, 100ms)
- Flow 2: LLM path (scenic route, 3.6 seconds)
- Flow 3: Error paths (when rivers overflow)
- Stage-by-stage data transformations
- Data storage (SQLite schema, indexes, caching)
- Data volume analysis (how much water we're moving)
- Bottlenecks and optimizations
- Complete end-to-end timing breakdown

### [9-opik-llm-evaluation.md](9-opik-llm-evaluation.md) - Opik LLM Evaluation
**Watching the watcher.** How we trace, evaluate, and debug all LLM calls with Opik.

- The black box problem (why we need tracing)
- What Opik is and why we integrated it
- Single integration point strategy (wrap once, trace everything)
- Data flow from user prompt to Opik dashboard
- What gets captured in traces (prompts, responses, costs, latency)
- How to read and search traces
- Common debugging workflows
- Architecture diagrams showing Opik integration
- Cost monitoring and optimization
- Troubleshooting guide
- Pytest integration for automated test tracking

### [10-deployment-guide.md](10-deployment-guide.md) - Deployment Guide
**Taking it live.** Complete deployment guide for production environments.

- Platform comparison (Streamlit Cloud, Render, Railway, Docker)
- Why NOT Vercel (Streamlit incompatibility)
- Step-by-step deployment (recommended: Streamlit Cloud, 5 minutes)
- Environment variables and secrets management
- Pre-deployment checklist
- Post-deployment monitoring setup
- Cost estimates ($0-25/month)
- Troubleshooting deployment issues
- Security checklist

### [11-implementation-changelog.md](11-implementation-changelog.md) - Implementation Changelog
**What's been built.** Complete changelog of all features and components implemented.

- Core system overview (multi-agent architecture, 3-tier cart system)
- LLM integration details (client, extractors, explainers)
- Opik monitoring integration (automatic tracing)
- Testing suite (30+ tests, pytest + Opik)
- UI features (toggles, indicators, explanations)
- Files changed and added
- Cost & performance metrics
- Environment setup guide
- Design principles achieved
- Next steps and future enhancements

### [12-troubleshooting-guide.md](12-troubleshooting-guide.md) - Troubleshooting Guide
**Fix common issues.** Comprehensive troubleshooting for all components.

- Environment setup issues (API keys, .env loading)
- LLM integration issues (failures, timeouts, hallucinations)
- Testing issues (skipped tests, timeouts, costs)
- Opik tracking issues (no traces, threads, local vs cloud)
- UI issues (duplicate keys, missing features)
- Deployment issues (build failures, database locks)
- Performance issues (slow responses, high costs)
- Debug mode and logging

### [13-ideal-ui-workflow.md](13-ideal-ui-workflow.md) - Ideal UI Workflow & Demo Guide
**The perfect demo.** Step-by-step user journey from landing to shopping list.

- 5-minute user journey walkthrough
- Act-by-act storytelling (landing, request, extraction, reveal, export)
- What happens behind the scenes (AI touchpoints, deterministic scoring)
- Perfect 2-minute demo pitch for stakeholders
- UI design principles that make it work
- Common demo pitfalls and how to avoid them
- Technical setup and demo checklist
- Variations for different audiences (PMs, engineers, business, users)
- Success metrics (immediate and post-demo)

---

## Quick Reference

### Current State (2026-01-24)

**Default Mode**: Deterministic (no LLM, no API calls)
- Free, fast, reliable
- Template-based ingredient extraction
- Rule-based decision scoring

**Optional LLM Features**:
- Ingredient extraction via Claude (natural language understanding)
- Decision explanations via Claude (detailed reasoning)
- Both disabled by default

### Usage Examples

```python
# Deterministic only (default)
orch = Orchestrator()
bundle = orch.process_prompt("biryani for 4")

# With LLM ingredient extraction
orch = Orchestrator(use_llm_extraction=True)
bundle = orch.process_prompt("I want something healthy")

# Full LLM (extraction + explanations)
orch = Orchestrator(
    use_llm_extraction=True,
    use_llm_explanations=True,
)
bundle = orch.process_prompt("healthy dinner ideas")
```

### Key Directories

```
conscious-cart-coach/
├── src/
│   ├── agents/              # IngredientAgent, ProductAgent, etc.
│   ├── engine/              # DecisionEngine (scoring logic)
│   ├── orchestrator/        # Flow coordinator
│   ├── llm/                 # LLM integration (optional)
│   ├── contracts/           # Data models
│   ├── ui/                  # Streamlit UI
│   └── data/                # FactsStore, FactsGateway
├── data/                    # CSV data (EWG, recalls, seasonal, stores)
├── tests/                   # 32+ integration tests
└── run.sh                   # Launch script
```

### Contact

For questions or contributions, see project README or open an issue.

Last updated: 2026-01-25
