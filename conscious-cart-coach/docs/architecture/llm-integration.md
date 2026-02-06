# LLM Integration: The AI That Knows Its Place

**Updated**: 2026-01-24

---

## The Great LLM Debate: To AI or Not to AI?

When we started building Conscious Cart Coach in 2024, everyone was screaming "PUT AI IN EVERYTHING!"

**VCs**: "Is it AI-powered?"
**Users**: "Does it use ChatGPT?"
**Tech Twitter**: "If you're not using LLMs, you're already obsolete!"

We had a choice:

**Option A**: Go full AI. Let Claude handle ingredient extraction, product matching, scoring, explanations—everything. Ship fast. Get funding. Call it "revolutionary AI shopping assistant."

**Option B**: Build deterministic first. Add AI strategically. Keep scoring rules-based. Take longer. Be boring.

**We chose Option B.**

Here's why—and how we actually integrated LLM in the places where it makes sense.

---

## The Restaurant Incident: A True Story

Let me tell you about a real thing that happened to one of our team members.

He used a popular AI-powered meal planning app. It suggested "healthy Mediterranean dinner." Great! He bought the ingredients. Then he checked the app again 10 minutes later to see the recipe.

**The ingredients were different.**

Same prompt. Same user. Different day. Different results.

He called support: "Why did the ingredient list change?"

Support: "Our AI model is probabilistic. Each query is unique!"

**Translation**: "We have no idea. The AI decided something different this time. ¯\\_(ツ)_/¯"

This is the moment we decided: **Core recommendations must be deterministic.**

---

## The Hybrid Philosophy: The Best of Both Worlds

Our approach: **LLM for the creative parts. Rules for the critical parts.**

Think of it like a hospital:
- **Doctors diagnose** (pattern recognition, creativity, judgment) ← LLM-like
- **Pharmacists dose medication** (precise calculations, no deviation) ← Deterministic

You want your doctor to be creative: "Hmm, these symptoms could indicate three different conditions..."

You DO NOT want your pharmacist to be creative: "Hmm, maybe 250mg? Or 300mg? Let's try 320mg today!"

In our system:
- **LLM handles**: Understanding vague prompts, explaining tradeoffs
- **Rules handle**: Scoring products, selecting winners, calculating prices

---

## Where We Use LLM: The Two Strategic Touchpoints

### Touchpoint 1: Ingredient Extraction (Input Side)

**The Problem**:

```
User: "I want something healthy and seasonal for dinner"
```

**What does this mean?**
- Salad? Soup? Grilled fish?
- How many people?
- What season? (System knows it's January in NJ)
- How healthy? (Low-cal? Organic? Heart-healthy?)

**Deterministic approach** (template matching):
```python
if "biryani" in prompt:
    return BIRYANI_RECIPE
elif "salad" in prompt:
    return SALAD_RECIPE
else:
    return ERROR
```

**Works great for**: Known recipes
**Fails miserably for**: "I want something healthy and seasonal"

---

**LLM approach**:

```python
def extract_ingredients_with_llm(prompt: str) -> list[dict]:
    """Ask Claude to interpret the user's intent."""

    system_prompt = """
    You are a grocery shopping assistant. Extract ingredients from user requests.

    Rules:
    - Return structured JSON
    - Include quantity, unit, category
    - Mark optional items
    - Consider seasonality (currently January in New Jersey)
    - For vague requests, suggest healthy, seasonal options
    """

    user_prompt = f"""
    User request: "{prompt}"

    Extract ingredients as JSON list.
    """

    response = claude.complete(system_prompt, user_prompt)
    return parse_json(response)
```

**Example output for "something healthy and seasonal"**:
```json
[
    {"name": "kale", "quantity": "1 bunch", "category": "produce", "optional": false},
    {"name": "sweet_potato", "quantity": "2 medium", "category": "produce", "optional": false},
    {"name": "quinoa", "quantity": "1 cup", "category": "grains", "optional": false},
    {"name": "olive_oil", "quantity": "2 tbsp", "category": "oils", "optional": false},
    {"name": "lemon", "quantity": "1", "category": "produce", "optional": true}
]
```

**Why this works**:
- Claude knows January in NJ → kale, sweet potato in season
- "Healthy" → plant-based, whole grains
- Reasonable portions
- Structured output we can validate

---

**The Fallback Strategy**:

```python
# Try LLM first (if enabled)
if self.use_llm and self.anthropic_client:
    try:
        result = extract_ingredients_with_llm(prompt)
        if validate_json(result):
            return AgentResult(
                status="ok",
                facts={"ingredients": result, "extraction_method": "llm"}
            )
    except APIError as e:
        logger.warning(f"LLM extraction failed: {e}")

# Fallback to templates
return self._extract_with_templates(prompt)
```

**What users see**:
- LLM works → "🤖 AI extracted from your request"
- LLM fails → "Using recipe template: biryani"

Like having a multilingual translator who falls back to a phrasebook when stuck.

---

### Touchpoint 2: Decision Explanations (Output Side)

**The Problem**:

After deterministic scoring, we have:
```python
item = DecisionItem(
    ingredient_name="spinach",
    selected_product_id="prod_12345",
    tier_symbol=TierSymbol.BALANCED,
    score=68,
    reason_short="Organic recommended (EWG)",  # ← Terse, code-like
    ...
)
```

**Users see**: "Organic recommended (EWG)"

**Users think**: "What does EWG mean? Why is organic 'recommended'? How much more does it cost?"

---

**LLM approach**:

```python
def explain_decision_with_llm(
    ingredient_name: str,
    recommended_product: dict,
    scoring_factors: list[str],
    cheaper_option: str | None,
    conscious_option: str | None,
    user_prefs: dict,
) -> str:
    """Generate natural language explanation."""

    system_prompt = """
    You are a grocery shopping advisor explaining product recommendations.

    Rules:
    - 1-2 sentences maximum
    - Reference actual prices and brands
    - Explain tradeoffs (health vs cost, ethics vs price)
    - Never hallucinate product details
    - Be conversational but factual
    """

    user_prompt = f"""
    Ingredient: {ingredient_name}
    Recommended: {recommended_product['brand']} at ${recommended_product['price']:.2f}
    Scoring factors: {', '.join(scoring_factors)}
    Cheaper option: {cheaper_option or 'None available'}
    Conscious option: {conscious_option or 'None available'}

    Explain why this product was recommended.
    """

    return claude.complete(system_prompt, user_prompt)
```

**Example output**:
```
"The Earthbound Farm option at $3.99 offers organic certification which is
important for spinach since it's on the EWG Dirty Dozen list for high
pesticide residue. While it costs $2 more than the conventional option,
you're avoiding 3-5 common pesticide residues."
```

**What we give Claude**:
- Actual product data (brand, price)
- Scoring factors from our deterministic engine
- Cheaper/conscious alternatives
- User preferences

**What Claude can't hallucinate**:
- Product prices (we provide them)
- Scoring logic (we provide the factors)
- Alternative options (we provide them)

**What Claude CAN do**:
- Synthesize into natural language
- Explain the tradeoff
- Reference domain knowledge (EWG Dirty Dozen, pesticides)

---

**The Implementation**:

```python
# In DecisionEngine.decide():

# Step 1: Score deterministically (always happens)
recommended = self._score_and_rank(candidates)[0]
tier = self._assign_tier(recommended)
reason_short = self._get_short_reason(recommended)

# Step 2: Optional LLM explanation
reason_llm = None
if self.use_llm_explanations:
    try:
        reason_llm = explain_decision_with_llm(
            ingredient_name=ingredient,
            recommended_product=recommended.as_dict(),
            scoring_factors=recommended.adjustments,
            cheaper_option=cheaper_neighbor,
            conscious_option=conscious_neighbor,
            user_prefs=user_prefs
        )
    except Exception as e:
        logger.warning(f"LLM explanation failed: {e}")
        # reason_llm stays None, we use reason_short

return DecisionItem(
    reason_short=reason_short,      # Always present (deterministic)
    reason_llm=reason_llm,          # Optional (LLM-enhanced)
    ...
)
```

**UI display**:

```python
# Always show the short reason
st.write(f"Why: {item.reason_short}")

# Optionally show LLM explanation
if item.reason_llm:
    with st.expander("🤖 Show AI explanation"):
        st.markdown(item.reason_llm)
```

**What users experience**:
- **Without LLM**: "Organic recommended (EWG)" ← Quick, functional
- **With LLM**: Click expander → Rich context ← Deeper understanding

Like reading a textbook (short reason) vs having a tutor explain it (LLM reason).

---

## What We Explicitly DON'T Use LLM For

### 1. Product Scoring

**Why not?**

```python
# ❌ DON'T DO THIS
score = claude.score_product(
    product=product,
    user_prefs=user_prefs,
    ewg_status=ewg_status
)
```

**Problems**:
1. **Non-deterministic**: Same product might score 72 one time, 68 next time
2. **Slow**: API latency for every product (100 products = 100 API calls)
3. **Expensive**: $0.01 per product × 100 products × 1000 users = $$$
4. **Un-auditable**: "Why did this score change?" → "The model decided differently"
5. **Hallucination risk**: Claude might invent facts about products

---

**Our approach**:

```python
# ✅ DO THIS
score = 50  # Neutral baseline

# EWG penalty (deterministic)
if dirty_dozen and not organic:
    score -= 20

# Seasonality bonus (deterministic)
if in_season:
    score += 15

# ... etc
```

**Benefits**:
1. **Deterministic**: Same input → same output
2. **Fast**: Pure computation, no API calls
3. **Free**: No LLM costs
4. **Auditable**: Every score has a paper trail
5. **Trustworthy**: Users can verify the logic

Like using a calculator vs asking someone to guess the math.

---

### 2. Product Matching

**Why not?**

```python
# ❌ DON'T DO THIS
products = claude.find_products(
    ingredient="spinach",
    store="ShopRite",
    inventory=inventory
)
```

**Problems**:
1. **Slow**: API call for every ingredient
2. **Unreliable**: Might return products that don't exist
3. **Miss results**: Might skip products due to naming variations
4. **Expensive**: API calls add up

---

**Our approach**:

```python
# ✅ DO THIS
products = database.query("""
    SELECT * FROM products
    WHERE ingredient_name = ?
    AND store = ?
    AND in_stock = true
""", (ingredient, store))
```

**Benefits**:
1. **Fast**: Local SQLite query
2. **Reliable**: Returns exactly what exists
3. **Complete**: SQL LIKE can handle variations
4. **Free**: No API costs

Like searching a library catalog vs asking someone to remember every book.

---

### 3. Cart Totals

**Why not?**

```python
# ❌ DON'T DO THIS
total = claude.calculate_total(cart_items)
```

**This is just... no.** Math is deterministic. Use a calculator.

---

## The Cost Analysis: Is LLM Worth It?

### Anthropic Claude Sonnet 4.5 Pricing (as of 2024)

```
Input tokens:  $0.003 / 1K tokens
Output tokens: $0.015 / 1K tokens
```

### Cost Breakdown Per Cart

**Ingredient Extraction** (1 API call)
```
System prompt:  ~200 tokens
User prompt:    ~50 tokens
Response:       ~300 tokens (JSON)
────────────────────────────────
Total: ~550 tokens
Cost:  ~$0.01
```

**Decision Explanations** (10 items, 10 API calls)
```
Per item:
  System prompt:  ~150 tokens
  User prompt:    ~200 tokens
  Response:       ~100 tokens
  Subtotal:       ~450 tokens × 10 = 4,500 tokens

Cost: ~$0.03
```

**Total per cart**: ~$0.045

---

### Monthly Cost Scenarios

| Usage | Deterministic | LLM Extraction Only | Full LLM |
|-------|---------------|---------------------|----------|
| 10 carts/month | $0 | $0.10 | $0.45 |
| 100 carts/month | $0 | $1.00 | $4.50 |
| 1,000 carts/month | $0 | $10.00 | $45.00 |
| 10,000 carts/month | $0 | $100.00 | $450.00 |

**Break-even analysis**:

If 10% of users enable LLM features:
- 10,000 carts/month → 1,000 LLM-enabled → $45/month
- Affordable for a small startup

If 100% of users enable LLM features:
- 10,000 carts/month → $450/month
- Still reasonable, but need to optimize

---

### Optimization Strategies

**1. Batch Explanations**

Instead of 10 API calls:
```python
# ❌ Current (10 calls)
for item in items:
    item.reason_llm = explain_decision(item)
```

Do this (1 call):
```python
# ✅ Batched (1 call)
all_explanations = explain_all_decisions(items)
for item, explanation in zip(items, all_explanations):
    item.reason_llm = explanation
```

**Savings**: $0.03 → $0.01 per cart (67% reduction)

---

**2. Caching Common Extractions**

```python
# Cache structure
cache = {
    "chicken biryani for 4": [cached ingredient list],
    "spinach salad": [cached ingredient list],
    ...
}

# Check cache first
if prompt in cache:
    return cache[prompt]  # Free!

# Otherwise, call LLM
result = extract_with_llm(prompt)
cache[prompt] = result
return result
```

**Savings**: 80% of users use common recipes → 80% fewer API calls

---

**3. Use Haiku for Simple Cases**

Claude has three models:
- **Sonnet**: Best quality (what we use)
- **Haiku**: Faster, cheaper (75% cost reduction)
- **Opus**: Highest quality (overkill for our use case)

For simple prompts ("chicken biryani for 4"), Haiku works fine.

**Savings**: $0.01 → $0.0025 for simple extractions

---

## The Latency Story: Fast vs Rich

### Deterministic Mode Latency

```
User clicks "Create cart"
  ↓
Extract ingredients (template)     10ms
Fetch products (SQLite)            50ms
Enrich with safety data            20ms
Score and decide                   15ms
Render UI                          5ms
══════════════════════════════════════
Total:                            100ms
```

**User experience**: Instant. Click → results.

Like using a calculator. Press button → answer.

---

### LLM Mode Latency

```
User clicks "Create cart"
  ↓
Extract ingredients (LLM)          1,500ms  ← API call
Fetch products (SQLite)            50ms
Enrich with safety data            20ms
Score and decide                   15ms
Generate explanations (LLM, 10x)   2,000ms  ← API calls
Render UI                          5ms
═══════════════════════════════════════════
Total:                            3,590ms
```

**User experience**: 3.6 seconds. Noticeable, but acceptable.

Like asking a librarian vs looking up the catalog yourself. Takes longer, but richer result.

---

### UI Patterns for Managing Latency

**1. Loading Indicators**

```python
if use_llm_extraction:
    with st.spinner("🤖 Analyzing your request..."):
        result = orch.step_ingredients(prompt)
else:
    result = orch.step_ingredients(prompt)
```

**User sees**: Spinner with message, knows what's happening.

**Psychology**: People tolerate latency when they understand why.

---

**2. Progressive Enhancement**

```python
# Show deterministic results immediately
st.write(f"Reason: {item.reason_short}")

# Add LLM explanation asynchronously
if item.reason_llm:
    with st.expander("🤖 Show detailed explanation"):
        st.markdown(item.reason_llm)
```

**User sees**: Quick answer first, rich context on demand.

Like Google search:
- Instant results (titles, URLs)
- Click for rich preview (takes a moment)

---

## Failure Modes: What Goes Wrong and How We Handle It

### Failure 1: API Key Missing

**Scenario**: User enables LLM features but forgets to add `ANTHROPIC_API_KEY` to `.env`.

**What happens**:
```python
try:
    from ..llm.client import get_anthropic_client
    client = get_anthropic_client()
    if not client:
        raise ValueError("No API key found")
except Exception as e:
    logger.warning(f"LLM initialization failed: {e}")
    self.use_llm = False  # Disable LLM
```

**User sees**: "⚠️ AI features unavailable (API key missing). Using standard mode."

**Result**: App continues working in deterministic mode.

---

### Failure 2: API Timeout

**Scenario**: Anthropic API is slow or down.

**What happens**:
```python
try:
    response = client.messages.create(
        model="claude-sonnet-4.5",
        messages=[...],
        timeout=10.0  # 10 second timeout
    )
except APITimeoutError:
    logger.warning("LLM request timed out")
    return None  # Fallback to templates/deterministic
```

**User sees**: "Using recipe templates" (ingredient extraction) or short reasons (explanations).

**Result**: Slightly worse UX, but no crash.

---

### Failure 3: Invalid JSON Response

**Scenario**: Claude returns malformed JSON for ingredient extraction.

**What happens**:
```python
try:
    ingredients = json.loads(response.content)
    validate_ingredient_schema(ingredients)
    return ingredients
except (JSONDecodeError, ValidationError) as e:
    logger.warning(f"Invalid LLM response: {e}")
    return None  # Trigger template fallback
```

**User sees**: "Using recipe templates" instead of LLM extraction.

**Result**: Less flexible input, but reliable output.

---

### Failure 4: Hallucination in Explanations

**Scenario**: Claude invents a product detail.

**Example bad output**:
```
"This organic spinach is locally grown in New Jersey farms and
harvested within 24 hours, ensuring peak freshness."
```

**Problem**: We never told Claude it was "locally grown" or "harvested within 24 hours." It hallucinated.

**How we prevent this**:

```python
system_prompt = """
Rules:
- ONLY reference data provided in the prompt
- DO NOT invent product details
- DO NOT assume shipping/harvest times
- If unsure, stay general
"""
```

**Example good output**:
```
"The Earthbound Farm option at $3.99 offers organic certification
which is important for spinach since it's on the EWG Dirty Dozen
list for high pesticide residue."
```

**Only references**:
- Brand name (we provided)
- Price (we provided)
- Organic status (we provided)
- EWG classification (we provided)

**Doesn't hallucinate**:
- Farm location
- Harvest time
- Freshness claims

---

### Failure 5: Cost Runaway

**Scenario**: User keeps clicking "Create cart" repeatedly, racking up API costs.

**Current state**: No protection.

**Future protection**:
```python
# Rate limiting
if user.api_calls_today > 100:
    return "Daily LLM limit reached. Switch to deterministic mode?"

# Cost tracking
user.total_cost += estimate_cost(prompt)
if user.total_cost > 10.00:  # $10 monthly cap
    notify_user("You've used $10 in LLM features this month")
```

Like credit card alerts: "You've spent $500 on coffee this month. Is that right?"

---

## The Anthropic API Client: Implementation Details

### Lazy Loading Pattern

```python
class IngredientAgent:
    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm
        self._llm_extractor = None  # Not loaded yet

        # Only import if needed
        if self.use_llm:
            try:
                from ..llm.ingredient_extractor import extract_ingredients_with_llm
                self._llm_extractor = extract_ingredients_with_llm
            except ImportError:
                logger.warning("LLM module not available")
                self.use_llm = False
```

**Why?**
- Faster startup when LLM disabled
- No unnecessary imports
- Graceful degradation if `anthropic` package missing

Like not loading winter gear until it snows.

---

### Shared Client Pattern

```python
class Orchestrator:
    def __init__(self, use_llm_extraction: bool, use_llm_explanations: bool):
        # Create ONE client, share it
        self.anthropic_client = get_anthropic_client() if (use_llm_extraction or use_llm_explanations) else None

        # Pass to agents
        self.ingredient_agent = IngredientAgent(
            use_llm=use_llm_extraction,
            anthropic_client=self.anthropic_client  # Shared!
        )

        self.decision_engine = DecisionEngine(
            use_llm_explanations=use_llm_explanations,
            anthropic_client=self.anthropic_client  # Shared!
        )
```

**Why?**
- Connection pooling (more efficient)
- One API key check
- Consistent configuration

Like carpooling instead of everyone driving separately.

---

### Retry Logic

```python
def call_claude_with_retry(
    client: Anthropic,
    prompt: str,
    max_retries: int = 2
) -> str | None:
    for attempt in range(max_retries):
        try:
            response = client.messages.create(...)
            return response.content[0].text
        except APITimeoutError:
            if attempt < max_retries - 1:
                time.sleep(1)  # Wait 1 sec, try again
                continue
            else:
                return None  # Give up
        except APIError as e:
            logger.error(f"API error: {e}")
            return None  # Don't retry on hard errors
```

**Why retry?**
- Network hiccups happen
- Transient timeouts
- Anthropic rate limiting (temporary)

Like redialing when a call drops vs giving up immediately.

---

## Design Principles: The Rules We Follow

### 1. LLM is Enhancement, Not Requirement

```python
# ✅ Good
if llm_available:
    enhance_experience()
else:
    provide_core_functionality()

# ❌ Bad
if not llm_available:
    raise Error("LLM required")
```

**Philosophy**: The core product works without LLM. LLM makes it better.

Like a car: works without AC, but AC makes it nicer.

---

### 2. Deterministic Scoring is Sacred

```python
# ✅ Good
score = calculate_score(product, rules)  # Deterministic
explanation = llm_explain(score)         # Optional

# ❌ Bad
score = llm_score(product)  # Non-deterministic
```

**Philosophy**: Recommendations must be auditable and consistent.

Like using GPS (deterministic) vs asking for directions (variable).

---

### 3. Fail Gracefully, Never Crash

```python
# ✅ Good
try:
    llm_result = call_llm()
except:
    return fallback_result

# ❌ Bad
llm_result = call_llm()  # Crash if fails
```

**Philosophy**: LLM failure shouldn't break the app.

Like a restaurant running out of dessert vs closing the whole restaurant.

---

### 4. Cost-Conscious by Default

```python
# ✅ Good
use_llm = False  # Default off, opt-in

# ❌ Bad
use_llm = True  # Default on, surprise bills
```

**Philosophy**: Users should consciously enable paid features.

Like toll roads: signs warn you before you enter.

---

### 5. Transparency in UI

```python
# ✅ Good
st.checkbox("Enable AI ($0.045 per cart)")

# ❌ Bad
st.checkbox("Enable AI")  # Hidden costs
```

**Philosophy**: Users deserve to know what they're paying for.

Like showing the bill before charging the credit card.

---

## The Future: What's Next for LLM Integration

### Near-Term Improvements

**1. Batch Explanations**
- Reduce API calls from 10 to 1 per cart
- 67% cost reduction
- Faster latency (parallel → single request)

**2. Caching Layer**
- Cache common ingredient extractions
- 80% API call reduction for popular recipes
- Redis or local cache

**3. Model Selection**
- Use Haiku for simple prompts
- Use Sonnet for complex ones
- 50% cost reduction on simple cases

---

### Long-Term Vision

**1. Personalized Explanations**
```
User A (budget-conscious): "This saves you $2 vs the organic option"
User B (health-focused): "This reduces pesticide exposure by 80%"
Same product, different angles.
```

**2. Conversational Follow-Ups**
```
User: "Why is this spinach recommended?"
Claude: "It's organic, which matters for spinach due to pesticides."
User: "How much would I save with conventional?"
Claude: "About $2, but you'd increase pesticide exposure."
```

**3. Recipe Suggestions**
```
User: "I have leftover chicken and spinach"
Claude: "I found 3 recipes you can make: chicken salad, spinach alfredo, or..."
```

**4. Nutritional Analysis**
```
LLM: "This cart has 2,400 calories and meets 80% of daily vitamin A needs"
```

But remember: **Core recommendations stay deterministic.** LLM enhances the experience around the edges.

---

## The Bottom Line: Did We Make the Right Call?

**What we got right**:
- ✅ Deterministic scoring (trust, consistency)
- ✅ Optional LLM (cost control)
- ✅ Graceful fallbacks (reliability)
- ✅ Strategic placement (UX enhancement, not critical path)

**What we're still figuring out**:
- ⏳ Cost optimization (batching, caching)
- ⏳ Latency management (async, progressive)
- ⏳ Hallucination prevention (better prompts, validation)

**The verdict**: **Hybrid was the right choice.**

Pure deterministic would be functional but rigid.
Pure LLM would be flexible but unreliable and expensive.
Hybrid gives us the best of both worlds.

**It's like a hybrid car**:
- Electric motor (LLM) for smooth acceleration (UX enhancement)
- Gas engine (deterministic) for reliability (core functionality)
- Both work together, but you can still drive if the battery dies

---

## Further Reading

- [Technical Architecture](5-technical-architecture.md) - How the system is built
- [UI Flows](7-ui-flows.md) - What the user experiences
- [Data Flows](8-data-flows.md) - How data moves through the system

---

*"AI is a tool, not a religion. Use it where it helps. Don't use it where rules work better."*

*"The best architecture is the one that knows when to be boring."*
