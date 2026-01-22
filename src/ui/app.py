"""
Streamlit UI for Conscious Cart Coach.
Turn meal plans into conscious shopping choices.
"""

import sys
from pathlib import Path

import streamlit as st

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
# Add project root for src.* imports
sys.path.insert(0, str(PROJECT_ROOT))
# Add src/llm first for Gemini decision engine
sys.path.insert(0, str(PROJECT_ROOT / "src"))
# Add conscious-cart-coach/src for facts_pack
sys.path.insert(0, str(PROJECT_ROOT / "conscious-cart-coach" / "src"))

from data_processing.facts_pack import generate_facts_pack, parse_user_input
from data_processing.store_selection import select_best_store, get_store_selection_summary, get_all_stores_comparison
from llm.decision_engine import decide_tiers
from src.data_processing.validator import validate_decision

# Page configuration
st.set_page_config(
    page_title="Conscious Cart Coach",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for styling
st.markdown("""
<style>
    /* Tier card styling */
    .tier-card {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .tier-cheaper {
        background-color: rgba(59, 130, 246, 0.1);
        border: 2px solid #3B82F6;
    }
    .tier-balanced {
        background-color: rgba(234, 179, 8, 0.1);
        border: 2px solid #EAB308;
    }
    .tier-conscious {
        background-color: rgba(34, 197, 94, 0.1);
        border: 2px solid #22C55E;
    }

    /* Recommended badge */
    .recommended-badge {
        background-color: #10B981;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
    }

    /* Item styling */
    .item-card {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 0.75rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }

    /* Price styling */
    .price-tag {
        font-size: 1.25rem;
        font-weight: bold;
    }

    /* Category header */
    .category-header {
        font-weight: 600;
        margin-bottom: 0.25rem;
    }

    /* Tier header colors */
    .cheaper-header { color: #3B82F6; }
    .balanced-header { color: #EAB308; }
    .conscious-header { color: #22C55E; }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# Human-readable display names for ingredient categories
CATEGORY_DISPLAY_NAMES = {
    # Miso soup ingredients
    "miso_paste": "Miso Paste",
    "tofu": "Tofu",
    "seaweed": "Seaweed (Wakame)",
    "dashi": "Dashi Stock",
    # Produce
    "produce_onions": "Green Onions",
    "produce_greens": "Leafy Greens",
    "produce_tomatoes": "Tomatoes",
    "produce_peppers": "Bell Peppers",
    "produce_squash": "Squash",
    "produce_beans": "Green Beans",
    "produce_cucumbers": "Cucumbers",
    "produce_mushrooms": "Mushrooms",
    "produce_aromatics": "Garlic & Ginger",
    "produce_roots": "Root Vegetables",
    "produce_root_veg": "Root Vegetables",
    # Fruits
    "fruit_tropical": "Tropical Fruits",
    "fruit_berries": "Berries",
    "fruit_citrus": "Citrus Fruits",
    "fruit_other": "Other Fruits",
    # Dairy
    "milk": "Milk",
    "yogurt": "Yogurt",
    "cheese": "Cheese",
    "eggs": "Eggs",
    "butter_ghee": "Butter/Ghee",
    "ice_cream": "Ice Cream",
    # Proteins
    "chicken": "Chicken",
    "meat_other": "Meat",
    "fermented": "Fermented Foods",
    # Pantry
    "grains": "Grains/Rice/Pasta",
    "bread": "Bread",
    "oils_olive": "Olive Oil",
    "oils_coconut": "Coconut Oil",
    "oils_other": "Cooking Oil",
    "vinegar": "Vinegar",
    "spices": "Spices",
    "canned_coconut": "Coconut Milk",
    "canned_beans": "Canned Beans",
    "nuts_almonds": "Almonds",
    "nuts_cashews": "Cashews",
    "nuts_peanuts": "Peanuts",
    "nuts_other": "Mixed Nuts",
    "hummus_dips": "Hummus/Dips",
    "chocolate": "Chocolate",
    "cookies_crackers": "Cookies/Crackers",
    "chips": "Chips",
    "tea": "Tea",
}


def format_category_name(category: str) -> str:
    """Format category name for display using human-readable names."""
    if category in CATEGORY_DISPLAY_NAMES:
        return CATEGORY_DISPLAY_NAMES[category]
    # Fallback to basic formatting
    return category.replace("_", " ").title()


def get_tier_color(tier: str) -> str:
    """Get color for a tier."""
    colors = {
        "cheaper": "#3B82F6",
        "balanced": "#EAB308",
        "conscious": "#22C55E",
    }
    return colors.get(tier, "#666666")


def display_product_flags(items: list, user_location: str = ""):
    """Display product flags (recalls, advisories, seasonal info) for items."""
    all_flags = []

    for item in items:
        category = item.get("category", "")
        flags = item.get("flags", [])
        for flag in flags:
            flag["category"] = category
            all_flags.append(flag)

    if not all_flags:
        return

    # Separate by severity
    recalls = [f for f in all_flags if f.get("type") == "recall"]
    advisories = [f for f in all_flags if f.get("type") == "info" or f.get("severity") == "advisory"]
    seasonal = [f for f in all_flags if f.get("type") == "seasonal"]

    # Display recalls prominently (red)
    if recalls:
        st.subheader("🚨 Active Recalls")
        for recall in recalls:
            # Filter by region if user location provided
            regions = recall.get("regions", [])
            if regions and regions != ["nationwide"]:
                if user_location:
                    # Check if user's state is in affected regions
                    user_state = user_location.split(",")[-1].strip().upper()[:2]
                    if user_state not in [r.upper() for r in regions]:
                        continue  # Skip if not in user's region

            severity = recall.get("severity", "")
            severity_color = "red" if "Class I" in severity else "orange"

            with st.container():
                st.error(f"**{recall.get('title', 'Recall Notice')}** ({severity})")
                st.caption(f"📍 {format_category_name(recall.get('category', ''))} | Source: {recall.get('source', 'FDA')} | {recall.get('date', '')}")
                st.write(recall.get("description", ""))
                if recall.get("affected_brands"):
                    st.write(f"**Affected brands:** {', '.join(recall.get('affected_brands', []))}")
                if recall.get("recommendation"):
                    st.info(f"💡 **Action:** {recall.get('recommendation')}")
                st.divider()

    # Display advisories (yellow)
    if advisories:
        with st.expander(f"⚠️ Health Advisories ({len(advisories)})", expanded=False):
            for advisory in advisories:
                st.warning(f"**{advisory.get('title', 'Advisory')}**")
                st.caption(f"📍 {format_category_name(advisory.get('category', ''))} | {advisory.get('source', '')}")
                st.write(advisory.get("description", ""))
                if advisory.get("recommendation"):
                    st.info(f"💡 {advisory.get('recommendation')}")

    # Display seasonal info (blue)
    if seasonal:
        with st.expander(f"📅 Seasonal Notes ({len(seasonal)})", expanded=False):
            for note in seasonal:
                st.info(f"**{note.get('title', 'Seasonal Info')}**")
                st.caption(f"📍 {format_category_name(note.get('category', ''))}")
                st.write(note.get("description", ""))
                if note.get("recommendation"):
                    st.write(f"💡 {note.get('recommendation')}")


def display_tier_item(tier_data: dict, is_recommended: bool = False):
    """Display a single tier item."""
    if not tier_data:
        st.write("*No data available*")
        return

    brand = tier_data.get("brand", "Unknown")
    product_name = tier_data.get("product_name", "")
    price = tier_data.get("est_price")
    packaging = tier_data.get("packaging", "")
    certifications = tier_data.get("certifications", [])

    # Display brand and product
    if product_name:
        st.markdown(f"**{brand}** - {product_name}")
    else:
        st.markdown(f"**{brand}**")

    # Display price
    if price is not None:
        st.markdown(f"<span class='price-tag'>${price:.2f}</span>", unsafe_allow_html=True)
    else:
        st.write("Price: N/A")

    # Display packaging
    if packaging:
        st.caption(f"📦 {packaging}")

    # Display certifications as tags
    if certifications:
        cert_tags = " ".join([f"`{cert}`" for cert in certifications])
        st.markdown(cert_tags)


def calculate_cart_total(decisions: list, tier: str) -> float:
    """Calculate total price for a tier across all items."""
    total = 0.0
    for decision in decisions:
        all_tiers = decision.get("all_tiers", {})
        tier_data = all_tiers.get(tier, {})
        if tier_data:
            price = tier_data.get("est_price")
            if price is not None:
                total += price
    return total


def build_cart_from_selections(decisions: list, selections: dict) -> dict:
    """
    Build a custom cart based on user tier selections.

    Args:
        decisions: List of decision dicts with all_tiers
        selections: Dict mapping category to selected tier

    Returns:
        Cart dict with items and total
    """
    cart_items = []
    total = 0.0

    for decision in decisions:
        category = decision.get("category", "unknown")
        all_tiers = decision.get("all_tiers", {})

        # Get selected tier for this category (default to recommended)
        selected_tier = selections.get(category, decision.get("recommended_tier", "balanced"))
        tier_data = all_tiers.get(selected_tier, {})

        if tier_data:
            price = tier_data.get("est_price", 0) or 0
            total += price

            cart_items.append({
                "category": category,
                "tier": selected_tier,
                "brand": tier_data.get("brand", "Unknown"),
                "product_name": tier_data.get("product_name", ""),
                "price": price,
                "packaging": tier_data.get("packaging", ""),
                "certifications": tier_data.get("certifications", []),
            })

    return {
        "items": cart_items,
        "total": total,
    }


def generate_csv(cart: dict) -> str:
    """
    Generate CSV content for shopping list download.

    Args:
        cart: Cart dict with items and total

    Returns:
        CSV string
    """
    import io
    import csv

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["Category", "Tier", "Brand", "Product", "Price", "Packaging", "Certifications"])

    # Items
    for item in cart.get("items", []):
        writer.writerow([
            format_category_name(item.get("category", "")),
            item.get("tier", "").upper(),
            item.get("brand", ""),
            item.get("product_name", ""),
            f"${item.get('price', 0):.2f}",
            item.get("packaging", ""),
            ", ".join(item.get("certifications", [])),
        ])

    # Total row
    writer.writerow([])
    writer.writerow(["TOTAL", "", "", "", f"${cart.get('total', 0):.2f}", "", ""])

    return output.getvalue()


def display_cart_customization(decisions: list):
    """
    Display cart customization section allowing tier swapping.

    Args:
        decisions: List of decision dicts
    """
    st.subheader("🔄 Customize Your Cart")
    st.write("Adjust tiers for each item to build your perfect cart.")

    # Initialize selections in session state if not present
    if "tier_selections" not in st.session_state:
        st.session_state.tier_selections = {}

    # Set defaults from recommendations
    for decision in decisions:
        category = decision.get("category", "unknown")
        if category not in st.session_state.tier_selections:
            st.session_state.tier_selections[category] = decision.get("recommended_tier", "balanced")

    # Display customization UI
    for decision in decisions:
        category = decision.get("category", "unknown")
        display_name = format_category_name(category)
        all_tiers = decision.get("all_tiers", {})
        recommended = decision.get("recommended_tier", "balanced")

        col1, col2, col3 = st.columns([2, 2, 2])

        with col1:
            st.write(f"**{display_name}**")
            # Show current selection info
            current_tier = st.session_state.tier_selections.get(category, recommended)
            current_data = all_tiers.get(current_tier, {})
            if current_data:
                price = current_data.get("est_price")
                if price:
                    st.caption(f"${price:.2f}")

        with col2:
            # Tier selector
            tier_options = ["cheaper", "balanced", "conscious"]
            current_index = tier_options.index(st.session_state.tier_selections.get(category, recommended))

            selected_tier = st.selectbox(
                f"Tier",
                tier_options,
                index=current_index,
                key=f"tier_{category}",
                format_func=lambda x: f"{x.upper()} {'⭐' if x == recommended else ''}",
                label_visibility="collapsed",
            )

            # Update session state
            st.session_state.tier_selections[category] = selected_tier

        with col3:
            # Show selected product info
            tier_data = all_tiers.get(selected_tier, {})
            if tier_data:
                brand = tier_data.get("brand", "Unknown")
                st.write(f"{brand}")
                certs = tier_data.get("certifications", [])
                if certs:
                    st.caption(", ".join(certs[:2]))

    st.divider()

    # Build and display final cart
    final_cart = build_cart_from_selections(decisions, st.session_state.tier_selections)

    st.subheader("📋 Your Final Cart")

    # Display cart summary
    col1, col2 = st.columns([3, 1])

    with col1:
        for item in final_cart["items"]:
            tier_color = get_tier_color(item["tier"])
            st.markdown(
                f"• **{item['category'].replace('_', ' ').title()}**: "
                f"{item['brand']} - <span style='color: {tier_color}'>{item['tier'].upper()}</span> "
                f"(${item['price']:.2f})",
                unsafe_allow_html=True
            )

    with col2:
        st.metric("Total", f"${final_cart['total']:.2f}")

    st.divider()

    # Lock Plan section
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔒 Lock Plan", type="primary", use_container_width=True):
            st.session_state.locked_cart = final_cart
            st.success("Plan locked! Download your shopping list below.")

    with col2:
        # Download button (always available)
        csv_data = generate_csv(final_cart)
        st.download_button(
            "📥 Download Shopping List",
            csv_data,
            "shopping_list.csv",
            "text/csv",
            use_container_width=True,
        )

    # Show locked cart confirmation
    if st.session_state.get("locked_cart"):
        st.info("✅ Your cart has been locked. You can still download or modify selections above.")


def display_cart_column(decisions: list, tier: str, tier_label: str):
    """Display a cart column for a specific tier."""
    color = get_tier_color(tier)
    total = calculate_cart_total(decisions, tier)

    # Header with total
    st.markdown(f"### <span style='color: {color}'>{tier_label}</span>", unsafe_allow_html=True)
    st.metric(label="Total", value=f"${total:.2f}")

    st.divider()

    # Display each item
    for decision in decisions:
        category = decision.get("category", "Unknown")
        all_tiers = decision.get("all_tiers", {})
        tier_data = all_tiers.get(tier, {})
        recommended = decision.get("recommended_tier") == tier

        # Category header
        display_name = format_category_name(category)
        if recommended:
            st.markdown(f"**{display_name}** ⭐")
        else:
            st.markdown(f"**{display_name}**")

        # Item details
        display_tier_item(tier_data, is_recommended=recommended)
        st.markdown("---")


def display_validation_results(validation_results: list[dict]):
    """Display validation results in an evaluation panel."""
    if not validation_results:
        return

    # Calculate overall stats
    total = len(validation_results)
    passed = sum(1 for v in validation_results if v.get("is_valid", False))
    failed = total - passed

    # Show summary
    st.subheader("🔍 LLM Output Evaluation")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Decisions", total)
    with col2:
        st.metric("✅ Passed", passed)
    with col3:
        st.metric("❌ Failed", failed)

    # Show pass rate
    pass_rate = (passed / total * 100) if total > 0 else 0
    if pass_rate == 100:
        st.success(f"Pass Rate: {pass_rate:.0f}%")
    elif pass_rate >= 70:
        st.warning(f"Pass Rate: {pass_rate:.0f}%")
    else:
        st.error(f"Pass Rate: {pass_rate:.0f}%")

    # Show detailed errors
    all_errors = []
    for v in validation_results:
        if not v.get("is_valid", False):
            category = v.get("category", "Unknown")
            for error in v.get("errors", []):
                all_errors.append({"category": category, "error": error})

    if all_errors:
        with st.expander(f"⚠️ Validation Issues ({len(all_errors)})"):
            for item in all_errors:
                error_type = "🔴"
                if "hallucinated" in item["error"].lower():
                    error_type = "🟡 Hallucination"
                elif "recall" in item["error"].lower():
                    error_type = "🔴 Safety"
                elif "dirty dozen" in item["error"].lower():
                    error_type = "🟠 Health"
                elif "missing" in item["error"].lower():
                    error_type = "⚪ Structure"

                st.markdown(f"**{item['category']}** - {error_type}")
                st.caption(item["error"])
                st.markdown("---")


def display_recommendations(decisions: list, validation_results: list[dict] = None):
    """Display LLM recommendations in expanders."""
    st.subheader("💡 Recommendations")

    # Create a lookup for validation results by category
    validation_lookup = {}
    if validation_results:
        for v in validation_results:
            validation_lookup[v.get("category", "")] = v

    for decision in decisions:
        category = decision.get("category", "Unknown")
        display_name = format_category_name(category)
        recommended_tier = decision.get("recommended_tier") or "balanced"
        reasoning = decision.get("reasoning", "")
        key_trade_off = decision.get("key_trade_off", "")
        llm_used = decision.get("llm_used", False)

        # Get validation result for this decision
        validation = validation_lookup.get(category, {})
        is_valid = validation.get("is_valid", True)
        errors = validation.get("errors", [])

        tier_color = get_tier_color(recommended_tier)

        # Add validation indicator to expander title
        valid_indicator = "✅" if is_valid else "⚠️"
        with st.expander(f"{valid_indicator} {display_name}"):
            # Recommendation header
            st.markdown(
                f"**Recommended: <span style='color: {tier_color}'>{recommended_tier.upper()}</span>**",
                unsafe_allow_html=True
            )

            # Reasoning
            if reasoning:
                st.write(reasoning)

            # Key trade-off
            if key_trade_off:
                st.info(f"⚖️ **Trade-off:** {key_trade_off}")

            # Show validation errors if any
            if errors:
                st.error("**Validation Issues:**")
                for error in errors:
                    st.caption(f"• {error}")

            # LLM indicator
            if llm_used:
                st.caption("🤖 AI-powered recommendation")
            else:
                st.caption("📊 Rule-based recommendation")


def show_error_message(error_type: str, details: str = ""):
    """Display styled error message."""
    if error_type == "empty_input":
        st.warning("👋 Please enter what you're looking for above!")
    elif error_type == "no_items":
        st.error(
            "🔍 Couldn't find matching items for your request. "
            "Try being more specific, like 'miso soup ingredients' or 'strawberry spinach salad'."
        )
        if details:
            st.caption(f"Details: {details}")
    elif error_type == "api_error":
        st.error(
            "⚠️ Oops! Something went wrong getting recommendations. "
            "Please try again in a moment."
        )
        if details:
            st.caption(f"Error: {details}")
    else:
        st.error(f"An unexpected error occurred: {details}")


def main():
    """Main Streamlit application."""
    # Title
    st.title("🛒 Conscious Cart Coach")
    st.write("Turn meal plans into conscious choices")

    st.divider()

    # Input section
    col_input, col_location = st.columns([3, 1])

    with col_input:
        user_input = st.text_input(
            "What do you need?",
            placeholder="e.g., miso soup ingredients, strawberry spinach salad",
            key="user_input",
        )

    with col_location:
        # Fixed location for demo
        location = "Woodbridge Township, NJ"
        st.text_input(
            "📍 Location",
            value=location,
            disabled=True,
            key="location_display",
        )

    # Get recommendations button
    if st.button("Get Recommendations", type="primary", use_container_width=True):
        # Validate input
        if not user_input or not user_input.strip():
            show_error_message("empty_input")
            return

        with st.spinner("🔍 Finding the best options for you..."):
            try:
                # 1. Parse user input to get categories
                requested_categories = parse_user_input(user_input)

                # 2. Select best store based on inventory match
                store_key, store_info = select_best_store(requested_categories)
                store_summary = get_store_selection_summary(store_info, requested_categories)

                # Get all stores comparison
                all_stores = get_all_stores_comparison(requested_categories)

                # Display selected store and ingredient breakdown
                st.subheader("🏪 Store Selection")

                col_store, col_available, col_missing = st.columns([1, 1, 1])

                with col_store:
                    st.success(f"**{store_summary['store_name']}**")
                    st.caption(store_summary['location'])
                    st.metric(
                        "Inventory Match",
                        f"{store_summary['match_count']}/{store_summary['total_requested']}",
                        f"{store_summary['match_percentage']:.0f}%"
                    )

                with col_available:
                    st.markdown("**Available Ingredients:**")
                    if store_summary['available_categories']:
                        for cat in store_summary['available_categories']:
                            name = format_category_name(cat)
                            st.markdown(f"✅ {name}")
                    else:
                        st.caption("None")

                with col_missing:
                    st.markdown("**Missing Ingredients:**")
                    if store_summary['missing_categories']:
                        for cat in store_summary['missing_categories']:
                            name = format_category_name(cat)
                            st.markdown(f"❌ {name}")
                    else:
                        st.caption("None - all ingredients available!")

                # Show all stores comparison
                st.divider()
                st.markdown("**All Stores Comparison:**")

                for store in all_stores:
                    is_selected = store['store_name'] == store_summary['store_name']
                    match_pct = store['match_percentage']
                    missing_count = len(store['missing_categories'])

                    # Format store row
                    if is_selected:
                        prefix = "✅ "
                        style = "**"
                    else:
                        prefix = "   "
                        style = ""

                    # Build missing ingredients string
                    if store['missing_categories']:
                        missing_names = [format_category_name(c) for c in store['missing_categories']]
                        missing_str = f" — Missing: {', '.join(missing_names)}"
                    else:
                        missing_str = " — All ingredients available!"

                    st.markdown(
                        f"{prefix}{style}{store['store_name']}{style} "
                        f"({store['match_count']}/{store['total_requested']}){missing_str}"
                    )

                # 3. Generate facts_pack
                user_context = {
                    "location": location,  # For seasonal/recall filtering
                }

                facts_pack = generate_facts_pack(user_input, user_context)

                # Check if we got any items
                items = facts_pack.get("items", [])
                if not items:
                    show_error_message("no_items", f"No categories matched for: {user_input}")
                    return

                # Check for validation warnings
                warnings = facts_pack.get("validation_warnings", [])
                if warnings:
                    with st.expander("⚠️ Data Warnings"):
                        for warning in warnings:
                            st.caption(f"• {warning}")

                # Display product flags (recalls, advisories, seasonal info)
                display_product_flags(items, location)

                # 4. Get LLM decisions
                try:
                    result = decide_tiers(facts_pack)
                    decisions = result.get("decisions", [])
                except Exception as e:
                    # Fallback: create decisions without LLM
                    st.warning("AI recommendations unavailable. Showing all options.")
                    decisions = []
                    for item in items:
                        decisions.append({
                            "category": item.get("category", "unknown"),
                            "all_tiers": item.get("alternatives", {}),
                            "recommended_tier": "balanced",
                            "reasoning": "Default recommendation (AI unavailable)",
                            "llm_used": False,
                        })

                if not decisions:
                    show_error_message("no_items", "No recommendations could be generated")
                    return

                # 5. Validate LLM decisions
                validation_results = []
                for decision in decisions:
                    # Build a mini facts_pack for this decision's category
                    category = decision.get("category", "")
                    item_facts = None
                    for item in items:
                        if item.get("category") == category:
                            item_facts = item
                            break

                    if item_facts:
                        single_facts_pack = {
                            "items": [item_facts],
                            "user_context": user_context,
                        }
                        is_valid, errors = validate_decision(decision, single_facts_pack)
                        validation_results.append({
                            "category": category,
                            "is_valid": is_valid,
                            "errors": errors,
                        })

                # 6. Display results
                st.success(f"Found {len(decisions)} item(s) for your request!")

                # Display 3 carts side-by-side
                st.subheader("🛒 Your Options")

                col1, col2, col3 = st.columns(3)

                with col1:
                    display_cart_column(decisions, "cheaper", "💙 CHEAPER")

                with col2:
                    display_cart_column(decisions, "balanced", "💛 BALANCED")

                with col3:
                    display_cart_column(decisions, "conscious", "💚 CONSCIOUS")

                st.divider()

                # Show LLM reasoning with validation
                display_recommendations(decisions, validation_results)

                st.divider()

                # Show validation evaluation panel
                display_validation_results(validation_results)

                st.divider()

                # Debug mode - show raw data for evaluation
                with st.expander("🔧 Debug: Raw Data (for evaluation)"):
                    st.subheader("Store Selection")
                    st.json(store_summary)

                    st.subheader("Facts Pack Input")
                    st.json(facts_pack)

                    st.subheader("LLM Decisions Output")
                    st.json(decisions)

                    st.subheader("Validation Results")
                    st.json(validation_results)

                st.divider()

                # Store decisions in session state for customization
                st.session_state.decisions = decisions

            except Exception as e:
                show_error_message("api_error", str(e))
                st.exception(e)  # Show full traceback in development

    # Show customization section if we have decisions
    if st.session_state.get("decisions"):
        display_cart_customization(st.session_state.decisions)


if __name__ == "__main__":
    main()
