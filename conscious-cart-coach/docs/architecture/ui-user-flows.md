# UI Flows: The User's Journey Through Conscious Cart Coach

**Updated**: 2026-01-29
**Current Version**: React + FastAPI Full-Stack (v2.0)

> ⚠️ **Note**: This document contains references to both Streamlit (v1.0, deprecated) and React (v2.0, current). Look for "Journey 3: The React/HTML Demo Flow" for the current production version.

---

## The Two Parallel Universes

Imagine you're playing a video game with two difficulty modes:

**Normal Mode (Deterministic)**:
- Fast loading times
- Straightforward menus
- Works offline
- Free to play

**Enhanced Mode (LLM)**:
- Richer graphics
- NPC dialogue that adapts to you
- Requires internet connection
- Monthly subscription

Conscious Cart Coach works the same way. **Same UI, two experiences.**

Let's walk through both.

---

## Journey 1: The Quick Recipe (Deterministic Mode)

### Meet Sarah: The Busy Parent

Sarah has 15 minutes before picking up her kids. She needs to grocery shop for tonight's dinner. She heard "chicken biryani" is good and wants to try it.

---

### Screen 1: Landing Page

```
┌─────────────────────────────────────┐
│ 🛒 Conscious Cart Coach             │
│ Find better grocery options         │
│                                     │
│ What are you making?                │
│ ┌─────────────────────────────────┐ │
│ │ [Empty text box]                │ │
│ │                                 │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [Create cart]                       │
│ We'll draft ingredients for you to  │
│ confirm.                            │
│                                     │
│ 🧾 Ingredients (disabled)           │
│ ⚙️ Preferences (disabled)           │
└─────────────────────────────────────┘
```

**Sarah types**: "chicken biryani for 4"

**What happens behind the scenes**:
1. Text stored in session state (`prompt_text`)
2. Nothing else yet (no processing until button click)
3. Buttons still disabled (no cart created yet)

**Why this design?**
- Clean, minimal (no cognitive overload)
- Clear call-to-action
- Instructions set expectations

---

### Screen 2: Ingredient Confirmation Modal

**Sarah clicks "Create cart"**

**Behind the scenes (50ms)**:
```python
# on_create_cart() callback fires
orch = Orchestrator()  # Deterministic mode (default)
result = orch.step_ingredients("chicken biryani for 4")
# ↓ Template match found: BIRYANI_RECIPE
# ↓ 12 ingredients extracted
# ↓ ProductAgent checks availability
# ↓ Modal opens
```

**Sarah sees**:

```
╔═══════════════════════════════════════╗
║ Confirm ingredients                   ║
╠═══════════════════════════════════════╣
║ Edit this list before we build cart   ║
║                                       ║
║ Store: ShopRite                       ║
║ ✓ 12 available · 0 unavailable        ║
║                                       ║
║ ┌───────────────────────────────────┐ ║
║ │ Ingredient    Include   Status    │ ║
║ │ ─────────────────────────────────  │ ║
║ │ ☑ Basmati rice   ✓   Available   │ ║
║ │ ☑ Chicken        ✓   Available   │ ║
║ │ ☑ Onions         ✓   Available   │ ║
║ │ ☑ Tomatoes       ✓   Available   │ ║
║ │ ☑ Yogurt         ✓   Available   │ ║
║ │ ☑ Ginger         ✓   Available   │ ║
║ │ ☑ Garlic         ✓   Available   │ ║
║ │ ☑ Cumin          ✓   Available   │ ║
║ │ ☑ Turmeric       ✓   Available   │ ║
║ │ ☑ Ghee           ✓   Available   │ ║
║ │ ☑ Cilantro       ✓   Available   │ ║
║ │ ☑ Bay leaves     ✓   Available   │ ║
║ └───────────────────────────────────┘ ║
║                                       ║
║ 12 ingredients · 0 unavailable        ║
║                                       ║
║ [Cancel]    [Confirm 12 ingredients]  ║
╚═══════════════════════════════════════╝
```

**What Sarah can do**:
- ✏️ Edit ingredient names ("Basmati rice" → "Brown rice")
- ☑️ Uncheck items she doesn't want
- ➕ Add new rows
- ❌ Cancel and start over

**Why this gate?**
- Template extraction might not be perfect
- User might have dietary restrictions ("Skip the ghee, I'm lactose intolerant")
- User might already have some ingredients ("I have onions at home")

It's like confirming your pizza toppings before the kitchen starts cooking.

---

**Sarah clicks "Confirm 12 ingredients"**

**Behind the scenes (100ms)**:
```python
# on_confirm_ingredients() fires
orch.step_candidates()  # Fetch products for all 12 ingredients
orch.step_enrich()      # Add safety/seasonal data
bundle = orch.step_decide()  # Score and rank products
# ↓ Modal closes
# ↓ Cart view appears
```

---

### Screen 3: The Cart View (Your Pick Mode)

```
┌─────────────────────────────────────────────────────────────┐
│ LEFT COLUMN                  │  RIGHT COLUMN: YOUR CART    │
├─────────────────────────────────────────────────────────────┤
│ 🛒 Conscious Cart Coach      │  Your Cart                   │
│ Find better grocery options  │  12 items · ShopRite         │
│                              │                               │
│ What are you making?         │  Cart mode:                  │
│ ┌─────────────────────────┐  │  [💸 Cheaper]               │
│ │ chicken biryani for 4   │  │  [✅ Your pick] ← ACTIVE    │
│ └─────────────────────────┘  │  [🤝 Ethical]               │
│                              │                               │
│ [Create cart]                │  Cart total: $67.80          │
│                              │                               │
│ 🧾 Ingredients (12)          │  ───────────────────────────  │
│ ⚙️ Preferences               │                               │
│                              │  ┌──────────────────────────┐ │
│ ☐ Show debug data            │  │ Basmati Rice             │ │
│                              │  │ ⚖️ BALANCED              │ │
│                              │  ├──────────────────────────┤ │
│                              │  │ Why: Good value          │ │
│                              │  │                          │ │
│                              │  │ India Gate Basmati       │ │
│                              │  │ $8.99 · 5 lb · $0.18/oz  │ │
│                              │  │                          │ │
│                              │  │ Organic · In Season      │ │
│                              │  │                          │ │
│                              │  │ [← Cheaper] [Ethical →]  │ │
│                              │  │ Qty: [1▼]                │ │
│                              │  └──────────────────────────┘ │
│                              │                               │
│                              │  ┌──────────────────────────┐ │
│                              │  │ Chicken                  │ │
│                              │  │ 💸 CHEAPER               │ │
│                              │  ├──────────────────────────┤ │
│                              │  │ Why: Best value per oz   │ │
│                              │  │                          │ │
│                              │  │ Store Brand Chicken      │ │
│                              │  │ $4.99 · 1 lb · $0.31/oz  │ │
│                              │  │                          │ │
│                              │  │ Fresh · Available        │ │
│                              │  │                          │ │
│                              │  │ [✓ Cheaper] [Ethical →]  │ │
│                              │  │ Qty: [2▼]                │ │
│                              │  └──────────────────────────┘ │
│                              │                               │
│                              │  ... (10 more items)          │
│                              │                               │
│                              │  ───────────────────────────  │
│                              │                               │
│                              │  [Shopping list (CSV)]        │
│                              │  [Continue to store] 🚧       │
└─────────────────────────────────────────────────────────────┘
```

**What Sarah sees**:
- **12 product cards** (scrollable area)
- **Cart total**: $67.80
- **Three mode buttons**: Cheaper, Your pick (active), Ethical
- **Stepper buttons** on each card: [← Cheaper] [Ethical →]

**What each tier means**:
- **💸 Cheaper**: Best price (might sacrifice organic/local)
- **⚖️ Balanced (Your pick)**: Recommended (middle ground)
- **🤝 Ethical**: Premium (organic, local, fair trade)

---

### Interaction 1: Switching to Cheaper Mode

**Sarah thinks**: "Hmm, $67.80 is a bit much. Let me see the cheaper option."

**Sarah clicks**: [💸 Cheaper −$8.30]

**Behind the scenes**:
```python
# on_cart_mode_change("cheaper") fires
for item in bundle.items:
    if item.cheaper_neighbor_id:
        selections[item.ingredient_name] = item.cheaper_neighbor_id
    else:
        selections[item.ingredient_name] = item.selected_product_id  # Keep same
# ↓ UI reruns with new selections
```

**Sarah sees**:

```
Cart mode:
[💸 Cheaper] ← ACTIVE NOW
[✅ Your pick]
[🤝 Ethical]

Cart total: $59.50  ← Changed!
```

**Product cards update**:
- Rice: Still India Gate ($8.99) ← No cheaper option
- Chicken: Now conventional instead of organic ($3.49 vs $4.99)
- Onions: Now bulk bag instead of small pack ($1.99 vs $2.49)
- ... etc

**At the bottom**:
```
┌─────────────────────────────────────┐
│ 3 items unchanged (no alternate)    │ ▼
│ • Basmati rice                      │
│ • Cumin                             │
│ • Bay leaves                        │
└─────────────────────────────────────┘
```

**Why show this?** Transparency. Sarah knows which items *couldn't* get cheaper.

---

### Interaction 2: Stepper Buttons (Individual Item Control)

**Sarah thinks**: "I like the cheaper cart, but I want organic chicken specifically. My kid has allergies."

**Sarah scrolls to the Chicken card**:

```
┌──────────────────────────┐
│ Chicken                  │
│ 💸 CHEAPER               │
├──────────────────────────┤
│ Why: Best value per oz   │
│                          │
│ Store Brand Chicken      │
│ $3.49 · 1 lb · $0.22/oz  │
│                          │
│ Fresh                    │
│                          │
│ [✓ Cheaper] [Ethical →]  │ ← Sarah clicks Ethical
│ Qty: [2▼]                │
└──────────────────────────┘
```

**Sarah clicks**: [Ethical →]

**Behind the scenes**:
```python
# Stepper callback fires
selections["chicken"] = item.conscious_neighbor_id
cart_mode = "custom"  # No longer pure "cheaper" mode
# ↓ UI reruns
```

**Card updates**:

```
┌──────────────────────────┐
│ Chicken                  │
│ 🤝 CONSCIOUS             │ ← Changed!
├──────────────────────────┤
│ Why: Organic certified   │
│                          │
│ Bell & Evans Organic     │ ← Changed!
│ $7.99 · 1 lb · $0.50/oz  │
│                          │
│ Organic · Humane         │
│                          │
│ [← Cheaper] [✓ Ethical]  │
│ Qty: [2▼]                │
└──────────────────────────┘
```

**Cart mode updates**:
```
Cart mode:
[💸 Cheaper]
[✅ Your pick]
[🤝 Ethical]
⚙️ Custom selections  ← New indicator

Cart total: $68.50  ← Updated
```

**Sarah's experience**: "Perfect! I got the cheaper cart overall, but splurged on organic chicken where it matters."

---

### Interaction 3: Downloading Shopping List

**Sarah is ready to shop.**

**Sarah clicks**: [Shopping list (CSV)]

**Behind the scenes**:
```python
# Generate CSV
csv_lines = ["ingredient,brand,product,price,qty"]
for item in bundle.items:
    pid = current_selections[item.ingredient_name]
    product = product_lookup[pid]
    csv_lines.append(f"{item.ingredient_name},{product.brand},...{qty}")

# Trigger browser download
st.download_button(data="\n".join(csv_lines), file_name="shopping_list.csv")
```

**Browser downloads**: `shopping_list.csv`

```csv
ingredient,brand,product,price,qty
basmati_rice,India Gate,India Gate Basmati Rice 5lb,8.99,1
chicken,Bell & Evans,Bell & Evans Organic Chicken Breast,7.99,2
onions,Store Brand,Yellow Onions 3lb Bag,1.99,1
...
```

**Sarah opens it on her phone**: Boom. Shopping list ready for ShopRite.

---

## Journey 2: The Creative Request (LLM Mode)

### Meet Alex: The Adventurous Eater

Alex is bored of the same recipes. He wants something "healthy and seasonal for dinner." He doesn't know exactly what.

Alex heard this app has an AI mode. He enables it.

---

### Screen 1: Enabling LLM Features

**Alex clicks**: ⚙️ Preferences

```
╔═══════════════════════════════════════╗
║ ⚙️ Preferences                        ║
╠═══════════════════════════════════════╣
║ Location: NJ / Mid-Atlantic           ║
║ Household size: [2▼]                  ║
║ Store: [ShopRite▼]                    ║
║                                       ║
║ Dietary restrictions:                 ║
║ [vegetarian, ____________]            ║
║                                       ║
║ ───────────────────────────────────   ║
║                                       ║
║ 🤖 AI Features                        ║
║                                       ║
║ ☑ Enable AI ingredient extraction    ║
║   Parse natural language prompts      ║
║   (~$0.01 per request)                ║
║                                       ║
║ ☑ Enable detailed explanations       ║
║   AI-powered reasoning                ║
║   (~$0.03 per cart)                   ║
║                                       ║
║ 💰 Cost: ~$0.045 per cart with both  ║
╚═══════════════════════════════════════╝
```

**Alex checks both boxes**.

**Behind the scenes**:
```python
st.session_state.use_llm_extraction = True
st.session_state.use_llm_explanations = True
```

**Alex closes the popover.**

---

### Screen 2: Natural Language Input

**Alex types**: "I want something healthy and seasonal for dinner"

**Alex clicks**: [Create cart]

**Behind the scenes (3 seconds)**:

```
Loading: "🤖 Analyzing your request..."

Python:
  orch = Orchestrator(
      use_llm_extraction=True,
      use_llm_explanations=True
  )
  result = orch.step_ingredients("I want something healthy...")

  ↓ IngredientAgent calls Claude:
    "User wants: healthy, seasonal, dinner"
    "Current month: January, Location: NJ"
    "Extract ingredients as JSON"

  ↓ Claude responds:
    [
      {name: "kale", quantity: "1 bunch"},
      {name: "sweet_potato", quantity: "2 medium"},
      {name: "quinoa", quantity: "1 cup"},
      {name: "chickpeas", quantity: "1 can"},
      {name: "olive_oil", quantity: "2 tbsp"},
      {name: "lemon", quantity: "1"},
      {name: "garlic", quantity: "2 cloves"},
      {name: "tahini", quantity: "1/4 cup"}
    ]

Loading: "Finding products..."

  ↓ ProductAgent fetches candidates
  ↓ SafetyAgent checks EWG/recalls
  ↓ SeasonalAgent checks crop calendar
  ↓ DecisionEngine scores products

  ↓ Modal opens
```

---

### Screen 3: LLM-Extracted Ingredients Modal

```
╔═══════════════════════════════════════╗
║ Confirm ingredients                   ║
╠═══════════════════════════════════════╣
║ 🤖 AI extracted from your request.    ║ ← New!
║ Edit before building cart.            ║
║                                       ║
║ Store: ShopRite                       ║
║ ✓ 8 available · 0 unavailable         ║
║                                       ║
║ ┌───────────────────────────────────┐ ║
║ │ Ingredient      Include   Status  │ ║
║ │ ─────────────────────────────────  │ ║
║ │ ☑ Kale            ✓   Available  │ ║
║ │ ☑ Sweet potato    ✓   Available  │ ║
║ │ ☑ Quinoa          ✓   Available  │ ║
║ │ ☑ Chickpeas       ✓   Available  │ ║
║ │ ☑ Olive oil       ✓   Available  │ ║
║ │ ☑ Lemon           ✓   Available  │ ║
║ │ ☑ Garlic          ✓   Available  │ ║
║ │ ☑ Tahini          ✓   Available  │ ║
║ └───────────────────────────────────┘ ║
║                                       ║
║ [Cancel]    [Confirm 8 ingredients]   ║
╚═══════════════════════════════════════╝
```

**What Alex notices**:
- 🤖 Badge indicates AI extraction (not template)
- Ingredients make sense (healthy, winter vegetables)
- Kale and sweet potato are seasonal for January in NJ
- No meat (system respected his "vegetarian" preference from settings)

**Alex thinks**: "Wow, it actually understood what I wanted."

**Alex clicks**: [Confirm 8 ingredients]

---

### Screen 4: Cart with LLM Explanations

**Behind the scenes (2 seconds)**:

```
Loading: "Generating explanations..."

Python:
  bundle = orch.step_decide()

  ↓ DecisionEngine scores all products (deterministic)
  ↓ For each item, calls Claude for explanation:

    For kale:
      "Recommended: Earthbound Farm Organic Kale, $3.99"
      "Score factors: organic +20, in_season +15, best_unit_price +10"
      "Cheaper option: Store Brand Conventional, $1.99"
      "Conscious option: Local Farm Organic, $5.49"
      "User prefs: vegetarian"

      ↓ Claude responds:
        "The Earthbound Farm option at $3.99 offers organic
        certification which is important for kale since it's
        on the EWG Dirty Dozen list. It's also peak season in
        New Jersey right now, meaning better flavor and value."

  ↓ UI renders with LLM explanations
```

---

**Cart view**:

```
┌──────────────────────────────────────────────────────────────┐
│ Kale                                                         │
│ ⚖️ BALANCED                                                  │
├──────────────────────────────────────────────────────────────┤
│ Why this pick: Organic recommended (EWG)  ← Deterministic   │
│                                                              │
│ [🤖 Show AI explanation ▼]  ← NEW! Alex clicks this         │
│                                                              │
│ Earthbound Farm — Organic Baby Kale                         │
│ $3.99 · 5oz · $0.80/oz                                       │
│                                                              │
│ Organic · In Season · EWG recommends organic                │
│                                                              │
│ [← Cheaper] [Ethical →]                                      │
│ Qty: [1▼]                                                    │
└──────────────────────────────────────────────────────────────┘
```

**Expander opens**:

```
┌──────────────────────────────────────────────────────────────┐
│ Kale                                                         │
│ ⚖️ BALANCED                                                  │
├──────────────────────────────────────────────────────────────┤
│ Why this pick: Organic recommended (EWG)                    │
│                                                              │
│ [🤖 Hide AI explanation ▲]  ← Expander is open              │
│                                                              │
│ 🤖 The Earthbound Farm option at $3.99 offers organic       │
│ certification which is important for kale since it's on     │
│ the EWG Dirty Dozen list for high pesticide residue. It's  │
│ also peak season in New Jersey right now, meaning better    │
│ flavor and fresher produce. While you could save $2 with    │
│ the conventional option, you'd be exposed to 3-5 common     │
│ pesticide residues.                                         │
│                                                              │
│ Earthbound Farm — Organic Baby Kale                         │
│ $3.99 · 5oz · $0.80/oz                                       │
│                                                              │
│ Organic · In Season · EWG recommends organic                │
│                                                              │
│ [← Cheaper] [Ethical →]                                      │
│ Qty: [1▼]                                                    │
└──────────────────────────────────────────────────────────────┘
```

**Alex's reaction**: "Oh! I didn't know kale was on the Dirty Dozen list. I didn't know it was peak season. This is really helpful context."

**Alex scrolls to sweet potato card**:

```
┌──────────────────────────────────────────────────────────────┐
│ Sweet Potato                                                 │
│ 💸 CHEAPER                                                   │
├──────────────────────────────────────────────────────────────┤
│ Why this pick: Best value per oz                            │
│                                                              │
│ [🤖 Show AI explanation ▼]                                   │
│                                                              │
│ Store Brand — Sweet Potatoes 3lb Bag                        │
│ $2.49 · 3 lb · $0.05/oz                                      │
│                                                              │
│ In Season · Local Available                                 │
│                                                              │
│ [✓ Cheaper] [Ethical →]                                      │
│ Qty: [1▼]                                                    │
└──────────────────────────────────────────────────────────────┘
```

**Expands**:

```
🤖 Sweet potatoes are in peak season and this 3lb bag at $2.49
offers excellent value. Unlike kale, sweet potatoes are on the
EWG Clean Fifteen list, so conventional is perfectly safe. The
store brand is locally sourced from New Jersey farms, making it
both affordable and fresh.
```

**Alex learns**: "Okay, sweet potatoes don't need to be organic. And they're local! Cool."

---

### Comparison: What Alex Saw vs What Sarah Saw

**Sarah (Deterministic)**:
- Prompt: "chicken biryani for 4" → Template match
- Extraction: 50ms
- Explanations: "Good value" (3-5 words)
- Total time: 100ms
- Cost: $0

**Alex (LLM)**:
- Prompt: "something healthy and seasonal" → Claude interprets
- Extraction: 1,500ms
- Explanations: Natural language paragraphs with context
- Total time: 3,600ms
- Cost: $0.045

**Same UI. Different experience.**

---

## Journey 3: The Power User (Mixing Modes)

### Meet Priya: The Optimization Queen

Priya is a data analyst. She likes control. She wants:
- Fast results (deterministic)
- But occasionally detailed explanations (LLM)

**Priya's strategy**:
1. Keep LLM **disabled** by default
2. Use template-based extraction (she knows the 4 recipes)
3. **Selectively** enable LLM explanations when curious

---

### Priya's Flow

**Step 1**: Priya types "spinach salad" (template match) → 100ms

**Step 2**: Cart loads instantly with deterministic reasons

**Step 3**: Priya sees a product with "Organic recommended (EWG)"

**Step 4**: Priya thinks: "Why? I want to understand the science."

**Step 5**: Priya goes to ⚙️ Preferences → Checks "Enable detailed explanations"

**Step 6**: Priya clicks "Create cart" again

**Step 7**: Now product cards have 🤖 expanders with rich context

**Result**: Priya gets speed by default, depth on demand.

---

## Edge Cases & Error States

### Edge Case 1: No Products Found

**Scenario**: User searches for "caviar" at ShopRite. ShopRite doesn't carry caviar.

**What happens**:

```
┌─────────────────────────────────────┐
│ Your Cart                           │
│ 0 items · ShopRite                  │
│                                     │
│ ⚠️ No products found                │
│                                     │
│ We couldn't find any products for:  │
│ • Caviar                            │
│                                     │
│ Try:                                │
│ - Different store (try Whole Foods) │
│ - Simpler ingredient (try "fish")   │
└─────────────────────────────────────┘
```

**Why this is good UX**:
- Clear error message
- Actionable suggestions
- Doesn't crash
- User can try again immediately

---

### Edge Case 2: LLM API Key Missing

**Scenario**: User enables LLM features but forgot to add API key.

**What happens**:

```
⚙️ Preferences
☑ Enable AI ingredient extraction
☑ Enable detailed explanations

[User clicks "Create cart"]

⚠️ AI features temporarily unavailable
   (API key not found)

Using standard ingredient matching.
Your cart will still be generated!

[Dismiss]
```

**Behind the scenes**:
```python
try:
    client = get_anthropic_client()
    if not client:
        raise ValueError("No API key")
except Exception:
    logger.warning("LLM unavailable, falling back")
    self.use_llm = False
```

**Result**: App continues in deterministic mode. No crash.

---

### Edge Case 3: LLM Returns Garbage

**Scenario**: Claude has a bad day and returns invalid JSON.

**What happens (user doesn't see this)**:

```python
try:
    ingredients = json.loads(claude_response)
    validate_schema(ingredients)  # Check structure
    return ingredients
except (JSONDecodeError, ValidationError) as e:
    logger.warning(f"Invalid LLM response: {e}")
    return None  # Trigger template fallback
```

**User sees**:

```
⚠️ AI extraction unavailable
Using recipe template: spinach salad
```

**Result**: Graceful degradation. User doesn't know Claude failed.

---

### Edge Case 4: Partial Ingredient Availability

**Scenario**: 10 out of 12 ingredients are available at ShopRite.

**Modal shows**:

```
╔═══════════════════════════════════════╗
║ Confirm ingredients                   ║
╠═══════════════════════════════════════╣
║ Store: ShopRite                       ║
║ ✓ 10 available · 2 unavailable        ║
║                                       ║
║ ⚠️ Not in inventory: saffron, ghee    ║
║                                       ║
║ ┌───────────────────────────────────┐ ║
║ │ Ingredient    Include   Status    │ ║
║ │ ─────────────────────────────────  │ ║
║ │ ☑ Rice          ✓   Available    │ ║
║ │ ☑ Chicken       ✓   Available    │ ║
║ │ ☑ Saffron       ✓   Unavailable  │ ← User can uncheck
║ │ ☑ Ghee          ✓   Unavailable  │ ← User can uncheck
║ └───────────────────────────────────┘ ║
╚═══════════════════════════════════════╝
```

**User can**:
- Uncheck unavailable items
- Try a different store
- Proceed anyway (items won't show in cart)

**Result**: User stays in control.

---

## UI Design Principles: Why It Works

### Principle 1: Progressive Disclosure

**Don't show everything at once.**

- Start with minimal UI (text box + button)
- Show ingredient modal only after extraction
- Show LLM explanations only when expanded
- Show debug data only when toggled

Like a book: you read one page at a time, not the whole thing at once.

---

### Principle 2: Reversible Actions

**Everything can be undone.**

- Selected cheaper mode? Switch back to balanced
- Confirmed ingredients? Can edit them later (via popover)
- Changed quantity? Just change it again

Like Ctrl+Z in a text editor. Confidence to experiment.

---

### Principle 3: Graceful Degradation

**The app should never crash.**

- LLM fails? → Use templates
- No products? → Show helpful error
- API timeout? → Continue with deterministic

Like a restaurant: if they're out of salmon, suggest sea bass. Don't close the restaurant.

---

### Principle 4: Immediate Feedback

**Users should know what's happening.**

- Button click → Loading spinner ("🤖 Analyzing...")
- Mode switch → Cart total updates instantly
- Stepper click → Product card updates immediately

Like a video game: press button → immediate response. No black holes.

---

### Principle 5: Cost Transparency

**Users should know what they're paying for.**

```
☑ Enable AI ingredient extraction
  (~$0.01 per request)

💰 Cost: ~$0.045 per cart with both features
```

No surprise bills. Like a restaurant menu with prices visible.

---

## Performance Optimization in the UI

### Optimization 1: Lazy Loading Ingredients Modal

**Problem**: If we fetch ALL product data upfront, it takes forever.

**Solution**: Two-stage loading.

```python
# Stage 1: Just check availability (fast)
on_create_cart():
    ingredients = extract_ingredients()
    availability = check_which_are_available(ingredients)  # Quick SQL
    show_modal()  # User can edit

# Stage 2: Full product fetch (only after confirmation)
on_confirm_ingredients():
    products = fetch_all_products()  # Heavier query
    enrich_data()
    score_and_rank()
    show_cart()
```

**Result**: Modal opens in 50ms. User can edit immediately. Full processing happens after confirmation.

Like a restaurant: server takes your order immediately (quick), then kitchen starts cooking (slow).

---

### Optimization 2: Session State Caching

**Problem**: Streamlit reruns on every interaction. Don't want to re-query database.

**Solution**: Cache in session state.

```python
if "decision_bundle" not in st.session_state:
    st.session_state.decision_bundle = orch.step_decide()  # Heavy computation

# Reuse on every rerun
bundle = st.session_state.decision_bundle  # Instant!
```

**Result**: Only compute once. Reuse for mode switches, stepper clicks, etc.

---

### Optimization 3: Streamlit Container Height

**Problem**: 12 product cards make the page infinitely long.

**Solution**: Scrollable container with fixed height.

```python
with st.container(height=400, border=False):  # 400px max height
    for item in bundle.items:
        render_ingredient_card(item)
```

**Result**: Cart fits on screen. User scrolls within the cart area, not the whole page.

Like a shopping cart with a fixed size vs a cart that grows to infinity.

---

## Mobile Considerations (Future Work)

**Current state**: Streamlit UI is desktop-optimized.

**Mobile challenges**:
1. Two-column layout doesn't fit narrow screens
2. Popovers are harder to tap
3. Stepper buttons might be too small
4. Scrolling feels clunky

**Future improvements**:
1. Responsive layout (stack columns on mobile)
2. Larger tap targets
3. Swipe gestures for steppers
4. Native mobile app (React Native?)

But for now: **desktop-first is fine.** Most grocery shopping is planned at home.

---

## Journey 3: The React/HTML Demo Flow (Hackathon Edition)

### Meet Alex: The Hackathon Judge

Alex is judging 50 projects today. They have 2 minutes per demo. No time for npm installs or "let me just fix this bug real quick."

They open your demo link (or demo.html file) and...

---

### The Clean Slate: Figma-Perfect Landing

```
┌──────────────────────────────────────────────────────────────┐
│                                                               │
│  🛒 Conscious Cart Coach        [About]  [Contact]  [GitHub] │
│                                                               │
└──────────────────────────────────────────────────────────────┘

┌─────────────────────────────┐   ┌───────────────────────────┐
│                             │   │                            │
│  PLAN YOUR MEAL             │   │  YOUR CART                 │
│                             │   │                            │
│  Tell us what you're        │   │  Empty                     │
│  making                     │   │                            │
│                             │   │  [Image: Empty cart]       │
│  ┌────────────────────────┐ │   │                            │
│  │ e.g., "chicken biryani │ │   │  Start by creating a       │
│  │ for 4" or "healthy     │ │   │  meal plan                 │
│  │ salad"                 │ │   │                            │
│  │                        │ │   │  0 items · $0.00          │
│  │                        │ │   │                            │
│  └────────────────────────┘ │   │                            │
│                             │   │                            │
│  [Create my cart] →         │   │  ──────────────────────    │
│                             │   │                            │
│  ○ Quick recipes (templates)│   │  [Continue to store]  ✕   │
│  ○ Natural language (AI)    │   │  [Download list]       ✕   │
│                             │   │  [Preferences]         ✓   │
│                             │   │                            │
└─────────────────────────────┘   └───────────────────────────┘

Color palette:
- Header: Warm brown (#6b5f3a)
- Background: Cream (#fef9f5)
- Borders: Soft beige (#e5d5b8)
- Accents: Earthy green (#4a7c59)
```

**Key differences from Streamlit**:
1. **Two-column layout**: Input left, cart right (always visible)
2. **Disabled states**: Clear visual feedback (✕ = disabled, ✓ = enabled)
3. **Preferences always accessible**: Not hidden behind ingredient confirmation
4. **Template vs AI toggle**: Users choose extraction mode upfront

**Why this layout?**
- **Spatial consistency**: Cart doesn't jump around
- **Visual feedback**: See cart populate in real-time
- **Professional**: Matches Figma prototype exactly

Like a retail store layout: products on shelves (left), shopping cart (right).

---

### User Interaction: Typing and Watching

**Alex types**: "stir fry for 4 with chicken"

**What Alex sees (real-time)**:
```
┌─────────────────────────────┐
│  ┌────────────────────────┐ │
│  │ stir fry for 4 with    │ │  ← Live typing
│  │ chicken█               │ │
│  └────────────────────────┘ │
│                             │
│  [Create my cart] →         │  ← Button enabled (text present)
│                             │
│  ● Quick recipes (templates)│  ← Selected (default)
│  ○ Natural language (AI)    │
└─────────────────────────────┘
```

**Button states**:
- Empty text → Button disabled (gray, no cursor)
- Has text → Button enabled (green gradient, hover effect)

**No surprises**. Clear affordances.

---

### The Loading Experience: Transparency

**Alex clicks "Create my cart"**

**What Alex sees** (300ms total):

```
┌─────────────────────────────┐
│  [Creating your cart...] 🔄 │  ← Button shows spinner
│                             │
│  ● Quick recipes (templates)│
│  ○ Natural language (AI)    │
└─────────────────────────────┘

┌───────────────────────────┐
│  YOUR CART                 │
│                            │
│  Loading...                │  ← Right panel shows status
│                            │
│  [Spinner animation]       │
│                            │
└───────────────────────────┘
```

**Behind the scenes**:
```javascript
async function createCart() {
  const mealPlan = document.getElementById('meal-plan-input').value;
  const useAI = document.getElementById('ai-toggle').checked;

  // Show loading state
  button.disabled = true;
  button.innerHTML = 'Creating your cart... 🔄';
  cartPanel.innerHTML = '<div class="loading">Loading...</div>';

  try {
    const response = await fetch('http://localhost:8000/api/create-cart', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        meal_plan: mealPlan,
        use_llm: useAI  // User's choice
      }),
    });

    const data = await response.json();

    // Display cart
    displayCart(data.items, data.total);

  } catch (error) {
    // Error handling
    cartPanel.innerHTML = `
      <div class="error">
        ⚠️ Couldn't create cart
        <p>${error.message}</p>
        <button onclick="retry()">Try again</button>
      </div>
    `;
  } finally {
    // Reset button
    button.disabled = false;
    button.innerHTML = 'Create my cart →';
  }
}
```

**Why this matters**:
- **Feedback**: User knows something's happening
- **Error handling**: Clear message if API fails
- **Retry**: Easy recovery

Like a good elevator: shows floor numbers as it moves, stops gracefully if stuck.

---

### The Populated Cart: Clean and Scannable

**The cart fills in (smooth animation)**:

```
┌───────────────────────────────────────┐
│  YOUR CART                             │
│  8 items · FreshDirect · NJ            │
│                                        │
│  Cart total: $42.30                    │
│  ────────────────────────────────────  │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │ 🌾 Basmati Rice                  │ │
│  │ India Gate, Basmati Rice 5 lb    │ │
│  │ $8.99 · 5 lb · $1.80/lb          │ │
│  │                                  │ │
│  │ Why pick:                        │ │
│  │ ✓ Best value  ✓ In season       │ │
│  │                                  │ │
│  │ Trade-offs:                      │ │
│  │ • Plastic packaging              │ │
│  │                                  │ │
│  │ Qty: [1 ▼]                       │ │
│  └──────────────────────────────────┘ │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │ 🍗 Chicken Breast                │ │
│  │ Bell & Evans, Organic Chicken    │ │
│  │ $7.99 · 1 lb · $7.99/lb          │ │
│  │                                  │ │
│  │ Why pick:                        │ │
│  │ ✓ Organic  ✓ Humane raised      │ │
│  │ ✓ No recent recalls              │ │
│  │                                  │ │
│  │ Trade-offs:                      │ │
│  │ • Premium price (+$3.50)         │ │
│  │                                  │ │
│  │ Qty: [2 ▼]                       │ │
│  └──────────────────────────────────┘ │
│                                        │
│  ... (6 more items)                    │
│                                        │
│  ────────────────────────────────────  │
│                                        │
│  [Continue to store checkout →] ✓     │
│  [Download list] ✓                    │
│  [Preferences] ✓                      │
│                                        │
└───────────────────────────────────────┘
```

**Card Design Principles**:

1. **Visual hierarchy**:
   - Product name (large, bold)
   - Brand + description (medium)
   - Price info (structured)
   - Tags (colored, scannable)

2. **Information density**:
   - Everything on one card
   - No hidden accordions
   - Scrollable if list is long

3. **Tag colors**:
   - **Green** (#4a7c59): Positive attributes (Organic, Local, In season)
   - **Yellow** (#d4a574): Neutral (Best value, Recyclable)
   - **Red** (#c17a7a): Trade-offs (Plastic packaging, EWG Dirty Dozen)

**Why this works**:
- **Scannable**: Eye can quickly parse multiple items
- **Informative**: All decision factors visible
- **Honest**: Shows both pros and cons
- **Actionable**: Quantity selector right there

Like a restaurant menu: grouped by category, prices visible, descriptions clear.

---

### The Preferences Modal: Power User Features

**Alex clicks [Preferences]**

**Modal slides in** (slide-up animation, 300ms):

```
╔═══════════════════════════════════════════════╗
║  USER PREFERENCES                        [✕]  ║
╠═══════════════════════════════════════════════╣
║                                               ║
║  Store Selection                              ║
║  ┌──────────────────────────────────────────┐ ║
║  │ [FreshDirect ▼]                          │ ║
║  └──────────────────────────────────────────┘ ║
║                                               ║
║  Default Serving Size                         ║
║  ┌──────────────────────────────────────────┐ ║
║  │ [2 ▼]     people                         │ ║
║  └──────────────────────────────────────────┘ ║
║                                               ║
║  Recipe Complexity                            ║
║  ○ Simple (5 ingredients or fewer)            ║
║  ● Moderate (6-10 ingredients)                ║
║  ○ Complex (10+ ingredients, long prep)       ║
║                                               ║
║  Produce Preference                           ║
║  ● Fresh whole (avoid microplastics)          ║
║  ○ Pre-cut for convenience                    ║
║  ○ Mixed (depends on item)                    ║
║                                               ║
║  Dietary Preferences                          ║
║  ☑ Prioritize organic when on Dirty Dozen    ║
║  ☑ Prefer local produce when in season        ║
║  ☑ Show seasonal indicators                   ║
║  ☐ Strict organic-only                        ║
║  ☐ Vegetarian                                 ║
║  ☐ Vegan                                      ║
║                                               ║
║  Exclude Items (comma-separated)              ║
║  ┌──────────────────────────────────────────┐ ║
║  │ e.g., "peanuts, shellfish, gluten"      │ ║
║  └──────────────────────────────────────────┘ ║
║                                               ║
║  [Cancel]                    [Save & Apply]   ║
║                                               ║
╚═══════════════════════════════════════════════╝
```

**Stored in localStorage**:
```javascript
const userPreferences = {
  store: 'FreshDirect',
  servings: 2,
  complexity: 'moderate',
  produce: 'fresh',        // Avoid microplastics!
  prioritizeOrganic: true,
  preferLocal: true,
  showSeasonal: true,
  strictOrganic: false,
  vegetarian: false,
  vegan: false,
  exclude: []              // Allergens/restrictions
};

localStorage.setItem('userPreferences', JSON.stringify(userPreferences));
```

**Why localStorage?**
- No account needed
- Persists across sessions
- Privacy-friendly (local only)
- Fast (no API calls)

**When preferences change**:
```javascript
function applyPreferences() {
  const prefs = JSON.parse(localStorage.getItem('userPreferences'));

  // Update UI immediately
  document.getElementById('store-display').textContent = prefs.store;

  // Next cart creation will use these prefs
  // (sent to API as query params or request body)
}
```

**Key design decision**: Preferences **always accessible**, even when cart is empty.

Why? Because users might want to set preferences before creating their first cart.

Like setting your GPS preferences before starting navigation.

---

### The Download Feature: Practical Export

**Alex clicks [Download list]**

**File downloads immediately** (no dialog):
```csv
Ingredient,Brand,Product,Size,Price,Qty,Store,Location
Basmati Rice,India Gate,Basmati Rice,5 lb,8.99,1,FreshDirect,NJ
Chicken Breast,Bell & Evans,Organic Chicken Breast,1 lb,7.99,2,FreshDirect,NJ
Broccoli,Earthbound Farm,Organic Broccoli Florets,12 oz,3.49,1,FreshDirect,NJ
...
```

**Why CSV?**
- **Universal**: Opens in Excel, Google Sheets, Notes
- **Printable**: Take to store
- **Shareable**: Email to roommate/partner
- **Importable**: Could integrate with store APIs

**Implementation**:
```javascript
function downloadCSV() {
  const rows = [
    ['Ingredient', 'Brand', 'Product', 'Size', 'Price', 'Qty', 'Store', 'Location']
  ];

  cartItems.forEach(item => {
    rows.push([
      item.name,
      item.brand,
      item.catalogueName,
      item.size,
      item.price.toFixed(2),
      item.quantity,
      item.store,
      item.location
    ]);
  });

  const csv = rows.map(row => row.join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = url;
  link.download = `conscious-cart-${Date.now()}.csv`;
  link.click();
}
```

**User experience**: Click → file appears in Downloads folder → done.

No "Save As" dialogs. No confirmation. Just works.

Like screenshotting: press button, get file.

---

### Error States: Honest and Helpful

**Scenario 1: API is down**

```
┌───────────────────────────────────┐
│  YOUR CART                         │
│                                    │
│  ⚠️ Couldn't create cart           │
│                                    │
│  The server isn't responding.      │
│  Make sure the FastAPI backend     │
│  is running on port 8000.          │
│                                    │
│  [Try again]  [Check server]       │
│                                    │
└───────────────────────────────────┘
```

**"Check server" button**:
```javascript
function checkServer() {
  window.open('http://localhost:8000/docs', '_blank');
  // Opens FastAPI docs in new tab
}
```

**Scenario 2: No ingredients found**

```
┌───────────────────────────────────┐
│  YOUR CART                         │
│                                    │
│  ℹ️ No ingredients recognized      │
│                                    │
│  We couldn't match "xyz" to any    │
│  known recipes. Try:               │
│  • "chicken biryani for 4"         │
│  • "stir fry with vegetables"      │
│  • "healthy salad"                 │
│                                    │
│  Or enable AI mode for natural     │
│  language understanding.           │
│                                    │
│  [Try AI mode]  [See examples]     │
│                                    │
└───────────────────────────────────┘
```

**Why this is good UX**:
1. **Clear problem**: Not vague "Error 500"
2. **Actionable solution**: Try these instead
3. **Upgrade path**: Enable AI for flexibility
4. **No shame**: "We couldn't match" (not "You did it wrong")

Like a good GPS: "Road closed ahead. Here are 3 alternate routes."

---

### Mobile Considerations: Desktop-First, But Responsive

**What breaks on mobile**:
1. Two-column layout → Stack vertically
2. Cart cards → Still readable (single column already)
3. Preferences modal → Full-screen overlay
4. Quantity selectors → Larger tap targets

**Current state**: Works okay on tablets, cramped on phones.

**CSS media queries** (already in demo.html):
```css
@media (max-width: 768px) {
  .grid {
    grid-template-columns: 1fr;  /* Stack columns */
  }

  .cart-item {
    font-size: 0.95rem;          /* Slightly smaller */
  }

  button {
    min-height: 44px;            /* iOS tap target minimum */
  }
}
```

**Future improvements**:
- Swipe gestures for quantity
- Pull-to-refresh
- Native app wrapper (Capacitor/React Native)

But for hackathon demos: **desktop is fine**. Judges use laptops.

---

### Performance: Fast by Default

**Load time** (demo.html):
```
HTML file:        12 KB
Tailwind CSS:     ~50 KB (CDN, cached)
JavaScript:       8 KB (inline)
Images:           Lazy-loaded from Unsplash
Total:            ~70 KB

First paint:      ~200ms
Interactive:      ~300ms
```

**API response time**:
```
Template mode:    ~150ms  (deterministic)
AI mode:          ~2-4s   (LLM latency)
```

**Why so fast?**
- No build step (HTML/JS/CSS inline or CDN)
- No framework overhead (vanilla JS)
- Minimal HTTP requests (1 API call)
- LocalStorage (no server round-trips for prefs)

**Comparison**:
```
Streamlit:       ~3-5s     (Python app cold start)
React (prod):    ~500ms    (bundled, optimized)
HTML demo:       ~300ms    (instant)
```

For hackathon demos: **speed matters**. Judges are impatient.

---

### The Accessibility Story: Room for Improvement

**What we got right**:
- ✅ Semantic HTML (`<button>`, `<form>`, `<label>`)
- ✅ Keyboard navigation works
- ✅ Focus indicators visible
- ✅ Color contrast passes WCAG AA

**What we need to improve**:
- ⚠️ No ARIA labels on custom components
- ⚠️ Screen reader testing incomplete
- ⚠️ No skip-to-content link
- ⚠️ Modal doesn't trap focus

**Why this matters**:
- Accessibility is important (obviously)
- But also: **judges might test it**
- And: **hackathon accessibility points**

**Quick wins for next version**:
```html
<button
  aria-label="Create shopping cart from meal plan"
  aria-describedby="meal-plan-input">
  Create my cart
</button>

<div
  role="dialog"
  aria-labelledby="preferences-title"
  aria-modal="true">
  <h2 id="preferences-title">User Preferences</h2>
  ...
</div>
```

Like building a ramp after building stairs. Should've been there from the start, but fixable.

---

### The React Advantage: Why We Built Both

**HTML demo** (demo.html):
- ✅ Zero dependencies
- ✅ Instant load
- ✅ Easy to demo
- ❌ Hard to maintain
- ❌ No state management
- ❌ Vanilla JS gets messy

**React app** (Figma_files/):
- ✅ Component reusability
- ✅ TypeScript safety
- ✅ Better state management (hooks)
- ✅ Testing framework
- ❌ Build step required
- ❌ Larger bundle size

**When to use which**:

| Scenario | Use HTML Demo | Use React App |
|----------|--------------|---------------|
| Hackathon judges | ✅ | ❌ |
| Local development | ❌ | ✅ |
| Production deployment | ❌ | ✅ |
| Quick iteration | ✅ | ❌ |
| Long-term maintenance | ❌ | ✅ |
| Team collaboration | ❌ | ✅ |

**The strategy**: Build both. HTML for demos, React for production.

Like having both a sports car (React) and a bicycle (HTML). Different tools for different needs.

---

## The Bottom Line: UI That Gets Out of the Way

**Good UI is invisible.**

Users shouldn't think about:
- How the agents work
- Whether LLM is enabled
- How scoring happens

Users should think about:
- "Do I want organic chicken?"
- "Is $67 too much for dinner?"
- "Can I get this cheaper?"

**The UI's job**: Present information clearly, enable quick decisions, stay out of the way.

Like a good waiter: helpful when needed, invisible when not.

---

## Further Reading

- [Technical Architecture](5-technical-architecture.md) - How it's built
- [LLM Integration](6-llm-integration-deep-dive.md) - How AI fits in
- [Data Flows](8-data-flows.md) - How data moves through the system

---

*"The best interface is no interface. But since we need one, make it obvious."*

*"Users don't care about your architecture. They care about their groceries."*
