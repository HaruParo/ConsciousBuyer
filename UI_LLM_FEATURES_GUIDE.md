# UI LLM Features - Quick Start Guide

**Updated**: 2026-01-24

## Problem Solved
The LLM features were hidden because the Preferences button was disabled on initial load. This has been fixed!

---

## Where to Find AI Features

### Step 1: Open the App
```bash
cd conscious-cart-coach
./run.sh
```

### Step 2: Click ⚙️ Preferences (Top Left)
**NOW AVAILABLE IMMEDIATELY** (previously disabled until first cart created)

You'll see:
```
┌─────────────────────────────────┐
│ ⚙️ Preferences                  │
├─────────────────────────────────┤
│ Location: NJ / Mid-Atlantic     │
│ Household size: [2]             │
│ Store: [ShopRite ▼]             │
│                                 │
│ Dietary restrictions: [____]    │
│ Preferred brands: [____]        │
│ Avoided brands: [____]          │
│ ☐ Strict safety                 │
│                                 │
│ ───────────────────────────     │
│                                 │
│ 🤖 AI Features                  │ ← NEW SECTION!
│                                 │
│ ☐ Enable AI ingredient         │
│   extraction                    │
│   (~$0.01 per request)          │
│                                 │
│ ☐ Enable detailed explanations │
│   (~$0.03 per cart)             │
│                                 │
│ 💰 Cost: ~$0.045 per cart       │
│    with both features           │
└─────────────────────────────────┘
```

### Step 3: Check the Boxes
- ☑ **Enable AI ingredient extraction** - Use natural language prompts
- ☑ **Enable detailed explanations** - Get rich AI-powered reasoning

---

## What Changes in the UI

### 1. Blue Info Box Appears
When AI features are disabled, you'll see:
```
💡 Tip: Enable AI Features in ⚙️ Preferences to use natural language
       ("I want something healthy") and get detailed explanations.
```

### 2. Placeholder Text Changes
**Without AI**:
```
e.g., chicken biryani for 4, spinach salad, stir fry, tikka masala...
```

**With AI enabled**:
```
e.g., I want something healthy and seasonal, quick dinner for 2,
      budget-friendly vegetarian...
```

### 3. Ingredient Modal Shows AI Badge
When you create a cart with AI extraction:
```
╔═══════════════════════════════════════╗
║ Confirm ingredients                   ║
╠═══════════════════════════════════════╣
║ 🤖 AI extracted from your request.    ║ ← This badge appears!
║ Edit before building cart.            ║
╚═══════════════════════════════════════╝
```

### 4. Product Cards Show AI Explanations
After cart is created with AI explanations enabled:
```
┌──────────────────────────────────────┐
│ Spinach                              │
│ ⚖️ BALANCED                          │
├──────────────────────────────────────┤
│ Why: Organic recommended (EWG)       │
│                                      │
│ [🤖 Show AI explanation ▼]           │ ← Click to expand!
│                                      │
│ Earthbound Farm — Organic Baby       │
│ $3.99 · 5oz · $0.80/oz               │
└──────────────────────────────────────┘
```

When expanded:
```
┌──────────────────────────────────────┐
│ [🤖 Hide AI explanation ▲]           │
│                                      │
│ The Earthbound Farm option at $3.99 │
│ offers organic certification which   │
│ is important for spinach since it's  │
│ on the EWG Dirty Dozen list...      │
└──────────────────────────────────────┘
```

---

## Testing the Features

### Test 1: Deterministic Mode (Default)
1. **Don't enable any AI features**
2. Type: `"chicken biryani for 4"`
3. Click "Create cart"
4. **Expected**: Modal opens in <100ms, no AI badge
5. **Expected**: Product cards show short reasons only (no expanders)

---

### Test 2: AI Ingredient Extraction Only
1. Go to ⚙️ Preferences
2. Check **"Enable AI ingredient extraction"**
3. Close preferences
4. **Notice**: Placeholder text changes
5. **Notice**: Blue tip disappears
6. Type: `"I want something healthy and seasonal"`
7. Click "Create cart"
8. **Expected**:
   - Takes 1-3 seconds (spinner: "🤖 Analyzing your request...")
   - Modal shows "🤖 AI extracted from your request"
   - Ingredients like kale, sweet potato, quinoa (winter vegetables)
9. Confirm ingredients
10. **Expected**: Product cards show short reasons (no AI explanations yet)

---

### Test 3: Both AI Features (Full Experience)
1. Go to ⚙️ Preferences
2. Check both:
   - ☑ Enable AI ingredient extraction
   - ☑ Enable detailed explanations
3. **Notice**: "💰 Cost: ~$0.045 per cart with both features" appears
4. Type: `"healthy dinner for my family"`
5. Click "Create cart"
6. **Expected**:
   - Spinner: "🤖 Analyzing your request..." (1-3 sec)
   - Modal shows AI badge
   - AI-suggested ingredients
7. Confirm ingredients
8. Wait for cart to build (2-4 seconds total)
9. **Expected**: Product cards now have "🤖 Show AI explanation" expanders
10. Click an expander
11. **Expected**: Rich 1-2 sentence explanation appears

---

## Troubleshooting

### Issue: "AI features temporarily unavailable"
**Cause**: No Anthropic API key configured

**Fix**:
1. Create `.env` file in project root:
   ```bash
   cd /Users/snair/Documents/projects/ConsciousBuyer
   touch .env
   ```

2. Add your API key:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-api03-...
   ```

3. Restart the app

**Alternative**: Disable AI features (system works fine without them)

---

### Issue: "LLM module not available"
**Cause**: `anthropic` package not installed

**Fix**:
```bash
cd conscious-cart-coach
pip install anthropic>=0.18.0
```

---

### Issue: Preferences button still disabled
**Cause**: Old browser cache

**Fix**:
1. Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
2. Or restart Streamlit

---

### Issue: No AI explanation expanders appear
**Possible causes**:
1. ☐ "Enable detailed explanations" is unchecked
2. LLM API call failed (check terminal for errors)
3. You're looking at cheaper/conscious alternatives (expanders only show on recommended product)

**Fix**:
1. Verify checkbox is checked in Preferences
2. Check terminal output for errors
3. Make sure you're looking at the main recommended product (center column)

---

## File Changes Made (2026-01-24)

### Fixed: Preferences Always Available
```python
# Before (BUG):
if has_prompt:  # Only after first cart
    with st.popover("⚙️ Preferences"):
        # AI features here
else:
    st.button("⚙️ Preferences", disabled=True)  # ← Disabled!

# After (FIXED):
with st.popover("⚙️ Preferences"):  # Always available!
    # AI features here
```

### Added: Discovery Hint
```python
# New blue info box on initial screen
if not st.session_state.use_llm_extraction and not st.session_state.use_llm_explanations:
    st.info("💡 Tip: Enable AI Features in ⚙️ Preferences...")
```

### Added: Dynamic Placeholder
```python
# Changes based on LLM mode
if st.session_state.use_llm_extraction:
    placeholder = "e.g., I want something healthy and seasonal..."
else:
    placeholder = "e.g., chicken biryani for 4, spinach salad..."
```

---

## Quick Visual Checklist

**Before enabling AI** (what you should see):
- [ ] Blue info box with tip about AI features
- [ ] ⚙️ Preferences button (NOT disabled)
- [ ] Placeholder: "e.g., chicken biryani for 4..."
- [ ] AI Features section in Preferences (unchecked)

**After enabling AI extraction** (what changes):
- [ ] Blue info box disappears
- [ ] Placeholder: "e.g., I want something healthy..."
- [ ] AI badge in ingredient modal
- [ ] Longer processing time (1-3 sec)

**After enabling AI explanations** (additional changes):
- [ ] "💰 Cost" note appears in Preferences
- [ ] 🤖 expanders on product cards
- [ ] Longer processing time (3-4 sec total)
- [ ] Rich natural language explanations

---

## For Developers

### Where to Look in Code
- **UI toggles**: `conscious-cart-coach/src/ui/app.py` lines 408-426
- **AI badge in modal**: `conscious-cart-coach/src/ui/app.py` lines 212-221
- **AI explanation expanders**: `conscious-cart-coach/src/ui/components.py` lines 227-229
- **Orchestrator wiring**: `conscious-cart-coach/src/ui/app.py` lines 109-114, 141-144

### Testing Without API Key
The system gracefully degrades:
```python
# Enable AI features (no API key)
# → System tries LLM
# → Catches error
# → Falls back to templates
# → Shows warning but continues working
```

You'll see:
```
⚠️ AI features temporarily unavailable (API key not found)
Using standard ingredient matching.
```

---

## Related Documentation

- **[7-ui-flows.md](architecture/7-ui-flows.md)**: Detailed user journeys with screenshots
- **[6-llm-integration-deep-dive.md](architecture/6-llm-integration-deep-dive.md)**: How LLM is integrated
- **[3-usage-guide.md](architecture/3-usage-guide.md)**: API usage examples
- **[4-ui-expectations.md](architecture/4-ui-expectations.md)**: Before/after comparisons

---

**Last updated**: 2026-01-24
**Status**: ✅ UI bugs fixed, LLM features now discoverable
