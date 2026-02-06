# UI Flows: The User Journey from "I'm Hungry" to "Cart Ready"

## The Core Philosophy: Conversational Shopping

Traditional grocery sites make you browse aisles and search for products. We flipped that:

**Old way**: "I need... let me search... chicken breast... filter by organic... add to cart... now search for rice..."

**Our way**: "I want to make chicken biryani for 4" → [cart appears with everything]

The UI reflects this philosophy: input is simple and conversational, output is detailed and actionable.

## The Main Interface: Split-Screen Design

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Conscious Cart Coach                                                   │
├──────────────────────────────────┬──────────────────────────────────────┤
│                                  │                                      │
│   LEFT PANEL                     │   RIGHT PANEL                        │
│   Meal Plan Input                │   Shopping Cart                      │
│                                  │                                      │
│   ┌────────────────────────────┐ │   ┌────────────────────────────────┐│
│   │ What are you cooking?      │ │   │ Your Cart                      ││
│   │                            │ │   │                                ││
│   │ [Text input area]          │ │   │ ┌────────────────────────────┐││
│   │                            │ │   │ │ FreshDirect                │││
│   │ e.g., "chicken biryani     │ │   │ │                            │││
│   │ for 4 people"              │ │   │ │ ├─ Chicken Breast, 365    │││
│   │                            │ │   │ │ │  $7.99 | 1.5 lbs        │││
│   │                            │ │   │ │ │  ✓ Organic              │││
│   │                            │ │   │ │ │  ⓘ Higher price         │││
│   │ [Create Cart button]       │ │   │ │ │                         │││
│   │                            │ │   │ │ ├─ Basmati Rice          │││
│   └────────────────────────────┘ │   │ │   $5.99 | 2 lbs          │││
│                                  │ │   │ │                          │││
│                                  │ │   │ └────────────────────────────┘││
│                                  │ │   │                                ││
│                                  │ │   │ ┌────────────────────────────┐││
│                                  │ │   │ │ Pure Indian Foods          │││
│                                  │ │   │ │                            │││
│                                  │ │   │ │ ├─ Cumin Seeds, 3oz       │││
│                                  │ │   │ │   $6.69                    │││
│                                  │ │   │ │   ✓ Organic                │││
│                                  │ │   │ │   ✓ Authentic Indian       │││
│                                  │ │   │ │                            │││
│                                  │ │   │ │ ├─ Cardamom, 2oz          │││
│                                  │ │   │ │   $12.99                   │││
│                                  │ │   │ │   ✓ Premium quality        │││
│                                  │ │   │ └────────────────────────────┘││
│                                  │ │   └────────────────────────────────┘│
│                                  │ │                                      │
│                                  │ │   Total: $XX.XX                     │
│                                  │ │   [Checkout] [Edit Cart]            │
│                                  │ │                                      │
└──────────────────────────────────┴──────────────────────────────────────┘
```

### Why Split-Screen?
1. **Input stays visible**: User can see what they typed while reviewing cart
2. **Cart builds in real-time**: Future version will show items appearing as agents work
3. **No page transitions**: Everything happens on one screen

## User Flow 1: Simple Meal Plan → Cart

### Step 1: User Enters Meal Plan
```
User types: "chicken biryani for 4"
Clicks: "Create Cart"
```

**What happens**:
- Input is sent to `POST /create-cart`
- Loading spinner appears (frontend shows "Building your cart...")
- Cart panel shows skeleton loading state

### Step 2: Backend Processes
```
Orchestrator:
  1. Ingredient Agent extracts ingredients
  2. Product Agent matches products
  3. Quantity Agent calculates amounts
  4. Explain Agent generates tags
```

**What user sees**:
- Loading animation (currently static, future: live progress)
- "Finding ingredients... ✓"
- "Matching products... ✓"
- "Optimizing quantities... ✓"

### Step 3: Cart Appears
```
┌─────────────────────────────────────────┐
│ FreshDirect (4 items) - $42.96          │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ [Image] 365 Organic Chicken Breast  │ │
│ │         $7.99 | 1.5 lbs | Qty: 1    │ │
│ │                                     │ │
│ │ Why this pick?                      │ │
│ │ ✓ USDA Organic certified            │ │
│ │ ✓ Good price per pound              │ │
│ │                                     │ │
│ │ Trade-offs:                         │ │
│ │ ⓘ Higher price than conventional    │ │
│ │                                     │ │
│ │ [Find Cheaper Swap] [Remove]        │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ... (more items)                        │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Pure Indian Foods (3 items) - $25.67    │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ [Image] Cumin Seeds (Jeera), 3oz    │ │
│ │         $6.69 | Qty: 1              │ │
│ │                                     │ │
│ │ Why this pick?                      │ │
│ │ ✓ Authentic Indian specialty        │ │
│ │ ✓ USDA Organic                      │ │
│ │ ✓ Whole seeds (better flavor)       │ │
│ │                                     │ │
│ │ [Find Cheaper Swap] [Remove]        │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ... (more spices)                       │
└─────────────────────────────────────────┘
```

**Key UX Decisions**:
- **Multi-store grouping**: Items grouped by store with subtotals
- **Why this pick?**: Transparent reasoning for each choice
- **Trade-offs visible**: User sees what they're compromising (if anything)
- **Size always shown**: Avoids confusion ("Why is cardamom $12.99?")

## User Flow 2: Ingredient Confirmation Modal

### Trigger: Ambiguous Meal Plan
```
User types: "I want to make curry"
```

**Problem**: "Curry" is ambiguous (Thai? Indian? Japanese? British?)

### Modal Appears
```
┌──────────────────────────────────────────────────────┐
│  Confirm Ingredients                          [×]    │
├──────────────────────────────────────────────────────┤
│                                                      │
│  We extracted these ingredients:                    │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │ ☑ Chicken (1.5 lbs)                         │   │
│  │ ☑ Curry powder (2 tbsp)                     │   │
│  │ ☑ Onions (2 medium)                         │   │
│  │ ☑ Coconut milk (1 can)                      │   │
│  │ ☑ Garlic (4 cloves)                         │   │
│  │ ☑ Ginger (1 inch)                           │   │
│  │ ☐ Potatoes (2 medium)          [Optional]   │   │
│  │ ☐ Carrots (2 medium)           [Optional]   │   │
│  │                                              │   │
│  │ [+ Add ingredient]                           │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
│  Note: This looks like a British-style curry.       │
│  Want Thai curry instead?                           │
│  [Switch to Thai] [Keep British]                    │
│                                                      │
│  [Cancel] [Confirm & Build Cart]                    │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**What This Enables**:
- User can **review and modify** ingredients before cart creation
- User can **add forgotten items** ("Oh, I need rice too!")
- User can **remove unwanted items** ("No potatoes, thanks")
- User gets **clarity** on interpretation ("British curry, not Thai")

**With LLM Enhancement**:
- LLM detects ambiguity and triggers modal
- LLM suggests variations ("Thai curry" vs "British curry")
- LLM explains differences ("Thai uses lemongrass and fish sauce")

## User Flow 3: Unavailable Product Handling

### Trigger: Product Not in Stock
```
Orchestrator finds: "365 Organic Chicken Breast - Out of Stock"
```

### In-Cart Indicator
```
┌─────────────────────────────────────────┐
│ [⚠] 365 Organic Chicken Breast          │
│      UNAVAILABLE                        │
│                                         │
│ This item is currently unavailable.     │
│ [Try another store]                     │
│                                         │
│ Alternatives:                           │
│ ├─ Bell & Evans Chicken ($6.99/lb)     │
│ ├─ Whole Foods 365 ($7.49/lb)          │
│ └─ Katie's Best ($7.99/lb)             │
│                                         │
│ [Auto-select alternative] [Remove item] │
└─────────────────────────────────────────┘
```

**User Options**:
1. **Try another store**: Re-run cart creation with different target_store
2. **Select alternative**: Pick from suggested products
3. **Auto-select**: Let system choose best alternative
4. **Remove item**: Delete from cart

## User Flow 4: Quantity Adjustment

### Trigger: User Wants More/Less
```
User clicks [-] or [+] buttons on quantity spinner
```

### Real-Time Update
```
Before:
┌────────────────────────────────┐
│ Cumin Seeds, 3oz               │
│ $6.69                          │
│                                │
│ [−] 1 [+]                      │
│                                │
│ Size: 3oz                      │
└────────────────────────────────┘

After clicking [+]:
┌────────────────────────────────┐
│ Cumin Seeds, 3oz               │
│ $6.69                          │
│                                │
│ [−] 2 [+]                      │
│                                │
│ Size: 3oz                      │
│ Total: 6oz for $13.38          │
└────────────────────────────────┘
```

**What Updates**:
- Quantity number
- Line item total
- Store subtotal
- Cart grand total

**Future Enhancement**:
```
System notices: User bought 2× cumin (6oz total)

Suggestion appears:
┌────────────────────────────────────────┐
│ 💡 Tip: You selected 2× 3oz jars.      │
│                                        │
│ Consider the 8oz bulk size instead:    │
│ Cumin Seeds, 8oz - $14.99              │
│ (Saves $0.39 and less packaging)       │
│                                        │
│ [Switch to bulk] [Keep 2× small]       │
└────────────────────────────────────────┘
```

## User Flow 5: "Find Cheaper Swap" Feature

### Trigger: User Wants to Save Money
```
User clicks: "Find Cheaper Swap" on an item
```

### Modal Shows Alternatives
```
┌──────────────────────────────────────────────────────┐
│  Find Cheaper Alternative                     [×]    │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Current: 365 Organic Chicken Breast                │
│  Price: $7.99/lb                                    │
│  Tags: ✓ USDA Organic | ✓ No antibiotics           │
│                                                      │
│  ─────────────────────────────────────────────      │
│                                                      │
│  Cheaper Options:                                   │
│                                                      │
│  ⬤ Bell & Evans Chicken Breast                     │
│     $6.99/lb (-13% cheaper)                         │
│     ✓ No antibiotics | ✓ Air-chilled                │
│     ⚠ Not organic                                   │
│     [Select this]                                    │
│                                                      │
│  ○ Katie's Best Chicken Breast                     │
│     $7.99/lb (same price)                           │
│     ✓ No antibiotics | ✓ Air-chilled                │
│     ⚠ Not organic                                   │
│     [Select this]                                    │
│                                                      │
│  ○ Springer Mountain Farms Chicken                 │
│     $6.49/lb (-19% cheaper)                         │
│     ✓ No antibiotics                                │
│     ⚠ Not organic | ⚠ Not air-chilled              │
│     [Select this]                                    │
│                                                      │
│  [Cancel] [Keep original]                            │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**UX Details**:
- **Price comparison**: Shows percentage savings
- **Feature comparison**: What you gain/lose with swap
- **Visual indicators**: ✓ for good, ⚠ for trade-offs
- **Radio buttons**: Clear selection model

## Mobile Responsiveness: Shopping on the Go

### Desktop (1440px+)
```
┌────────────────┬──────────────────┐
│                │                  │
│  Input Panel   │   Cart Panel     │
│  (40% width)   │   (60% width)    │
│                │                  │
└────────────────┴──────────────────┘
```

### Tablet (768px - 1439px)
```
┌────────────────┬──────────────────┐
│                │                  │
│  Input Panel   │   Cart Panel     │
│  (35% width)   │   (65% width)    │
│                │                  │
└────────────────┴──────────────────┘
```

### Mobile (< 768px)
```
┌──────────────────┐
│                  │
│  Input Panel     │
│  (full width)    │
│                  │
│  [Create Cart]   │
│                  │
└──────────────────┘
       ⬇ (scrolls down after cart created)
┌──────────────────┐
│                  │
│  Cart Panel      │
│  (full width)    │
│                  │
└──────────────────┘
```

**Mobile-Specific Optimizations**:
- **Touch targets**: Minimum 44×44px for buttons
- **Simplified cards**: Less visual detail on small screens
- **Accordion stores**: Collapse store sections to save space
- **Bottom sheet modals**: Instead of center modals

## The Floating Cart Coach Button (Future Feature)

### Concept: AI Assistant That Pops Up
```
┌─────────────────────────────────────┐
│                                     │
│  [Shopping Cart]                    │
│                                     │
│                                     │
│                         ┌─────┐     │
│                         │ 🛒  │ ← Floating button
│                         └─────┘     │
│                                     │
└─────────────────────────────────────┘

When clicked:
┌─────────────────────────────────────┐
│                                     │
│  ┌───────────────────────────────┐ │
│  │ Cart Coach 💬                 │ │
│  │                               │ │
│  │ Need help?                    │ │
│  │ • Find substitutions          │ │
│  │ • Optimize for budget         │ │
│  │ • Suggest meal plans          │ │
│  │                               │ │
│  │ [Chat with me]                │ │
│  └───────────────────────────────┘ │
│                                     │
└─────────────────────────────────────┘
```

**With LLM Integration**:
```
User: "Can I substitute quinoa for rice?"

Cart Coach:
"Yes! Quinoa works great in biryani. I found:
- Organic Quinoa, 12oz - $5.99

Want me to swap it in?"

[Yes, swap] [No thanks]
```

## Loading States: Building Trust During Processing

### Current (Simple Spinner)
```
┌────────────────────────────┐
│                            │
│     ⌛ Building cart...    │
│                            │
└────────────────────────────┘
```

### Future (Progressive Loading)
```
┌─────────────────────────────────────┐
│  Building your cart...              │
│                                     │
│  ✅ Extracted 12 ingredients        │
│  🔄 Finding products... (8/12)      │
│  ⏳ Calculating quantities...       │
│  ⏳ Splitting across stores...      │
│                                     │
│  [Cancel]                           │
└─────────────────────────────────────┘
```

**Why Progressive Loading**:
- **Transparency**: User sees what's happening
- **Trust**: System isn't frozen, it's working
- **Patience**: People wait longer when they see progress
- **Cancellation**: Can stop if it's taking too long

## Error States: When Things Go Wrong

### Product Not Found
```
┌─────────────────────────────────────┐
│ ⚠️ Couldn't find: "saffron threads" │
│                                     │
│ Try:                                │
│ • More common alternative?          │
│ • Different store?                  │
│ • Remove from cart?                 │
│                                     │
│ [Suggest alternative] [Remove]      │
└─────────────────────────────────────┘
```

### Backend Timeout
```
┌─────────────────────────────────────┐
│ 😕 Taking longer than expected      │
│                                     │
│ This is unusual. Your cart might be │
│ especially complex or our system is │
│ slow right now.                     │
│                                     │
│ [Keep waiting] [Try simpler meal]   │
└─────────────────────────────────────┘
```

### Complete Failure
```
┌─────────────────────────────────────┐
│ ❌ Something went wrong             │
│                                     │
│ We couldn't create your cart.       │
│ Please try again or contact support.│
│                                     │
│ Error ID: abc123 (for support)      │
│                                     │
│ [Try again] [Contact support]       │
└─────────────────────────────────────┘
```

## Future: Real-Time Streaming Cart Creation

### Vision: Cart Appears Item-by-Item
```
Second 1:
┌─────────────────────────────────────┐
│ FreshDirect                         │
│ ├─ 365 Chicken Breast ✓            │
│ └─ ... (loading)                    │
└─────────────────────────────────────┘

Second 2:
┌─────────────────────────────────────┐
│ FreshDirect                         │
│ ├─ 365 Chicken Breast ✓            │
│ ├─ Basmati Rice ✓                  │
│ ├─ Yellow Onions ✓                 │
│ └─ ... (loading)                    │
└─────────────────────────────────────┘

Second 5:
┌─────────────────────────────────────┐
│ FreshDirect (complete) ✓            │
│ Pure Indian Foods                   │
│ ├─ Cumin Seeds ✓                   │
│ └─ ... (loading)                    │
└─────────────────────────────────────┘
```

**Technical Implementation**: WebSocket or Server-Sent Events

```typescript
// Frontend
const eventSource = new EventSource('/api/cart/stream');

eventSource.onmessage = (event) => {
  const item = JSON.parse(event.data);
  addItemToCart(item); // Real-time update
};
```

**Why This Matters**:
- **Engagement**: User watches cart build (like watching a loading bar)
- **Speed perception**: Feels faster than waiting for complete cart
- **Debugging**: Can see which item is slow to load

---

**Next**: [Data Flows & Product Selection Logic](./04-data-flows.md) - How products get from CSV to cart

