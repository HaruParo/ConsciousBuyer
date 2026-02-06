# LLM Skills Guide: Teaching Your Grocery Coach to Think

## The Big Idea

Think of LLM skills as **teaching moments** for your grocery shopping assistant. While most of the app runs on deterministic code (same input → same output), LLM skills add **contextual intelligence** that would be impossible to hard-code.

**Analogy**: Your grocery app is like a smart calculator that can add up prices perfectly. But when you ask "What ingredients do I need for chicken biryani?", you need more than math — you need culinary knowledge, portion sizing, and common sense. That's where LLM skills come in.

---

## Architecture: The LLM Integration Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Ingredient  │  │   Decision   │  │   Recipe     │      │
│  │  Extraction  │  │  Explanation │  │   Product    │      │
│  │              │  │              │  │   Matcher    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                  │               │
│         └─────────────────┴──────────────────┘               │
│                           │                                  │
│                  ┌────────▼────────┐                         │
│                  │  LLM CLIENT     │                         │
│                  │  (Multi-provider)│                        │
│                  └────────┬────────┘                         │
│                           │                                  │
│         ┌─────────────────┼─────────────────┐               │
│         │                 │                 │               │
│    ┌────▼─────┐    ┌─────▼──────┐   ┌─────▼──────┐        │
│    │ Ollama   │    │ Anthropic  │   │  Gemini    │        │
│    │ (Local)  │    │  (Claude)  │   │  OpenAI    │        │
│    └──────────┘    └────────────┘   └────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Multi-Provider Support**: Works with local (Ollama) or cloud (Anthropic, Gemini, OpenAI) LLMs
2. **Optional Imports**: Code works even if LLM libraries aren't installed (graceful degradation)
3. **Deterministic Core**: LLM skills enhance the experience but aren't required for core functionality
4. **Opik Tracing**: All LLM calls are traced for debugging and cost monitoring

---

## Available LLM Skills

### 1. **Ingredient Extraction** 🧠

**File**: [`src/llm/ingredient_extractor.py`](../src/llm/ingredient_extractor.py)

**What it does**: Converts natural language meal plans into structured ingredient lists.

**Example**:
```
Input: "chicken biryani for 4"

Output: [
  {name: "chicken", quantity: "2", unit: "lb"},
  {name: "basmati rice", quantity: "2", unit: "cups"},
  {name: "ginger", quantity: "2", unit: "inch"},
  {name: "garlic", quantity: "6", unit: "cloves"},
  {name: "garam masala", quantity: "2", unit: "tbsp"},
  ... (12-16 total ingredients)
]
```

**Smart Features**:
- **Dish Recognition**: Knows that "biryani" needs 12-16 specific ingredients
- **Portion Scaling**: Adjusts quantities for servings (4 people vs 8 people)
- **Ingredient Forms**: Understands "fresh ginger" vs "ginger powder"
- **Modifier Preservation**: Keeps "organic", "free-range", etc.

**Technical Details**:
```python
from src.llm.ingredient_extractor import extract_ingredients_with_llm

ingredients = extract_ingredients_with_llm(
    client=anthropic_client,  # or ollama_client
    prompt="chicken biryani for 4",
    servings=4
)
# Returns: list[dict] with name, quantity, unit, category
```

**Configuration**:
- `max_tokens`: 3000 (allows for long ingredient lists)
- `temperature`: 0.1 (mostly deterministic, slight creativity for completeness)
- Prompt engineering: See lines 18-111 for the full prompt template

**Why This Needed an LLM**:
- Hard to enumerate all possible dishes and their ingredients
- Recipe variations (simple biryani vs full biryani)
- Cultural context (Indian biryani needs ghee, mint, cardamom)
- Portion math (2 people vs 8 people)

---

### 2. **Decision Explanation** 💬

**File**: [`src/llm/decision_explainer.py`](../src/llm/decision_explainer.py)

**What it does**: Explains **why** the app recommended a specific product over alternatives.

**Example**:
```
Input:
  - Recommended: Organic Turmeric Powder ($8.99, 4oz)
  - Cheaper: Regular Turmeric ($4.99, 4oz)
  - Scoring factors: [organic_specialty: +15, value_efficiency_good: +6]

Output:
  "Pure Indian Foods Organic Turmeric Powder was selected for its quality
   certification and direct sourcing. It costs $4 more than the non-organic
   option but ensures pesticide-free spices."
```

**Smart Features**:
- References **actual prices** and **specific products**
- Mentions the **key tradeoff** (e.g., "$4 more but organic")
- Uses natural, conversational language
- Avoids hallucination (only uses provided data)

**Technical Details**:
```python
from src.llm.decision_explainer import explain_decision_with_llm

explanation = explain_decision_with_llm(
    client=anthropic_client,
    ingredient_name="turmeric",
    recommended_product={
        "brand": "Pure Indian Foods",
        "price": 8.99,
        "size": "4oz",
        "unit_price": 2.25,
        "organic": True
    },
    scoring_factors=["organic_specialty: +15", "value_efficiency_good: +6"],
    cheaper_option="Regular Turmeric at $4.99",
    conscious_option=None,  # This IS the conscious option
    user_prefs={"preferred_brands": ["Pure Indian Foods"]}
)
# Returns: str (1-2 sentence explanation)
```

**Configuration**:
- `max_tokens`: 256 (concise explanations only)
- `temperature`: 0.3 (slightly creative but consistent)
- Enforces: No markdown, no JSON, just clean text

**Why This Needed an LLM**:
- Humanizing technical scoring factors ("+15 organic_specialty" → "quality certification")
- Contextual phrasing (don't say "more expensive" for a $0.20 difference)
- Tradeoff framing (positive vs negative tone)

---

### 3. **Recipe Product Matcher** 🔍

**File**: [`src/llm/recipe_product_matcher.py`](../src/llm/recipe_product_matcher.py)

**What it does**: Evaluates products against **recipe requirements** across 7 attributes.

**Example**:
```
Input:
  - Recipe: "Chicken Biryani" (needs fresh ginger root)
  - Candidates:
    1. Fresh Organic Ginger Root (8oz, $5.99)
    2. Ginger Root Coarse Granules (2oz, $3.99)
    3. Organic Ginger Powder (4oz, $6.99)

Output:
  Ranked products with recipe-fit scores:
  1. Fresh Organic Ginger Root (score: 95/100)
     - Form: ✓ Fresh root (perfect for biryani)
     - Quality: ✓ Organic
     - Processing: ✓ Whole/unprocessed
  2. Ginger Root Coarse Granules (score: 35/100)
     - Form: ✗ Granules not suitable for fresh recipes
     - Processing: ✗ Dried/processed
```

**The 7 Attributes**:

| Attribute | What It Checks | Example |
|-----------|---------------|---------|
| **FORM** | Fresh vs dried, powder vs whole, stick vs ground | Turmeric: powder > granules > whole root |
| **QUALITY** | Organic, certifications, grade | USDA Organic > conventional |
| **VARIETY** | Specific cultivar/type if it matters | Basmati rice > generic long-grain |
| **ORIGIN** | Geographic source (for authenticity) | Indian spices > domestic |
| **PROCESSING** | Minimal vs heavily processed | Whole cloves > clove powder |
| **BRAND** | Trusted specialty brands vs generic | Pure Indian Foods (direct import) > store brand |
| **VALUE** | Price-quality balance | Not just cheapest, but reasonable |

**Technical Details**:
```python
from src.llm.recipe_product_matcher import select_best_product_for_recipe

best_product = select_best_product_for_recipe(
    client=anthropic_client,
    recipe_context="Chicken Biryani (traditional Indian dish)",
    ingredient_name="ginger",
    ingredient_form="fresh root",  # from recipe
    candidates=[
        {"title": "Fresh Organic Ginger Root", "price": 5.99, ...},
        {"title": "Ginger Root Granules", "price": 3.99, ...}
    ]
)
# Returns: dict with selected product + reasoning
```

**Configuration**:
- `max_tokens`: 1500
- `temperature`: 0.2 (deterministic, recipe-accurate)
- Prompt includes: recipe context, ingredient requirements, all candidates

**Why This Needed an LLM**:
- Complex multi-attribute evaluation (7 factors, weighted context-dependently)
- Recipe understanding (biryani needs **fresh** ginger, not granules)
- Cultural authenticity (Indian dishes benefit from specialty brands)
- Impossible to hard-code all recipe × product × attribute combinations

---

## Multi-Provider LLM Support

The system supports 4 LLM providers with automatic fallback:

### 1. **Ollama (Local)** 🏠

**Best for**: Privacy, development, no API costs

```python
# .env
LLM_PROVIDER=ollama
OLLAMA_MODEL=mistral:latest
OLLAMA_BASE_URL=http://localhost:11434
```

**Setup**:
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull mistral:latest

# Start server
ollama serve
```

**Pros**: Free, private, fast for local development
**Cons**: Lower quality than Claude/GPT-4, requires GPU for speed

---

### 2. **Anthropic (Claude)** 🤖

**Best for**: Production, highest quality, structured outputs

```python
# .env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

**Models**:
- `claude-opus-4-5`: Best quality (expensive)
- `claude-sonnet-4-5`: Balanced (recommended)
- `claude-haiku-4`: Fast & cheap

**Pros**: Best reasoning, excellent instruction-following, JSON output
**Cons**: Costs money (~$3-$15 per 1M tokens)

---

### 3. **Google Gemini** 🌟

**Best for**: Multimodal tasks, Google ecosystem

```python
# .env
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIza...
```

**Pros**: Free tier available, fast, good quality
**Cons**: Less reliable structured output than Claude

---

### 4. **OpenAI (GPT)** 🧠

**Best for**: Broad compatibility, well-documented

```python
# .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-...
```

**Pros**: Industry standard, excellent docs
**Cons**: More expensive than Claude for similar quality

---

## How to Create a New LLM Skill

### Step 1: Define the Problem

**Ask yourself**:
1. Could this be solved with deterministic code? (If yes, don't use LLM!)
2. Does this require context understanding or creative reasoning?
3. Will the LLM have enough data to avoid hallucination?

**Good LLM Use Cases**:
- ✅ Parsing unstructured user input ("I want to make dinner tonight")
- ✅ Contextual ranking (product X is better for recipe Y)
- ✅ Natural language generation (explain why product A > product B)

**Bad LLM Use Cases**:
- ❌ Math calculations (use code!)
- ❌ Exact string matching (use regex!)
- ❌ Deterministic rules (if X then Y → use code!)

---

### Step 2: Create the Skill File

**Template**: Create `src/llm/my_skill.py`

```python
"""LLM-powered [brief description]."""

import logging
from typing import Optional

# Optional import pattern
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

from .client import call_claude_with_retry

logger = logging.getLogger(__name__)

# Define your prompt template
MY_SKILL_PROMPT = """You are a [role]. [Task description].

INPUT:
{input_data}

RULES:
1. [Rule 1]
2. [Rule 2]
3. Output ONLY valid JSON (no markdown, no extra text)

EXAMPLE:
Input: [example input]
Output: {{"result": "example output"}}

NOW PROCESS THE INPUT ABOVE.

JSON OUTPUT:"""


def my_llm_skill(
    client: Anthropic,
    input_data: str,
    **kwargs
) -> Optional[dict]:
    """
    [Detailed description of what this skill does]

    Args:
        client: Anthropic client instance
        input_data: [Description]
        **kwargs: Additional parameters

    Returns:
        [Description of return value]
    """
    if not client:
        logger.warning("No LLM client provided")
        return None

    # Format prompt
    formatted_prompt = MY_SKILL_PROMPT.format(
        input_data=input_data,
        **kwargs
    )

    # Call LLM with Opik tracing
    response_text = call_claude_with_retry(
        client=client,
        prompt=formatted_prompt,
        max_tokens=1000,  # Adjust based on expected output length
        temperature=0.2,  # 0.0-0.3 for deterministic, 0.5-0.8 for creative
        trace_name="my_skill",  # For Opik tracing
        metadata={
            "input": input_data,
            "operation": "my_skill"
        }
    )

    if not response_text:
        logger.warning("LLM call failed")
        return None

    # Parse response (customize based on your output format)
    try:
        import json
        result = json.loads(response_text.strip())
        return result
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse LLM response: {e}")
        return None
```

---

### Step 3: Write Effective Prompts

**The Formula**:

```
1. ROLE: "You are a [expert role]"
2. TASK: "Extract/Analyze/Rank/Generate [specific output]"
3. INPUT: Clearly formatted input data
4. RULES: Numbered list of constraints
5. EXAMPLES: 2-3 concrete input/output examples
6. OUTPUT FORMAT: Explicit structure (JSON, text, etc.)
```

**Prompt Engineering Tips**:

1. **Be Specific**: "Extract ingredients" → "Extract ingredient name, quantity, and unit"
2. **Show, Don't Tell**: Include 2-3 examples (good and edge cases)
3. **Constrain Output**: "Output ONLY valid JSON (no markdown, no extra text)"
4. **Handle Edge Cases**: "If uncertain, return empty list (not null)"
5. **Use Formatting**: Make input data visually distinct (ALL CAPS, code blocks)

**Example** (from ingredient extractor):
```
CRITICAL RULES:
1. If a dish name is mentioned WITH specific ingredients listed, extract ONLY those
2. If ONLY a dish name is mentioned, extract ENHANCED CORE ingredients (12-15 items)
3. DO NOT duplicate ingredients
4. Use simple, common names
```

---

### Step 4: Configure Temperature & Tokens

| Task Type | Temperature | Max Tokens | Rationale |
|-----------|------------|------------|-----------|
| **Extraction** (structured data) | 0.0 - 0.2 | 1500-3000 | Need consistency, determinism |
| **Explanation** (natural language) | 0.3 - 0.5 | 200-500 | Slight creativity, readability |
| **Ranking** (evaluation) | 0.1 - 0.3 | 1000-2000 | Consistent scoring, some reasoning |
| **Creative** (brainstorming) | 0.7 - 0.9 | 500-1500 | High variation, exploration |

**General Rules**:
- Lower temperature = more deterministic (same input → same output)
- Higher temperature = more creative (same input → varied outputs)
- Max tokens should fit expected output + 50% buffer

---

### Step 5: Add Opik Tracing

**Why**: Track LLM calls, costs, latency, and failures

```python
response_text = call_claude_with_retry(
    client=client,
    prompt=formatted_prompt,
    max_tokens=1000,
    temperature=0.2,
    trace_name="my_skill",  # Shows up in Opik dashboard
    metadata={
        "input_length": len(input_data),
        "user_id": user_id,  # Optional
        "operation": "my_skill"
    }
)
```

**View traces**:
```bash
# Local Opik dashboard (if configured)
open http://localhost:5000
```

---

### Step 6: Test Your Skill

**Create**: `test_my_skill.py`

```python
#!/usr/bin/env python3
"""Test my LLM skill."""
import os
import sys

# Configure environment
os.environ['LLM_PROVIDER'] = 'ollama'  # or 'anthropic'
os.environ['OLLAMA_MODEL'] = 'mistral:latest'

sys.path.insert(0, '/path/to/conscious-cart-coach')

from src.utils.llm_client import OllamaClient
from src.llm.my_skill import my_llm_skill

# Create client
client = OllamaClient(
    base_url='http://localhost:11434',
    model='mistral:latest'
)

# Test cases
test_cases = [
    {"input": "test case 1", "expected": "result 1"},
    {"input": "test case 2", "expected": "result 2"},
    {"input": "edge case", "expected": "fallback behavior"}
]

for i, test in enumerate(test_cases):
    print(f"\n=== Test {i+1} ===")
    print(f"Input: {test['input']}")

    result = my_llm_skill(client, test['input'])

    print(f"Output: {result}")
    print(f"Expected: {test['expected']}")
    print(f"✓ PASS" if result == test['expected'] else "✗ FAIL")
```

**Run**:
```bash
python test_my_skill.py
```

---

## Best Practices

### 1. **Fail Gracefully**

LLM calls can fail (network, rate limits, parsing errors). Always handle failures:

```python
result = my_llm_skill(client, user_input)

if result is None:
    # Fallback to deterministic logic
    result = simple_rule_based_fallback(user_input)
```

### 2. **Cache Expensive Calls**

If the same input is called repeatedly, cache it:

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def cached_llm_skill(input_hash: str):
    return my_llm_skill(client, input_hash)
```

### 3. **Validate LLM Output**

Never trust LLM output blindly:

```python
def validate_ingredients(data: dict) -> bool:
    """Ensure LLM returned valid ingredient structure."""
    if not isinstance(data, dict):
        return False
    if "ingredients" not in data:
        return False
    for ing in data["ingredients"]:
        if "name" not in ing or not isinstance(ing["name"], str):
            return False
    return True

result = my_llm_skill(client, input_data)
if result and validate_ingredients(result):
    # Safe to use
    ingredients = result["ingredients"]
else:
    # Invalid output, use fallback
    logger.warning("LLM returned invalid data")
```

### 4. **Monitor Costs**

Track token usage and costs:

```python
# In production, log all LLM calls
logger.info(f"LLM call: {trace_name}, tokens: {response.usage.total_tokens}")

# Set budgets
if total_llm_cost_today > DAILY_BUDGET:
    logger.warning("LLM budget exceeded, falling back to rules")
    use_rule_based_fallback = True
```

### 5. **Use Structured Output**

Prefer JSON output over free text:

**Bad** (hard to parse):
```
The ingredients are chicken, rice, onions, and spices including turmeric and cumin.
```

**Good** (structured):
```json
{
  "ingredients": [
    {"name": "chicken", "quantity": "2", "unit": "lb"},
    {"name": "rice", "quantity": "2", "unit": "cups"},
    {"name": "onions", "quantity": "2", "unit": "medium"}
  ]
}
```

---

## Debugging LLM Skills

### Problem: LLM Returns Inconsistent Output

**Symptoms**: Sometimes works, sometimes fails

**Solutions**:
1. Lower temperature (0.0 for maximum consistency)
2. Add more explicit examples in prompt
3. Add output format validation
4. Increase max_tokens (output might be cut off)

---

### Problem: LLM Hallucinates Data

**Symptoms**: Makes up product names, prices, or attributes

**Solutions**:
1. Add "ONLY use provided data, do NOT invent" to prompt
2. Provide all necessary context in prompt
3. Add validation to reject hallucinated fields
4. Use temperature ≤ 0.3

---

### Problem: LLM Fails to Parse JSON

**Symptoms**: `JSONDecodeError` in logs

**Solutions**:
1. Add "Output ONLY valid JSON (no markdown, no extra text)" to prompt
2. Use multiple parsing strategies (see `ingredient_extractor.py:114-150`)
3. Strip markdown code blocks before parsing
4. Log raw LLM output for debugging

**Example** (robust parsing):
```python
def parse_json_response(text: str) -> Optional[dict]:
    # Try direct parsing
    try:
        return json.loads(text.strip())
    except:
        pass

    # Try extracting from markdown
    match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass

    # Try finding JSON object
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end+1])
        except:
            pass

    return None
```

---

### Problem: LLM Too Slow

**Symptoms**: API calls take >5 seconds

**Solutions**:
1. Use faster models (Haiku instead of Opus)
2. Use local Ollama for development
3. Reduce max_tokens
4. Cache frequent calls
5. Run LLM calls in background (async)

---

## Integration Points

### Where LLM Skills Are Called

1. **API Endpoint**: [`api/main.py:60-100`](../api/main.py#L60-L100)
   - Ingredient extraction from user input
   - Called on every meal plan submission

2. **Decision Engine**: [`src/engine/decision_engine.py:266-298`](../src/engine/decision_engine.py#L266-L298)
   - Optional LLM explanations for product recommendations
   - Enabled via `use_llm_explanations=True`

3. **Product Agent**: (not yet integrated)
   - Recipe Product Matcher skill
   - Will be added for recipe-aware product ranking

---

## Session Context Recording

All changes made in this session are tracked:

### Key Files Modified:
1. ✅ [`src/llm/ingredient_extractor.py`](../src/llm/ingredient_extractor.py) - Enhanced extraction (12-16 ingredients)
2. ✅ [`src/llm/decision_explainer.py`](../src/llm/decision_explainer.py) - Optional imports
3. ✅ [`src/llm/recipe_product_matcher.py`](../src/llm/recipe_product_matcher.py) - NEW skill (7-attribute matching)
4. ✅ [`src/agents/product_agent.py`](../src/agents/product_agent.py) - Fresh produce prioritization fix
5. ✅ [`api/main.py`](../api/main.py) - Relative tradeoff tags with neighbor comparisons
6. ✅ [`src/utils/llm_client.py`](../src/utils/llm_client.py) - Optional anthropic import

### Session Changelog:
See [`conscious-cart-coach/CHANGELOG_SESSION_2026-02-01.md`](../CHANGELOG_SESSION_2026-02-01.md) for detailed change log.

---

## Next Steps

### Immediate
1. ✅ Test "chicken biryani for 4" with all fixes
2. ⏳ Integrate Recipe Product Matcher into product_agent
3. ⏳ Add bundle detection (Biryani Bundle auto-selection)

### Future Enhancements
1. **Dietary Restriction Skill**: LLM-powered allergy detection and substitutions
2. **Meal Plan Generator**: "Feed me for a week under $50" → full meal plan
3. **Recipe Suggester**: Based on available ingredients in cart
4. **Price Predictor**: Forecast price trends for seasonal items

---

## Summary

LLM skills add **contextual intelligence** to deterministic grocery logic:

| Without LLM | With LLM |
|-------------|----------|
| "biryani" → no results | "biryani" → 16 ingredients with portions |
| Product selected (no explanation) | "Selected for organic certification, costs $2 more but pesticide-free" |
| Cheapest turmeric (wrong form) | Recipe-appropriate turmeric powder (not granules) |

**Remember**: LLMs are tools, not magic. Use them for tasks that require understanding, not tasks that need precision. When in doubt, code beats prompts.

---

**Questions?** Check the source files or add new skills following the template above!
