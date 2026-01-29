# Opik Experiments & UI Mapping Guide

## What Shows Up in Opik Dashboard

This guide maps what happens in your code to what you see in the Opik UI at https://www.comet.com/opik.

---

## Your Code → Opik Dashboard

### 1. **Traces** (Main View)

**What it is**: One trace = one cart creation request

**In your code**:
```python
# api/main.py line 280
orch = Orchestrator(use_llm_extraction=True, use_llm_explanations=True)
result = orch.process_prompt("chicken biryani for 4", servings=4)
```

**In Opik UI**:
```
🔍 Traces (List View)

┌─────────────────────────────────────────────────────────────┐
│ Trace Name: process_prompt                                  │
│ Input: "chicken biryani for 4", servings=4                  │
│ Output: 12 items, $78.50 total                             │
│ Duration: 2.3s                                              │
│ Status: ✅ Success                                          │
│ Timestamp: 2026-01-28 18:45:23                             │
└─────────────────────────────────────────────────────────────┘
```

Click on a trace to drill down → see the step-by-step breakdown.

---

### 2. **Spans** (Inside a Trace)

**What it is**: Each agent/step within the orchestrator

**In your code**:
```python
# src/orchestrator/orchestrator.py
def process_prompt(self, user_prompt: str, servings: int):
    with self.tracker.trace("process_prompt"):           # ← Main trace
        self.tracker.track_step("step_ingredients", ...)  # ← Span 1
        self.tracker.track_step("step_candidates", ...)   # ← Span 2
        self.tracker.track_step("step_enrich", ...)       # ← Span 3
        self.tracker.track_step("step_decide", ...)       # ← Span 4
```

**In Opik UI** (drill-down view):
```
📊 Trace Timeline: process_prompt (2.3s total)

├─ step_ingredients (0.8s)
│  Input: "chicken biryani for 4"
│  Output: 8 ingredients extracted
│  ├─ LLM Call: claude-sonnet-4 (0.7s)
│  │  Tokens: 450 input, 120 output
│  │  Cost: $0.0032
│  └─ Metadata: use_llm=True
│
├─ step_candidates (0.6s)
│  Input: 8 ingredients
│  Output: 48 candidate products
│  Metadata: avg 6 products per ingredient
│
├─ step_enrich (0.3s)
│  Input: 48 candidates
│  Output: safety + seasonal signals
│  ├─ safety_agent (0.2s)
│  └─ seasonal_agent (0.1s)
│
└─ step_decide (0.6s)
   Input: 48 candidates + signals
   Output: 12 final items (3 tiers × 4 ingredients)
   Metadata: tier_distribution={CHEAPER: 4, BALANCED: 4, CONSCIOUS: 4}
```

---

### 3. **LLM Calls** (Nested in Spans)

**What it is**: Every Claude API call made during the request

**In your code**:
```python
# src/llm/ingredient_extractor.py
response = self.client.messages.create(
    model="claude-sonnet-4-20250514",
    messages=[{"role": "user", "content": prompt}]
)
```

**In Opik UI** (inside a span):
```
🤖 LLM Call: claude-sonnet-4-20250514

┌──────────────────────────────────────────────────┐
│ Provider: Anthropic                              │
│ Model: claude-sonnet-4-20250514                  │
│ Duration: 0.7s                                   │
│ Cost: $0.0032                                    │
│                                                  │
│ Tokens:                                          │
│   Input: 450 tokens ($0.0027)                   │
│   Output: 120 tokens ($0.0005)                  │
│                                                  │
│ Temperature: 0.3                                 │
│ Max Tokens: 1000                                 │
└──────────────────────────────────────────────────┘

📝 Prompt (click to expand)
───────────────────────────────────────────────────
Extract ingredients from: "chicken biryani for 4"
Return JSON format...

💬 Response (click to expand)
───────────────────────────────────────────────────
{
  "ingredients": [
    {"name": "chicken", "quantity": "2 lbs"},
    {"name": "basmati rice", "quantity": "2 cups"},
    ...
  ]
}
```

You can click to see the FULL prompt and response.

---

## Conducting Experiments

### Experiment Setup

**Question**: "How do I test if my new prompt is better than the old one?"

**Answer**: Use Opik's comparison features

#### Approach 1: Tags

**In your code**:
```python
# api/main.py

# Experiment A: Old prompt
orch_a = Orchestrator(use_llm_extraction=True)
with tracker.trace("process_prompt", metadata={"experiment": "prompt_v1"}):
    result_a = orch_a.process_prompt(meal_plan, servings)

# Experiment B: New prompt
orch_b = Orchestrator(use_llm_extraction=True)
with tracker.trace("process_prompt", metadata={"experiment": "prompt_v2"}):
    result_b = orch_b.process_prompt(meal_plan, servings)
```

**In Opik UI**:
```
🔬 Filter by metadata: experiment=prompt_v1
   → Shows all traces using old prompt

🔬 Filter by metadata: experiment=prompt_v2
   → Shows all traces using new prompt

📊 Compare:
   Prompt V1: Avg latency 2.3s, avg cost $0.032
   Prompt V2: Avg latency 1.8s, avg cost $0.028

   Winner: V2 is faster AND cheaper! ✅
```

#### Approach 2: Projects

Create separate Opik projects for each experiment:

```python
# In .env
OPIK_PROJECT_NAME=conscious-cart-v1  # Baseline
# vs
OPIK_PROJECT_NAME=conscious-cart-v2  # New version
```

Then compare projects side-by-side in Opik.

---

## What to Look For in Opik UI

### 1. **Performance Metrics**

**Navigation**: Dashboard → Traces → Sort by duration

**Look for**:
- **Slow traces**: > 5s (investigate bottleneck)
- **Fast traces**: < 2s (good!)
- **Outliers**: One agent taking 80% of time

**Example**:
```
Trace 1: 8.2s (⚠️ WHY SO SLOW?)
├─ step_ingredients: 0.8s
├─ step_candidates: 0.6s
├─ step_enrich: 6.5s  ← 🔴 BOTTLENECK!
└─ step_decide: 0.3s
```

**Action**: Investigate why `step_enrich` is slow. Is FDA API down?

---

### 2. **Cost Tracking**

**Navigation**: Dashboard → Traces → Cost column

**Look for**:
- **Cost per cart**: Should be ~$0.02 with LLM
- **Expensive outliers**: > $0.10 (investigate why)
- **Daily spend**: Track total cost

**Example**:
```
Today's Usage:
─────────────────────────────────────
100 carts created
Total cost: $2.10
Avg per cart: $0.021 ✅

LLM breakdown:
- Ingredient extraction: $1.20 (60%)
- Explanations: $0.90 (40%)
```

**Action**: If cost too high, consider:
- Shorter prompts
- Use Haiku instead of Sonnet
- Cache common queries

---

### 3. **Error Tracking**

**Navigation**: Dashboard → Traces → Filter by status=failed

**Look for**:
- **Failed traces**: Red ❌ indicator
- **Error messages**: Click to see stack trace
- **Failure patterns**: Does "pasta" always fail?

**Example**:
```
❌ Failed Trace: process_prompt
   Input: "gluten-free pasta for 2"
   Error: KeyError: 'pasta'

   Stack trace:
   File: src/agents/product_agent.py, line 234
   Cause: No products found for "pasta"
```

**Action**: Add pasta to synthetic inventory or handle missing products gracefully.

---

### 4. **Quality Metrics** (with LLM-as-a-Judge)

**In your code**:
```python
# After creating cart
from src.opik_integration.llm_judge import evaluate_recommendation

evaluation = evaluate_recommendation(meal_plan, servings, cart_items, total)

# Log to Opik
tracker.log_feedback(
    trace_id=current_trace_id,
    scores={
        "relevance": evaluation["dimensions"]["relevance"],
        "value": evaluation["dimensions"]["value"],
        "ethics": evaluation["dimensions"]["ethics"],
        "safety": evaluation["dimensions"]["safety"],
        "clarity": evaluation["dimensions"]["clarity"],
        "overall": evaluation["overall_score"]
    }
)
```

**In Opik UI**:
```
📈 Feedback Scores

Trace: "chicken biryani for 4"
┌─────────────────────────────┐
│ Relevance:  ⭐⭐⭐⭐⭐  5/5  │
│ Value:      ⭐⭐⭐⭐    4/5  │
│ Ethics:     ⭐⭐⭐⭐    4/5  │
│ Safety:     ⭐⭐⭐⭐⭐  5/5  │
│ Clarity:    ⭐⭐⭐⭐    4/5  │
│                             │
│ Overall:    4.2/5           │
│ Verdict:    Excellent ✅    │
└─────────────────────────────┘
```

You can then:
- Filter traces by score range (e.g., show all with score < 3)
- Compare average scores across experiments
- Find low-scoring carts to investigate

---

## UI Elements Map

### Main Dashboard
```
┌────────────────────────────────────────────────────────────┐
│ 🏠 Opik Dashboard                                          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Projects: [conscious-cart-coach ▼]                       │
│                                                            │
│  📊 Today's Stats:                                        │
│     • 127 traces                                          │
│     • 98.4% success rate                                  │
│     • 2.3s avg latency                                    │
│     • $2.84 total cost                                    │
│                                                            │
│  🔍 Traces (Recent)                                       │
│  ┌──────────────────────────────────────────────────┐    │
│  │ ✅ "chicken biryani for 4" | 2.1s | $0.021       │    │
│  │ ✅ "seasonal veggies"      | 1.8s | $0.019       │    │
│  │ ❌ "gluten-free pasta"     | 0.4s | $0.002       │    │
│  │ ✅ "salmon dinner for 2"   | 2.4s | $0.023       │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
│  Filters: [Status ▼] [Duration ▼] [Cost ▼] [Date ▼]     │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Trace Detail View
```
┌────────────────────────────────────────────────────────────┐
│ ← Back to Traces                                           │
├────────────────────────────────────────────────────────────┤
│ Trace: process_prompt                                      │
│ ID: tr_abc123xyz                                           │
│ Status: ✅ Success | Duration: 2.1s | Cost: $0.021        │
│                                                            │
│ 📥 Input:                                                  │
│    meal_plan: "chicken biryani for 4"                     │
│    servings: 4                                            │
│                                                            │
│ 📤 Output:                                                 │
│    items: 12 products                                     │
│    total: $78.50                                          │
│                                                            │
│ ⏱️  Timeline:                                              │
│  ├─ [████░░░░] step_ingredients (0.8s)                    │
│  ├─ [███░░░░░] step_candidates (0.6s)                     │
│  ├─ [█░░░░░░░] step_enrich (0.3s)                         │
│  └─ [██░░░░░░] step_decide (0.4s)                         │
│                                                            │
│ 🤖 LLM Calls:                                              │
│  • claude-sonnet-4: 450 in, 120 out | $0.0032            │
│  • claude-sonnet-4: 780 in, 340 out | $0.0056            │
│                                                            │
│ 📊 Feedback:                                               │
│  • Overall Score: 4.2/5                                   │
│  • Verdict: Excellent                                     │
│                                                            │
│ [View Full Trace JSON] [Compare] [Export]                │
└────────────────────────────────────────────────────────────┘
```

### Comparison View
```
┌────────────────────────────────────────────────────────────┐
│ Compare Experiments                                        │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Experiment A: prompt_v1 (50 traces)                      │
│  Experiment B: prompt_v2 (50 traces)                      │
│                                                            │
│  Metric         │ Prompt V1  │ Prompt V2  │ Δ           │
│  ───────────────┼────────────┼────────────┼─────────────│
│  Avg Latency    │ 2.3s       │ 1.8s       │ -22% 🟢     │
│  Success Rate   │ 96%        │ 98%        │ +2% 🟢      │
│  Avg Cost       │ $0.032     │ $0.028     │ -13% 🟢     │
│  Quality Score  │ 4.1/5      │ 4.3/5      │ +0.2 🟢     │
│                                                            │
│  Winner: Prompt V2 is better across all metrics! ✅       │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Example Experiment Workflow

### Scenario: Test if removing LLM extraction improves speed

**Step 1: Baseline** (current state)
```python
# api/main.py
orch = Orchestrator(
    use_llm_extraction=True,   # Uses Claude to parse
    use_llm_explanations=True
)

# Add metadata
with tracker.trace("process_prompt", metadata={"experiment": "llm_extraction_on"}):
    result = orch.process_prompt(meal_plan, servings)
```

Run 50 test carts, note in Opik:
- Avg latency: 2.3s
- Avg cost: $0.032
- Success rate: 98%

**Step 2: Experiment** (new approach)
```python
# api/main.py
orch = Orchestrator(
    use_llm_extraction=False,  # Uses templates instead
    use_llm_explanations=True
)

# Add metadata
with tracker.trace("process_prompt", metadata={"experiment": "llm_extraction_off"}):
    result = orch.process_prompt(meal_plan, servings)
```

Run 50 test carts, note in Opik:
- Avg latency: 1.1s (⚡ 52% faster!)
- Avg cost: $0.012 (💰 62% cheaper!)
- Success rate: 92% (⚠️ 6% worse)

**Step 3: Compare in Opik**
1. Go to Traces
2. Filter: `metadata.experiment=llm_extraction_on`
3. Export metrics
4. Filter: `metadata.experiment=llm_extraction_off`
5. Export metrics
6. Compare side-by-side

**Step 4: Decision**
- Templates are faster and cheaper ✅
- But 6% lower success rate ❌
- **Decision**: Use templates for known recipes, LLM for complex requests

---

## Quick Reference

### What Opik Tracks Automatically
✅ Every trace (cart creation)
✅ Every span (agent step)
✅ Every LLM call (with tokens/cost)
✅ Duration for each step
✅ Input/output for each step
✅ Success/failure status
✅ Timestamps

### What You Need to Add Manually
⚠️ Experiment tags (`metadata={"experiment": "v2"}`)
⚠️ Custom metrics (quality scores)
⚠️ Business metrics (user satisfaction, conversion rate)
⚠️ Feedback loops (LLM-as-a-Judge scores)

### Where to Look For...

| What You Want | Where in Opik UI |
|--------------|------------------|
| Slow requests | Traces → Sort by duration DESC |
| Failed requests | Traces → Filter status=failed |
| Expensive requests | Traces → Sort by cost DESC |
| LLM prompt/response | Trace detail → LLM Calls → Click to expand |
| Compare experiments | Traces → Group by metadata → Export |
| Daily cost | Dashboard → Cost graph |
| Quality trends | Traces → Feedback scores |

---

## Best Practices

1. **Always tag experiments**
   ```python
   metadata={"experiment": "prompt_v3", "date": "2026-01-28"}
   ```

2. **Log quality scores**
   ```python
   tracker.log_feedback(trace_id, scores={"overall": 4.2})
   ```

3. **Use consistent naming**
   - trace name: always `"process_prompt"`
   - span names: `"step_ingredients"`, `"step_candidates"`, etc.

4. **Filter strategically**
   - Time range: Last 24 hours (for daily monitoring)
   - Status: Failed only (for debugging)
   - Metadata: experiment=v2 (for A/B tests)

5. **Export data for analysis**
   - Opik has export → CSV feature
   - Load into Python/Excel for deeper analysis
