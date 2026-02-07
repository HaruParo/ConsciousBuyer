# Conscious Cart Coach - Architecture Documentation

> **Purpose**: Comprehensive documentation explaining how Conscious Cart Coach works, why we made certain technical decisions, and how to work with the codebase.

## Who This Is For

- **New developers** joining the project
- **LLM agents** helping with development and debugging
- **Future you** when you forget why something was built a certain way
- **Contributors** who want to understand the philosophy before submitting PRs

## Reading Guide

### Start Here (First Time)
1. **[Mental Models & Design Decisions](./05-mental-models.md)** - Understand the "why" before the "how"
2. **[Technical Architecture](./01-technical-architecture.md)** - Get the big picture of how components connect
3. **[UI Flows](./03-ui-flows.md)** - See how users experience the system

### Deep Dives (When You Need Details)
4. **[Data Flows](./04-data-flows.md)** - Understand how products get from CSV to cart
5. **[LLM Integration](./02-llm-integration.md)** - AI enhancement strategy (now active!)
6. **[LLM Skills Guide](./06-llm-skills.md)** - Working with LLM modules
7. **[Agents Architecture](./07-agents.md)** - All agents, their responsibilities, and examples

## The Seven Documents

### 01. Technical Architecture
**What it covers**:
- The tech stack (Python/FastAPI, React/TypeScript, CSV data)
- How the components connect (agents, orchestrator, API, frontend)
- File structure and organization
- Key technical decisions (why CSV not database, why agent pattern, etc.)

**Read this when**:
- Setting up the development environment
- Understanding the codebase structure
- Making architectural changes

### 02. LLM Integration
**What it covers**:
- Current rule-based vs future LLM-enhanced approach
- How each agent will use LLMs (ingredient extraction, product matching, explanations)
- Cost and performance considerations
- Implementation roadmap (which agents to enhance first)

**Read this when**:
- Adding LLM features
- Optimizing LLM costs
- Understanding the AI strategy

### 07. Agents Architecture
**What it covers**:
- All agents (Ingredient, Product, Safety, Seasonal, UserHistory)
- Agent responsibilities and methods
- Orchestrator flow and gating
- Code examples for each agent
- LLM client integration

**Read this when**:
- Working with agents
- Adding a new agent
- Understanding the orchestration flow
- Debugging agent behavior

### 03. UI Flows
**What it covers**:
- User journey from input to cart
- Modal interactions (ingredient confirmation, product swaps)
- Mobile responsiveness design
- Loading states and error handling
- Future streaming cart creation

**Read this when**:
- Working on frontend features
- Designing new UI components
- Improving user experience
- Debugging frontend issues

### 04. Data Flows
**What it covers**:
- How product data loads from CSV
- Product matching algorithm (fuzzy search, ranking, store filtering)
- Quantity calculation logic (unit conversion, size optimization)
- Multi-store cart splitting
- The ranking/scoring system (how products are chosen)

**Read this when**:
- Adding new products to the database
- Changing product selection logic
- Understanding why a specific product was chosen
- Debugging cart creation issues

### 05. Mental Models & Design Decisions
**What it covers**:
- The conscious buyer philosophy
- Why multi-store carts matter
- The three-tier system (cheaper/balanced/conscious)
- Organic hierarchy (Dirty Dozen prioritization)
- Authenticity over convenience principle
- Trade-off transparency

**Read this when**:
- Making product-related decisions
- Questioning "why did we do it this way?"
- Onboarding new team members
- Planning new features

## Quick Reference

### Common Questions

**Q: Why CSV files instead of a database?**
A: See [Mental Models - Design Decision: CSV vs Database](./05-mental-models.md#design-decision-why-csv-instead-of-database)

**Q: How does product matching work?**
A: See [Data Flows - Flow 3: Ingredients → Products](./04-data-flows.md#flow-3-ingredients-→-products-product-agent)

**Q: How do I add LLM features?**
A: See [LLM Integration - Implementation Roadmap](./02-llm-integration.md#the-implementation-roadmap)

**Q: Why do we split carts across stores?**
A: See [Mental Models - Multi-Store Reality](./05-mental-models.md#mental-model-1-the-multi-store-reality)

**Q: How does quantity calculation work?**
A: See [Data Flows - Flow 4: Products → Quantities](./04-data-flows.md#flow-4-products-→-quantities-quantity-agent)

**Q: How do I add a new store?**
A: See [Data Flows - Store Inference Logic](./04-data-flows.md#store-inference-logic)

### Common Tasks

**Adding a new product**:
1. Read [Data Flows - The Source: source_listings.csv](./04-data-flows.md#the-source-source_listingscsv)
2. Add row to `data/alternatives/source_listings.csv`
3. Verify size field is specific (not "varies")
4. Update `STORE_EXCLUSIVE_BRANDS` if needed
5. Restart backend to reload CSV

**Changing product selection logic**:
1. Read [Data Flows - Stage 3: Ranking Algorithm](./04-data-flows.md#stage-3-detail-ranking-algorithm)
2. Modify `src/agents/product_agent.py` scoring system
3. Test with real meal plans
4. Document changes in git commit

**Adding a new UI component**:
1. Read [UI Flows - The Main Interface](./03-ui-flows.md#the-main-interface-split-screen-design)
2. Create component in `frontend/src/app/components/`
3. Follow existing patterns (TypeScript, Tailwind CSS)
4. Add to `App.tsx` or relevant parent component

**Enhancing an agent with LLM**:
1. Read [LLM Integration - Agent-by-Agent Plan](./02-llm-integration.md#agent-by-agent-llm-integration-plan)
2. Add `anthropic_client` parameter to agent
3. Implement LLM-enhanced version with fallback to rules
4. Add cost monitoring and logging
5. A/B test before full rollout

## Key Mental Models (Quick Summary)

### The Core Philosophy
> Grocery shopping is a values problem, not just a logistics problem.

### The User Journey
1. User expresses intent ("chicken biryani for 4")
2. System understands context (Indian cuisine, 4 servings)
3. System finds authentic ingredients (Pure Indian Foods spices)
4. System splits cart by store (produce from FreshDirect, spices from specialty)
5. System explains choices (transparent reasoning)

### The Three Principles
1. **Multi-store**: Different stores serve different needs
2. **Transparency**: Show why each product was chosen
3. **Values-alignment**: Organic where it matters, local when possible, authentic for specialty items

## Codebase Overview

```
conscious-cart-coach/
├── architecture/           ← You are here (documentation)
│   ├── README.md
│   ├── 01-technical-architecture.md
│   ├── 02-llm-integration.md
│   ├── 03-ui-flows.md
│   ├── 04-data-flows.md
│   ├── 05-mental-models.md
│   ├── 06-llm-skills.md
│   └── 07-agents.md
│
├── api/
│   └── main.py            ← FastAPI endpoints (/api/plan-v2)
│
├── src/
│   ├── agents/            ← Ingredient, Product, Safety agents
│   ├── contracts/         ← Data models (CartPlan, CartItem)
│   ├── llm/               ← LLM modules (ingredient_extractor, decision_explainer)
│   ├── planner/           ← PlannerEngine (core planning logic)
│   ├── scoring/           ← Component scoring system
│   ├── utils/             ← Unified LLM client, helpers
│   └── data/              ← EWG categories, form constraints
│
├── data/
│   ├── inventories/       ← Store product inventories (CSV)
│   └── source_listings.csv ← Consolidated product database
│
├── frontend/
│   └── src/app/           ← React/TypeScript UI
│       ├── components/    ← CartItemCard, MultiStoreCart, etc.
│       └── services/      ← API client
│
├── index.py               ← Vercel serverless entry point
└── vercel.json            ← Vercel deployment config
```

## Contributing Guidelines

### Before Making Changes
1. Read the relevant architecture document
2. Understand the mental model behind the feature
3. Check if your change aligns with project values
4. Consider impact on multi-store cart splitting

### When Adding Features
1. Start with the mental model (why does this feature exist?)
2. Design the data flow (how does data move through the system?)
3. Implement with clear variable names and comments
4. Add tests for critical paths
5. Document in commit message

### When Fixing Bugs
1. Understand the intended behavior (check architecture docs)
2. Identify where actual behavior diverges
3. Fix root cause, not symptoms
4. Add regression test
5. Update docs if behavior changed

## Keeping Documentation Updated

### When to Update These Docs

**Update immediately when**:
- Architecture changes (new agent, new service, database migration)
- Mental model shifts (change in product selection philosophy)
- Major features added (LLM integration, new store support)

**Update eventually when**:
- Bug fixes that reveal misunderstanding in docs
- Performance optimizations that change recommendations
- UI/UX changes that affect user flows

**Don't update for**:
- Minor bug fixes
- Code refactoring that doesn't change behavior
- CSS tweaks

### How to Update

1. Identify which document(s) need updating
2. Read the existing section to understand context
3. Make minimal, focused edits (don't rewrite entire sections)
4. Keep the engaging, narrative style
5. Update the "Last Updated" timestamp at the bottom

## Last Updated

**Created**: February 1, 2026
**Last Modified**: February 7, 2026
**Version**: 2.0 (Post-cleanup, LLM integration enabled)

## Questions or Feedback?

If these docs don't answer your question or something is unclear:
1. Check the code directly (sometimes code is clearer than docs)
2. Ask in team chat/discussion
3. Propose documentation improvements

Remember: **Good documentation is a conversation starter, not a conversation ender.**

