# Conscious Cart Coach - React Demo

Multi-store cart planning with ingredient confirmation flow.

## ✨ Features Implemented

### 1. **Ingredient Confirmation Flow**
- User enters a meal prompt (e.g., "chicken biryani for 4")
- System extracts ingredients
- **NEW:** Ingredient confirmation modal appears BEFORE cart creation
- User can add, remove, or edit ingredients
- Cart is only created after confirmation

### 2. **Multi-Store Cart Display**
- **Clear multi-store awareness** in cart header
  - Shows "Multi-store cart: 2 stores selected" or "1 store selected"
  - Displays store breakdown: "FreshDirect (12) • Indian Grocer (6)"
- **Store tabs** to filter items:
  - "All items" tab
  - Individual store tabs (FreshDirect, Indian Grocer)
- **Per-item store indicators**:
  - Store chip/badge on each item (orange for primary, purple for specialty)
  - "Unavailable" chip for out-of-stock items
  - Unavailable items remain visible with "Try another store" link

### 3. **Agent Checkout Experience**
- "Agent checkout" button in cart view
- **Progress UI** showing cart creation:
  - "Creating carts..."
  - "✅ FreshDirect cart ready"
  - "✅ Indian Grocer cart ready"
- **Checkout options**:
  - "Checkout all (opens tabs)" - opens all store carts
  - Individual store checkout buttons
- **Disclaimer**: "Opens store carts in new tabs. Payment happens on store sites."
- Mock store URLs open in new tabs

### 4. **Design System**
All components use the existing design system:
- **Colors**:
  - Primary store (FreshDirect): Orange (#d4976c)
  - Specialty store: Purple (#8b7ba8)
  - Unavailable: Beige (#a89968)
- **Components**: Button, Chip, Modal, Tabs, Cards

## 🗂️ File Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Button.tsx                    # Reusable button component
│   │   ├── Chip.tsx                      # Store/status indicator chips
│   │   ├── Modal.tsx                     # Base modal component
│   │   ├── IngredientConfirmModal.tsx    # Ingredient editing modal
│   │   ├── CartView.tsx                  # Multi-store cart with tabs
│   │   └── AgentCheckoutModal.tsx        # Checkout launcher
│   ├── App.tsx                           # Main app with state machine
│   ├── main.tsx                          # React entry point
│   ├── types.ts                          # TypeScript types
│   ├── design-system.ts                  # Design tokens
│   └── mockData.ts                       # Mock ingredient extraction
├── package.json
├── vite.config.ts
├── tsconfig.json
└── index.html
```

## 🚀 Running the App

### Development Mode
```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:5173

### Production Build
```bash
npm run build
npm run preview
```

## 🧪 Test Scenarios

### 1. **Biryani (Multi-Store)**
- Prompt: "chicken biryani for 4"
- Expected: 2 stores
  - FreshDirect: chicken, onions, tomatoes, yogurt, cilantro
  - Indian Grocer: biryani masala, saffron, ghee, garam masala, basmati rice

### 2. **Salad (Single Store)**
- Prompt: "fresh salad for 2"
- Expected: 1 store (FreshDirect)
  - All fresh ingredients

### 3. **Seasonal Veggies (Single Store)**
- Prompt: "seasonal vegetables"
- Expected: 1 store (FreshDirect)
  - All produce items

## 🎯 User Flow

```
┌─────────────────────────────────────────────────────┐
│ 1. PROMPT                                           │
│    User: "chicken biryani for 4"                   │
│    [Create my cart] ────────────────────────┐      │
└─────────────────────────────────────────────┼──────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────┐
│ 2. CONFIRM INGREDIENTS (Modal)                      │
│    ✓ basmati rice          [edit] [×]              │
│    ✓ chicken               [edit] [×]              │
│    ✓ biryani masala        [edit] [×]              │
│    ...                                              │
│    [+ Add ingredient]                               │
│    [Cancel] [Confirm ingredients] ─────────┐       │
└─────────────────────────────────────────────┼───────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────┐
│ 3. CART VIEW                                        │
│    Multi-store cart: 2 stores selected              │
│    FreshDirect (5) • Indian Grocer (4)             │
│    [Agent Checkout]                                 │
│                                                      │
│    Tabs: [All] [FreshDirect] [Indian Grocer]       │
│                                                      │
│    Items:                                           │
│    ┌─────────────────────────────────────┐         │
│    │ Chicken Breast                      │         │
│    │ FreshDirect Brand • 2 lbs           │         │
│    │ [FreshDirect] [Fresh] [In Season]   │         │
│    └─────────────────────────────────────┘         │
│    ┌─────────────────────────────────────┐         │
│    │ Biryani Masala                      │         │
│    │ Authentic Indian • 3 tbsp           │         │
│    │ [Indian Grocer] [Specialty]         │         │
│    └─────────────────────────────────────┘         │
│                                                      │
│    [Agent Checkout] ────────────────────────┐      │
└─────────────────────────────────────────────┼──────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────┐
│ 4. AGENT CHECKOUT (Modal)                           │
│    Creating carts...                                │
│    ✅ FreshDirect cart ready                        │
│    ✅ Indian Grocer cart ready                      │
│                                                      │
│    [Checkout FreshDirect]                           │
│    [Checkout Indian Grocer]                         │
│                                                      │
│    Opens store carts in new tabs.                   │
│    Payment happens on store sites.                  │
│                                                      │
│    [Close] [Checkout all (opens tabs)]              │
└─────────────────────────────────────────────────────┘
```

## 🎨 Design Highlights

- **No availability/recall indicators** in ingredient confirmation modal
- **Availability shown in cart view** with "Unavailable" chips
- **Multi-store awareness** is obvious in cart header
- **Store chips** on every item make store assignment clear
- **Tabs** allow filtering by store
- **Agent checkout** simulates creating carts with progress UI

## 🔧 Technical Details

- **State Machine**: `idle → confirmingIngredients → cartReady → agentCheckout`
- **Mock Data**: Hardcoded extraction for biryani, salad, seasonal veggies
- **Store Rules**:
  - Specialty items (2+): biryani masala, saffron, ghee, garam masala → Indian Grocer
  - Fresh items: chicken, produce → FreshDirect
  - 1-item rule: Single specialty item merges to primary store
- **Availability**: Random 10% unavailability to demonstrate indicators

## ✅ Deliverables Completed

- ✅ Ingredient confirmation modal (editable with add/remove/edit)
- ✅ Multi-store cart header with clear notification
- ✅ Store tabs (All | FreshDirect | Indian Grocer)
- ✅ Per-item store chips
- ✅ Unavailable item indicators in cart
- ✅ Agent checkout launcher with progress UI
- ✅ Opens mock store cart URLs in new tabs
- ✅ Uses existing design system (colors, components, typography)
- ✅ State machine implementation

---

**Built with**: React 18, TypeScript, Vite
**Design System**: Based on existing Conscious Cart Coach colors
