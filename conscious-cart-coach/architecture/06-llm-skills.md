# LLM Skills Guide

## Overview

This document defines the **strict boundaries** for LLM usage in Conscious Cart Coach. LLMs are used for ONE PURPOSE ONLY: **ingredient extraction with form inference**.

**Core Principle**: LLMs extract structured ingredient data from natural language. ALL other logic (product matching, store assignment, pricing, shipping, safety analysis, ethical scoring) is deterministic and handled by the planner engine.

---

## Skill: Ingredient Extraction with Form Inference

### Purpose

Extract structured ingredient list from natural language meal prompts, including ingredient form/cut specification.

**Input**: User prompt (e.g., "chicken biryani for 4")
**Output**: JSON with ingredients, forms, quantities, servings

### LLM Scope (What LLM MUST Do)

✅ **Extract ingredient names** from the prompt
✅ **Infer ingredient form/cut** using controlled vocabulary (see below)
✅ **Parse quantities and units** when mentioned
✅ **Determine servings** from context
✅ **Apply canonical defaults** for known cuisines (biryani, pasta, etc.)
✅ **Strict override mode**: Return EXACTLY what's in INGREDIENT_LIST when present

### LLM Boundaries (What LLM MUST NOT Do)

❌ **NO store assignments** ("available at Whole Foods", "buy from FreshDirect")
❌ **NO shipping/delivery estimates** ("ships in 1-2 days", "specialty store delay")
❌ **NO availability claims** ("this is in stock", "unavailable")
❌ **NO pricing/value judgments** ("this will cost $50", "best value")
❌ **NO safety/recall claims** ("this was recalled", "safe to eat")
❌ **NO health/nutrition claims** ("organic is healthier", "avoid this")
❌ **NO brand trust/recommendations** ("buy Brand X", "avoid Brand Y")
❌ **NO ethical/sustainability judgments** ("this is ethical", "bad for environment")
❌ **NO additions in override mode** when INGREDIENT_LIST is provided

---

## JSON Schema

```json
{
  "servings": number,
  "ingredients": [
    {
      "name": string,
      "form": string,
      "quantity": number,
      "unit": string,
      "notes": string (optional)
    }
  ]
}
```

### Field Definitions

- **name**: Canonical ingredient name (e.g., "ginger", "coriander", "chicken")
- **form**: Ingredient form/cut from controlled vocabulary (REQUIRED, see below)
- **quantity**: Numeric amount (default: 1)
- **unit**: Unit of measurement (default: "unit")
- **notes**: Optional context (e.g., "bone-in preferred", "fresh preferred")

---

## Controlled Vocabulary: `form` Field

The `form` field MUST use one of these values. This is NOT free text.

### Produce & Herbs
- **fresh**: Fresh root/bulb (ginger, garlic, turmeric root)
- **leaves**: Fresh leaves (mint, cilantro, basil, bay leaves)
- **whole**: Whole vegetables (onions, tomatoes, potatoes)
- **chopped**: Pre-chopped/diced
- **paste**: Paste form (ginger paste, garlic paste)
- **powder**: Dried powder (onion powder, garlic powder)

### Spices
- **powder**: Ground spice (coriander powder, turmeric powder, garam masala)
- **seeds**: Whole seeds (cumin seeds, mustard seeds, fennel seeds)
- **whole_spice**: Whole spice pieces (cardamom pods, star anise, cinnamon stick, cloves)

### Meat & Protein
- **thighs**: Chicken/turkey thighs
- **breast**: Chicken/turkey breast
- **drumsticks**: Chicken drumsticks
- **whole_chicken**: Whole bird
- **bone_in**: Bone-in cuts
- **boneless**: Boneless cuts
- **ground**: Ground meat

### Rice & Grains
- **basmati**: Basmati rice
- **jasmine**: Jasmine rice
- **long_grain**: Long grain rice
- **short_grain**: Short grain rice
- **whole_grain**: Whole grain (brown rice, whole wheat)

### Default
- **unspecified**: Use when form is not mentioned or not applicable

---

## Biryani Canonical Defaults

When the prompt suggests biryani (or similar Indian rice dish), apply these canonical defaults:

| User says | Canonical name | Form | Notes |
|-----------|----------------|------|-------|
| rice | basmati rice | basmati | Default to basmati for biryani |
| coriander | coriander | powder | "coriander powder" unless user says "seeds" |
| cumin | cumin | seeds | "cumin seeds" (jeera) |
| cardamom | cardamom | whole_spice | Green cardamom pods unless "black cardamom" mentioned |
| black cardamom | black cardamom | whole_spice | Black cardamom pods |
| bay leaves | bay leaves | leaves | Whole bay leaves |
| garam masala | garam masala | powder | Spice blend powder |
| turmeric | turmeric | powder | Ground turmeric |
| ginger | ginger | fresh | Fresh ginger root |
| garlic | garlic | fresh | Fresh garlic cloves |
| mint | mint | leaves | Fresh mint leaves |
| cilantro | cilantro | leaves | Fresh cilantro leaves |
| chicken | chicken | thighs | Bone-in thighs preferred unless specified |
| onions | onions | whole | Whole onions |
| tomatoes | tomatoes | whole | Whole tomatoes |
| yogurt | yogurt | unspecified | Plain yogurt |
| ghee | ghee | unspecified | Clarified butter |

### Canonical Name vs Display Label

The LLM returns canonical `name` + `form`. The backend will construct display labels:
- `name="ginger"`, `form="fresh"` → display: **"fresh ginger root"**
- `name="coriander"`, `form="powder"` → display: **"coriander powder"**
- `name="cumin"`, `form="seeds"` → display: **"cumin seeds"**
- `name="mint"`, `form="leaves"` → display: **"fresh mint leaves"**

---

## Forbidden Substitutions

The LLM MUST NOT make these mistakes:

### ❌ Cumin → Kalonji
- **WRONG**: User says "cumin seeds", LLM returns "kalonji" or "black seed" or "nigella"
- **RIGHT**: User says "cumin seeds" → `name="cumin"`, `form="seeds"`
- **Why**: Kalonji (nigella) is NOT cumin. This is a different spice.

### ❌ Bay Leaves → Spice Blends
- **WRONG**: User says "bay leaves", LLM returns "garam masala" or "chaat masala" or "DIY spice blend"
- **RIGHT**: User says "bay leaves" → `name="bay leaves"`, `form="leaves"`
- **Why**: Bay leaves are specific leaves, not a blend.

### ❌ Coriander Powder → Cilantro Leaves
- **WRONG**: User says "coriander powder", LLM returns "cilantro leaves" or "coriander seeds"
- **RIGHT**: User says "coriander powder" → `name="coriander"`, `form="powder"`
- **Why**: Powder, seeds, and leaves are different forms.

### ❌ Fresh Ginger → Ginger Powder
- **WRONG**: User says "fresh ginger", LLM returns `form="powder"`
- **RIGHT**: User says "fresh ginger" → `name="ginger"`, `form="fresh"`
- **Why**: Fresh and powder are different forms.

---

## Override Mode (STRICT)

When the prompt contains `INGREDIENT_LIST:`, the LLM MUST enter **Strict Override Mode**.

### Override Mode Rules

1. **INGREDIENT_LIST is authoritative** - this is the complete, final list
2. **DO NOT add ingredients** not in INGREDIENT_LIST
3. **DO NOT remove ingredients** from INGREDIENT_LIST
4. **DO NOT infer missing ingredients** based on meal type
5. **Parse form from ingredient phrase** if embedded:
   - "coriander powder" → `name="coriander"`, `form="powder"`
   - "fresh ginger" → `name="ginger"`, `form="fresh"`
   - "cumin seeds" → `name="cumin"`, `form="seeds"`
   - "mint leaves" → `name="mint"`, `form="leaves"`
   - "chicken thighs" → `name="chicken"`, `form="thighs"`
6. **Use default values** for missing metadata:
   - `quantity`: 1
   - `unit`: "unit"
   - `notes`: omit
7. **Use SERVINGS value** if provided, otherwise default to 2

### Override Mode Example

**Prompt**:
```
Chicken biryani for 4

SERVINGS: 4
IMPORTANT: Use this exact ingredient list. Do not add or remove items.
INGREDIENT_LIST: fresh ginger | coriander powder | cumin seeds | mint leaves
```

**Expected Output**:
```json
{
  "servings": 4,
  "ingredients": [
    {"name": "ginger", "form": "fresh", "quantity": 1, "unit": "unit"},
    {"name": "coriander", "form": "powder", "quantity": 1, "unit": "unit"},
    {"name": "cumin", "form": "seeds", "quantity": 1, "unit": "unit"},
    {"name": "mint", "form": "leaves", "quantity": 1, "unit": "unit"}
  ]
}
```

**Note**: Only 4 ingredients returned, even though typical biryani has 15+. This is correct behavior in override mode.

### Common Mistakes to Avoid

❌ **WRONG**: "The prompt says biryani, so I'll add missing spices (garam masala, turmeric, etc.)"
✅ **CORRECT**: "INGREDIENT_LIST contains only 4 items, so I return exactly those 4 items"

❌ **WRONG**: "User forgot bay leaves, I'll add them"
✅ **CORRECT**: "INGREDIENT_LIST doesn't include bay leaves, so I don't include them"

❌ **WRONG**: "Returning ingredient names without parsing embedded forms"
✅ **CORRECT**: "Parse 'coriander powder' into name=coriander, form=powder"

---

## Example Outputs

### Example 1: Chicken Biryani for 4 (No Override)

**Prompt**: `"chicken biryani for 4"`

**Expected Output**:
```json
{
  "servings": 4,
  "ingredients": [
    {"name": "chicken", "form": "thighs", "quantity": 1.5, "unit": "lb"},
    {"name": "basmati rice", "form": "basmati", "quantity": 2, "unit": "cups"},
    {"name": "onions", "form": "whole", "quantity": 2, "unit": "medium"},
    {"name": "tomatoes", "form": "whole", "quantity": 3, "unit": "medium"},
    {"name": "yogurt", "form": "unspecified", "quantity": 1, "unit": "cup"},
    {"name": "ginger", "form": "fresh", "quantity": 2, "unit": "inches"},
    {"name": "garlic", "form": "fresh", "quantity": 8, "unit": "cloves"},
    {"name": "ghee", "form": "unspecified", "quantity": 3, "unit": "tbsp"},
    {"name": "garam masala", "form": "powder", "quantity": 2, "unit": "tsp"},
    {"name": "turmeric", "form": "powder", "quantity": 1, "unit": "tsp"},
    {"name": "coriander", "form": "powder", "quantity": 1, "unit": "tbsp"},
    {"name": "cumin", "form": "seeds", "quantity": 1, "unit": "tsp"},
    {"name": "cardamom", "form": "whole_spice", "quantity": 4, "unit": "pods"},
    {"name": "bay leaves", "form": "leaves", "quantity": 2, "unit": "leaves"},
    {"name": "mint", "form": "leaves", "quantity": 0.25, "unit": "cup"},
    {"name": "cilantro", "form": "leaves", "quantity": 0.25, "unit": "cup"}
  ]
}
```

### Example 2: Override Mode with Forms

**Prompt**:
```
Chicken biryani for 4

SERVINGS: 4
INGREDIENT_LIST: fresh ginger | coriander powder | cumin seeds | bay leaves | chicken thighs
```

**Expected Output**:
```json
{
  "servings": 4,
  "ingredients": [
    {"name": "ginger", "form": "fresh", "quantity": 1, "unit": "unit"},
    {"name": "coriander", "form": "powder", "quantity": 1, "unit": "unit"},
    {"name": "cumin", "form": "seeds", "quantity": 1, "unit": "unit"},
    {"name": "bay leaves", "form": "leaves", "quantity": 1, "unit": "unit"},
    {"name": "chicken", "form": "thighs", "quantity": 1, "unit": "unit"}
  ]
}
```

---

## Deterministic Fallback

If LLM returns invalid JSON after 1 retry, use deterministic template-based extraction.

### Fallback Strategy

1. **Parse servings**: Look for "for N", "serves N", "N people" → default 2
2. **Identify meal type**: Look for keywords (biryani, pasta, salad, tacos)
3. **Load template**: Use pre-defined ingredient list with forms
4. **Scale quantities**: Multiply by (servings / template_default_servings)

### Fallback Templates (with Forms)

```python
MEAL_TEMPLATES = {
    "biryani": {
        "ingredients": [
            {"name": "chicken", "form": "thighs", "quantity": 1.5, "unit": "lb"},
            {"name": "basmati rice", "form": "basmati", "quantity": 2, "unit": "cups"},
            {"name": "ginger", "form": "fresh", "quantity": 2, "unit": "inches"},
            {"name": "garlic", "form": "fresh", "quantity": 8, "unit": "cloves"},
            {"name": "coriander", "form": "powder", "quantity": 1, "unit": "tbsp"},
            {"name": "cumin", "form": "seeds", "quantity": 1, "unit": "tsp"},
            {"name": "bay leaves", "form": "leaves", "quantity": 2, "unit": "leaves"},
            {"name": "mint", "form": "leaves", "quantity": 0.25, "unit": "cup"},
            # ... full template
        ],
        "default_servings": 4
    },
    "pasta": {
        "ingredients": [
            {"name": "pasta", "form": "unspecified", "quantity": 1, "unit": "lb"},
            {"name": "tomato sauce", "form": "unspecified", "quantity": 2, "unit": "cups"},
            {"name": "garlic", "form": "fresh", "quantity": 4, "unit": "cloves"},
            {"name": "olive oil", "form": "unspecified", "quantity": 2, "unit": "tbsp"},
            {"name": "basil", "form": "leaves", "quantity": 0.25, "unit": "cup"}
        ],
        "default_servings": 4
    }
}
```

---

## Model Configuration

### Supported Models

- **Ollama** (local): `mistral`, `llama2`, `codellama`
- **Anthropic Claude**: `claude-3-5-sonnet-20241022`, `claude-3-5-haiku-20241022`
- **OpenAI GPT**: `gpt-4`, `gpt-3.5-turbo`
- **Google Gemini**: `gemini-pro`, `gemini-1.5-flash`

### Configuration File

Edit `src/utils/llm_client.py`:

```python
LLM_PROVIDER = "ollama"  # Options: "ollama", "anthropic", "openai", "gemini"
LLM_MODEL = "mistral"    # Model name for selected provider

# Provider-specific settings
OLLAMA_BASE_URL = "http://localhost:11434"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
```

### Model Settings

| Model | Temperature | Max Tokens | Notes |
|-------|-------------|------------|-------|
| Ollama Mistral | 0.1 | 3000 | Good balance, local |
| Claude Sonnet | 0.0 | 2000 | Most reliable JSON |
| Claude Haiku | 0.1 | 1500 | Fastest, cheapest |
| GPT-4 | 0.0 | 2000 | Expensive but good |
| Gemini Flash | 0.1 | 2000 | Fast, good, free tier |

---

## Evaluation Harness

### Test Set

Located at `tests/fixtures/extraction_test_cases.json`

Must include:
- **Biryani form cases** (6+ tests): Verify basmati rice, coriander powder, cumin seeds, mint leaves, fresh ginger, chicken thighs
- **Override compliance** (3+ tests): Verify exact list returned, no additions/removals
- **Form correctness** (10+ tests): Verify controlled vocabulary compliance
- **Edge cases** (5+ tests): Ambiguous prompts, minimal input, unusual cuisines

### Scoring Metrics

1. **Ingredient Precision**: `correct_ingredients / extracted_ingredients`
2. **Ingredient Recall**: `extracted_ingredients / expected_ingredients`
3. **Form Accuracy**: `correct_forms / total_ingredients`
4. **Override Compliance**: `100%` if exact match in override mode, `0%` if any deviation
5. **Schema Validity**: `valid_json_outputs / total_outputs`

### Running Evaluation

```bash
# Evaluate current model
python scripts/eval_llm_extraction.py

# With specific model
python scripts/eval_llm_extraction.py --model mistral

# Show form scores
python scripts/eval_llm_extraction.py --show-forms

# Test override mode only
python scripts/eval_llm_extraction.py --override-only
```

### Expected Baseline Scores

| Model | Ingredient Precision | Ingredient Recall | Form Accuracy | Override Compliance |
|-------|---------------------|-------------------|---------------|---------------------|
| Ollama Mistral | 92% | 87% | 85% | 90% |
| Claude Sonnet | 98% | 94% | 98% | 100% |
| Claude Haiku | 95% | 91% | 95% | 100% |
| GPT-4 | 96% | 93% | 94% | 95% |

---

## Prompt Engineering Guidelines

### System Prompt Structure

```
You are an ingredient extraction specialist. Your ONLY job is to extract structured ingredient data from meal prompts.

STRICT BOUNDARIES:
- Extract ingredient names, forms, quantities only
- Use controlled vocabulary for forms (fresh, powder, seeds, leaves, whole_spice, thighs, breast, etc.)
- Apply canonical defaults for known cuisines
- In override mode: return EXACTLY the ingredients listed, no additions/removals
- NEVER suggest stores, prices, shipping, availability, safety, ethics

OUTPUT FORMAT: Valid JSON only, no explanation text
```

### User Prompt Structure

```
Extract ingredients from this meal request:
"{user_prompt}"

Return JSON with this exact schema:
{
  "servings": number,
  "ingredients": [
    {"name": string, "form": string, "quantity": number, "unit": string, "notes": string}
  ]
}

FORM must be from: fresh, leaves, whole, chopped, paste, powder, seeds, whole_spice, thighs, breast, drumsticks, whole_chicken, bone_in, boneless, ground, basmati, jasmine, long_grain, short_grain, whole_grain, unspecified

[Include override mode instructions if INGREDIENT_LIST present]
```

---

## Safety & Validation

1. **Always validate JSON schema** before passing to planner
2. **Validate form field** against controlled vocabulary
3. **Use deterministic fallback** if LLM fails validation
4. **Log all LLM calls** for debugging and cost tracking
5. **Rate limit** if using paid APIs
6. **Never expose raw LLM output** to users without validation
7. **Sanitize ingredient names** (lowercase, strip whitespace)

---

## Debugging Tips

### Issue: Invalid JSON

**Fix**: Add explicit instruction: "Return ONLY valid JSON, no markdown, no explanation"

### Issue: Wrong forms

**Fix**: Emphasize controlled vocabulary in prompt, show examples

### Issue: Override mode violations

**Fix**: Make override instructions more explicit, add examples of correct behavior

### Issue: Biryani defaults not applied

**Fix**: Check meal type detection, verify canonical mappings in code

### Issue: Forbidden substitutions

**Fix**: Add negative examples to prompt ("cumin is NOT kalonji")

---

## Revision History

- **2026-02-03**: Updated with form field, controlled vocabulary, biryani defaults, strict override mode
- **2026-02-02**: Initial version (v2.0 architecture)
