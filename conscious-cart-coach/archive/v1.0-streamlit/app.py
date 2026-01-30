"""
Conscious Cart Coach - Streamlit Web App.

2-panel layout:
- LEFT: prompt (text_area) + assumptions + "Create cart" CTA
- RIGHT: cart casing with product cards + cart-wide switcher + downloads

Run: streamlit run src/ui/app.py
"""

import sys
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st
from src.orchestrator.orchestrator import Orchestrator
from src.contracts.models import DecisionBundle, UserPrefs, TierSymbol
from src.ui.styles import get_global_css
from src.ui.components import (
    build_product_lookup,
    render_cart_switcher,
    render_ingredient_card,
    render_unchanged_summary,
    tier_badge,
    format_safety_note,
    ETHICAL_TOOLTIP,
)

# Import store classification
import importlib.util
def load_module(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load store split modules
orchestrator_path = PROJECT_ROOT / "src" / "orchestrator"
sys.path.insert(0, str(orchestrator_path))
store_split_module = load_module('store_split', str(orchestrator_path / 'store_split.py'))
split_ingredients_by_store = store_split_module.split_ingredients_by_store
format_store_split_for_ui = store_split_module.format_store_split_for_ui
UserPreferences = store_split_module.UserPreferences


# =============================================================================
# Page Config
# =============================================================================

st.set_page_config(
    page_title="Conscious Cart Coach",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Inject global CSS
st.markdown(get_global_css(), unsafe_allow_html=True)


# =============================================================================
# Session State Init
# =============================================================================

def init_state():
    """Initialize session state keys if not present."""
    defaults = {
        "step": "input",
        "user_prefs": {},
        "ingredients_draft": [],
        "ingredients_confirmed": [],
        "decision_bundle": None,
        "product_lookup": {},
        "candidates": {},
        "current_selections": {},
        "cart_mode": "pick",
        "show_debug": False,
        "show_ingredient_modal": False,
        "ingredient_availability": {},
        "ingredient_safety": {},
        "qty_overrides": {},
        "show_preferences": False,
        "use_llm_extraction": False,
        "use_llm_explanations": False,
        "prompt_text": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


# =============================================================================
# Safety Helpers
# =============================================================================

EWG_DIRTY_DOZEN = {
    "spinach", "kale", "strawberries", "blueberries", "tomatoes",
    "cherry_tomatoes", "bell_pepper", "hot_peppers", "celery",
    "potatoes", "lettuce",
}


def _compute_ingredient_safety(ingredient_name: str) -> str:
    """Get safety note for an ingredient (EWG-based)."""
    normalized = ingredient_name.lower().strip().replace(" ", "_")
    if normalized in EWG_DIRTY_DOZEN:
        return "Organic recommended (EWG)"
    return ""


# =============================================================================
# Callbacks
# =============================================================================

def on_create_cart():
    """Run ingredient extraction + candidates (for availability), then open modal."""
    prompt = st.session_state.prompt_text
    if not prompt.strip():
        return

    orch = Orchestrator(
        use_llm_extraction=st.session_state.use_llm_extraction,
        use_llm_explanations=st.session_state.use_llm_explanations,
    )
    result = orch.step_ingredients(prompt)

    if result.status == "ok":
        ingredients = result.facts.get("ingredients", [])
        st.session_state.ingredients_draft = ingredients

        # Run product agent to determine availability
        orch.confirm_ingredients(ingredients)
        cand_result = orch.step_candidates()

        candidates = orch.state.candidates_by_ingredient
        st.session_state.candidates = candidates

        # Compute availability per ingredient
        availability = {}
        safety = {}
        for ing in ingredients:
            name = ing.get("name", "")
            availability[name] = name in candidates and len(candidates.get(name, [])) > 0
            safety[name] = _compute_ingredient_safety(name)

        st.session_state.ingredient_availability = availability
        st.session_state.ingredient_safety = safety
        st.session_state.step = "ingredients"
        st.session_state.show_ingredient_modal = True
    else:
        st.session_state.step = "input"


def on_confirm_ingredients(confirmed_names: list[str]):
    """Confirm ingredients and run full pipeline."""
    orch = Orchestrator(
        use_llm_extraction=st.session_state.use_llm_extraction,
        use_llm_explanations=st.session_state.use_llm_explanations,
    )

    # Rebuild ingredients list from confirmed names
    confirmed = [{"name": n, "quantity": "", "category": ""} for n in confirmed_names]
    st.session_state.ingredients_confirmed = confirmed

    # Run full flow
    orch.step_ingredients(st.session_state.prompt_text)
    orch.confirm_ingredients(confirmed)
    orch.step_candidates()
    orch.step_enrich()
    bundle = orch.step_decide()

    # Store results
    st.session_state.decision_bundle = bundle
    st.session_state.candidates = orch.state.candidates_by_ingredient
    st.session_state.product_lookup = build_product_lookup(orch.state.candidates_by_ingredient)

    # Initialize selections to recommended
    selections = {}
    for item in bundle.items:
        selections[item.ingredient_name] = item.selected_product_id
    st.session_state.current_selections = selections
    st.session_state.cart_mode = "pick"
    st.session_state.step = "recommendations"
    st.session_state.show_ingredient_modal = False


def on_cart_mode_change(mode: str):
    """Apply cart-wide mode switch."""
    bundle = st.session_state.decision_bundle
    if not bundle:
        return

    st.session_state.cart_mode = mode
    selections = {}

    for item in bundle.items:
        if mode == "cheaper":
            selections[item.ingredient_name] = item.cheaper_neighbor_id or item.selected_product_id
        elif mode == "ethical":
            selections[item.ingredient_name] = item.conscious_neighbor_id or item.selected_product_id
        else:  # "pick"
            selections[item.ingredient_name] = item.selected_product_id

    st.session_state.current_selections = selections


def _build_user_prefs() -> UserPrefs:
    """Build UserPrefs from session state."""
    p = st.session_state.user_prefs
    return UserPrefs(
        preferred_brands=[b.strip() for b in p.get("preferred_brands", "").split(",") if b.strip()],
        avoided_brands=[b.strip() for b in p.get("avoided_brands", "").split(",") if b.strip()],
        dietary_restrictions=[d.strip() for d in p.get("dietary", "").split(",") if d.strip()],
        strict_safety=p.get("strict_safety", False),
    )


# =============================================================================
# Ingredient Confirmation Dialog
# =============================================================================

@st.dialog("Confirm ingredients", width="large")
def show_ingredient_dialog():
    """Modal dialog for ingredient confirmation with data_editor."""
    ingredients = st.session_state.ingredients_draft
    availability = st.session_state.ingredient_availability
    safety = st.session_state.ingredient_safety

    # Header with AI indicator
    if st.session_state.use_llm_extraction:
        st.markdown(
            '<p class="modal-subtext">🤖 AI extracted from your request. Edit before building cart.</p>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<p class="modal-subtext">Edit this list before we build your cart.</p>',
            unsafe_allow_html=True,
        )

    # Store Split Display
    ingredient_names = [ing.get("name", "") for ing in ingredients]
    candidates = st.session_state.get("candidates", {})

    # Calculate store split
    try:
        user_prefs = UserPreferences(urgency="planning")  # Default to planning mode
        store_split = split_ingredients_by_store(ingredient_names, candidates, user_prefs)
        split_ui = format_store_split_for_ui(store_split)

        # Store split tabs with design system colors
        st.markdown(
            f'''<div style="display: flex; gap: 12px; margin: 16px 0;">
                <div style="flex: 1; padding: 12px; border-radius: 8px; background: #fef9f5; border: 2px solid #d4976c;">
                    <div style="color: #d4976c; font-weight: 600; font-size: 12px; margin-bottom: 4px;">PRIMARY STORE</div>
                    <div style="font-size: 20px; font-weight: 700; color: #333;">{split_ui['primary_store']['count']}</div>
                    <div style="font-size: 11px; color: #666; margin-top: 4px;">{split_ui['primary_store']['store']}</div>
                </div>
                <div style="flex: 1; padding: 12px; border-radius: 8px; background: #fef9f5; border: 2px solid #8b7ba8;">
                    <div style="color: #8b7ba8; font-weight: 600; font-size: 12px; margin-bottom: 4px;">SPECIALTY STORE</div>
                    <div style="font-size: 20px; font-weight: 700; color: #333;">{split_ui['specialty_store']['count']}</div>
                    <div style="font-size: 11px; color: #666; margin-top: 4px;">{split_ui['specialty_store']['store']}</div>
                </div>
                <div style="flex: 1; padding: 12px; border-radius: 8px; background: #fef9f5; border: 2px solid #e5d5b8;">
                    <div style="color: #a89968; font-weight: 600; font-size: 12px; margin-bottom: 4px;">UNAVAILABLE</div>
                    <div style="font-size: 20px; font-weight: 700; color: #333;">{len(split_ui['unavailable'])}</div>
                    <div style="font-size: 11px; color: #666; margin-top: 4px;">Not in stock</div>
                </div>
            </div>''',
            unsafe_allow_html=True,
        )

        # Show 1-item rule message if applied
        if store_split.applied_1_item_rule:
            st.markdown(
                f'<div class="modal-store-info" style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 8px 12px; margin: 8px 0;">'
                f'💡 1-item efficiency rule: Merged specialty items to primary store for efficiency</div>',
                unsafe_allow_html=True,
            )
    except Exception as e:
        # Fallback to simple display if store split fails
        available_count = sum(1 for v in availability.values() if v)
        unavailable_count = sum(1 for v in availability.values() if not v)
        st.markdown(
            '<div class="modal-store-info">Store: ShopRite (chosen for availability)</div>',
            unsafe_allow_html=True,
        )

    # Availability summary (keep for backwards compatibility)
    available_count = sum(1 for v in availability.values() if v)
    unavailable_count = sum(1 for v in availability.values() if not v)
    unavailable_names = [k for k, v in availability.items() if not v]

    # Safety callouts
    safety_items = [(k, v) for k, v in safety.items() if v]
    recall_matches = [k for k, v in safety.items() if "Recall match" in v]

    if recall_matches:
        st.markdown(
            '<div class="modal-safety-callout">'
            'Recall match found for: ' + ", ".join(recall_matches) + '</div>',
            unsafe_allow_html=True,
        )
    elif safety_items:
        notes_str = "; ".join(f"{k}: {v}" for k, v in safety_items[:3])
        if len(safety_items) > 3:
            notes_str += f" +{len(safety_items) - 3} more"
        st.markdown(
            f'<div class="modal-safety-callout">{notes_str}</div>',
            unsafe_allow_html=True,
        )

    # Build DataFrame for data_editor
    rows = []
    for ing in ingredients:
        name = ing.get("name", "")
        rows.append({
            "ingredient": name,
            "include": True,
            "status": "Available" if availability.get(name, False) else "Unavailable",
            "safety_note": safety.get(name, ""),
        })

    df = pd.DataFrame(rows)

    # Data editor (editable ingredient names + include checkbox)
    edited_df = st.data_editor(
        df,
        column_config={
            "ingredient": st.column_config.TextColumn("Ingredient", width="medium"),
            "include": st.column_config.CheckboxColumn("Include", default=True),
            "status": st.column_config.TextColumn("Status", disabled=True, width="small"),
            "safety_note": st.column_config.TextColumn("Safety", disabled=True, width="medium"),
        },
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
        key="ingredient_editor",
    )

    # Footer buttons
    st.markdown("---")

    included_count = int(edited_df["include"].sum()) if not edited_df.empty else 0
    footer_cols = st.columns([2, 1, 1])

    with footer_cols[0]:
        st.markdown(
            f'<p class="modal-subtext" style="margin-top:8px;">'
            f'{included_count} ingredients · {unavailable_count} unavailable</p>',
            unsafe_allow_html=True,
        )

    with footer_cols[1]:
        if st.button("Cancel", width="stretch", key="modal_cancel"):
            st.session_state.show_ingredient_modal = False
            st.session_state.step = "input"
            st.rerun()

    with footer_cols[2]:
        if st.button(
            f"Confirm {included_count} ingredients",
            type="primary",
            width="stretch",
            key="modal_confirm",
        ):
            # Get confirmed ingredient names
            confirmed = edited_df[edited_df["include"]]["ingredient"].tolist()
            confirmed = [name for name in confirmed if name.strip()]
            on_confirm_ingredients(confirmed)
            st.rerun()


# =============================================================================
# Layout: Two Columns
# =============================================================================

left_col, right_col = st.columns([1, 1], gap="large")


# =============================================================================
# LEFT COLUMN: Prompt + Assumptions + CTA
# =============================================================================

with left_col:
    st.markdown("## 🛒 Conscious Cart Coach")
    st.caption("Find better grocery options for your meals")

    # --- Prompt Input (text_area) ---
    st.markdown("### What are you making?")

    # Show AI features hint if not enabled
    if not st.session_state.use_llm_extraction and not st.session_state.use_llm_explanations:
        st.info("💡 Tip: Enable **AI Features** in ⚙️ Preferences to use natural language (\"I want something healthy\") and get detailed explanations.")

    # Dynamic placeholder based on LLM mode
    placeholder_text = (
        "e.g., I want something healthy and seasonal, quick dinner for 2, budget-friendly vegetarian..."
        if st.session_state.use_llm_extraction
        else "e.g., chicken biryani for 4, spinach salad, stir fry, tikka masala..."
    )

    # Text area with unique key
    st.text_area(
        "Meal or recipe",
        placeholder=placeholder_text,
        label_visibility="collapsed",
        height=100,
        key="prompt_text",  # Use session state key directly
    )

    # --- Primary CTA ---
    st.button("Create cart", on_click=on_create_cart, type="primary")
    st.markdown(
        '<p class="cta-helper">We\'ll draft ingredients for you to confirm.</p>',
        unsafe_allow_html=True,
    )

    # --- Secondary popovers (compact pills, left-aligned) ---
    has_prompt = st.session_state.step != "input"
    pop_cols = st.columns([1, 1], gap="small")

    with pop_cols[0]:
        if has_prompt and st.session_state.step == "recommendations":
            n_items = len(st.session_state.ingredients_draft)
            with st.popover(f"\U0001f9fe Ingredients ({n_items})"):
                for ing in st.session_state.ingredients_draft[:8]:
                    st.write(f"- {ing.get('name', '')}")
                if len(st.session_state.ingredients_draft) > 8:
                    st.caption(f"+{len(st.session_state.ingredients_draft) - 8} more")
                if st.button("Edit ingredients", key="pop_edit_ing"):
                    st.session_state.show_ingredient_modal = True
                    st.rerun()
        else:
            st.button("\U0001f9fe Ingredients", disabled=True, key="pop_ing_disabled", width="stretch")

    with pop_cols[1]:
        # Always show Preferences (users need to enable LLM features before first cart)
        with st.popover("\u2699\ufe0f Preferences"):
            st.text_input("Location", value="NJ / Mid-Atlantic", disabled=True, key="_location")
            col_a, col_b = st.columns(2)
            with col_a:
                st.number_input("Household size", min_value=1, max_value=10, value=2, key="_household")
            with col_b:
                st.selectbox("Store", ["ShopRite", "Whole Foods", "Trader Joe's"], key="_store")
            dietary = st.text_input("Dietary restrictions", placeholder="e.g., vegetarian, gluten-free", key="_dietary")
            preferred = st.text_input("Preferred brands", placeholder="e.g., Organic Valley", key="_preferred_brands")
            avoided = st.text_input("Avoided brands", placeholder="e.g., Nestle", key="_avoided_brands")
            strict = st.checkbox("Strict safety (require organic for EWG items)", key="_strict_safety")

            # AI Features Section
            st.markdown("---")
            st.markdown("**🤖 AI Features**")
            use_llm_extraction = st.checkbox(
                "Enable AI ingredient extraction",
                value=st.session_state.use_llm_extraction,
                help="Parse natural language prompts using Claude AI (~$0.01 per request)",
                key="_use_llm_extraction",
            )
            use_llm_explanations = st.checkbox(
                "Enable detailed explanations",
                value=st.session_state.use_llm_explanations,
                help="Get AI-powered product explanations (~$0.03 per cart)",
                key="_use_llm_explanations",
            )

            if use_llm_extraction or use_llm_explanations:
                st.caption("💰 Cost: ~$0.045 per cart with both features")

            st.session_state.use_llm_extraction = use_llm_extraction
            st.session_state.use_llm_explanations = use_llm_explanations
            st.session_state.user_prefs = {
                "dietary": dietary,
                "preferred_brands": preferred,
                "avoided_brands": avoided,
                "strict_safety": strict,
            }

    # --- Debug Toggle ---
    st.markdown("---")
    st.checkbox("Show debug data", key="show_debug")


# =============================================================================
# RIGHT COLUMN: Cart Casing + Cards + Switcher + Downloads
# =============================================================================

with right_col:
    if st.session_state.step == "input":
        st.markdown(
            '<div class="cart-header"><h3>Your Cart</h3></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="empty-hint">Enter a meal or recipe to get started.</div>',
            unsafe_allow_html=True,
        )

    elif st.session_state.step == "ingredients":
        st.markdown(
            '<div class="cart-header"><h3>Your Cart</h3></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="empty-hint">Review and confirm ingredients to see recommendations.</div>',
            unsafe_allow_html=True,
        )

    elif st.session_state.step == "recommendations":
        bundle: DecisionBundle = st.session_state.decision_bundle
        product_lookup = st.session_state.product_lookup

        if not bundle or not bundle.items:
            st.warning("No recommendations available.")
        else:
            # --- Cart Header Zone (fixed, non-scrolling) ---
            st.markdown(
                '<div class="cart-header"><h3>Your Cart</h3></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<p class="cart-subtitle">{bundle.item_count} items · ShopRite</p>',
                unsafe_allow_html=True,
            )

            # Not found warning
            not_found = [
                ing for ing in [i.get("name", "") for i in st.session_state.ingredients_confirmed]
                if ing and ing not in st.session_state.candidates
            ]
            if not_found:
                st.markdown(
                    f'<p class="cart-warning">Not in inventory: {", ".join(not_found)}</p>',
                    unsafe_allow_html=True,
                )

            # Cart-Wide Switcher
            new_mode = render_cart_switcher(bundle, st.session_state.cart_mode)
            if new_mode:
                on_cart_mode_change(new_mode)
                st.rerun()

            # Unchanged items note
            render_unchanged_summary(bundle, st.session_state.cart_mode)

            # Current Cart Total
            current_total = sum(
                product_lookup.get(pid, {}).get("price", 0)
                for pid in st.session_state.current_selections.values()
            )
            st.markdown(
                f'<p class="cart-total">Cart total: ${current_total:.2f}</p>',
                unsafe_allow_html=True,
            )

            # --- Header/Content separator ---
            st.markdown('<div style="border-top:1px solid rgba(0,0,0,0.12); margin:8px 0 12px 0;"></div>', unsafe_allow_html=True)

            # --- Scroll Zone (cards, scrollable) ---
            with st.container(height=400, border=False):
                for i, item in enumerate(bundle.items):
                    current_pid = st.session_state.current_selections.get(
                        item.ingredient_name, item.selected_product_id
                    )

                    # Get qty from session state
                    qty = st.session_state.qty_overrides.get(item.ingredient_name, 1)

                    new_pid = render_ingredient_card(
                        item=item,
                        product_lookup=product_lookup,
                        current_product_id=current_pid,
                        card_index=i,
                        qty=qty,
                    )

                    if new_pid and new_pid != current_pid:
                        st.session_state.current_selections[item.ingredient_name] = new_pid
                        st.session_state.cart_mode = "custom"
                        st.rerun()

                # Data Gaps
                if bundle.data_gaps:
                    with st.expander(f"{len(bundle.data_gaps)} data gaps"):
                        for gap in bundle.data_gaps:
                            st.write(f"• {gap}")

            # --- Content/Footer separator ---
            st.markdown('<div style="border-top:1px solid rgba(0,0,0,0.12); margin:8px 0 12px 0;"></div>', unsafe_allow_html=True)

            # --- Footer Zone (fixed, non-scrolling) ---
            footer_cols = st.columns([1, 1])

            with footer_cols[0]:
                csv_lines = ["ingredient,brand,product,price,qty"]
                for item in bundle.items:
                    pid = st.session_state.current_selections.get(
                        item.ingredient_name, item.selected_product_id
                    )
                    p = product_lookup.get(pid, {})
                    q = st.session_state.qty_overrides.get(item.ingredient_name, 1)
                    csv_lines.append(
                        f"{item.ingredient_name},{p.get('brand','')},{p.get('title','')},{p.get('price',0)},{q}"
                    )
                csv_content = "\n".join(csv_lines)
                st.download_button(
                    "Shopping list (CSV)",
                    data=csv_content,
                    file_name="shopping_list.csv",
                    mime="text/csv",
                    width="stretch",
                )

            with footer_cols[1]:
                st.button("Continue to store", disabled=True, help="Coming soon", width="stretch")

    # --- Debug Panel ---
    if st.session_state.show_debug and st.session_state.step == "recommendations":
        with st.expander("Debug: DecisionBundle", expanded=False):
            bundle = st.session_state.decision_bundle
            if bundle:
                st.json({
                    "item_count": bundle.item_count,
                    "totals": bundle.totals,
                    "deltas": bundle.deltas,
                    "data_gaps": bundle.data_gaps,
                    "constraint_notes": bundle.constraint_notes,
                })

        with st.expander("Debug: Candidates", expanded=False):
            candidates = st.session_state.candidates
            if candidates:
                for ing, cands in list(candidates.items())[:5]:
                    st.write(f"**{ing}**: {len(cands)} candidates")
                    st.dataframe(cands)

        with st.expander("Debug: Current Selections", expanded=False):
            st.json(st.session_state.current_selections)


# =============================================================================
# Auto-open Ingredient Modal (triggered by "Create cart")
# =============================================================================

if st.session_state.show_ingredient_modal:
    show_ingredient_dialog()
