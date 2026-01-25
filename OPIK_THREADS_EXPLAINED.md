# Opik Threads vs Individual Traces - Explained

**Date**: 2026-01-24

---

## Current Behavior: Individual Traces (Not Threads)

With the current implementation using `track_anthropic()`, each LLM call appears as a **separate trace** in Opik, not as part of a conversation thread.

### What You'll See in Opik Dashboard

**Current setup shows**:
```
Trace 1: ingredient_extraction
  └─ API call: extract ingredients from "healthy dinner for 2"

Trace 2: decision_explanation
  └─ API call: explain why spinach product was chosen

Trace 3: decision_explanation
  └─ API call: explain why chicken product was chosen
```

Each trace is independent. This is **correct behavior** for the current implementation.

---

## Why No "Threads"?

### Opik Threads Require Explicit Grouping

**Threads in Opik** = Multiple related LLM calls grouped under a single conversation/session ID.

**Our current implementation**:
- Uses `track_anthropic(client)` - automatically tracks individual calls
- Each call gets its own trace
- No explicit grouping/threading

**To see threads**, we would need to:
1. Use `@opik.track()` decorator or context manager
2. Pass a `session_id` or `conversation_id` to group calls
3. Create a parent trace that contains child traces

---

## Option 1: Keep Current Setup (Recommended)

**Pros**:
- ✅ Simple, automatic tracking
- ✅ Every LLM call captured with full details
- ✅ Easy to search and filter by operation type
- ✅ Works out of the box with `track_anthropic()`

**Cons**:
- ❌ No visual grouping of related calls
- ❌ Can't see "cart creation session" as a single unit

**Use case**: When you want to track individual LLM calls independently.

---

## Option 2: Add Explicit Thread Tracking

If you want to see related calls grouped as a "cart creation session", here's how:

### Implementation Example

```python
# In orchestrator.py
from opik import track
import uuid

class Orchestrator:
    def process_prompt(self, prompt: str):
        # Generate session ID for this cart creation
        session_id = str(uuid.uuid4())

        # Wrap entire cart creation in a tracked session
        with track(
            name="cart_creation_session",
            metadata={
                "user_prompt": prompt,
                "session_id": session_id,
                "use_llm": self.use_llm_extraction
            }
        ):
            # All LLM calls within this block will be grouped
            ingredients = self._extract_ingredients(prompt, session_id)
            decisions = self._make_decisions(ingredients, session_id)
            return decisions
```

### What You'd See in Opik

```
Thread: cart_creation_session (session_abc123)
  ├─ Trace: ingredient_extraction
  │   └─ API call: extract ingredients
  ├─ Trace: decision_explanation (spinach)
  │   └─ API call: explain spinach choice
  ├─ Trace: decision_explanation (chicken)
  │   └─ API call: explain chicken choice
  └─ Trace: decision_explanation (rice)
      └─ API call: explain rice choice
```

All calls grouped under one session!

---

## Comparison Table

| Feature | Current Setup (Individual) | With Thread Tracking |
|---------|---------------------------|----------------------|
| **Setup complexity** | Simple | Moderate |
| **Automatic tracking** | ✅ Yes | ✅ Yes |
| **Group related calls** | ❌ No | ✅ Yes |
| **Session visibility** | ❌ No | ✅ Yes |
| **Cost per cart** | $0.045 | $0.045 (same) |
| **Search by operation** | ✅ Easy | ✅ Easy |
| **See full cart flow** | ❌ Manual | ✅ Visual |

---

## When to Use Each Approach

### Use Individual Traces (Current) When:
- ✅ You want simple automatic tracking
- ✅ You care about individual operation performance
- ✅ You want to compare similar operations across sessions
- ✅ You don't need session-level aggregation

### Use Thread Tracking When:
- ✅ You want to see full cart creation flow
- ✅ You need session-level cost totals
- ✅ You want to track user journey through cart creation
- ✅ You need to debug issues across multiple LLM calls in one session

---

## How to Add Thread Tracking (Step-by-Step)

If you want to implement thread tracking, here's the complete guide:

### 1. Update Orchestrator

```python
# conscious-cart-coach/src/orchestrator/orchestrator.py

from opik import track
import uuid

class Orchestrator:
    def process_prompt(
        self,
        prompt: str,
        servings: int = 4,
        session_id: str = None
    ) -> DecisionBundle:
        """Process prompt with optional session tracking."""

        # Generate session ID if not provided
        if session_id is None:
            session_id = str(uuid.uuid4())

        # Track entire cart creation as one session
        with track(
            name="cart_creation_session",
            tags=["orchestrator", "consciousbuyer"],
            metadata={
                "user_prompt": prompt,
                "servings": servings,
                "session_id": session_id,
                "use_llm_extraction": self.use_llm_extraction,
                "use_llm_explanations": self.use_llm_explanations
            }
        ):
            # Existing logic - all calls automatically grouped
            return self._process_internal(prompt, servings, session_id)

    def _process_internal(self, prompt, servings, session_id):
        # Your existing process_prompt logic here
        # All LLM calls will be children of the session trace
        ...
```

### 2. Pass Session ID to LLM Calls

```python
# In ingredient_extractor.py
def extract_ingredients_with_llm(
    client: Anthropic,
    prompt: str,
    servings: int = 4,
    session_id: str = None  # Add this
):
    response_text = call_claude_with_retry(
        client=client,
        prompt=formatted_prompt,
        max_tokens=2048,
        temperature=0.0,
        trace_name="ingredient_extraction",
        metadata={
            "user_prompt": prompt,
            "servings": servings,
            "session_id": session_id,  # Include session ID
            "operation": "extract_ingredients"
        }
    )
```

### 3. Update UI to Track Sessions

```python
# In app.py
import uuid

# In session state initialization
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = str(uuid.uuid4())

# When creating cart
def on_create_cart():
    # Generate new session ID for this cart
    session_id = str(uuid.uuid4())
    st.session_state.current_session_id = session_id

    orch = Orchestrator(
        use_llm_extraction=st.session_state.use_llm_extraction,
        use_llm_explanations=st.session_state.use_llm_explanations
    )

    bundle = orch.process_prompt(
        prompt=st.session_state.prompt_text,
        session_id=session_id  # Pass session ID
    )
```

---

## Testing Thread Tracking

### Without Thread Tracking (Current)

```bash
# Run test
pytest tests/test_llm.py::TestIngredientExtraction::test_extract_simple_recipe -v

# View in Opik dashboard
# You'll see: 1 trace named "ingredient_extraction"
```

### With Thread Tracking

```bash
# Run test with explicit thread
pytest tests/test_llm.py::TestLLMIntegration::test_full_workflow -v

# View in Opik dashboard
# You'll see: 1 thread "cart_creation_session" containing 2 traces
#   - ingredient_extraction
#   - decision_explanation
```

---

## Current Test Behavior

**Why tests show individual traces**:

Tests call LLM functions directly:
```python
def test_extract_simple_recipe(anthropic_client):
    ingredients = extract_ingredients_with_llm(
        client=anthropic_client,
        prompt="chicken biryani for 4",
        servings=4
    )
```

This creates **1 trace** per test, not a thread.

**To see threads in tests**, wrap in `@track()`:
```python
from opik import track

@pytest.mark.llm
@track(name="test_extract_with_thread")
def test_extract_simple_recipe(anthropic_client):
    ingredients = extract_ingredients_with_llm(...)
    # Now this appears as a thread in Opik
```

---

## Recommendation

### For Now: Keep Current Setup ✅

**Reasons**:
1. Simple and working
2. Individual traces are easier to analyze
3. Can search by operation type
4. No code changes needed

### Future Enhancement: Add Thread Tracking

**When you want**:
- Session-level cost tracking
- Full cart creation flow visibility
- User journey analysis

**Implementation time**: ~30 minutes

---

## Quick Fix: Run Tests with .env Loaded

Your ANTHROPIC_API_KEY issue is likely because .env isn't being loaded. I've fixed this in `conftest.py`:

```bash
# Make sure python-dotenv is installed
pip install python-dotenv

# Run tests (will now load .env automatically)
pytest -m llm -v
```

You should now see:
```
✅ Loaded environment from /path/to/.env
✅ Opik test tracking enabled
```

---

## Summary

| Question | Answer |
|----------|--------|
| **Why no threads?** | Using `track_anthropic()` creates individual traces, not threads |
| **Is this wrong?** | No! This is correct behavior for current setup |
| **How to add threads?** | Use `@opik.track()` decorator with session_id |
| **Should I add threads?** | Optional. Current setup works great for most use cases |
| **How to fix API key issue?** | Updated `conftest.py` to load `.env` automatically |

---

**Last updated**: 2026-01-24
**Current status**: Individual trace tracking (working as designed)
**Thread tracking**: Optional enhancement (not required)
