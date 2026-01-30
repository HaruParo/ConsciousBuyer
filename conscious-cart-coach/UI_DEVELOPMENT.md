# UI_NOTE - Streamlit UX Layer

## Two-Panel Layout

```
┌─────────────────────────┬─────────────────────────┐
│  LEFT COLUMN            │  RIGHT COLUMN           │
│                         │                         │
│  App title + subtitle   │  Cart header + store    │
│  Prompt input           │  Cart-wide switcher     │
│  [Find ingredients]     │  Cart total             │
│  Assumptions expander   │  ─────────────────      │
│  ─────────────────      │  Ingredient card 1      │
│  Ingredient editor      │  Ingredient card 2      │
│  [Confirm N items]      │  ...                    │
│  ─────────────────      │  ─────────────────      │
│  Debug toggle           │  Download CSV / Footer  │
└─────────────────────────┴─────────────────────────┘
```

## Session State Keys

| Key | Type | Description |
|-----|------|-------------|
| `step` | str | "input" / "ingredients" / "confirmed" / "recommendations" |
| `prompt_text` | str | User's meal/recipe input |
| `user_prefs` | dict | Dietary, brands, strict_safety |
| `ingredients_draft` | list[dict] | Editable ingredient list |
| `ingredients_confirmed` | list[dict] | Final confirmed ingredients |
| `decision_bundle` | DecisionBundle | Engine output |
| `product_lookup` | dict[str, dict] | product_id → display fields |
| `candidates` | dict[str, list] | ingredient → candidate list |
| `current_selections` | dict[str, str] | ingredient → selected product_id |
| `cart_mode` | str | "cheaper" / "pick" / "ethical" / "custom" |
| `show_debug` | bool | Show debug expanders |

## How Neighbor Stepping Works

Each ingredient card has `[← Cheaper]` and `[Ethical →]` buttons.

1. The `DecisionBundle` provides per-item:
   - `selected_product_id` (recommended pick)
   - `cheaper_neighbor_id` (next-cheaper viable candidate)
   - `conscious_neighbor_id` (next-more-ethical candidate)

2. When user clicks a stepper button:
   - `current_selections[ingredient]` updates to the neighbor's product_id
   - `cart_mode` switches to "custom" (no longer a full-cart preset)
   - `st.rerun()` refreshes the card display

3. The card renders whichever product is in `current_selections`, looking up
   display fields from `product_lookup`.

4. Cart-wide switcher applies the same logic across all items:
   - "Cheaper": each item → `cheaper_neighbor_id or selected_product_id`
   - "Your pick": each item → `selected_product_id`
   - "Ethical": each item → `conscious_neighbor_id or selected_product_id`

5. Items without a neighbor stay on their recommended pick. The "N items
   unchanged" expander shows which ones.

## Tier Display Names

| Backend Value | UI Label | Emoji |
|---|---|---|
| CHEAPER | Cheaper | 💸 |
| BALANCED | Your pick | ✅ |
| CONSCIOUS | Ethical brands | 🤝 |

"Ethical brands" has a tooltip: "Uses verified signals like Fair Trade,
co-op/worker-owned, or local partners when available. Not a moral rating."

## Cart Shell Layout (Flex-Based)

The right column is the cart shell, constrained to viewport height via CSS flex:

```
┌─────────────────────────────────┐  ← Right column = cart-shell
│  Cart Header (flex: 0 0 auto)   │     (height: calc(100vh - 80px))
│  Title · Store · Switcher · $   │     (overflow: hidden)
├─────────────────────────────────┤
│                                 │
│  Scroll Zone (flex: 1 1 auto)   │  ← overflow-y: auto
│  ┌───────────────────────────┐  │     Cards scroll here
│  │  Ingredient Card 1        │  │
│  │  Ingredient Card 2        │  │
│  │  ...                      │  │
│  │  Data gaps expander       │  │
│  └───────────────────────────┘  │
│                                 │
├─────────────────────────────────┤
│  Footer (flex: 0 0 auto)        │  ← border-top separator
│  [Download CSV]  [Checkout]     │     Always visible at bottom
└─────────────────────────────────┘
```

Implementation:
- **app.py**: Header and footer render directly in the right column.
  The card list is wrapped in `st.container(height=400, border=False)`.
- **styles.py**: CSS overrides the container height to fill remaining
  flex space (`flex: 1 1 auto; min-height: 0; overflow-y: auto`).
  Uses `:has()` selector to target the scroll zone's element-container.
- The right column itself carries the cart visual styling (white bg,
  border, rounded corners, box-shadow) — no outer `st.container(border=True)`.

## Running the App

```bash
cd conscious-cart-coach
streamlit run src/ui/app.py
```
