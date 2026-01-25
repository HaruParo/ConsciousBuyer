# Troubleshooting Guide: Common Issues & Solutions

**Last Updated**: 2026-01-24

This guide consolidates all troubleshooting information for Conscious Cart Coach, including environment setup, LLM integration, testing, and Opik tracking issues.

---

## Quick Navigation

- [Environment Setup Issues](#environment-setup-issues)
- [LLM Integration Issues](#llm-integration-issues)
- [Testing Issues](#testing-issues)
- [Opik Tracking Issues](#opik-tracking-issues)
- [UI Issues](#ui-issues)
- [Deployment Issues](#deployment-issues)

---

## Environment Setup Issues

### Issue: ANTHROPIC_API_KEY Not Found

**Symptoms**:
```
pytest.skip: ANTHROPIC_API_KEY not found. Skipping LLM tests.
```
or
```
WARNING: ANTHROPIC_API_KEY not found in environment
```

**Root Cause**: Environment variables not loaded from `.env` file

**Solutions**:

**Solution 1: Verify .env File Exists**
```bash
# Check file exists
ls -la conscious-cart-coach/.env

# Should show:
# -rw-r--r-- 1 user user 234 Jan 24 14:32 .env
```

**Solution 2: Check .env File Contents**
```bash
cat conscious-cart-coach/.env
```

Should contain:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-your_actual_key_here
OPIK_API_KEY=your_opik_key
OPIK_WORKSPACE=chat
OPIK_PROJECT_NAME=consciousbuyer
```

**Solution 3: Install python-dotenv**
```bash
pip install python-dotenv
```

**Solution 4: Manual Environment Loading** (temporary workaround)
```bash
# Load environment manually
export $(cat conscious-cart-coach/.env | xargs)

# Verify
echo $ANTHROPIC_API_KEY  # Should show your key

# Then run app/tests
streamlit run conscious-cart-coach/src/ui/app.py
```

**Solution 5: Run Environment Verification**
```bash
cd conscious-cart-coach
pytest tests/test_env_loading.py -v -s
```

Expected output:
```
✅ .env file exists
✅ ANTHROPIC_API_KEY loaded: sk-ant-api03-...
✅ OPIK_API_KEY loaded: SsQ3gVmM8r...
✅ Ready to run LLM tests!
```

---

### Issue: Wrong .env File Path

**Symptoms**: Variables not loading even though .env file exists

**Root Cause**: .env file in wrong directory

**Solution**:

```bash
# Correct path (inside conscious-cart-coach)
conscious-cart-coach/.env  ✅

# Wrong paths
.env                       ❌ (too high)
src/.env                   ❌ (too deep)
```

**Fix**:
```bash
# Move to correct location
mv .env conscious-cart-coach/.env

# Or copy template
cp conscious-cart-coach/.env.example conscious-cart-coach/.env
# Then edit with your API keys
```

---

### Issue: Pydantic Compatibility Warning

**Symptoms**:
```
UserWarning: Core Pydantic V1 functionality isn't compatible with Python 3.14
```

**Root Cause**: Opik dependency using older Pydantic version

**Impact**: Just a warning, doesn't affect functionality

**Solutions**:

**Solution 1: Ignore** (recommended)
- This is a dependency warning, not an error
- App works fine despite warning
- Will be fixed when Opik updates

**Solution 2: Suppress Warning**
```bash
# Add to environment
export PYTHONWARNINGS="ignore::UserWarning"
```

**Solution 3: Downgrade Python** (not recommended)
```bash
# Use Python 3.11 instead of 3.14
pyenv install 3.11
pyenv local 3.11
```

---

## LLM Integration Issues

### Issue: LLM Calls Failing

**Symptoms**:
```
Failed to initialize Anthropic client: <error>
All 2 Claude API attempts failed
```

**Common Causes**:

**1. Invalid API Key**

**Check**:
```bash
echo $ANTHROPIC_API_KEY
# Should start with: sk-ant-api03-
```

**Fix**:
```bash
# Get new key from https://console.anthropic.com/settings/keys
# Update .env
echo "ANTHROPIC_API_KEY=sk-ant-api03-your_new_key" > conscious-cart-coach/.env
```

**2. Rate Limit Exceeded**

**Check**: Anthropic dashboard → Usage

**Fix**:
- Wait a few minutes
- Reduce request frequency
- Upgrade API tier

**3. Network Issues**

**Check**:
```bash
curl https://api.anthropic.com/v1/messages
# Should return 401 (unauthorized) not timeout
```

**Fix**:
- Check internet connection
- Try different network
- Check firewall settings

**4. API Timeout**

**Check logs**:
```
API timeout on attempt 1: <timeout error>
```

**Fix**: Increase timeout in `client.py`:
```python
API_TIMEOUT = 60.0  # Increase from 30.0
```

---

### Issue: LLM Returns Non-JSON

**Symptoms**:
```
Failed to parse ingredient JSON: <parse error>
```

**Root Cause**: LLM returned text instead of valid JSON

**Solutions**:

**Solution 1: Check Prompt**
- Verify prompt explicitly requests JSON
- Check for "JSON only, no markdown" instruction

**Solution 2: Add JSON Validation**
```python
import json

try:
    data = json.loads(response)
except json.JSONDecodeError:
    # Strip markdown if present
    if response.startswith("```json"):
        response = response.split("```json")[1].split("```")[0]
        data = json.loads(response)
```

**Solution 3: Increase Temperature Tolerance**
```python
# In extractor, change from temp=0.0 to:
temperature=0.1  # Slightly more flexible
```

---

### Issue: Hallucinated Ingredients

**Symptoms**: LLM suggests ingredients not in user's prompt

**Root Cause**: Vague prompts lead to LLM assumptions

**Solutions**:

**Solution 1: Clearer Prompts**
```python
# Vague (leads to hallucinations)
"dinner"

# Better
"chicken biryani for 4 people"

# Best
"chicken biryani, 4 servings: 2 cups rice, 1 lb chicken, onions, spices"
```

**Solution 2: Add Validation**
```python
# In ingredient_extractor.py
if len(ingredients) > 15:
    logger.warning("Too many ingredients extracted, may contain hallucinations")
```

**Solution 3: User Review**
- Ingredient modal allows users to edit
- Users can remove hallucinated items
- This is by design!

---

## Testing Issues

### Issue: Tests Skipping with "ANTHROPIC_API_KEY not found"

**Symptoms**:
```bash
pytest -m llm
# All tests show: SKIPPED (ANTHROPIC_API_KEY not found)
```

**Root Cause**: Environment not loading in pytest

**Solution**: See [Environment Setup Issues](#issue-anthropic_api_key-not-found) above

**Quick Fix**:
```bash
# 1. Verify conftest.py auto-loads .env
cat conscious-cart-coach/tests/conftest.py | grep load_dotenv

# 2. Run environment test
pytest tests/test_env_loading.py -v -s

# 3. If still failing, load manually
export $(cat conscious-cart-coach/.env | xargs)
pytest -m llm -v
```

---

### Issue: Tests Failing with Timeout

**Symptoms**:
```
test_extract_simple_recipe FAILED
APITimeoutError: Request timed out
```

**Root Cause**: LLM calls taking too long

**Solutions**:

**Solution 1: Increase Timeout**
```bash
# Run with custom timeout
pytest -m llm --timeout=300
```

**Solution 2: Skip Slow Tests**
```bash
# Skip performance tests
pytest -m "llm and not slow"
```

**Solution 3: Check Network**
```bash
# Test Anthropic API directly
curl -X POST https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "content-type: application/json" \
  -d '{"model":"claude-sonnet-4-20250514","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}'
```

---

### Issue: Test Costs Too High

**Symptoms**: Spending too much on test runs

**Solutions**:

**Solution 1: Run Fewer Tests**
```bash
# Run only specific test
pytest tests/test_llm.py::TestIngredientExtraction::test_extract_simple_recipe

# Run only fast tests
pytest -m "llm and not slow"
```

**Solution 2: Use Mocks for Development**
```python
# In conftest.py, add:
@pytest.fixture
def mock_anthropic_client(monkeypatch):
    # Mock LLM responses for free testing
    pass
```

**Solution 3: Set Daily Budget**
- Anthropic dashboard → Usage limits
- Set $1/day limit during development
- Tests will fail if limit exceeded (better than surprise bills!)

---

## Opik Tracking Issues

### Issue: No Traces Appearing in Opik

**Symptoms**: Opik dashboard shows no traces after running app/tests

**Common Causes & Solutions**:

**1. Opik Not Installed**

**Check**:
```bash
pip list | grep opik
```

**Fix**:
```bash
pip install opik>=0.1.0
```

**2. OPIK_API_KEY Not Set**

**Check**:
```bash
echo $OPIK_API_KEY
```

**Fix**:
```bash
# Add to .env
echo "OPIK_API_KEY=your_key" >> conscious-cart-coach/.env

# Reload environment
export $(cat conscious-cart-coach/.env | xargs)
```

**3. Wrong Project Name**

**Check**: Opik dashboard → Projects

**Fix**:
```bash
# Set correct project name
export OPIK_PROJECT_NAME=consciousbuyer
```

**4. LLM Features Not Enabled**

**Check**: In Streamlit UI → ⚙️ Preferences

**Fix**:
- Enable "AI ingredient extraction" OR
- Enable "Detailed explanations"
- Create a cart
- Check Opik dashboard

**5. Network Blocking Opik**

**Check**:
```bash
curl https://api.comet.com/opik/v1/health
```

**Fix**:
- Check firewall settings
- Try different network
- Use local Opik instance (see below)

---

### Issue: Want to Use Local Opik Instead of Cloud

**Solution**: Run Opik locally with Docker

```bash
# Start local Opik server
docker run -d \
  -p 5000:5000 \
  --name opik-local \
  comet-opik/opik:latest

# Configure app to use local instance
export OPIK_URL_OVERRIDE=http://localhost:5000

# Restart app
streamlit run conscious-cart-coach/src/ui/app.py

# View traces at http://localhost:5000
```

---

### Issue: Not Seeing Conversation "Threads"

**Symptoms**: Each LLM call appears as separate trace, not grouped

**Root Cause**: This is **expected behavior**

**Explanation**:

Our current implementation uses `track_anthropic()` which tracks individual API calls, not conversation threads.

**What you'll see**:
```
Trace 1: ingredient_extraction
Trace 2: decision_explanation
Trace 3: decision_explanation
```

Each trace is independent. **This is correct!**

**Why not threads?**:
- Current setup is simpler
- Easier to search by operation type
- Sufficient for cost tracking and debugging

**Want threads anyway?**:

See detailed implementation guide in [9-opik-llm-evaluation.md](9-opik-llm-evaluation.md#pytest-integration) section on thread tracking.

**TL;DR**: You'd need to add `@opik.track()` decorator with session IDs. Current setup is fine for 99% of use cases.

---

## UI Issues

### Issue: Streamlit Duplicate Element Key Error

**Symptoms**:
```
StreamlitDuplicateElementKey: There are multiple elements with the same key='...'
```

**Root Cause**: Widget registered twice with same key

**Solutions**:

**Solution 1: Use Unique Keys**
```python
# Bad
st.text_area("Input", key="input")
st.text_area("Output", key="input")  # ❌ Duplicate!

# Good
st.text_area("Input", key="user_input")
st.text_area("Output", key="llm_output")
```

**Solution 2: Use Session State Directly**
```python
# Bad (manual syncing causes duplication)
user_input = st.text_area("Input", key="temp_input")
st.session_state.user_input = user_input  # ❌

# Good (auto-sync)
st.text_area("Input", key="user_input")  # ✅
# Streamlit auto-syncs to st.session_state.user_input
```

**Solution 3: Check for Conditional Rendering**
```python
# Bad (key persists across renders)
if condition:
    st.button("Click", key="my_button")
if other_condition:
    st.button("Click", key="my_button")  # ❌ Duplicate!

# Good (unique keys)
if condition:
    st.button("Click", key="button_condition_1")
if other_condition:
    st.button("Click", key="button_condition_2")
```

---

### Issue: LLM Features Not Showing in UI

**Symptoms**: Can't find AI toggles in Preferences

**Solutions**:

**Solution 1: Check Preferences Popover**
- Look for ⚙️ icon in top-right
- Click it
- Scroll to "🤖 AI Features" section

**Solution 2: Verify Session State**
```python
# In Streamlit debug mode
st.write(st.session_state.use_llm_extraction)
st.write(st.session_state.use_llm_explanations)
```

**Solution 3: Clear Browser Cache**
```bash
# Streamlit caches UI state
# Clear cache:
# - In browser: Ctrl+Shift+R (hard reload)
# - Or: streamlit cache clear
```

---

### Issue: AI Explanation Not Appearing

**Symptoms**: LLM explanations enabled but not showing in cart

**Causes & Solutions**:

**1. LLM Toggle Disabled**

**Check**: ⚙️ Preferences → "Enable detailed explanations"

**Fix**: Turn it on!

**2. API Key Not Set**

**Check**: Terminal logs for warnings

**Fix**: Set ANTHROPIC_API_KEY in .env

**3. LLM Call Failed**

**Check**: Terminal logs for errors

**Fix**:
```bash
# Check logs
streamlit run src/ui/app.py 2>&1 | grep -i error

# Look for:
# - "Failed to initialize Anthropic client"
# - "API error"
# - "Timeout"
```

**4. Only Shows for Recommended Product**

**By Design**: Explanation only appears for the recommended tier (Balanced)

**Fix**: This is intentional! We only explain the recommendation, not alternatives.

---

## Deployment Issues

### Issue: Streamlit Cloud Deployment Fails

**Symptoms**: Build errors or runtime errors after deployment

**Common Causes & Solutions**:

**1. Missing Dependencies**

**Symptom**:
```
ModuleNotFoundError: No module named 'opik'
```

**Fix**:
```bash
# Ensure all packages in requirements.txt
cat conscious-cart-coach/requirements.txt

# Should include:
# anthropic>=0.18.0
# opik>=0.1.0
# python-dotenv>=1.0.0
```

**2. Wrong Main File Path**

**Symptom**: "Could not find main file"

**Fix**: In Streamlit Cloud dashboard:
- Main file path: `conscious-cart-coach/src/ui/app.py`
- NOT: `src/ui/app.py` or `app.py`

**3. Secrets Not Set**

**Symptom**: App runs but features don't work

**Fix**: In Streamlit Cloud → Settings → Secrets:
```toml
ANTHROPIC_API_KEY = "sk-ant-api03-your_key"
OPIK_API_KEY = "your_opik_key"
OPIK_WORKSPACE = "chat"
OPIK_PROJECT_NAME = "consciousbuyer"
```

**4. Python Version Mismatch**

**Symptom**: Build fails with "unsupported Python version"

**Fix**: Add `.streamlit/config.toml`:
```toml
[server]
pythonVersion = "3.11"
```

---

### Issue: Vercel Deployment Fails

**Symptoms**: Serverless function timeout, WebSocket errors

**Root Cause**: Vercel doesn't support Streamlit well

**Solution**: **Don't use Vercel for Streamlit apps!**

Use instead:
- ✅ Streamlit Cloud (recommended)
- ✅ Render
- ✅ Railway
- ✅ Google Cloud Run (Docker)

See [10-deployment-guide.md](10-deployment-guide.md) for full deployment instructions.

---

### Issue: Database Locked in Production

**Symptoms**:
```
sqlite3.OperationalError: database is locked
```

**Root Cause**: SQLite doesn't handle concurrent users well

**Solutions**:

**Solution 1: Use PostgreSQL** (recommended for production)

```python
# Update database.py
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///conscious_cart.db"  # Fallback
)
engine = create_engine(DATABASE_URL)
```

Deploy with PostgreSQL:
```bash
# Render: Adds PostgreSQL automatically
# Railway: railway add postgres
# Heroku: heroku addons:create heroku-postgresql
```

**Solution 2: File Locking** (temporary fix)
```python
# In database.py
from sqlalchemy.pool import NullPool

engine = create_engine(
    "sqlite:///conscious_cart.db",
    poolclass=NullPool,  # Disable connection pooling
    connect_args={"check_same_thread": False}
)
```

---

## Performance Issues

### Issue: Slow LLM Response Times

**Symptoms**: LLM calls taking >5 seconds

**Solutions**:

**1. Reduce max_tokens**
```python
# In ingredient_extractor.py
max_tokens=1024  # Down from 2048
```

**2. Use Faster Model** (if available)
```python
# In client.py
MODEL = "claude-haiku-3"  # Faster, cheaper
# Instead of: "claude-sonnet-4-20250514"
```

**3. Cache Common Prompts**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def extract_ingredients_cached(prompt: str):
    # Caches results for repeated prompts
    return extract_ingredients_with_llm(...)
```

**4. Check Network**
```bash
# Test latency to Anthropic API
time curl https://api.anthropic.com/v1/messages
```

---

### Issue: High API Costs

**Symptoms**: Anthropic bill higher than expected

**Solutions**:

**1. Review Opik Dashboard**
- Sort by cost (descending)
- Identify expensive calls
- Optimize prompts

**2. Reduce Token Usage**
```python
# Shorter prompts
# Lower max_tokens
# Remove unnecessary context
```

**3. Set API Limits**
- Anthropic dashboard → Usage limits
- Daily/monthly caps
- Email alerts

**4. Disable LLM by Default**
```python
# In UI, default to LLM off
use_llm_extraction = False  # Default
use_llm_explanations = False  # Default
```

---

## Debug Mode & Logging

### Enable Debug Logging

**For App**:
```bash
# Run with debug mode
streamlit run src/ui/app.py --logger.level=debug
```

**For Tests**:
```bash
# Verbose pytest
pytest -m llm -vv --log-cli-level=DEBUG
```

**In Code**:
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Detailed debug info")
logger.info("General info")
logger.warning("Warning message")
logger.error("Error occurred")
```

---

## Getting Help

### Check These First

1. **Architecture docs**: [architecture/README.md](README.md)
2. **Implementation guide**: [11-implementation-changelog.md](11-implementation-changelog.md)
3. **Deployment guide**: [10-deployment-guide.md](10-deployment-guide.md)
4. **Opik details**: [9-opik-llm-evaluation.md](9-opik-llm-evaluation.md)

### Still Stuck?

1. **Check logs**: Terminal output has detailed error messages
2. **Run diagnostic**: `pytest tests/test_env_loading.py -v -s`
3. **Verify environment**: All required variables set
4. **Test minimal example**: Single LLM call in isolation
5. **Review Opik traces**: See exact prompts/responses that failed

### Report Issues

When reporting issues, include:
- ✅ Error message (full traceback)
- ✅ Environment (OS, Python version)
- ✅ Configuration (.env variables - **hide API keys!**)
- ✅ Steps to reproduce
- ✅ Expected vs actual behavior

---

**Last updated**: 2026-01-24
**Status**: ✅ Comprehensive troubleshooting coverage
**Most common issue**: ANTHROPIC_API_KEY not loading → **Solution**: Run `pytest tests/test_env_loading.py -v -s`
