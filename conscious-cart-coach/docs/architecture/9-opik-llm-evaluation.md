# Opik LLM Evaluation: Watching the Watcher

**Updated**: 2026-01-29
**Current Version**: React + FastAPI Full-Stack (v2.0)

---

## The Black Box Problem: A True Story

It's 2:47 AM. You're debugging why the LLM extracted "2 cups of salt" from a user prompt that said "healthy dinner for 2."

You check the logs:
```
INFO: LLM extraction started
INFO: LLM extraction completed in 2.3s
```

That's it. That's all you have.

**Questions racing through your mind**:
- What prompt did we actually send?
- What did Claude respond with?
- Was it temperature=0.0 or did someone change it?
- How many tokens did we use?
- Did we retry? How many times?
- What was the full conversation context?

**Your options**:
1. Add 47 logger.debug() statements everywhere
2. Build your own tracing infrastructure
3. Cry and try different prompts until something works

**Or...**

Use Opik.

---

## What is Opik?

Opik is an **LLM evaluation and tracing framework** built by Comet ML. Think of it as:
- **Application Performance Monitoring (APM)** for your LLM calls
- **Time-travel debugger** for AI interactions
- **Cost calculator** that shows you exactly where your API budget went

It captures:
- 📝 Full prompts and responses
- ⏱️ Timing and latency for every call
- 💰 Token usage and estimated costs
- 🔄 Retry attempts and failures
- 🎯 Model parameters (temperature, max_tokens, etc.)
- 🔗 Full trace chains (when one LLM call triggers another)

---

## Why We Integrated Opik

### Problem 1: "It worked yesterday"

**Before Opik**:
```
User: "Your app gave me weird ingredients yesterday"
You: "Can you remember exactly what you typed?"
User: "Something like... healthy dinner? Or was it quick dinner?"
You: *sweats* "I'll investigate"
```

**With Opik**:
```
You: Opens Opik dashboard
You: Searches for user's session ID
You: Sees EXACT prompt: "helathy diner for 2" (typos and all)
You: Sees EXACT response: ["kale", "sweet potato", "quinoa"]
You: "Ah, the LLM ignored the typos. Working as intended."
```

---

### Problem 2: "Why is our API bill $342 this month?"

**Before Opik**:
```
You: *scrolls through Anthropic usage dashboard*
You: "We made... 8,247 API calls?"
You: "Which ones? Why? Were they retries? What failed?"
You: *shrugs*
```

**With Opik**:
```
You: Opens Opik dashboard
You: Sorts by token usage
You: "Oh. Someone ran 2,000 test prompts in production last Tuesday."
You: "And we're retrying failed explanation calls 3 times each."
You: Filters by status="error"
You: "These 400 calls failed because of timeouts. We're paying for failures."
```

---

### Problem 3: "The LLM is slow"

**Before Opik**:
```
User: "Your app takes forever"
You: "LLM calls take time"
User: "But HOW LONG? And WHY?"
You: "...2-3 seconds?"
User: "Sometimes it's 8 seconds"
You: *opens CloudWatch logs, drowns in JSON*
```

**With Opik**:
```
You: Opens Opik dashboard
You: Looks at P50, P95, P99 latencies
You: "Ah. Ingredient extraction: 1.2s average"
You: "Explanation generation: 0.8s average"
You: "But 5% of calls take 7+ seconds (timeout retries)"
You: Clicks a trace → sees 2 retries → sees timeout errors
You: "We need better error handling, not faster LLMs"
```

---

## How Opik is Integrated in Our Codebase

### The Single Integration Point Strategy

We could have added Opik tracking to:
- `ingredient_extractor.py` ❌
- `decision_explainer.py` ❌
- `orchestrator.py` ❌
- Every file that calls Claude ❌

**Instead, we did this**:

```python
# conscious-cart-coach/src/llm/client.py

from opik import configure as opik_configure
from opik.integrations.anthropic import track_anthropic

def get_anthropic_client() -> Optional[Anthropic]:
    """Initialize Anthropic client with Opik tracing."""

    # 1. Configure Opik (connects to Opik cloud or local)
    if OPIK_AVAILABLE:
        opik_configure()

    # 2. Create Anthropic client
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # 3. Wrap client with Opik tracking
    if OPIK_AVAILABLE:
        client = track_anthropic(client)

    return client
```

**That's it.**

Every LLM call in our system goes through `client.py`. By wrapping the client once, we automatically trace:
- ✅ Ingredient extraction calls
- ✅ Decision explanation calls
- ✅ Any future LLM features we add

**Single point of integration. Zero code duplication.**

---

## Data Flow: From User Prompt to Opik Dashboard

Let me show you what happens when a user types: "healthy dinner for 2"

```
┌─────────────────────────────────────────────────────────────────┐
│ USER TYPES: "healthy dinner for 2"                             │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ STREAMLIT UI (app.py)                                           │
│ - Captures prompt: "healthy dinner for 2"                       │
│ - User has LLM extraction enabled                               │
│ - Creates Orchestrator(use_llm_extraction=True)                 │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR (orchestrator.py)                                  │
│ - Calls IngredientAgent with use_llm=True                       │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ INGREDIENT AGENT (agents/ingredient_agent.py)                   │
│ - Checks: use_llm=True and client available?                    │
│ - Calls extract_ingredients_with_llm(...)                       │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ INGREDIENT EXTRACTOR (llm/ingredient_extractor.py)              │
│ - Formats prompt with system instructions                       │
│ - Calls call_claude_with_retry(...)                             │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ CLIENT (llm/client.py)                                          │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ client.messages.create(                                  │   │
│ │   model="claude-sonnet-4-20250514",                     │   │
│ │   messages=[{"role": "user", "content": "Extract..."}], │   │
│ │   max_tokens=2048,                                       │   │
│ │   temperature=0.0                                        │   │
│ │ )                                                        │   │
│ └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              │ ◄─── OPIK INTERCEPTS HERE       │
│                              ▼                                  │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ track_anthropic() wrapper captures:                     │   │
│ │ - Full prompt text                                       │   │
│ │ - Model name                                             │   │
│ │ - Parameters (temp, max_tokens)                         │   │
│ │ - Start timestamp                                        │   │
│ └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼ (API call to Anthropic)
┌─────────────────────────────────────────────────────────────────┐
│ ANTHROPIC CLAUDE API                                            │
│ - Processes request                                             │
│ - Returns response                                              │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ CLIENT (llm/client.py)                                          │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ track_anthropic() wrapper captures:                     │   │
│ │ - Full response text                                     │   │
│ │ - End timestamp                                          │   │
│ │ - Latency (end - start)                                 │   │
│ │ - Token usage (prompt + completion)                     │   │
│ │ - Success/failure status                                │   │
│ └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              │ ◄─── SENDS TO OPIK               │
│                              ▼                                  │
│ Returns response to ingredient_extractor                        │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ OPIK PLATFORM (cloud or local)                                  │
│ - Stores trace with unique ID                                   │
│ - Indexes by: timestamp, model, user_id, status                 │
│ - Calculates cost estimate                                      │
│ - Makes searchable in dashboard                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## What Gets Captured (Example Trace)

When the LLM extracts ingredients, Opik captures a trace like this:

```json
{
  "trace_id": "trace_abc123def456",
  "name": "anthropic.messages.create",
  "start_time": "2026-01-24T14:23:01.234Z",
  "end_time": "2026-01-24T14:23:02.567Z",
  "duration_ms": 1333,
  "status": "success",

  "input": {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 2048,
    "temperature": 0.0,
    "messages": [
      {
        "role": "user",
        "content": "Extract ingredients from this user request...\nUSER REQUEST: healthy dinner for 2\nSERVINGS: 2\n..."
      }
    ]
  },

  "output": {
    "content": [
      {
        "type": "text",
        "text": "{\n  \"ingredients\": [\n    {\"name\": \"salmon\", \"quantity\": \"2\", \"unit\": \"fillet\", \"category\": \"protein_fish\", \"optional\": false},\n    {\"name\": \"broccoli\", \"quantity\": \"1\", \"unit\": \"bunch\", \"category\": \"produce_greens\", \"optional\": false},\n    ...\n  ]\n}"
      }
    ],
    "role": "assistant",
    "usage": {
      "input_tokens": 453,
      "output_tokens": 187
    }
  },

  "metadata": {
    "provider": "anthropic",
    "model": "claude-sonnet-4-20250514",
    "usage": {
      "prompt_tokens": 453,
      "completion_tokens": 187,
      "total_tokens": 640
    },
    "cost_usd": 0.0096,  // Estimated
    "retries": 0
  },

  "tags": ["ingredient_extraction", "production"]
}
```

---

## How to Follow Traces in Opik

### Option 1: Opik Cloud Dashboard

1. **Sign up for Opik** (free tier available):
   ```bash
   # Visit https://www.comet.com/opik
   # Create account
   # Get API key
   ```

2. **Configure locally**:
   ```bash
   export OPIK_API_KEY="your_api_key_here"
   export OPIK_WORKSPACE="your_workspace_name"
   ```

3. **Run the app**:
   ```bash
   cd conscious-cart-coach
   ./run.sh
   ```

4. **Make some LLM calls** (enable AI features in Preferences, create a cart)

5. **View traces**:
   - Go to https://www.comet.com/opik
   - Click "Traces"
   - See all your LLM calls in real-time

---

### Option 2: Local Opik Instance (Self-Hosted)

```bash
# Run Opik locally with Docker
docker run -d \
  -p 5000:5000 \
  --name opik-local \
  comet-opik/opik:latest

# Configure app to use local Opik
export OPIK_URL_OVERRIDE="http://localhost:5000"

# Run the app
cd conscious-cart-coach
./run.sh

# View traces at http://localhost:5000
```

---

## Reading a Trace: Step-by-Step

Let's say you opened Opik and see a trace. Here's how to read it:

### 1. Overview Panel
```
┌─────────────────────────────────────────────────────────┐
│ Trace: anthropic.messages.create                       │
│ Status: ✅ Success                                      │
│ Duration: 1.33s                                         │
│ Cost: $0.0096                                           │
│ Timestamp: 2026-01-24 14:23:01 UTC                      │
│ Tags: ingredient_extraction, production                 │
└─────────────────────────────────────────────────────────┘
```

**What to look for**:
- ❌ **Status: Error** → Something failed
- ⏱️ **Duration > 5s** → Unusually slow
- 💰 **Cost > $0.05** → Expensive call (check if worth it)

---

### 2. Input Tab (What We Sent)

Click "Input" to see the full prompt:

```
Extract ingredients from this user request for grocery shopping.

USER REQUEST: healthy dinner for 2
SERVINGS: 2

Extract a structured list of ingredients with:
- name: ingredient name (e.g., "spinach", "chicken breast")
- quantity: amount needed (e.g., "2 bunches", "1 lb")
- unit: normalized unit (e.g., "bunch", "lb", "cup")
- category: broad category (e.g., "produce_greens", "protein_poultry")
- optional: true if ingredient is optional/garnish

RULES:
1. Use common ingredient names (not brand names)
2. Normalize quantities for the specified servings
3. Include cooking essentials (oil, salt) if recipe requires them
4. Mark garnishes/optional items as optional: true
5. Use canonical categories: produce_*, protein_*, grain, dairy, spice
6. If the request is vague, suggest 5-8 common ingredients

OUTPUT FORMAT (JSON only, no markdown):
{
  "ingredients": [...]
}
```

**What to check**:
- ✅ Is the prompt clear and well-formatted?
- ✅ Are the instructions correct?
- ❌ Is there PII (user email, address) leaking into prompts?

---

### 3. Output Tab (What Claude Returned)

Click "Output" to see the full response:

```json
{
  "ingredients": [
    {
      "name": "salmon",
      "quantity": "2",
      "unit": "fillet",
      "category": "protein_fish",
      "optional": false
    },
    {
      "name": "broccoli",
      "quantity": "1",
      "unit": "bunch",
      "category": "produce_greens",
      "optional": false
    },
    {
      "name": "quinoa",
      "quantity": "1",
      "unit": "cup",
      "category": "grain",
      "optional": false
    },
    {
      "name": "olive_oil",
      "quantity": "2",
      "unit": "tbsp",
      "category": "oil",
      "optional": false
    },
    {
      "name": "lemon",
      "quantity": "1",
      "unit": "whole",
      "category": "produce",
      "optional": true
    }
  ]
}
```

**What to check**:
- ✅ Is the JSON valid?
- ✅ Are the ingredients reasonable?
- ❌ Did Claude hallucinate weird categories?
- ❌ Did Claude include markdown (```json) when we said "no markdown"?

---

### 4. Metadata Tab (Technical Details)

Click "Metadata" to see:

```json
{
  "model": "claude-sonnet-4-20250514",
  "temperature": 0.0,
  "max_tokens": 2048,
  "usage": {
    "prompt_tokens": 453,
    "completion_tokens": 187,
    "total_tokens": 640
  },
  "cost_usd": 0.0096,
  "duration_ms": 1333,
  "retries": 0,
  "api_version": "2023-06-01"
}
```

**What to check**:
- ⚠️ **retries > 0** → Call failed initially, had to retry
- ⚠️ **duration_ms > 5000** → Slow response (timeout risk)
- 💰 **cost_usd** → Make sure it's in expected range
- 🌡️ **temperature** → Should be 0.0 for deterministic calls

---

## Searching and Filtering Traces

Opik's dashboard lets you filter traces:

### By Status
```
Status = "error"
```
Shows all failed LLM calls. Great for debugging.

---

### By Duration
```
Duration > 3000ms
```
Shows slow calls. Helps identify timeout risks.

---

### By Cost
```
Cost > $0.05
```
Shows expensive calls. Helps optimize API spend.

---

### By Tag
```
Tags = "ingredient_extraction"
```
Shows only ingredient extraction calls (not explanation calls).

---

### By Date Range
```
Start Time >= "2026-01-24" AND Start Time < "2026-01-25"
```
Shows all calls from January 24th.

---

### By Model
```
Model = "claude-sonnet-4-20250514"
```
Useful if you're A/B testing different models.

---

## Common Debugging Workflows

### Workflow 1: "Why did this extraction fail?"

1. User reports: "I typed 'biryani for 4' but got an error"
2. You: Open Opik dashboard
3. Search: `Tags = "ingredient_extraction" AND Status = "error"`
4. Click the failed trace
5. Check **Input** tab → See the exact prompt sent
6. Check **Output** tab → See if Claude returned non-JSON
7. Check **Metadata** tab → See if it was a timeout or API error
8. Fix the issue:
   - **Non-JSON response** → Improve prompt clarity
   - **Timeout** → Reduce max_tokens or retry logic
   - **API error** → Check API key, rate limits

---

### Workflow 2: "Why is our API bill so high?"

1. You: Open Opik dashboard
2. Sort by: **Cost (descending)**
3. Identify expensive calls:
   - Explanation calls using 2000+ tokens?
   - Retries on failed calls?
   - Someone testing in production?
4. Optimize:
   - Reduce max_tokens for explanation calls
   - Better error handling to avoid retries
   - Add rate limiting

---

### Workflow 3: "Is temperature=0.0 really deterministic?"

1. Make the same call 3 times: "healthy dinner for 2"
2. Open Opik dashboard
3. Filter: `Tags = "ingredient_extraction" AND Input contains "healthy dinner for 2"`
4. Compare **Output** tabs of all 3 traces
5. Verify outputs are identical (they should be with temp=0.0)

---

## Architecture Diagram: Opik Integration

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                           │
│                      (Streamlit app.py)                          │
└──────────────────────────────────────────────────────────────────┘
                                │
                                │ User enables LLM features
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR                             │
│                   (orchestrator/orchestrator.py)                 │
│                                                                  │
│  Coordinates agents with use_llm flags                           │
└──────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
┌─────────────────────────────┐  ┌─────────────────────────────┐
│    INGREDIENT AGENT         │  │    DECISION ENGINE          │
│ (agents/ingredient_agent.py)│  │ (engine/decision_engine.py) │
│                             │  │                             │
│  if use_llm:                │  │  if use_llm:                │
│    extract_with_llm()       │  │    explain_with_llm()       │
└─────────────────────────────┘  └─────────────────────────────┘
                    │                       │
                    ▼                       ▼
┌─────────────────────────────┐  ┌─────────────────────────────┐
│  INGREDIENT EXTRACTOR       │  │  DECISION EXPLAINER         │
│ (llm/ingredient_extractor)  │  │  (llm/decision_explainer)   │
│                             │  │                             │
│  Formats prompt             │  │  Formats prompt             │
│  Calls client API           │  │  Calls client API           │
└─────────────────────────────┘  └─────────────────────────────┘
                    │                       │
                    └───────────┬───────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                          LLM CLIENT                              │
│                      (llm/client.py)                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ get_anthropic_client():                                    │ │
│  │   1. opik_configure()                    ◄────────────────┼─┤
│  │   2. client = Anthropic(api_key)                          │ │
│  │   3. client = track_anthropic(client) ◄─ OPIK WRAPPER     │ │
│  │   4. return client                                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ call_claude_with_retry():                                  │ │
│  │   client.messages.create(...)  ◄───────────────────────────┼─┤
│  │     ↑ Intercepted by track_anthropic()                    │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
┌─────────────────────────────┐  ┌─────────────────────────────┐
│     ANTHROPIC API           │  │      OPIK PLATFORM          │
│  (Claude Sonnet 4)          │  │  (Tracing & Evaluation)     │
│                             │  │                             │
│  - Processes prompt         │  │  - Stores trace             │
│  - Returns response         │  │  - Calculates cost          │
│  - Bills API usage          │  │  - Indexes for search       │
└─────────────────────────────┘  │  - Makes dashboard          │
                                 └─────────────────────────────┘
                                            │
                                            ▼
                                 ┌─────────────────────────────┐
                                 │    OPIK DASHBOARD           │
                                 │  (Web UI for Engineers)     │
                                 │                             │
                                 │  - Search traces            │
                                 │  - View prompts/responses   │
                                 │  - Analyze costs            │
                                 │  - Debug failures           │
                                 └─────────────────────────────┘
```

---

## What Gets Traced (Summary Table)

| LLM Call Type | Where | Model | Avg Tokens | Avg Cost | Avg Latency |
|--------------|--------|-------|------------|----------|-------------|
| **Ingredient Extraction** | `ingredient_extractor.py` | Claude Sonnet 4 | 640 | $0.0096 | 1.2s |
| **Decision Explanation** | `decision_explainer.py` | Claude Sonnet 4 | 350 | $0.0053 | 0.8s |
| **Full Cart (7 items)** | Both | Claude Sonnet 4 | ~3000 | ~$0.045 | 3.6s |

All of these are automatically traced by Opik with zero manual instrumentation.

---

## Configuration Options

Opik can be configured via environment variables:

```bash
# Option 1: Use Opik Cloud (recommended for teams)
export OPIK_API_KEY="opik_key_abc123"
export OPIK_WORKSPACE="conscious-cart-coach"

# Option 2: Use local Opik instance (self-hosted)
export OPIK_URL_OVERRIDE="http://localhost:5000"

# Option 3: Disable Opik (for testing)
# Just don't install opik package, or:
export OPIK_ENABLED="false"
```

**Note**: If Opik is not installed or configured, the system gracefully falls back:
```python
try:
    from opik import configure as opik_configure
    from opik.integrations.anthropic import track_anthropic
    OPIK_AVAILABLE = True
except ImportError:
    OPIK_AVAILABLE = False
    logger.info("Opik not installed. LLM tracing disabled.")
```

The app works fine without Opik. You just won't get tracing.

---

## Opik Best Practices

### 1. Tag Your Traces

Add custom tags for easier filtering:

```python
# In client.py (future enhancement)
@track_with_opik(tags=["ingredient_extraction", "production"])
def extract_ingredients_with_llm(...):
    ...
```

---

### 2. Add User Context

Include user session IDs in traces:

```python
# Pass metadata to Opik
trace_metadata = {
    "user_session_id": session_id,
    "household_size": household_size,
    "feature_flags": {"use_llm": True}
}
```

---

### 3. Monitor Costs Weekly

Set up a weekly review:
- Total API spend
- Most expensive traces
- Failed calls (wasted money)
- Optimization opportunities

---

### 4. Use Traces for Prompt Engineering

When improving prompts:
1. Run old prompt → Save trace ID
2. Run new prompt → Save trace ID
3. Compare outputs side-by-side in Opik
4. Pick winner based on:
   - Output quality
   - Token usage
   - Latency

---

## Troubleshooting

### Issue: "No traces appearing in Opik"

**Check 1**: Is Opik installed?
```bash
pip list | grep opik
# Should show: opik 0.1.0 (or higher)
```

**Check 2**: Is Opik configured?
```bash
echo $OPIK_API_KEY
# Should show your API key
```

**Check 3**: Are LLM features enabled?
- Open Streamlit app
- Go to ⚙️ Preferences
- Check "Enable AI ingredient extraction"
- Check "Enable detailed explanations"

**Check 4**: Are you making LLM calls?
- Type a prompt that requires LLM (e.g., "healthy dinner")
- Check terminal logs for: `INFO: Opik LLM tracing enabled`

---

### Issue: "Opik integration broke the app"

**Cause**: Import error or network issue

**Fix**: Opik is optional. The code has fallback:
```python
if OPIK_AVAILABLE:
    try:
        opik_configure()
    except Exception as e:
        logger.warning(f"Failed to configure Opik: {e}")
        # App continues without tracing
```

If app is broken:
1. Check terminal for error messages
2. Try running without Opik:
   ```bash
   pip uninstall opik
   ./run.sh
   ```
3. If app works without Opik, reinstall:
   ```bash
   pip install opik>=0.1.0
   ```

---

### Issue: "Traces are incomplete or cut off"

**Cause**: Large responses exceed Opik's default limits

**Fix**: Increase trace size limits in Opik config:
```python
# In client.py (future enhancement)
opik_configure(max_trace_size_mb=10)
```

---

## What We Don't Trace (And Why)

### ❌ Deterministic Operations
- Template-based ingredient extraction
- Product scoring calculations
- Price comparisons
- EWG lookups

**Why not?**: No API calls, no variability. Logs are sufficient.

---

### ❌ Database Queries
- SQLite reads
- Cache lookups
- FactsGateway operations

**Why not?**: Opik is for LLM evaluation, not database monitoring.

---

### ❌ User PII
- Email addresses
- Home addresses
- Payment info

**Why not?**: Privacy and compliance. We only log:
- Anonymous session IDs
- Ingredient names
- Product categories

---

## Future Enhancements

### 1. Custom Evaluators

Add automatic quality scoring:
```python
from opik import evaluate

@evaluate(
    name="ingredient_extraction_quality",
    metrics=["valid_json", "reasonable_quantities", "category_accuracy"]
)
def extract_ingredients_with_llm(...):
    ...
```

---

### 2. A/B Testing Prompts

Compare prompt versions:
```python
# Version A: Original prompt
# Version B: Shorter prompt
# Track which performs better in Opik
```

---

### 3. Cost Alerts

Get notified when costs spike:
```python
# Alert if daily cost > $5
# Alert if single call > $0.10
```

---

### 4. Feedback Loop

Capture user feedback on LLM outputs:
```python
# User clicks "This was helpful" or "This was wrong"
# Link feedback to trace_id
# Train better prompts
```

---

## Summary: What Opik Gives Us

✅ **Full visibility** into LLM calls (prompts, responses, timing, cost)
✅ **Debugging superpowers** (see exactly what went wrong)
✅ **Cost optimization** (identify expensive calls)
✅ **Performance monitoring** (track latency trends)
✅ **Prompt engineering** (A/B test prompts)
✅ **Zero manual instrumentation** (automatic via wrapper)
✅ **Graceful degradation** (works without Opik installed)

---

## Related Documentation

- **[6-llm-integration-deep-dive.md](6-llm-integration-deep-dive.md)**: Why we use LLM (and why we don't)
- **[3-usage-guide.md](3-usage-guide.md)**: How to use LLM features
- **[8-data-flows.md](8-data-flows.md)**: Where LLM fits in the data pipeline

---

## Quick Start Checklist

- [ ] Install Opik: `pip install opik>=0.1.0`
- [ ] Sign up at https://www.comet.com/opik (or run local)
- [ ] Set `OPIK_API_KEY` environment variable
- [ ] Set `OPIK_WORKSPACE` environment variable
- [ ] Run app: `cd conscious-cart-coach && ./run.sh`
- [ ] Enable AI features in ⚙️ Preferences
- [ ] Make a cart with LLM extraction
- [ ] Open Opik dashboard
- [ ] See your first trace
- [ ] Marvel at the visibility

---

**Last updated**: 2026-01-24
**Status**: ✅ Opik integrated into LLM client
**Tracing**: All Anthropic API calls automatically tracked
**Overhead**: ~10ms per call (negligible)
**Cost**: Free tier available, self-hosting supported
