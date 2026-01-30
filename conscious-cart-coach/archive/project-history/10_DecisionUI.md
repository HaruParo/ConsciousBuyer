Create src/ui/app.py with Streamlit interface.

Layout:

# Title
st.title("🛒 Conscious Cart Coach")
st.write("Turn meal plans into conscious choices")

# Input
user_input = st.text_input("What do you need?", placeholder="e.g., miso soup ingredients")

# Priority sliders
col1, col2, col3 = st.columns(3)
with col1:
    budget = st.select_slider("Budget Priority", ["Low", "Medium", "High"])
with col2:
    health = st.select_slider("Health Priority", ["Low", "Medium", "High"])
with col3:
    packaging = st.select_slider("Packaging Priority", ["Low", "Medium", "High"])

if st.button("Get Recommendations"):
    with st.spinner("Thinking..."):
        # 1. Generate facts_pack
        facts_pack = generate_facts_pack(user_input, {
            "budget": budget.lower(),
            "health": health.lower(),
            "packaging": packaging.lower()
        })
        
        # 2. Get LLM decisions
        decisions = decide_tiers(facts_pack)
        
        # 3. Display 3 carts side-by-side
        st.subheader("Your Options")
        
        col1, col2, col3 = st.columns(3)
        
        # Build each cart
        cheaper_total = 0
        balanced_total = 0
        conscious_total = 0
        
        for item in decisions['items']:
            cheaper_total += item['tiers']['cheaper']['price']
            balanced_total += item['tiers']['balanced']['price']
            conscious_total += item['tiers']['conscious']['price']
        
        # Display carts
        with col1:
            st.metric("CHEAPER", f"${cheaper_total:.2f}")
            for item in decisions['items']:
                st.markdown(f"**{item['category']}**")
                st.write(f"{item['tiers']['cheaper']['brand']}")
                st.caption(f"${item['tiers']['cheaper']['price']}")
        
        # ... similar for balanced and conscious
        
        # Show LLM reasoning for recommended tier
        st.subheader("💡 Recommendation")
        for item in decisions['items']:
            with st.expander(f"{item['category']}"):
                st.write(f"**Recommended: {item['recommended_tier'].upper()}**")
                st.write(item['reasoning'])
                
                # Show chips
                st.markdown(" ".join([
                    f"`{tag}`" for tag in item.get('tags', [])
                ]))

Styling:
- Use st.set_page_config for wide layout
- Add custom CSS for tier cards
- Color-code tiers: blue=cheaper, yellow=balanced, green=conscious
- Make recommended tier stand out

Error handling:
- Unknown ingredients -> show message
- API errors -> retry or show fallback
- Empty input -> prompt user


---------------


Enhance src/ui/app.py to allow swapping items within tiers.

After displaying carts, add:

st.subheader("🔄 Customize Your Cart")

for item in decisions['items']:
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.write(f"**{item['category']}**")
    
    with col2:
        # Let user choose tier
        selected_tier = st.selectbox(
            f"Tier for {item['category']}",
            ["cheaper", "balanced", "conscious"],
            index=1,  # default to balanced
            key=f"tier_{item['category']}"
        )
    
    with col3:
        # If alternatives exist within tier, show dropdown
        if len(item['tiers'][selected_tier].get('alternatives', [])) > 0:
            selected_option = st.selectbox(
                "Option",
                item['tiers'][selected_tier]['alternatives'],
                key=f"option_{item['category']}"
            )

# Recalculate totals based on selections
final_cart = build_cart_from_selections(st.session_state)

st.subheader("Final Cart")
st.metric("Total", f"${final_cart['total']:.2f}")

# Lock button
if st.button("🔒 Lock Plan"):
    # Save to session/database
    save_decision(final_cart)
    
    # Offer download
    csv_data = generate_csv(final_cart)
    st.download_button(
        "Download Shopping List",
        csv_data,
        "shopping_list.csv",
        "text/csv"
    )
    
    st.success("Plan locked! Scroll down for download.")

Add helper functions for cart management
