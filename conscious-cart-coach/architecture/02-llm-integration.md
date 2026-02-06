# LLM Integration: Teaching the Cart to Think

## The Vision: From Rule-Based to AI-Enhanced Shopping

Right now, Conscious Cart Coach works like a very sophisticated calculator. Give it "chicken biryani for 4" and it executes a series of programmed rules:
1. Parse for keywords (chicken, biryani)
2. Look up standard biryani ingredients
3. Match against product database
4. Calculate quantities

It works, but it's brittle. What happens when someone says "I want to make what my Pakistani grandmother used to cook on Fridays"? The rules break down.

**The LLM integration strategy** isn't about replacing the rules - it's about making the system understand nuance, ambiguity, and context the way a human shopping assistant would.

## The Hybrid Approach: Best of Both Worlds

Think of it like a kitchen with both a precise scale and an experienced chef:
- **The scale** (rules): Always gives exact measurements, never deviates, costs nothing to use
- **The chef** (LLM): Understands "a pinch of this, until it looks right", adapts to context, but takes time

We'll use both.

### When to Use Rules
- **Exact matches**: "chicken breast" → look for products with "chicken" AND "breast"
- **Calculations**: Recipe needs 2 tsp, jar has 16 tsp → buy 1 jar
- **Store filtering**: "365 brand" → must be Whole Foods
- **Price comparisons**: $5.99 < $7.99 → choose cheaper

### When to Use LLM
- **Ambiguous ingredient names**: "curry powder" (British blend? Indian masala? Thai paste?)
- **Cultural context**: "Pakistani grandmother's Friday dish" → likely chicken pulao or biryani
- **Substitutions**: User says "no onions" → LLM suggests shallots or skip
- **Explanations**: Why we chose this cardamom over that one → natural language reasoning

## Agent-by-Agent LLM Integration Plan

### 1. Ingredient Agent: The Smart Parser

**Current (Rule-Based)**:
```python
def extract_ingredients(text: str) -> List[str]:
    # Pattern matching for known ingredients
    if "biryani" in text.lower():
        return ["chicken", "basmati rice", "onion", "tomato",
                "ginger", "garlic", "cumin", "coriander"...]
    # Rigid, predefined patterns
```

**Future (LLM-Enhanced)**:
```python
async def extract_ingredients_llm(text: str) -> List[Ingredient]:
    prompt = f"""
    User wants to cook: {text}

    Extract ingredients needed, considering:
    - Cultural/regional variations
    - Serving size
    - Standard vs. authentic preparations

    Return as JSON with quantities and notes.
    """

    response = await anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": prompt}]
    )

    # Parse structured output
    ingredients = parse_llm_response(response)
    return ingredients
```

**What This Enables**:
- "Make something with what I have: chicken, rice, random spices" → LLM suggests recipes AND missing ingredients
- "Healthy meal for a diabetic" → LLM considers dietary restrictions
- "Quick weeknight dinner" → LLM prioritizes simple, fast recipes

**Fallback Strategy**:
```python
try:
    ingredients = await extract_ingredients_llm(text)
except (APIError, TimeoutError):
    # LLM failed, fall back to rules
    ingredients = extract_ingredients_rules(text)
```

### 2. Product Agent: The Smart Matcher

**Current (Rule-Based)**:
```python
def match_product(ingredient: str) -> Product:
    # Fuzzy string matching
    matches = []
    for product in products:
        if ingredient.lower() in product.name.lower():
            matches.append(product)

    # Return best match by some heuristic
    return max(matches, key=lambda p: quality_score(p))
```

**Future (LLM-Enhanced)**:
```python
async def match_product_llm(ingredient: Ingredient, candidates: List[Product]) -> Product:
    # First pass: rule-based filtering (fast)
    filtered = fuzzy_match(ingredient.name, candidates)

    # If ambiguous (multiple good matches), ask LLM
    if len(filtered) > 1 and is_ambiguous(ingredient):
        prompt = f"""
        User needs: {ingredient.name} ({ingredient.notes})
        Recipe context: {ingredient.recipe_context}

        Available products:
        {format_products(filtered)}

        Which product best matches the user's need?
        Consider: authenticity, quality, price tier preference.
        """

        response = await anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=[{"role": "user", "content": prompt}]
        )

        return parse_product_choice(response, filtered)

    # Clear match, no LLM needed
    return filtered[0]
```

**What This Enables**:
- "Curry powder for Thai curry" → Thai red curry paste (not Indian garam masala)
- "Good cardamom for biryani" → Green cardamom pods (not ground cardamom)
- "Authentic Indian spice" → Pure Indian Foods brand (not generic store brand)

### 3. Quantity Agent: The Smart Calculator

**Current (Rule-Based)**:
```python
def calculate_quantity(recipe_amount: str, product_size: str) -> int:
    # Convert to common unit, divide, round up
    needed_oz = convert_to_oz(recipe_amount)
    product_oz = convert_to_oz(product_size)
    return math.ceil(needed_oz / product_oz)
```

**Future (LLM-Enhanced)**:
```python
async def calculate_quantity_llm(ingredient: Ingredient, product: Product) -> QuantityDecision:
    # For standard conversions, use rules (fast & reliable)
    if is_standard_conversion(ingredient, product):
        return calculate_quantity_rules(ingredient, product)

    # For complex cases, ask LLM
    prompt = f"""
    Recipe calls for: {ingredient.amount} {ingredient.unit}
    Product size: {product.size}
    Context: {ingredient.notes}

    How many units should we buy?
    Consider:
    - Minimum purchase quantity
    - Pantry staple vs one-time use
    - Freshness/shelf life
    """

    response = await anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": prompt}]
    )

    return parse_quantity_decision(response)
```

**What This Enables**:
- "A handful of cilantro" → LLM knows that's ~1/4 cup, suggests 1 bunch
- "Season to taste" → LLM suggests pantry staple size (keep extra)
- "Fresh herbs" → LLM considers they spoil quickly, suggests smaller size

### 4. Explain Agent: The Natural Language Generator

**Current (Rule-Based)**:
```python
def explain_choice(product: Product) -> str:
    tags = []
    if product.organic:
        tags.append("USDA Organic certified")
    if product.local:
        tags.append("From local co-op")

    return f"Selected for: {', '.join(tags)}"
```

**Future (LLM-Native)**:
```python
async def explain_choice_llm(product: Product, context: Context) -> Explanation:
    prompt = f"""
    We selected: {product.name} from {product.brand}
    Price: ${product.price}
    Certifications: {product.certifications}

    User preferences: {context.user_preferences}
    Recipe: {context.recipe}
    Alternative products considered: {context.alternatives}

    Explain this choice in 1-2 sentences.
    Be specific about why this product over others.
    Use casual, friendly tone.
    """

    response = await anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": prompt}]
    )

    return {
        "why_pick": extract_why_pick_tags(response),
        "trade_offs": extract_trade_offs(response),
        "explanation": response.content[0].text
    }
```

**What This Enables**:
- "I chose Pure Indian Foods Cardamom because authentic biryani needs aromatic green cardamom pods, not ground powder. Yes, $12.99 for 2oz seems expensive, but this jar will last you 8 biryani recipes - works out to $1.62 per meal."
- "Trade-off: This organic chicken costs $2/lb more than conventional, but chicken is #5 on the Dirty Dozen list - the pesticide reduction is worth it."

## The Implementation Roadmap

### Phase 1: Foundation (Current)
**Status**: ✅ Complete
- Rule-based agents working
- API structure in place
- Frontend ready for enhanced responses

### Phase 2: Explain Agent LLM Integration (Next)
**Why First**: Lowest risk, highest user value
- Doesn't affect cart accuracy
- Fails gracefully (rules generate basic tags)
- Immediate UX improvement (natural explanations)

**Implementation**:
```python
# In api/main.py
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

orch = Orchestrator(
    use_llm_extraction=False,      # Still use rules
    use_llm_explanations=True,     # Enable LLM here
    anthropic_client=client
)
```

### Phase 3: Ingredient Agent LLM Enhancement
**Why Second**: Highest impact on flexibility
- Handles "grandma's Friday chicken" inputs
- Understands dietary restrictions
- Suggests recipes from vague descriptions

**Risk**: If LLM fails, cart creation fails
**Mitigation**: Fallback to rule-based extraction

### Phase 4: Product Agent LLM Enhancement
**Why Third**: Handles ambiguous matches
- "Curry powder for butter chicken" → picks Indian blend, not Thai
- "Best cardamom for biryani" → green pods, not ground

**Risk**: Wrong product selection affects meal quality
**Mitigation**: Only use LLM for tie-breaking between good options

### Phase 5: Quantity Agent LLM Enhancement
**Why Last**: Rules handle 90% of cases fine
- LLM only for ambiguous amounts ("a bunch", "to taste")
- Most conversions are straightforward math

## Cost & Performance Considerations

### API Costs (Anthropic Claude)
**Current Pricing** (Claude 3.5 Sonnet):
- Input: $3 / million tokens
- Output: $15 / million tokens

**Estimated Per-Cart Cost**:
```
Ingredient Agent:
  - Prompt: ~500 tokens
  - Response: ~300 tokens
  - Cost: ~$0.006 per cart

Product Agent (4 ambiguous products):
  - Prompt: ~800 tokens each
  - Response: ~200 tokens each
  - Cost: ~$0.015 per cart

Explain Agent (10 products):
  - Prompt: ~400 tokens each
  - Response: ~150 tokens each
  - Cost: ~$0.025 per cart

Total: ~$0.046 per cart (~5 cents)
```

**At Scale**:
- 1,000 carts/day = $46/day = $1,380/month
- 10,000 carts/day = $460/day = $13,800/month

**Cost Optimization**:
1. **Caching**: Same ingredients → cache LLM response
2. **Batching**: Send multiple products in one LLM call
3. **Selective Usage**: Only use LLM when rules are uncertain
4. **Model Selection**: Use Claude Haiku for simple tasks ($0.25/$1.25 per million tokens)

### Latency Considerations

**Current (Rule-Based)**:
- Cart generation: 100-300ms
- User sees results: <500ms total

**With LLM (Naive)**:
- Each LLM call: 1-3 seconds
- 15 LLM calls serially: 15-45 seconds (unacceptable!)

**With LLM (Optimized)**:
```python
async def create_cart_optimized(meal_plan: str):
    # Parallel LLM calls where possible
    ingredient_task = extract_ingredients_llm(meal_plan)

    # Wait for ingredients first
    ingredients = await ingredient_task

    # Batch product matching (all products in one call)
    product_tasks = [
        match_product_llm_batch(ingredients)
    ]

    # Parallel explanation generation
    explanation_tasks = [
        explain_choice_llm(product) for product in products
    ]

    await asyncio.gather(*explanation_tasks)

    # Total time: ~3-5 seconds (acceptable)
```

**Target**: <5 seconds end-to-end with LLM

## Prompt Engineering: The Secret Sauce

### Good Prompt Pattern

```python
prompt = f"""
You are a grocery shopping assistant helping someone plan meals.

CONTEXT:
- User wants to make: {meal_plan}
- Budget preference: {budget_tier}
- Dietary restrictions: {restrictions}

AVAILABLE PRODUCTS:
{format_products_for_llm(products)}

TASK:
Select the best product for {ingredient}.

CRITERIA (in order of importance):
1. Matches ingredient type and quality needed
2. Appropriate size for recipe
3. Aligns with budget preference
4. Organic where it matters (Dirty Dozen items)
5. Local when available at similar price

OUTPUT FORMAT:
Return JSON:
{{
  "selected_product_id": "...",
  "reasoning": "...",
  "trade_offs": ["..."]
}}
"""
```

### Why This Works
- **Clear role**: LLM knows it's a shopping assistant
- **Rich context**: Budget, restrictions, available products
- **Explicit criteria**: Priority order prevents arbitrary choices
- **Structured output**: JSON ensures parseable responses

## Monitoring & Debugging LLM Decisions

### Logging Every LLM Call
```python
async def call_llm_with_logging(prompt: str, context: dict):
    logger.info(f"LLM call started", extra={
        "prompt_length": len(prompt),
        "context": context
    })

    start = time.time()
    response = await client.messages.create(...)
    duration = time.time() - start

    logger.info(f"LLM call completed", extra={
        "duration_ms": duration * 1000,
        "tokens_in": response.usage.input_tokens,
        "tokens_out": response.usage.output_tokens,
        "cost_usd": calculate_cost(response.usage)
    })

    return response
```

### A/B Testing LLM vs Rules
```python
# Randomly use LLM or rules, compare results
if random.random() < 0.5:
    result = await llm_approach(input)
    log_result("llm", result)
else:
    result = rule_approach(input)
    log_result("rules", result)

# Later: analyze which produces better carts
```

## The Future: Multi-Agent Collaboration

**Vision**: Agents don't just run sequentially - they collaborate

```python
# Ingredient Agent suggests: "chicken, rice, tomatoes..."
# Product Agent thinks: "This looks like biryani, need Indian spices"
# Product Agent asks Ingredient Agent: "Should I add garam masala?"
# Ingredient Agent responds: "Yes, and cardamom + cinnamon"

# Multi-turn LLM conversation between agents
```

**Why This Is Powerful**:
- Recovers from missing ingredients ("You didn't mention spices, but biryani needs...")
- Suggests substitutions ("No basmati? Use jasmine rice instead")
- Adapts to availability ("Cardamom sold out, use cardamom powder × 2")

## Error Handling & Graceful Degradation

### The Fallback Chain
```
Try: LLM-enhanced agent
↓ (if timeout/error)
Try: Rule-based agent
↓ (if still fails)
Return: Partial result with error message
↓ (if critical failure)
Show: "Try again later" message
```

### Example: Ingredient Extraction Failure
```python
async def robust_ingredient_extraction(text: str) -> List[Ingredient]:
    try:
        # Try LLM first (best quality)
        return await extract_ingredients_llm(text, timeout=3)
    except (APIError, TimeoutError) as e:
        logger.warning(f"LLM extraction failed: {e}")

        try:
            # Fall back to rules (good quality)
            return extract_ingredients_rules(text)
        except Exception as e:
            logger.error(f"Rule extraction failed: {e}")

            # Return best guess (minimal quality)
            return fallback_extract(text)
```

## Privacy & Data Handling

### What We Send to LLMs
- ✅ Meal descriptions ("chicken biryani for 4")
- ✅ Product names and attributes
- ✅ Recipe context

### What We DON'T Send
- ❌ User identities
- ❌ Purchase history
- ❌ Location data beyond "local preference"
- ❌ Payment information

### Compliance
- All LLM calls logged for debugging
- User can opt out of LLM features (fall back to rules)
- Data retention: LLM calls not stored beyond logging period

---

**Next**: [UI Flows & User Interactions](./03-ui-flows.md) - How users experience the AI-enhanced cart

