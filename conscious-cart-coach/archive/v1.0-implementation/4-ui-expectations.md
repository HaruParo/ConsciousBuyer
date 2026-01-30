# UI Experience with LLM Features

**What changes in the UI when LLM is enabled**

## Overview

The core UI stays the same - same layout, same 3-column cart display. **LLM adds two enhancements**:

1. **Better ingredient extraction** from natural language
2. **Richer explanations** for product recommendations

---

## 1. Ingredient Input & Extraction

### Without LLM (Deterministic)

**User Types:**
```
chicken biryani for 4
```

**What Happens:**
- ✅ Matches template: "biryani"
- ✅ Extracts 12 ingredients (rice, onions, tomatoes, etc.)
- ✅ Fast (<100ms)
- ❌ Only works with known recipes

**Ingredient Modal Shows:**
```
✓ 12 ingredients found
Using biryani recipe template
Scaled from 4 to 4 servings
```

---

### With LLM (`use_llm_extraction=True`)

**User Types:**
```
I want something healthy and seasonal for dinner tonight
```

**What Happens:**
- ✅ Claude parses natural language
- ✅ Suggests ingredients based on context
- ✅ Handles vague/creative requests
- ⏱️ +1-3 second delay

**Ingredient Modal Shows:**
```
✓ 8 ingredients found
LLM extracted from natural language
Servings: 4

Ingredients:
- Mixed greens
- Tomatoes (cherry)
- Cucumber
- Avocado
- Olive oil
- Lemon
- Feta cheese
- Grilled chicken (optional)
```

**Visual Indicator:**
```
[Badge] "AI-Powered" or "🤖 Claude"
```

---

## 2. Product Recommendations & Explanations

### Without LLM (Deterministic Only)

**Product Card Shows:**

```
┌─────────────────────────────────────┐
│ Spinach                             │
│ ⚖️ BALANCED                         │
├─────────────────────────────────────┤
│ Earthbound Farm Organic Baby Spinach│
│ $3.99 (5oz)                         │
│                                     │
│ Score: 68/100                       │
│ Reason: Organic recommended (EWG)   │  ← Short, rule-based
│                                     │
│ Attributes: [Organic] [In Season]  │
│ Safety: EWG recommends organic      │
└─────────────────────────────────────┘

Cheaper option: Store Brand at $1.99
Conscious option: Local Farm at $4.99
```

**Explanation is terse:**
- "Organic recommended (EWG)"
- "Best value per oz"
- "Peak season local"
- "Preferred brand"

---

### With LLM (`use_llm_explanations=True`)

**Product Card Shows:**

```
┌─────────────────────────────────────────────────────────────┐
│ Spinach                                                     │
│ ⚖️ BALANCED                                                 │
├─────────────────────────────────────────────────────────────┤
│ Earthbound Farm Organic Baby Spinach                        │
│ $3.99 (5oz) • $0.80/oz                                      │
│                                                             │
│ Score: 68/100                                               │
│ Quick: Organic recommended (EWG)                            │  ← Deterministic
│                                                             │
│ [Toggle: Show Details ▼]                                   │  ← NEW!
│                                                             │
│ Detailed Explanation:                                       │  ← NEW! From Claude
│ "The Earthbound Farm option at $3.99 offers organic        │
│  certification which is important for spinach since it's   │
│  on the EWG Dirty Dozen list for high pesticide residue.  │
│  While it costs $2 more than the conventional option,      │
│  you're avoiding 3-5 common pesticide residues. The        │
│  unit price of $0.80/oz is competitive for organic         │
│  greens."                                                   │
│                                                             │
│ Attributes: [Organic] [In Season]                          │
│ Safety: EWG recommends organic                              │
└─────────────────────────────────────────────────────────────┘

Cheaper option: Store Brand (conventional) at $1.99
Conscious option: Local Farm (certified organic) at $4.99
```

**Explanation is rich:**
- References specific prices
- Explains the tradeoff
- Mentions health benefits
- Contextualizes the decision
- Natural language

---

## 3. Side-by-Side Comparison

### Deterministic vs LLM-Enhanced

| Feature | Without LLM | With LLM |
|---------|-------------|----------|
| **Prompt Support** | "chicken biryani for 4" | "I want something healthy" |
| | "salad", "stir fry" | "quick dinner for 2" |
| | (4 hardcoded recipes) | (any natural language) |
| **Explanation Style** | "Best value per oz" | "This product offers..." |
| | "Organic recommended" | (1-2 full sentences) |
| | (3-5 words) | (contextual, detailed) |
| **Visual Indicators** | None needed | [Badge] "AI-Powered" |
| **Response Time** | Instant (<100ms) | +2-4 seconds |
| **Cost** | Free | ~$0.045 per cart |

---

## 4. Complete User Flow Examples

### Example A: Deterministic Mode (Default)

**Step 1: User Input**
```
┌─────────────────────────────────────┐
│ What are you making?                │
│ ┌─────────────────────────────────┐ │
│ │ chicken biryani for 4           │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [Create cart]                       │
└─────────────────────────────────────┘
```

**Step 2: Ingredient Confirmation (Modal)**
```
╔═══════════════════════════════════════╗
║ Confirm ingredients                   ║
╠═══════════════════════════════════════╣
║ Edit this list before we build cart   ║
║                                       ║
║ Store: ShopRite                       ║
║ ✓ 12 available · 0 unavailable        ║
║                                       ║
║ [✓] Basmati rice                      ║
║ [✓] Onions                            ║
║ [✓] Tomatoes                          ║
║ [✓] Yogurt                            ║
║ ... (8 more)                          ║
║                                       ║
║ [Cancel] [Confirm 12 ingredients]     ║
╚═══════════════════════════════════════╝
```

**Step 3: Cart Display**
```
┌─────────────────────────────────────┐
│ Your Cart                           │
│ 12 items · ShopRite                 │
│                                     │
│ Cart mode: [Pick] Cheaper Ethical   │
│ Cart total: $67.80                  │
├─────────────────────────────────────┤
│ Basmati Rice                        │
│ ⚖️ BALANCED                         │
│ India Gate Basmati • $8.99          │
│ Reason: Good value                  │ ← Short
│ [Organic] [Peak Season]             │
├─────────────────────────────────────┤
│ Onions                              │
│ 💸 CHEAPER                          │
│ Store Brand Yellow Onions • $1.49   │
│ Reason: Best value per oz           │ ← Short
├─────────────────────────────────────┤
│ ... (10 more items)                 │
└─────────────────────────────────────┘
```

---

### Example B: Full LLM Mode

**Step 1: User Input (More Natural)**
```
┌─────────────────────────────────────┐
│ What are you making?                │
│ ┌─────────────────────────────────┐ │
│ │ I want something healthy and    │ │
│ │ seasonal for dinner, maybe a    │ │
│ │ salad or light meal             │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [Create cart] 🤖 AI-Powered         │ ← Indicator
└─────────────────────────────────────┘

[Loading spinner] Analyzing your request...
```

**Step 2: Ingredient Confirmation (Modal)**
```
╔═══════════════════════════════════════╗
║ Confirm ingredients                   ║
╠═══════════════════════════════════════╣
║ 🤖 AI extracted from your request     ║ ← NEW!
║                                       ║
║ Store: ShopRite                       ║
║ ✓ 8 available · 1 unavailable         ║
║                                       ║
║ [✓] Mixed greens      Available       ║
║ [✓] Cherry tomatoes   Available       ║
║ [✓] Cucumber          Available       ║
║ [✓] Avocado           Available       ║
║ [✓] Feta cheese       Unavailable     ║
║ [✓] Olive oil         Available       ║
║ [✓] Lemon             Available       ║
║ [✓] Grilled chicken   Available       ║
║                                       ║
║ [Cancel] [Confirm 8 ingredients]      ║
╚═══════════════════════════════════════╝
```

**Step 3: Cart Display with Rich Explanations**
```
┌──────────────────────────────────────────────────┐
│ Your Cart                                        │
│ 8 items · ShopRite                               │
│                                                  │
│ Cart mode: [Pick] Cheaper Ethical                │
│ Cart total: $34.50                               │
├──────────────────────────────────────────────────┤
│ Mixed Greens                                     │
│ ⚖️ BALANCED                                      │
│ Organic Girl Spring Mix • $4.99 (5oz)            │
│                                                  │
│ Score: 72/100                                    │
│ Quick: Organic option                            │ ← Short
│                                                  │
│ [Show Details ▼]                                 │ ← Expandable
│                                                  │
│ "The Organic Girl Spring Mix at $4.99 provides  │ ← NEW! Rich
│  a good balance of quality and value. While      │
│  you can save $1 with the conventional option,   │
│  this organic choice avoids pesticide residues   │
│  and the pre-washed convenience is worth the     │
│  slight premium for busy weeknights."            │
│                                                  │
│ [Organic] [Local] [In Season]                    │
├──────────────────────────────────────────────────┤
│ Cherry Tomatoes                                  │
│ 🌍 CONSCIOUS                                     │
│ Local Farm Cherry Tomatoes • $5.99 (pint)        │
│                                                  │
│ Score: 85/100                                    │
│ Quick: Peak season local                         │ ← Short
│                                                  │
│ [Show Details ▼]                                 │
│                                                  │
│ "Local Farm's cherry tomatoes at $5.99 are at    │ ← NEW! Rich
│  peak season right now in New Jersey, meaning    │
│  they're fresher and more flavorful than         │
│  imported options. The $2 premium over store     │
│  brand supports local agriculture and reduces    │
│  transportation emissions."                      │
│                                                  │
│ [Organic] [Local] [In Season]                    │
├──────────────────────────────────────────────────┤
│ ... (6 more items)                               │
└──────────────────────────────────────────────────┘
```

---

## 5. Recommended UI Components to Add

### Option 1: Toggle in Settings (Recommended)

```
┌─────────────────────────────────────┐
│ ⚙️ Preferences                      │
├─────────────────────────────────────┤
│ Location: NJ / Mid-Atlantic         │
│ Household size: 2                   │
│ Store: ShopRite                     │
│                                     │
│ ┌─ AI Features ─────────────────┐  │
│ │ [✓] Enable AI ingredient       │  │ ← NEW!
│ │     extraction                 │  │
│ │     Parse natural language     │  │
│ │                                │  │
│ │ [✓] Enable detailed            │  │ ← NEW!
│ │     explanations               │  │
│ │     AI-powered reasoning       │  │
│ │                                │  │
│ │ Note: Uses Claude API          │  │
│ │ Cost: ~$0.045 per cart         │  │
│ └────────────────────────────────┘  │
└─────────────────────────────────────┘
```

### Option 2: Explanation Display Toggle

```
┌─────────────────────────────────────┐
│ Spinach                             │
│ ⚖️ BALANCED                         │
├─────────────────────────────────────┤
│ Earthbound Farm • $3.99             │
│ Score: 68/100                       │
│                                     │
│ Reason: Organic recommended (EWG)   │
│                                     │
│ [▼ Show AI Explanation]             │ ← Click to expand
│                                     │
│ Attributes: [Organic] [In Season]   │
└─────────────────────────────────────┘

↓ Expands to:

┌─────────────────────────────────────┐
│ Spinach                             │
│ ⚖️ BALANCED                         │
├─────────────────────────────────────┤
│ Earthbound Farm • $3.99             │
│ Score: 68/100                       │
│                                     │
│ Reason: Organic recommended (EWG)   │
│                                     │
│ [▲ Hide AI Explanation]             │ ← Click to collapse
│                                     │
│ 🤖 AI Insight:                      │
│ "The Earthbound Farm option at      │
│  $3.99 offers organic certification │
│  which is important for spinach..." │
│                                     │
│ Attributes: [Organic] [In Season]   │
└─────────────────────────────────────┘
```

### Option 3: Loading States

**During LLM Processing:**
```
┌─────────────────────────────────────┐
│ [Spinner] Analyzing your request... │
│ Using AI to understand ingredients  │
└─────────────────────────────────────┘

↓ Then:

┌─────────────────────────────────────┐
│ [Spinner] Finding products...       │
│ Matching 8 ingredients              │
└─────────────────────────────────────┘

↓ Then:

┌─────────────────────────────────────┐
│ [Spinner] Generating explanations...│
│ Creating detailed recommendations   │
└─────────────────────────────────────┘
```

---

## 6. Error States & Fallbacks

### When LLM Fails (API Error, No Key, etc.)

**User Should See:**
```
┌─────────────────────────────────────┐
│ ⚠️ AI features temporarily          │
│    unavailable                      │
│                                     │
│ Using standard ingredient matching  │
│ Your cart will still be generated!  │
└─────────────────────────────────────┘
```

**Or inline:**
```
┌─────────────────────────────────────┐
│ Spinach                             │
│ ⚖️ BALANCED                         │
├─────────────────────────────────────┤
│ Earthbound Farm • $3.99             │
│ Score: 68/100                       │
│                                     │
│ Reason: Organic recommended (EWG)   │
│                                     │
│ [AI explanation unavailable]        │ ← Graceful
│                                     │
│ Attributes: [Organic] [In Season]   │
└─────────────────────────────────────┘
```

---

## 7. Implementation Checklist for UI

To show LLM features, you need to:

### Backend (Already Done ✅)
- ✅ LLM module created
- ✅ `reason_llm` field in DecisionItem
- ✅ Orchestrator supports LLM flags

### Frontend (To Do)

**Step 1: Add LLM Toggle to UI**
```python
# In app.py
with st.popover("⚙️ Preferences"):
    # ... existing code ...

    st.markdown("**AI Features**")
    use_llm_extraction = st.checkbox(
        "Enable AI ingredient extraction",
        help="Parse natural language prompts using Claude AI (~$0.01 per request)"
    )
    use_llm_explanations = st.checkbox(
        "Enable detailed explanations",
        help="Get AI-powered product explanations (~$0.03 per cart)"
    )
```

**Step 2: Pass Flags to Orchestrator**
```python
# When creating orchestrator
orch = Orchestrator(
    use_llm_extraction=use_llm_extraction,
    use_llm_explanations=use_llm_explanations,
)
```

**Step 3: Display LLM Explanations**
```python
# In product card rendering
if item.reason_llm:
    with st.expander("🤖 Show AI Explanation"):
        st.markdown(item.reason_llm)
else:
    st.caption(item.reason_short)
```

**Step 4: Add Loading States**
```python
if use_llm_extraction or use_llm_explanations:
    with st.spinner("Using AI to analyze your request..."):
        bundle = orch.process_prompt(user_prompt)
else:
    bundle = orch.process_prompt(user_prompt)
```

**Step 5: Add Visual Indicators**
```python
# In ingredient modal
if extraction_method == "llm":
    st.info("🤖 AI extracted from natural language")
else:
    st.info("Using recipe template")
```

---

## 8. Summary: What Users Will Notice

| Without LLM | With LLM |
|-------------|----------|
| "biryani for 4" | "I want something healthy" ✨ |
| "Best value" | "The Earthbound Farm option at $3.99..." ✨ |
| Instant response | +2-4 second delay |
| Free | ~$0.045 per cart |
| 4 hardcoded recipes | Unlimited natural language |
| Terse explanations | Rich, contextual explanations ✨ |

**Key Takeaway**: The UI layout stays the same, but **input flexibility** and **explanation richness** dramatically improve with LLM enabled.

---

Last updated: 2026-01-24
