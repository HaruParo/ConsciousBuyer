# Architecture Documentation

This directory contains comprehensive documentation for the Conscious Cart Coach project.

## Documents

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

Last updated: 2026-01-24
