# Architecture Refactor Plan
**Goal**: Simplify to 4-layer architecture for hackathon reliability

## Files to Create

### Core Contracts & Engine
- [x] `src/contracts/cart_plan.py` - CartPlan output contract
- [ ] `src/planner/__init__.py` - Package init
- [ ] `src/planner/product_index.py` - Product retrieval with fresh produce merge
- [ ] `src/planner/engine.py` - Deterministic planner engine
- [ ] `src/planner/store_selector.py` - Multi-store optimization

### Data Layer
- [ ] `data/inventory_snapshots/fresh_store.csv` - Fresh Direct inventory
- [ ] `data/inventory_snapshots/specialty_store.csv` - Specialty inventory
- [ ] `data/store_catalog.json` - Store metadata + checkout URLs

### LLM Skills & Evaluation
- [ ] `docs/LLM_SKILLS.md` - LLM skill documentation
- [ ] `scripts/eval_llm_extraction.py` - Evaluation harness
- [ ] `tests/fixtures/extraction_test_cases.json` - Test prompts + expected outputs

### Tests
- [ ] `tests/test_cart_plan.py` - CartPlan contract validation
- [ ] `tests/test_product_index.py` - Fresh produce retrieval tests
- [ ] `tests/test_planner_engine.py` - End-to-end planner tests

## Files to Modify

### Integration Points
- [ ] `api/main.py` - Add /api/plan-v2 and /api/debug endpoints
- [ ] `src/orchestrator/orchestrator.py` - Use new planner engine
- [ ] `src/llm/ingredient_extractor.py` - Add deterministic fallback

## Files to Archive
- [ ] `archive/old_pipeline/store_split.py` - Old multi-store logic
- [ ] `archive/old_pipeline/decision_engine.py` - Old scoring system

## Success Criteria

### P0 - Fresh Produce Retrieval
```python
# Test: ginger search must include fresh + dried
candidates = product_index.retrieve("ginger")
assert any("Fresh" in c.title for c in candidates)
assert any("Granules" in c.title for c in candidates)
```

### P1 - Store Assignment Preserved
```python
# Test: store_id set in planner, never changes
plan = planner.create_plan(ingredients)
for item in plan.items:
    assert item.store_id in plan.store_plan.stores
    # No reassignment allowed after this point
```

### P2 - Tradeoff Tags Present
```python
# Test: cheaper_swap populated when available
plan = planner.create_plan(["organic chicken"])
item = plan.items[0]
assert item.cheaper_swap is not None
assert item.chips.tradeoffs  # "$3 more for organic"
```

## Implementation Order

1. **Phase 1**: CartPlan + ProductIndex (with tests)
2. **Phase 2**: PlannerEngine core (retrieve → enrich → select)
3. **Phase 3**: API integration + /debug endpoint
4. **Phase 4**: LLM docs + eval harness
5. **Phase 5**: UI adapter (CartPlan → old format)

## Rollout Strategy

- Keep old endpoints active (`/api/create-multi-cart`)
- Add new endpoint (`/api/plan-v2`)
- Feature flag: `USE_NEW_PLANNER=false` (default off)
- Cut over after 3 bugs verified fixed
