# Mental Models & Design Decisions: The Philosophy Behind Conscious Cart Coach

## The Core Insight: Grocery Shopping Is a Values Problem, Not Just a Logistics Problem

Most grocery apps treat shopping as pure logistics:
- Find products
- Add to cart
- Check out

We realized: **People don't just want food. They want food that aligns with their values.**

Someone who cares about organic food doesn't want to manually check every item for certification. Someone who values authentic ingredients doesn't want to settle for "close enough" substitutes. Someone on a budget doesn't want to overspend, but also doesn't want bottom-tier quality.

**The mental model**: Shopping cart as a reflection of values, not just a transaction.

## Mental Model 1: The Multi-Store Reality

### The Problem: One Store Can't Do It All

**Traditional thinking**: Build a cart from one store (Amazon Fresh, Instacart + Whole Foods, etc.)

**Our realization**: Different stores serve different needs

```
┌─────────────────────────────────────────────────────┐
│  Your Ideal Shopping Trip                           │
├─────────────────────────────────────────────────────┤
│                                                      │
│  FreshDirect                                        │
│  └─ Fresh produce, proteins, pantry staples        │
│     Why: Convenient, good quality, reasonable price │
│                                                      │
│  Pure Indian Foods                                  │
│  └─ Specialty Indian spices                        │
│     Why: Authentic, fresh, properly sourced         │
│                                                      │
│  Local Co-op                                        │
│  └─ Seasonal vegetables, artisan products          │
│     Why: Support local, ultra-fresh, unique items   │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### The Design Decision: Multi-Store Cart Splitting

**Why We Split Carts**:
1. **Quality**: Authentic spices from specialty shops, not generic supermarkets
2. **Values**: Local co-ops for seasonal produce supports community
3. **Economics**: Bulk staples from warehouse stores, specialty items elsewhere

**Implementation Philosophy**:
```python
# Don't force everything into FreshDirect
# Instead, route products to their natural home

def route_product_to_store(product):
    if is_specialty_spice(product):
        return "Pure Indian Foods"  # Authenticity matters

    if is_seasonal_local(product):
        return "Lancaster Farm Fresh Coop"  # Support local

    if is_everyday_staple(product):
        return "FreshDirect"  # Convenience wins

    return "FreshDirect"  # Default fallback
```

### The User Mental Model

**Old way**: "I'll shop at Whole Foods for everything because organic"

**Our way**: "I'll get chicken and onions from FreshDirect, but cardamom from Pure Indian Foods because that's where the authentic stuff is"

**Key insight**: Users already shop this way in real life. We're digitizing their existing behavior.

## Mental Model 2: Size & Quantity Optimization

### The Problem: "Just Buy One" Doesn't Always Make Sense

**Scenario 1: Cardamom for Biryani**
```
Recipe needs: 6 cardamom pods
Smallest size: 2oz jar (~50 pods)

Naive approach: Buy 1 jar ($12.99)
User thinks: "This is expensive!"

Smart approach: Buy 1 jar ($12.99)
System explains: "This jar contains ~50 pods. You're using 6 for this recipe,
                 so this jar will last you 8 biryani meals. That's $1.62 per meal."

User thinks: "Oh, that's actually reasonable."
```

**Scenario 2: Fresh Cilantro**
```
Recipe needs: 1/4 cup fresh cilantro
Smallest size: 1 bunch (yields ~1 cup)

Naive approach: Buy 1 bunch ($1.99)
System explains: "Fresh herbs spoil quickly. This bunch is perfect for this recipe,
                 but use it within 3-5 days."

Smart approach: Buy 1 bunch, suggest using extra
System suggests: "Got extra cilantro? Try making cilantro chutney or add to salads."
```

### The Design Decision: Context-Aware Quantity Calculation

**Not just math**: quantity = ceil(needed / package_size)

**Contextual logic**:
```python
def calculate_smart_quantity(ingredient, product):
    base_qty = math.ceil(ingredient.amount / product.size)

    # Adjust for product type
    if product.category == "spices":
        # Spices last forever, always buy smallest practical size
        return 1 if base_qty <= 1 else base_qty

    if product.item_type == "fresh_herb":
        # Herbs spoil quickly, minimize waste
        return 1  # Never buy extra herbs

    if product.category == "grains" and product.size >= ingredient.amount * 2:
        # Bulk grains are fine, they store well
        return 1  # One large package is fine

    return base_qty
```

### The User Mental Model

**Old way**: "Add 1 to cart" (no thought about size)

**Our way**: "This recipe needs 2 tsp, the jar is 3oz, that's plenty" (informed decision)

**Key insight**: Users want to understand WHY they're buying this size, not just WHAT size it is.

## Mental Model 3: The Organic Hierarchy (Dirty Dozen)

### The Problem: Organic Is Expensive, But Sometimes Necessary

**User dilemma**:
- "I want to eat healthy (organic)"
- "I don't want to blow my budget"
- "Which items MUST be organic?"

**Our solution**: EWG's Dirty Dozen + Clean Fifteen

```
┌─────────────────────────────────────────────────────┐
│  DIRTY DOZEN (Always buy organic)                   │
├─────────────────────────────────────────────────────┤
│  1. Strawberries  ← Highest pesticide residue       │
│  2. Spinach                                          │
│  3. Kale, Collards, Mustard Greens                  │
│  4. Peaches                                          │
│  ... (12 total)                                      │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  CLEAN FIFTEEN (Conventional is fine)               │
├─────────────────────────────────────────────────────┤
│  1. Avocados     ← Lowest pesticide residue         │
│  2. Sweet Corn                                       │
│  3. Pineapple                                        │
│  4. Onions                                           │
│  ... (15 total)                                      │
└─────────────────────────────────────────────────────┘
```

### The Design Decision: Prioritize Organic Where It Matters

**Implementation**:
```python
def should_prefer_organic(ingredient):
    dirty_dozen = [
        "strawberries", "spinach", "kale", "peaches", "pears",
        "nectarines", "apples", "grapes", "bell peppers", "cherries",
        "blueberries", "green beans"
    ]

    clean_fifteen = [
        "avocados", "corn", "pineapple", "onions", "papaya",
        "peas", "asparagus", "mangoes", "eggplant", "kiwi",
        "cabbage", "cauliflower", "cantaloupe", "broccoli", "mushrooms"
    ]

    if ingredient.name.lower() in dirty_dozen:
        return "MUST"  # Strong preference

    if ingredient.name.lower() in clean_fifteen:
        return "OPTIONAL"  # Save money here

    return "NICE_TO_HAVE"  # Moderate preference
```

**Scoring impact**:
```python
if should_prefer_organic(ingredient) == "MUST":
    if "Organic" in product.certifications:
        score += 20  # Heavy weight
    else:
        score -= 10  # Penalty for non-organic
```

### The User Mental Model

**Old way**: "Organic is always better, but I can't afford everything organic"

**Our way**: "Spinach MUST be organic (#2 Dirty Dozen), but onions can be conventional (#4 Clean Fifteen)"

**Key insight**: Users want guidance on where to spend and where to save.

## Mental Model 4: Authenticity Over Convenience

### The Problem: Generic Substitutes Miss the Point

**Scenario: Making Chicken Biryani**

**Wrong approach**:
```
User needs: Cardamom for biryani
System finds: McCormick Ground Cardamom, $5.99 (at FreshDirect)
System logic: "It's cardamom, it's at the store we're already using, it's cheaper"
```

**Right approach**:
```
User needs: Cardamom for biryani
System finds: Pure Indian Foods Green Cardamom Pods, $12.99
System logic: "Biryani requires green cardamom PODS, not ground cardamom.
               Pure Indian Foods specializes in authentic Indian spices.
               Yes, it costs 2× more, but it's the right ingredient."
```

### The Design Decision: Specialty Stores for Specialty Ingredients

**Store routing logic**:
```python
SPECIALTY_MAPPINGS = {
    "indian_spices": "Pure Indian Foods",
    "thai_spices": "ImportFood.com",
    "japanese_ingredients": "Weee!",
    "local_seasonal_produce": "Lancaster Farm Fresh Coop"
}

def route_specialty_ingredient(ingredient):
    if ingredient.category == "spices" and ingredient.cuisine == "indian":
        return "Pure Indian Foods"  # Even if it means separate order

    if ingredient.is_seasonal and ingredient.locality_available:
        return "Lancaster Farm Fresh Coop"  # Support local when possible

    return "FreshDirect"  # Convenience for everything else
```

### The User Mental Model

**Old way**: "Buy cardamom from wherever is convenient"

**Our way**: "Buy AUTHENTIC cardamom from the Indian spice specialist, even if it means two shopping carts"

**Key insight**: Users making ethnic cuisine care about authenticity more than convenience.

## Mental Model 5: Transparent Trade-Offs

### The Problem: Every Choice Has Trade-Offs

**Users deserve to know**:
- Why this product over that one?
- What am I gaining?
- What am I sacrificing?

### The Design Decision: Show the Trade-Offs

**Example 1: Organic Chicken**
```
┌─────────────────────────────────────────┐
│ 365 Organic Chicken Breast              │
│ $7.99/lb                                │
│                                         │
│ Why this pick?                          │
│ ✓ USDA Organic certified                │
│ ✓ No antibiotics used                   │
│ ✓ Free-range farming                    │
│                                         │
│ Trade-offs:                             │
│ ⓘ Costs $2/lb more than conventional    │
│ ⓘ May have slightly less tender texture │
└─────────────────────────────────────────┘
```

**Example 2: Bulk Spice**
```
┌─────────────────────────────────────────┐
│ Cumin Seeds, 8oz (bulk size)            │
│ $14.99                                  │
│                                         │
│ Why this pick?                          │
│ ✓ Better value per ounce                │
│ ✓ You'll use this often                 │
│                                         │
│ Trade-offs:                             │
│ ⓘ Higher upfront cost                   │
│ ⓘ Takes storage space                   │
│ ⓘ Flavor fades after 6 months           │
└─────────────────────────────────────────┘
```

### The User Mental Model

**Old way**: "Added to cart" (no understanding of what was chosen)

**Our way**: "I chose organic chicken despite higher price because pesticides matter for poultry, but I'm aware it costs $2/lb more"

**Key insight**: Informed users make better decisions and trust the system more.

## Mental Model 6: The Three-Tier System

### The Problem: Not Everyone Has the Same Budget or Values

**User personas**:
1. **Budget-conscious**: "I want healthy food but can't afford premium prices"
2. **Balanced**: "I'll pay more for quality where it matters"
3. **Values-driven**: "I prioritize organic, local, sustainable, regardless of cost"

### The Design Decision: Three-Tier Product Selection

```
┌─────────────────────────────────────────────────────┐
│  CHEAPER TIER                                        │
├─────────────────────────────────────────────────────┤
│  Philosophy: Maximize value, minimize cost          │
│  Choices:                                            │
│  - Conventional produce (when Clean Fifteen)        │
│  - Store brands over name brands                    │
│  - Bulk sizes for staples                           │
│  Example: Yellow Onions, $0.99/lb (conventional)    │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  BALANCED TIER                                       │
├─────────────────────────────────────────────────────┤
│  Philosophy: Quality where it matters, save elsewhere│
│  Choices:                                            │
│  - Organic for Dirty Dozen, conventional for rest   │
│  - Trusted brands for specialty items               │
│  - Appropriate sizes (not always bulk)              │
│  Example: Bell & Evans Chicken, $6.99/lb (no antibiotics)│
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  CONSCIOUS TIER                                      │
├─────────────────────────────────────────────────────┤
│  Philosophy: Values over price                      │
│  Choices:                                            │
│  - Organic everything                                │
│  - Local co-ops and small producers                 │
│  - Specialty authentic ingredients                  │
│  Example: Lancaster Coop Organic Onions, $1.99/lb (local)│
└─────────────────────────────────────────────────────┘
```

**Scoring by tier**:
```python
def apply_tier_preference(score, product, user_tier):
    if user_tier == "conscious":
        if product.local:
            score += 15
        if product.organic:
            score += 10
        if product.sustainable:
            score += 10
        # Price penalty ignored for conscious tier

    elif user_tier == "balanced":
        if product.organic and ingredient.dirty_dozen:
            score += 20  # Organic matters for Dirty Dozen
        if product.quality_score > 7:
            score += 5
        if product.price > average_price * 1.5:
            score -= 5  # Moderate price sensitivity

    elif user_tier == "cheaper":
        if product.price < average_price * 0.8:
            score += 15  # Strong preference for cheap
        if product.organic:
            score += 2  # Slight bonus, but not priority
        if product.bulk:
            score += 10  # Bulk saves money

    return score
```

### The User Mental Model

**Old way**: "Cheapest" or "Organic everything" (binary choice)

**Our way**: "I'm balanced tier - organic chicken (Dirty Dozen-adjacent), conventional onions (Clean Fifteen), authentic spices (quality matters)"

**Key insight**: Users want a strategy that fits their budget AND their values.

## Mental Model 7: The Future Vision - Conversational Shopping

### Where We're Heading: Natural Language Planning

**Today**:
```
User types: "chicken biryani for 4"
System: [returns fixed cart based on rules]
```

**Tomorrow**:
```
User: "I want to make chicken biryani for 4, but I'm on a budget"
AI: "I can do that! Let me prioritize affordable options.
     - Using conventional chicken instead of organic (saves $6)
     - Smaller spice sizes since you mentioned budget
     - Still getting authentic Pure Indian Foods spices where it matters

     Total: $42 instead of $68. Want to see the cart?"

User: "Actually, I care about organic chicken, but don't need fancy spices"
AI: "Got it, swapping to organic chicken and using store-brand spices:
     - Organic chicken: $7.99/lb
     - FreshDirect curry powder instead of Pure Indian Foods garam masala

     Total: $51. Better?"

User: "Perfect!"
```

### The Design Decision: LLM as Negotiator

**Mental model**: Shopping as a conversation, not a form

```python
class ConversationalOrchestrator:
    async def negotiate_cart(self, user_message: str, cart_history: List[Cart]) -> Response:
        """
        User and AI negotiate the cart through conversation

        Capabilities:
        - Understand budget constraints
        - Suggest swaps and alternatives
        - Explain trade-offs in natural language
        - Remember user preferences across conversations
        """

        # Build context from history
        context = self._build_context(cart_history)

        # LLM understands user intent
        intent = await self.llm.parse_intent(user_message, context)

        if intent.type == "budget_constraint":
            return await self._optimize_for_budget(intent, cart_history[-1])

        if intent.type == "substitution_request":
            return await self._find_substitution(intent, cart_history[-1])

        # ... etc
```

### The User Mental Model

**Old way**: "Fill out form → get result → accept or reject"

**New way**: "Have conversation → negotiate preferences → arrive at personalized cart"

**Key insight**: Shopping is social. People want to discuss and negotiate, not just click buttons.

## Design Decision: Why CSV Instead of Database?

### The Question

"Why use CSV files for 353 products instead of PostgreSQL?"

### The Answer: Right Tool for the Stage

**Stage 1 (Now): Exploration**
- **Need**: Fast iteration on product data
- **Reality**: Changing prices, adding products, adjusting categories daily
- **Tool**: CSV (human-readable, git-tracked, no migrations)

**Stage 2 (Soon): Growth**
- **Need**: 1,000-5,000 products, basic search
- **Reality**: CSV loading takes <100ms, good enough
- **Tool**: CSV + in-memory indexing

**Stage 3 (Future): Scale**
- **Need**: 10,000+ products, user accounts, purchase history
- **Reality**: CSV loading becomes slow, need complex queries
- **Tool**: PostgreSQL with proper indexes

**Stage 4 (Long-term): Production**
- **Need**: Multi-tenant, real-time inventory, recommendations
- **Reality**: Need ACID transactions, complex joins, caching layer
- **Tool**: PostgreSQL + Redis + proper data architecture

### The Philosophy

> "Premature optimization is the root of all evil" - Donald Knuth

**What we optimized for**:
- ✅ Speed of development (CSV edits in VS Code)
- ✅ Transparency (git diff shows exactly what changed)
- ✅ Simplicity (no database server to run locally)

**What we'll optimize for later**:
- ⏳ Query performance (when CSV becomes bottleneck)
- ⏳ Concurrent writes (when multiple people update inventory)
- ⏳ Complex queries (when we add recommendations)

**Key insight**: The best architecture is the simplest one that solves today's problem, with a clear path to tomorrow's solution.

## Design Decision: Why Agent Pattern Instead of Monolithic Function?

### The Temptation

```python
# Simple approach: one big function
def create_cart(meal_plan: str) -> Cart:
    ingredients = extract_ingredients(meal_plan)
    products = match_products(ingredients)
    quantities = calculate_quantities(products, ingredients)
    return Cart(products, quantities)
```

**Pros**: Simple, straightforward, easy to understand

**Cons**: Can't enhance individual steps independently

### The Agent Pattern

```python
# Agent approach: specialized components
class Orchestrator:
    def __init__(self):
        self.ingredient_agent = IngredientAgent()
        self.product_agent = ProductAgent()
        self.quantity_agent = QuantityAgent()
        self.explain_agent = ExplainAgent()

    def create_cart(self, meal_plan: str) -> Cart:
        ingredients = self.ingredient_agent.extract(meal_plan)
        products = self.product_agent.match(ingredients)
        quantities = self.quantity_agent.calculate(products, ingredients)
        explanations = self.explain_agent.generate(products)
        return Cart(products, quantities, explanations)
```

**Pros**:
- Each agent can be LLM-enhanced independently
- Easy to A/B test (LLM vs rules for one agent)
- Clear separation of concerns

**Cons**:
- More code complexity
- Slight performance overhead (object creation, function calls)

### The Philosophy: Design for Future Enhancement

**We knew**:
- LLM integration was coming
- Different agents would need different enhancement strategies
- We'd want to A/B test individual improvements

**We chose**: Agent pattern for flexibility, even though it's more code upfront

**Key insight**: Architecture should enable future improvements, not just solve today's problem.

## The Unwritten Rules: What We Learned Building This

### Rule 1: Users Want Transparency, Not Magic

**Bad**: "Added 12 items to cart" (black box)

**Good**: "Added organic chicken ($7.99) because poultry is Dirty Dozen-adjacent" (transparent reasoning)

### Rule 2: Perfect Is the Enemy of Good

**Bad**: Wait to launch until we have 10,000 products from 50 stores

**Good**: Launch with 353 curated products from 3 stores, iterate based on feedback

### Rule 3: Optimize for Understanding, Not Just Performance

**Bad**: Highly optimized code that's impossible to debug

**Good**: Readable code with clear variable names and comments, even if slightly slower

### Rule 4: Build for the User You Want, Not the User You Have

**Today's user**: Types "chicken biryani", gets cart

**Tomorrow's user**: Converses with AI about meal planning, budget, dietary restrictions

**Architecture**: Built agent pattern and API structure to support both

### Rule 5: Data Quality > Data Quantity

**Better**: 353 products with accurate sizes, certifications, and store mappings

**Worse**: 10,000 products with "varies" for size and missing certifications

## The North Star: What Success Looks Like

### One Year From Now

**User testimonial (imagined)**:
> "I used to spend 2 hours planning meals and shopping across 3 stores.
> Now I tell Conscious Cart Coach 'meal plan for the week, I'm vegetarian, budget $150',
> and it gives me recipes + shopping lists across stores.
> It knows I care about local produce but don't mind conventional onions.
> It remembers I'm allergic to peanuts.
> It's like having a personal nutritionist + shopping assistant."

### Technical Metrics

- **Accuracy**: 95%+ of carts require no manual adjustments
- **Speed**: <5 seconds to generate complete multi-store cart with LLM
- **Cost**: <$0.10 per cart (LLM + infrastructure)
- **Trust**: Users understand why each product was chosen

### Values Metrics

- **Organic adoption**: Users buy organic where it matters (Dirty Dozen)
- **Local support**: Increased purchases from local co-ops
- **Authentic cooking**: Users make ethnic dishes with proper ingredients
- **Food waste**: Smaller package sizes reduce waste

## The Philosophy in One Sentence

> **Conscious Cart Coach helps people shop according to their values, not just their wallets or convenience.**

That's the mental model. That's why every technical decision flows back to: Does this help users make value-aligned choices?

---

**End of Architecture Documentation**

These five documents capture the technical architecture, LLM integration strategy, UI flows, data flows, and mental models behind Conscious Cart Coach. Use them as a guide for future development and onboarding new team members.

