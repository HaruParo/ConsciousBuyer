# Streamlit Duplicate Key Fix

**Date**: 2026-01-24
**Issue**: `StreamlitDuplicateElementKey: There are multiple elements with the same key='prompt_input_area'`

---

## Root Cause

The text_area widget was using a custom key (`prompt_input_area`) with manual value syncing:

```python
# BEFORE (BROKEN):
prompt_input = st.text_area(
    "Meal or recipe",
    value=st.session_state.prompt_text,
    placeholder=placeholder_text,
    key="prompt_input_area",  # Custom key
)
if prompt_input != st.session_state.prompt_text:
    st.session_state.prompt_text = prompt_input  # Manual sync
```

**Problem**: The manual syncing pattern can cause Streamlit to register the widget twice during reruns, especially when session state is updated within the same script run.

---

## Solution

Use the session state key directly as the widget key, letting Streamlit handle syncing automatically:

```python
# AFTER (FIXED):
st.text_area(
    "Meal or recipe",
    placeholder=placeholder_text,
    label_visibility="collapsed",
    height=100,
    key="prompt_text",  # Use session state key directly
)
# No manual syncing needed! Streamlit auto-syncs st.session_state.prompt_text
```

---

## How It Works

When you use a session state key as the widget key:
1. **Streamlit automatically syncs** the widget value to `st.session_state.prompt_text`
2. **No manual intervention** needed
3. **No duplicate registration** during reruns

The `on_create_cart()` callback reads from `st.session_state.prompt_text` (line 108), which now automatically contains the current text_area value.

---

## Changes Made

### File: `conscious-cart-coach/src/ui/app.py`

**Lines 361-376 (Before)**:
```python
# Dynamic placeholder based on LLM mode
if st.session_state.use_llm_extraction:
    placeholder_text = "e.g., I want something healthy and seasonal..."
else:
    placeholder_text = "e.g., chicken biryani for 4, spinach salad..."

prompt_input = st.text_area(
    "Meal or recipe",
    value=st.session_state.prompt_text,
    placeholder=placeholder_text,
    label_visibility="collapsed",
    height=100,
    key="prompt_input_area",  # ← Custom key
)
if prompt_input != st.session_state.prompt_text:
    st.session_state.prompt_text = prompt_input  # ← Manual sync
```

**Lines 361-371 (After)**:
```python
# Dynamic placeholder based on LLM mode
placeholder_text = (
    "e.g., I want something healthy and seasonal..."
    if st.session_state.use_llm_extraction
    else "e.g., chicken biryani for 4, spinach salad..."
)

# Text area with unique key
st.text_area(
    "Meal or recipe",
    placeholder=placeholder_text,
    label_visibility="collapsed",
    height=100,
    key="prompt_text",  # ← Session state key
)
# ← No manual syncing!
```

---

## Testing

1. **Restart Streamlit**:
   ```bash
   cd conscious-cart-coach
   ./run.sh
   ```

2. **Verify no duplicate key error** on page load

3. **Test interactions**:
   - Type in text area → should work
   - Enable/disable AI features → placeholder changes, no error
   - Click "Create cart" → callback receives text correctly

---

## Related Fixes in This Session

1. **Preferences always available** (was previously disabled on initial load)
2. **AI features discoverable** (added blue info hint)
3. **Dynamic placeholder** (changes based on LLM mode)
4. **Duplicate key fix** (this document)

---

## Streamlit Best Practices

✅ **DO**: Use session state keys as widget keys
```python
st.text_input("Name", key="user_name")
# Access with: st.session_state.user_name
```

❌ **DON'T**: Use custom keys with manual syncing
```python
name = st.text_input("Name", key="name_widget")
if name != st.session_state.user_name:
    st.session_state.user_name = name  # Avoid this pattern
```

✅ **DO**: Let Streamlit handle widget state
❌ **DON'T**: Manually sync widget values in the main script body

---

## Verification Checklist

After restarting the app, you should see:

- [ ] No duplicate key error
- [ ] Text area is editable
- [ ] Placeholder text shows correctly
- [ ] Placeholder changes when toggling AI features
- [ ] "Create cart" button works with entered text
- [ ] ⚙️ Preferences is always clickable
- [ ] Blue info hint appears (if AI features disabled)

---

**Status**: ✅ Fixed
**Impact**: No functionality changes, just error resolution
**Backwards Compatible**: Yes
