"""
CSS styles for Conscious Cart Coach UI.

Palette (from brand guide):
- Sweet Cream: #FBF1E5 (page bg)
- Dusk: #CCD7D9 (muted blue-gray)
- Springtime: #CED8B2 (sage green)
- Clay: #DD9057 (warm accent)
- Peach: #FEDBB1 (light warm)
- Olive: #5B5120 (dark accent)

Injected via st.markdown(unsafe_allow_html=True) at page load.
"""


def get_global_css() -> str:
    """Return global CSS for the app."""
    return """
<style>
/* ═══════════════════════════════════════════════════════════════
   Page-level palette overrides
   ═══════════════════════════════════════════════════════════════ */
.stApp {
    background-color: #FBF1E5;
}

/* ═══════════════════════════════════════════════════════════════
   Text and heading colors (ensure visibility on cream background)
   Target left column specifically to avoid interfering with card styles
   ═══════════════════════════════════════════════════════════════ */
/* Headers in left column */
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child h1,
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child h2,
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child h3 {
    color: #5B5120 !important;
}

/* General markdown text in left column */
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child .stMarkdown p {
    color: #333333;
}

/* Caption text */
.stCaptionContainer, [data-testid="stCaptionContainer"] {
    color: #777777 !important;
}

/* Info/warning/success boxes - ensure visibility */
[data-testid="stAlert"] {
    background-color: #FFFFFF !important;
    border: 1px solid rgba(0, 0, 0, 0.1) !important;
}

[data-testid="stAlert"] p {
    color: #333333 !important;
}

/* Expander headers - AI explanation visibility */
[data-testid="stExpander"] summary {
    color: #5B5120 !important;
    font-weight: 600 !important;
}

[data-testid="stExpander"] [data-testid="StyledFullScreenButton"] {
    display: none !important;
}

/* ═══════════════════════════════════════════════════════════════
   All buttons: force single-line text (no wrapping)
   ═══════════════════════════════════════════════════════════════ */
.stApp button {
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
.stApp button p {
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    margin: 0 !important;
}

/* ═══════════════════════════════════════════════════════════════
   Left Column: top-level buttons left-aligned, not full-width
   (scoped to exclude buttons inside nested columns like pop_cols)
   ═══════════════════════════════════════════════════════════════ */
[data-testid="stHorizontalBlock"]:not([data-testid="stColumn"] *) > [data-testid="stColumn"]:first-child > div > [data-testid="stVerticalBlock"] > div > [data-testid="stButton"] {
    text-align: left !important;
}
[data-testid="stHorizontalBlock"]:not([data-testid="stColumn"] *) > [data-testid="stColumn"]:first-child > div > [data-testid="stVerticalBlock"] > div > [data-testid="stButton"] > button {
    width: auto !important;
    display: inline-flex !important;
    padding: 8px 20px !important;
}

/* ═══════════════════════════════════════════════════════════════
   Left Column: Popover pill buttons (fill column evenly)
   ═══════════════════════════════════════════════════════════════ */
[data-testid="stColumn"]:first-child [data-testid="stPopover"] > div > button,
[data-testid="stColumn"]:first-child [data-testid="stPopover"] button {
    white-space: nowrap !important;
    height: 38px !important;
    min-height: 38px !important;
    max-height: 38px !important;
    padding: 0 18px !important;
    border: 1px solid rgba(0, 0, 0, 0.14) !important;
    border-radius: 999px !important;
    background: #ffffff !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    line-height: 1 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100% !important;
    overflow: hidden !important;
    box-shadow: none !important;
}
[data-testid="stColumn"]:first-child [data-testid="stPopover"] > div > button:hover,
[data-testid="stColumn"]:first-child [data-testid="stPopover"] button:hover {
    border-color: rgba(0, 0, 0, 0.28) !important;
    background: #fafafa !important;
}
[data-testid="stColumn"]:first-child [data-testid="stPopover"] > div > button p,
[data-testid="stColumn"]:first-child [data-testid="stPopover"] button p {
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    margin: 0 !important;
}
[data-testid="stColumn"]:first-child [data-testid="stPopover"] {
    display: block !important;
}

/* ═══════════════════════════════════════════════════════════════
   Cart Shell: right column = viewport-height flex container
   (top-level only — exclude columns nested inside another column)
   ═══════════════════════════════════════════════════════════════ */
[data-testid="stHorizontalBlock"]:not([data-testid="stColumn"] *) > [data-testid="stColumn"]:last-child {
    height: calc(100vh - 80px);
    overflow: hidden;
    position: sticky;
    top: 1rem;
    background: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.14);
    border-radius: 16px;
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.10);
    padding: 18px;
}

/* Inner block: flex column filling the cart shell */
[data-testid="stHorizontalBlock"]:not([data-testid="stColumn"] *) > [data-testid="stColumn"]:last-child > div {
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
}

[data-testid="stHorizontalBlock"]:not([data-testid="stColumn"] *) > [data-testid="stColumn"]:last-child > div > [data-testid="stVerticalBlock"] {
    display: flex !important;
    flex-direction: column !important;
    height: 100% !important;
    gap: 0 !important;
}

/* Header elements: fixed height, don't grow */
[data-testid="stHorizontalBlock"]:not([data-testid="stColumn"] *) > [data-testid="stColumn"]:last-child > div > [data-testid="stVerticalBlock"] > div {
    flex: 0 0 auto !important;
}

/* ═══════════════════════════════════════════════════════════════
   Scroll Zone: the height-constrained container fills remaining space
   (targets the element-container holding the st.container(height=400))
   ═══════════════════════════════════════════════════════════════ */
[data-testid="stHorizontalBlock"]:not([data-testid="stColumn"] *) > [data-testid="stColumn"]:last-child > div > [data-testid="stVerticalBlock"] > div:has(> div > [data-testid="stVerticalBlock"]) {
    flex: 1 1 auto !important;
    min-height: 0 !important;
    overflow: hidden !important;
}

/* The scroll container itself: fill parent, scroll content */
[data-testid="stHorizontalBlock"]:not([data-testid="stColumn"] *) > [data-testid="stColumn"]:last-child > div > [data-testid="stVerticalBlock"] > div > div > [data-testid="stVerticalBlock"] {
    overflow-y: auto !important;
    height: 100% !important;
    padding-bottom: 90px;
}

/* ═══════════════════════════════════════════════════════════════
   Footer Zone: fixed at bottom, border separator
   ═══════════════════════════════════════════════════════════════ */
[data-testid="stHorizontalBlock"]:not([data-testid="stColumn"] *) > [data-testid="stColumn"]:last-child > div > [data-testid="stVerticalBlock"] > div:last-child {
    flex: 0 0 auto !important;
    padding: 6px 0;
    background: #ffffff;
}

/* Remove default border/padding from scroll zone wrapper if Streamlit adds it */
[data-testid="stHorizontalBlock"]:not([data-testid="stColumn"] *) > [data-testid="stColumn"]:last-child > div > [data-testid="stVerticalBlock"] > div:has(> div > [data-testid="stVerticalBlock"]) > div {
    height: 100% !important;
    max-height: 100% !important;
    border: none !important;
    box-shadow: none !important;
    border-radius: 0 !important;
    background: transparent !important;
    padding: 0 !important;
}

/* ═══════════════════════════════════════════════════════════════
   Cart header
   ═══════════════════════════════════════════════════════════════ */
.cart-header h3 {
    color: #5B5120;
    font-size: 1.4rem;
    margin-bottom: 0.15rem;
    font-weight: 700;
}
.cart-subtitle {
    font-size: 0.85rem;
    color: #777;
    margin-bottom: 0.5rem;
}
.cart-warning {
    display: inline-block;
    font-size: 0.75rem;
    color: #DD9057;
    background: #FEDBB1;
    padding: 3px 10px;
    border-radius: 10px;
    font-weight: 600;
    margin-bottom: 0.5rem;
}
.cart-total {
    font-size: 1.1rem;
    font-weight: 700;
    color: #5B5120;
    margin: 0.5rem 0;
}

/* ═══════════════════════════════════════════════════════════════
   Empty state (inside cart panel)
   ═══════════════════════════════════════════════════════════════ */
.empty-hint {
    background: #f6f6f6;
    border: 1px dashed rgba(0, 0, 0, 0.18);
    border-radius: 12px;
    padding: 14px;
    color: rgba(0, 0, 0, 0.60);
    font-size: 0.88rem;
    margin-top: 1rem;
}

/* ═══════════════════════════════════════════════════════════════
   Tier pill badges (palette-based) - used in switcher
   ═══════════════════════════════════════════════════════════════ */
.tier-pill {
    display: inline-block;
    font-size: 0.75rem;
    padding: 2px 10px;
    border-radius: 12px;
    font-weight: 600;
    white-space: nowrap;
    vertical-align: middle;
}
.tier-pill-cheaper {
    background: #CED8B2;
    color: #5B5120;
}
.tier-pill-balanced {
    background: #CCD7D9;
    color: #3a4a50;
}
.tier-pill-conscious {
    background: #FEDBB1;
    color: #9a5a20;
}

/* ═══════════════════════════════════════════════════════════════
   Card layout lines
   ═══════════════════════════════════════════════════════════════ */
.card-why {
    font-size: 0.82rem;
    color: #5B5120;
    margin: 2px 0 4px 0;
    opacity: 0.85;
}
.card-why i {
    font-style: italic;
}

.card-product {
    font-size: 0.84rem;
    color: #444;
    margin: 2px 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.card-price {
    font-size: 0.85rem;
    font-weight: 600;
    color: #5B5120;
    margin: 2px 0;
}

.card-meta {
    font-size: 0.73rem;
    color: #888;
    margin: 2px 0;
}

/* ═══════════════════════════════════════════════════════════════
   Cart-wide switcher
   ═══════════════════════════════════════════════════════════════ */
[data-testid="stHorizontalBlock"]:not([data-testid="stColumn"] *) > [data-testid="stColumn"]:last-child button {
    font-size: 0.78rem !important;
    padding: 6px 12px !important;
}
.switcher-helper {
    font-size: 0.75rem;
    color: #999;
    margin-top: 4px;
    margin-bottom: 8px;
}

/* ═══════════════════════════════════════════════════════════════
   Safety / recall badges
   ═══════════════════════════════════════════════════════════════ */
.safety-badge {
    font-size: 0.73rem;
    color: #DD9057;
    background: #FEDBB1;
    padding: 2px 8px;
    border-radius: 8px;
    display: inline-block;
    margin: 1px 2px;
}

/* ═══════════════════════════════════════════════════════════════
   Ingredient modal overlay styling
   (applied to @st.dialog content)
   ═══════════════════════════════════════════════════════════════ */
.modal-header {
    margin-bottom: 0.75rem;
}
.modal-header h3 {
    color: #5B5120;
    margin-bottom: 0.15rem;
}
.modal-subtext {
    font-size: 0.85rem;
    color: #777;
    margin-bottom: 0.75rem;
}
.modal-store-info {
    font-size: 0.82rem;
    color: #5B5120;
    background: #FBF1E5;
    padding: 8px 12px;
    border-radius: 8px;
    margin-bottom: 0.75rem;
}
.modal-availability {
    font-size: 0.8rem;
    margin-bottom: 0.5rem;
}
.modal-availability .avail-ok {
    color: #5B5120;
    font-weight: 600;
}
.modal-availability .avail-warn {
    color: #DD9057;
    font-weight: 600;
}
.modal-safety-callout {
    font-size: 0.78rem;
    color: #DD9057;
    background: #FEDBB1;
    padding: 6px 10px;
    border-radius: 8px;
    margin-bottom: 0.75rem;
}

/* ═══════════════════════════════════════════════════════════════
   Qty control on cards
   ═══════════════════════════════════════════════════════════════ */
.qty-row {
    font-size: 0.78rem;
    color: #666;
    margin-top: 4px;
}

/* ═══════════════════════════════════════════════════════════════
   CTA helper text
   ═══════════════════════════════════════════════════════════════ */
.cta-helper {
    font-size: 0.78rem;
    color: #999;
    margin-top: 4px;
    margin-bottom: 16px;
}

/* ═══════════════════════════════════════════════════════════════
   Ethical tooltip wrapper
   ═══════════════════════════════════════════════════════════════ */
.ethical-tip {
    cursor: help;
    border-bottom: 1px dotted #999;
}
</style>
"""
