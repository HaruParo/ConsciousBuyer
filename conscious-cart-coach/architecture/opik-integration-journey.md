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

## Slide 3: Online Evaluation with LLM-as-Judge

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

## Slide 4: Key Takeaways

### What Opik Enabled

1. **Visibility** - Traced every LLM call with inputs, outputs, and latency
2. **Optimization** - Reduced token usage by 75% with Opik Assist
3. **Quality Assurance** - Automated scoring with custom metrics
4. **Production Monitoring** - Real-time evaluation with LLM-as-Judge

### Impact on Conscious Cart Coach

| Area | Improvement |
|------|-------------|
| Token Costs | 75% reduction |
| Prompt Quality | Measurable via experiments |
| Response Accuracy | Validated with LLM judge |
| Development Velocity | Faster iteration with traces |

---

*Powered by Opik - LLM Observability & Evaluation Platform*
