# LLM Integration: Teaching the Cart to Think

## Current Implementation Status (Updated Feb 2025)

| Feature | Status | Implementation |
|---------|--------|----------------|
| **Ingredient Extraction** | ✅ Enabled | `src/llm/ingredient_extractor.py` - Claude extracts ingredients from natural language |
| **Decision Explanations** | ✅ Enabled | `src/llm/decision_explainer.py` - Claude generates natural language reasons |
| **Product Scoring** | ✅ Deterministic | `src/planner/engine.py` - Rules-based scoring (100% reproducible) |
| **LLM Observability** | ✅ Enabled | Opik integration for tracing and cost monitoring |

### How It Works Now

```
User: "chicken biryani for 4"
         ↓
┌─────────────────────────────────────────────────────────┐
│  1. INGREDIENT EXTRACTION (LLM)                         │
│     src/llm/ingredient_extractor.py                     │
│     → Claude extracts: chicken, basmati rice, ginger... │
│     → Fallback: deterministic rules if LLM fails        │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│  2. PRODUCT MATCHING & SCORING (Deterministic)          │
│     src/planner/engine.py                               │
│     → Multi-factor scoring (EWG, organic, price, form)  │
│     → Same input = same output (no LLM randomness)      │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│  3. DECISION EXPLANATIONS (LLM)                         │
│     src/llm/decision_explainer.py                       │
│     → Claude explains: "Organic spinach at $3.99..."    │
│     → Fallback: deterministic reason if LLM fails       │
└─────────────────────────────────────────────────────────┘
```

### LLM Provider Configuration

```python
# Environment variables
LLM_PROVIDER=anthropic          # or "ollama" for local
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-haiku-20240307  # Cost-optimized

# Opik observability
OPIK_API_KEY=...
OPIK_PROJECT_NAME=consciousbuyer
```

### Cost Per Cart (Optimized Prompts)

| Component | Tokens | Cost |
|-----------|--------|------|
| Ingredient Extraction | ~600 in + ~100 out | ~$0.001 |
| Decision Explanations (10 items) | ~150 in + ~50 out × 10 | ~$0.01 |
| **Total per cart** | | **~$0.01** |

---

## The Vision: From Rule-Based to AI-Enhanced Shopping

Conscious Cart Coach uses a **hybrid approach**:
- **Rules** for deterministic scoring (reproducible, fast, free)
- **LLM** for understanding and explaining (flexible, natural, costs money)

Think of it like a kitchen with both a precise scale and an experienced chef:
- **The scale** (rules): Always gives exact measurements, never deviates, costs nothing to use
- **The chef** (LLM): Understands "a pinch of this, until it looks right", adapts to context, but takes time

### When to Use Rules
- **Product scoring**: EWG category, organic status, price comparison
- **Form matching**: "powder" vs "whole" for spices
- **Store filtering**: Which stores have this ingredient
- **Price calculations**: Unit price, cheaper swaps

### When to Use LLM
- **Ingredient extraction**: "Pakistani grandmother's Friday dish" → chicken biryani ingredients
- **Explanations**: Why we chose this cardamom over that one → natural language reasoning
- **Ambiguity resolution**: "curry powder" (British blend? Indian masala? Thai paste?)

---

## Active LLM Modules

### 1. Ingredient Extractor (`src/llm/ingredient_extractor.py`)

**Purpose**: Extract structured ingredient list from natural language meal descriptions.

**Implementation**:
```python
# System prompt (cached for cost savings)
INGREDIENT_SYSTEM_PROMPT = """You extract ingredients from meal requests as JSON. Rules:
- Output ONLY valid JSON, no markdown/explanation
- quantity: number or null (never strings)
- form: fresh|powder|seeds|whole|unspecified
- Match cuisine (no cumin in Chinese, no soy sauce in Italian)"""

# User prompt (minimal, variable data only)
INGREDIENT_EXTRACTION_PROMPT = """Extract ingredients from: {prompt}
Servings: {servings}
Schema: {"servings": N, "ingredients": [{"name": str, "form": str, "quantity": num|null, "unit": str|null}]}
JSON:"""
```

**What It Enables**:
- "Make something with what I have: chicken, rice, random spices" → Suggests biryani ingredients
- "Healthy meal for a diabetic" → Considers dietary restrictions
- "Quick weeknight dinner" → Prioritizes simple, fast recipes

**Fallback**: If LLM fails, returns `None` and API falls back to error handling.

### 2. Decision Explainer (`src/llm/decision_explainer.py`)

**Purpose**: Generate natural language explanations for product recommendations.

**Implementation**:
```python
# System prompt (cached)
EXPLANATION_SYSTEM_PROMPT = """You explain grocery product recommendations concisely.
Rules:
- 1-2 sentences max
- Reference actual prices and attributes
- Mention key tradeoff if relevant
- Be conversational, not technical"""

# User prompt
EXPLANATION_USER_PROMPT = """Explain why {brand} {ingredient_name} (${price:.2f}, {size}) was recommended.
Scoring: {scoring_factors}
Cheaper option: {cheaper_option}
Explanation:"""
```

**What It Enables**:
- "The Earthbound Farm spinach at $3.99 offers organic certification for just $1 more than conventional—worth it for a high-pesticide item."
- "Pure Indian Foods turmeric has 4-5% curcumin content vs generic 2%, making it worth the premium for authentic biryani."

**Fallback**: If LLM fails, uses deterministic `reason_line` from scoring engine.

---

## Unified LLM Client (`src/utils/llm_client.py`)

The project uses a unified LLM client that supports multiple providers:

```python
from src.utils.llm_client import get_llm_client

client = get_llm_client()  # Auto-detects provider from env
response = client.generate_sync(
    prompt="Extract ingredients from: chicken biryani for 4",
    system="You are a grocery shopping assistant",
    max_tokens=1024,
    temperature=0.2
)
```

**Supported Providers**:
- `anthropic` (default on Vercel): Claude API
- `ollama`: Local LLMs (Mistral, Llama, etc.)
- `gemini`: Google Gemini API
- `openai`: GPT models

**Auto-detection**:
- On Vercel/AWS Lambda → defaults to `anthropic`
- On local development → defaults to `ollama`
- Override with `LLM_PROVIDER` env var

---

## Opik Observability

All LLM calls are traced via Opik for monitoring and debugging:

```python
# Automatic wrapping in get_llm_client()
from opik.integrations.anthropic import track_anthropic

client.client = track_anthropic(
    client.client,
    project_name="consciousbuyer"
)
```

**What Opik Tracks**:
- Token usage (input/output)
- Cost per call
- Latency
- Prompt/response content
- Error rates

**Dashboard**: View traces at `https://www.comet.com/opik`

---

## Prompt Optimization Strategy

### Before Optimization (Verbose)
```python
# ~2,353 tokens per call
PROMPT = """You are an expert grocery shopping assistant specialized in...
[100+ lines of instructions]
[5 examples]
[Detailed rules]
"""
```

### After Optimization (Minimal)
```python
# ~500-600 tokens per call
SYSTEM_PROMPT = """Concise instructions (cached by API)"""
USER_PROMPT = """Minimal variable data + 1 example"""
```

**Savings**: ~75% token reduction, ~75% cost reduction

### Prompt Caching (Anthropic)

System prompts are cached using Anthropic's ephemeral caching:

```python
kwargs["system"] = [
    {
        "type": "text",
        "text": system,
        "cache_control": {"type": "ephemeral"}
    }
]
```

This means repeated calls with the same system prompt only pay for the user prompt tokens.

---

## Error Handling & Graceful Degradation

### The Fallback Chain
```
Try: LLM extraction/explanation
↓ (if timeout/error)
Use: Deterministic fallback
↓ (if still fails)
Return: Partial result with error message
```

### Example: Ingredient Extraction Failure
```python
# In src/llm/ingredient_extractor.py
try:
    response = client.generate_sync(prompt=formatted_prompt, ...)
except Exception as e:
    logger.error(f"LLM API call failed: {e}")
    return None  # Caller handles fallback
```

### Example: Decision Explanation Failure
```python
# In src/planner/engine.py
if self.use_llm_explanations and self._llm_client:
    try:
        llm_explanation = self._llm_explainer(...)
        if llm_explanation:
            reason_line = llm_explanation  # Use LLM version
    except Exception as e:
        logger.warning(f"LLM explanation failed: {e}")
        # Keep deterministic reason_line
```

---

## Privacy & Data Handling

### What We Send to LLMs
- ✅ Meal descriptions ("chicken biryani for 4")
- ✅ Product names and attributes
- ✅ Recipe context
- ✅ Scoring factors

### What We DON'T Send
- ❌ User identities
- ❌ Purchase history
- ❌ Location data
- ❌ Payment information

### Compliance
- All LLM calls logged via Opik for debugging
- User can disable LLM features (set `use_llm_explanations=False`)
- Prompts designed to minimize PII exposure

---

## Future Enhancements

### Not Yet Implemented
- **Product matching LLM**: Use Claude to select between ambiguous product matches
- **Quantity estimation LLM**: Handle "a handful" or "to taste" amounts
- **Multi-agent collaboration**: Agents that talk to each other

### Why Not Implemented
- Current deterministic scoring works well enough
- Adding more LLM calls increases cost and latency
- Focus has been on getting core flow working

---

**Next**: [UI Flows & User Interactions](./03-ui-flows.md)
