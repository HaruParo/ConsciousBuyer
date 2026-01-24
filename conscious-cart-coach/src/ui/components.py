"""
UI Components for Conscious Cart Coach.

Render helpers for the 2-panel Streamlit layout:
- render_cart_switcher: 3-button row for cart-wide tier switching
- render_ingredient_card: compact card (7 lines) with qty control
- render_unchanged_summary: expander for items without alternates
- build_product_lookup: product_id -> display fields from candidates
"""

import streamlit as st
from typing import Any

from ..contracts.models import DecisionBundle, DecisionItem, TierSymbol


# =============================================================================
# Tier Display Config (UI-only naming)
# =============================================================================

TIER_DISPLAY = {
    TierSymbol.CHEAPER: {"emoji": "\U0001f4b8", "label": "Cheaper", "css": "tier-pill-cheaper"},
    TierSymbol.BALANCED: {"emoji": "\u2705", "label": "Your pick", "css": "tier-pill-balanced"},
    TierSymbol.CONSCIOUS: {"emoji": "\U0001f91d", "label": "Ethical", "css": "tier-pill-conscious"},
}

ETHICAL_TOOLTIP = (
    "Uses verified signals like Fair Trade, co-op/worker-owned, "
    "or local partners when available. Not a moral rating."
)


# =============================================================================
# Product Lookup Builder
# =============================================================================

def build_product_lookup(candidates_by_ingredient: dict[str, list[dict]]) -> dict[str, dict]:
    """Build a product_id -> display fields map from candidates."""
    lookup = {}
    for ingredient, cands in candidates_by_ingredient.items():
        for c in cands:
            lookup[c["product_id"]] = {
                "product_id": c["product_id"],
                "ingredient_name": c.get("ingredient_name", ingredient),
                "title": c.get("title", ""),
                "brand": c.get("brand", ""),
                "size": c.get("size", ""),
                "price": c.get("price", 0),
                "unit_price": c.get("unit_price", 0),
                "unit_price_unit": c.get("unit_price_unit", "oz"),
                "organic": c.get("organic", False),
                "in_stock": c.get("in_stock", True),
            }
    return lookup


# =============================================================================
# Tier Badge (HTML pill)
# =============================================================================

def tier_badge(tier: TierSymbol) -> str:
    """Return emoji + label for a tier."""
    display = TIER_DISPLAY.get(tier, TIER_DISPLAY[TierSymbol.BALANCED])
    return f"{display['emoji']} {display['label']}"


def tier_pill_html(tier: TierSymbol) -> str:
    """Return an HTML pill span for a tier badge."""
    display = TIER_DISPLAY.get(tier, TIER_DISPLAY[TierSymbol.BALANCED])
    css_class = display["css"]
    label = f"{display['emoji']} {display['label']}"
    if tier == TierSymbol.CONSCIOUS:
        return (
            f'<span class="tier-pill {css_class}" '
            f'title="{ETHICAL_TOOLTIP}">{label}</span>'
        )
    return f'<span class="tier-pill {css_class}">{label}</span>'


# =============================================================================
# Truncate With More
# =============================================================================

def truncate_with_more(items: list[str], max_show: int = 2) -> tuple[list[str], int]:
    """Return (visible_items, overflow_count)."""
    if len(items) <= max_show:
        return items, 0
    return items[:max_show], len(items) - max_show


# =============================================================================
# Safety Note Formatting
# =============================================================================

def format_safety_note(note: str) -> str:
    """Translate internal safety notes to user-friendly wording."""
    lower = note.lower()
    if "dirty dozen" in lower or "ewg recommends" in lower:
        return "Organic recommended (EWG)"
    if "elevated recall" in lower:
        return "Recent category recalls"
    if "recall data" in lower or "data gap" in lower:
        return "Recall data limited"
    if "recall match" in lower:
        return "Recall match found"
    return note


# =============================================================================
# Render Cart-Wide Switcher
# =============================================================================

def render_cart_switcher(
    bundle: DecisionBundle,
    current_mode: str,
) -> str | None:
    """
    Render 3-button cart-wide switcher row with helper text.
    Returns the new mode if clicked, else None.
    """
    cheaper_delta = bundle.deltas.get("cheaper_vs_recommended", 0)
    ethical_delta = bundle.deltas.get("conscious_vs_recommended", 0)

    cols = st.columns(3)

    with cols[0]:
        cheaper_label = "\U0001f4b8 Cheaper"
        if cheaper_delta < 0:
            cheaper_label += f" \u2212${abs(cheaper_delta):.2f}"
        if st.button(
            cheaper_label,
            width="stretch",
            type="primary" if current_mode == "cheaper" else "secondary",
            key="cart_cheaper",
        ):
            return "cheaper"

    with cols[1]:
        if st.button(
            "\u2705 Your pick",
            width="stretch",
            type="primary" if current_mode == "pick" else "secondary",
            key="cart_pick",
        ):
            return "pick"

    with cols[2]:
        ethical_label = "\U0001f91d Ethical"
        if ethical_delta > 0:
            ethical_label += f" +${ethical_delta:.2f}"
        if st.button(
            ethical_label,
            width="stretch",
            type="primary" if current_mode == "ethical" else "secondary",
            key="cart_ethical",
            help=ETHICAL_TOOLTIP,
        ):
            return "ethical"

    # Helper text
    st.markdown(
        '<p class="switcher-helper">Applies the closest option per item. '
        'You can still adjust any item below.</p>',
        unsafe_allow_html=True,
    )

    return None


# =============================================================================
# Render Ingredient Card (7-line hierarchy with qty)
# =============================================================================

def render_ingredient_card(
    item: DecisionItem,
    product_lookup: dict[str, dict],
    current_product_id: str,
    card_index: int,
    qty: int = 1,
) -> str | None:
    """
    Render a compact ingredient card.

    Layout:
    1) Header: ingredient name + tier pill
    2) Why line: reason_short (italic)
    3) Product: brand - title
    4) Price: $price . size . $unit/oz
    5) Meta: attributes + safety (muted, +N more)
    6) Stepper: [<- Cheaper] [Ethical ->]
    7) Qty control

    Returns new product_id if stepper clicked, else None.
    """
    product = product_lookup.get(current_product_id, {})
    if not product:
        st.warning(f"Product not found: {current_product_id}")
        return None

    # Determine current tier
    if current_product_id == item.selected_product_id:
        current_tier = item.tier_symbol
    elif current_product_id == item.cheaper_neighbor_id:
        current_tier = TierSymbol.CHEAPER
    elif current_product_id == item.conscious_neighbor_id:
        current_tier = TierSymbol.CONSCIOUS
    else:
        current_tier = item.tier_symbol

    with st.container(border=True):
        # 1) HEADER: ingredient name + tier pill
        pill_html = tier_pill_html(current_tier)
        st.markdown(
            f'<div class="card-header-row">'
            f'<strong>{item.ingredient_name.title()}</strong> {pill_html}</div>',
            unsafe_allow_html=True,
        )

        # 2) WHY LINE
        reason = _get_display_reason(item, current_product_id, current_tier)
        st.markdown(
            f'<p class="card-why">Why this pick: <i>{reason}</i></p>',
            unsafe_allow_html=True,
        )

        # 3) PRODUCT LINE (always show brand — title)
        title = product["title"]
        brand = product["brand"]
        product_text = f"{brand} \u2014 {title}" if brand else title
        if len(product_text) > 45:
            product_text = product_text[:42] + "\u2026"
        st.markdown(f'<p class="card-product">{product_text}</p>', unsafe_allow_html=True)

        # 4) PRICE LINE
        unit_price_str = f"${product['unit_price']:.2f}/{product['unit_price_unit']}"
        st.markdown(
            f'<p class="card-price">${product["price"]:.2f} \u00b7 '
            f'{product["size"]} \u00b7 {unit_price_str}</p>',
            unsafe_allow_html=True,
        )

        # 5) META LINE (muted, attributes + safety)
        meta_parts = []
        if item.attributes:
            shown_attrs, attr_overflow = truncate_with_more(item.attributes, 2)
            attr_str = " \u00b7 ".join(shown_attrs)
            if attr_overflow > 0:
                attr_str += f" +{attr_overflow} more"
            meta_parts.append(attr_str)
        if item.safety_notes:
            first_note = format_safety_note(item.safety_notes[0])
            meta_parts.append(first_note)
        if meta_parts:
            meta_text = " &nbsp;\u00b7&nbsp; ".join(meta_parts)
            st.markdown(f'<p class="card-meta">{meta_text}</p>', unsafe_allow_html=True)

        # 6) STEPPER CONTROLS (equal-width buttons)
        new_selection = _render_stepper(item, current_product_id, card_index)

        # 7) QTY (compact inline)
        qty_cols = st.columns([3, 1])
        with qty_cols[1]:
            st.number_input(
                "Qty",
                min_value=1,
                max_value=20,
                value=qty,
                key=f"qty_{card_index}",
                label_visibility="collapsed",
            )

    return new_selection


def _get_display_reason(item: DecisionItem, current_pid: str, current_tier: TierSymbol) -> str:
    """Get the display reason for the current selection."""
    if current_pid == item.selected_product_id:
        reason = item.reason_short or ""
        # Replace vague fallbacks with specific reasons
        if not reason or reason in ("Best match", "Recommended pick", "Best available"):
            if item.attributes and "organic" in " ".join(item.attributes).lower():
                reason = "Organic recommended (EWG)"
            elif item.safety_notes:
                reason = "Good availability"
            else:
                reason = "Best unit price"
    elif current_tier == TierSymbol.CHEAPER:
        reason = "Lower cost option"
    elif current_tier == TierSymbol.CONSCIOUS:
        reason = "Verified impact signal"
    else:
        reason = "Matches preferences"

    # Truncate to 6 words max
    words = reason.split()
    if len(words) > 6:
        reason = " ".join(words[:6]) + "\u2026"
    return reason


def _render_stepper(
    item: DecisionItem,
    current_product_id: str,
    card_index: int,
) -> str | None:
    """Render [<- Cheaper] [Ethical ->] stepper buttons."""
    cols = st.columns([1, 1])
    new_id = None

    with cols[0]:
        has_cheaper = (
            item.cheaper_neighbor_id
            and current_product_id != item.cheaper_neighbor_id
        )
        if st.button(
            "\u2190 Cheaper",
            disabled=not has_cheaper,
            width="stretch",
            key=f"cheaper_{card_index}",
            help=None if has_cheaper else "No cheaper alternate",
        ):
            new_id = item.cheaper_neighbor_id

    with cols[1]:
        has_ethical = (
            item.conscious_neighbor_id
            and current_product_id != item.conscious_neighbor_id
        )
        if st.button(
            "Ethical \u2192",
            disabled=not has_ethical,
            width="stretch",
            key=f"ethical_{card_index}",
            help=None if has_ethical else "No ethical alternate",
        ):
            new_id = item.conscious_neighbor_id

    return new_id


# =============================================================================
# Unchanged Items Summary
# =============================================================================

def render_unchanged_summary(
    bundle: DecisionBundle,
    cart_mode: str,
):
    """Show how many items didn't change when switching cart mode."""
    if cart_mode == "pick":
        return

    unchanged = []
    for item in bundle.items:
        if cart_mode == "cheaper" and not item.cheaper_neighbor_id:
            unchanged.append(item.ingredient_name)
        elif cart_mode == "ethical" and not item.conscious_neighbor_id:
            unchanged.append(item.ingredient_name)

    if unchanged:
        with st.expander(f"{len(unchanged)} items unchanged (no alternate)"):
            for name in unchanged:
                st.write(f"\u2022 {name.title()}")
