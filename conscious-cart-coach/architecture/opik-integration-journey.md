# Opik Integration Journey
## Optimizing LLM Performance for Conscious Cart Coach

---

## Slide 1: Prompt Optimization with Opik Assist

### The Challenge
Our initial LLM prompts were verbose and costly, consuming **2,353 tokens** per request.

### Opik Assist Recommendations
- Move reusable instructions to **system prompt** (enables caching)
- Remove redundant examples from user prompts
- Consolidate verbose formatting instructions

### Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Token Count | ~2,353 | ~500-600 | **75% reduction** |
| API Cost | Baseline | -75% | Significant savings |
| Cache Efficiency | None | Enabled | System prompt caching |

---

## Slide 2: Experiment-Driven Evaluation

### Datasets Created

**Ingredient Extraction Test**
```
Input: "chicken biryani for 4"
Expected: ["chicken", "basmati rice", "onion", "yogurt", "ginger", "garlic"]
```

**Decision Explanation Test**
```
Input: Olive oil recommendation
Product: California Olive Ranch ($12.99)
Cheaper Option: Store brand ($7.99)
Should Mention: ["California", "quality"]
```

### Experiment Results

| Experiment | Latency | Quality Score |
|------------|---------|---------------|
| Ingredient Extractor | 4.6s | 0.8 avg coverage |
| Decision Explainer | 1.3s | 0.6 quality, 0.7 length |

---

## Slide 3: Batching Optimization (Traced with Opik)

### The Problem
Initial implementation made **N+1 LLM calls** per request:
- 1 call for ingredient extraction
- N calls for decision explanations (one per ingredient)

With 21 ingredients, that's **22 API calls** → hitting rate limits!

### The Solution
Batch all explanations into a **single LLM call**:

```python
# BEFORE: N separate calls
for item in cart_items:
    explanation = explain_decision_with_llm(client, item)  # 1 call each

# AFTER: 1 batched call
explanations = explain_decisions_batch(client, all_items)  # Returns JSON
```

### Opik Trace Comparison

| Approach | Traces | Latency | Rate Limit Safe |
|----------|--------|---------|-----------------|
| Individual calls | N+1 traces | ~N×1.5s | ❌ Hits 15 req/min |
| Batched call | 2 traces | ~3s total | ✅ Well under limit |

### Batch Response Format
```json
{
  "chicken": "Perdue at $8.99 offers...",
  "basmati rice": "Lundberg organic at $6.49...",
  "onion": "Yellow onions at $0.99/lb..."
}
```

**Opik traces showed the dramatic reduction in API calls and helped us validate the batched output quality.**

---

## Slide 4: Online Evaluation with LLM-as-Judge

### Implementation
Used Opik's online evaluation to score production responses in real-time.

### Judge Prompt
> *"You are an impartial AI judge. Evaluate if the assistant's output effectively addresses the user's input. Consider: accuracy, completeness, and relevance."*

### Sample Evaluation Response
```json
{
  "Correctness": {
    "score": true,
    "reason": "The output accurately explains the recommendation
               for Pure Indian Foods salt by highlighting its organic
               certification, affordability, and clean EWG rating."
  }
}
```

---

## Slide 5: Human Review with Annotation Queues

### The Need
Automated scoring catches most issues, but edge cases require human judgment.

### Annotation Queue Setup
Created review queues for traces that need human validation:

```
Traces with score < 0.8  →  Annotation Queue  →  Human Review
```

### Review Workflow

| Step | Action |
|------|--------|
| 1. Queue | Low-confidence traces auto-added to review queue |
| 2. Review | Human reviewer sees input, output, and LLM scores |
| 3. Annotate | Add labels: correct, incorrect, hallucination |
| 4. Export | Build curated dataset from reviewed samples |

### Annotations Added
- **Correctness labels** - Binary pass/fail on ingredient extraction
- **Quality scores** - 1-5 rating on explanation clarity
- **Edge case tags** - Flagged unusual ingredient combinations

---

## Slide 6: Key Takeaways

### What Opik Enabled

1. **Visibility** - Traced every LLM call with inputs, outputs, and latency
2. **Optimization** - Reduced token usage by 75% with Opik Assist
3. **Batching Insights** - Traced N+1 → 2 calls optimization clearly
4. **Quality Assurance** - Automated scoring with custom metrics
5. **Production Monitoring** - Real-time evaluation with LLM-as-Judge
6. **Human-in-the-Loop** - Annotation queues for edge case review

### Impact on Conscious Cart Coach

| Area | Improvement |
|------|-------------|
| Token Costs | 75% reduction |
| API Calls | 91% reduction (22 → 2 calls) |
| Prompt Quality | Measurable via experiments |
| Response Accuracy | Validated with LLM judge |
| Edge Cases | Caught via human annotation |
| Development Velocity | Faster iteration with traces |

---

*Powered by Opik - LLM Observability & Evaluation Platform*
