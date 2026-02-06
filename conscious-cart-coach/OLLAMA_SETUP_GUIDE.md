# Ollama Setup Guide for Conscious Cart Coach

This guide shows you how to use **Ollama** (local LLMs) instead of the Anthropic API for Conscious Cart Coach.

## Benefits of Using Ollama

✅ **Free**: No API costs
✅ **Private**: Data never leaves your machine
✅ **Fast**: No network latency for API calls
✅ **Offline**: Works without internet
✅ **Flexible**: Easy to switch between different models

## Step 1: Install Ollama

### macOS (Your Current System)
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Verify Installation
```bash
ollama --version
```

## Step 2: Start Ollama Server

Open a terminal and run:
```bash
ollama serve
```

**Keep this terminal running** - Ollama needs to be running in the background.

## Step 3: Pull a Model

In a **new terminal**, pull the Mistral model (recommended for Conscious Cart Coach):

```bash
# Mistral (4.1GB) - Good balance of speed and quality
ollama pull mistral

# Alternative options:
# ollama pull phi           # Faster but less capable (2.7GB)
# ollama pull llama2        # Similar to Mistral (3.8GB)
# ollama pull llama2:13b    # Better quality but slower (7.3GB)
```

**Wait for download to complete** (may take 5-10 minutes depending on your internet speed).

## Step 4: Verify Ollama is Working

Test that Ollama can generate text:

```bash
ollama run mistral
```

You should see a prompt. Type something like:
```
>>> Hello, are you working?
```

Press `Ctrl+D` to exit when done.

## Step 5: Configure Your .env File

Your `.env` file has already been updated with:

```bash
# LLM Configuration
LLM_PROVIDER=ollama

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```

**No changes needed** - this is already configured!

## Step 6: Install Python Dependencies

Make sure you have the required packages:

```bash
pip install python-dotenv requests anthropic
```

## Step 7: Test the Setup

Run the automated test script:

```bash
python test_ollama_setup.py
```

You should see:
```
============================================================
Ollama Setup Test for Conscious Cart Coach
============================================================

1. Checking Ollama server...
   ✅ Ollama server is running

2. Checking if model 'mistral' is available...
   ✅ Model 'mistral' is available

3. Testing simple text generation...
   ✅ Generation successful

4. Testing ingredient extraction...
   ✅ Ingredient extraction successful

5. Checking .env configuration...
   ✅ LLM_PROVIDER set to ollama

============================================================
Summary
============================================================
✅ PASS - Ollama Server
✅ PASS - Model Available
✅ PASS - Simple Generation
✅ PASS - Ingredient Extraction
✅ PASS - ENV Configuration

🎉 All tests passed! Ollama is ready to use.
```

## Step 8: Test the Ingredient Agent

Test the enhanced ingredient agent:

```bash
python src/agents/ingredient_agent_llm.py
```

Expected output:
```
Testing Ingredient Agent with LLM

1. Testing with LLM (Ollama):
------------------------------------------------------------
Extracted 12 ingredients:
  - 1.5 lb chicken (protein)
  - 2.0 cup basmati rice (grains)
  - 2.0 medium onion (produce)
  - 2.0 tsp cumin (spices)
  ...

2. Testing with Rules (fallback):
------------------------------------------------------------
Extracted 12 ingredients:
  - 2.25 lb chicken (protein)
  - 3.0 cup basmati rice (grains)
  ...
```

## Step 9: Update Your Backend to Use Ollama

The unified LLM client is ready at `src/utils/llm_client.py`.

To use it in your orchestrator or agents:

```python
from src.utils.llm_client import get_llm_client

# In your agent or orchestrator
class MyAgent:
    def __init__(self):
        # Automatically uses Ollama based on .env LLM_PROVIDER setting
        self.llm_client = get_llm_client()

    def process(self, input_text):
        response = self.llm_client.generate_sync(
            prompt=f"Process this: {input_text}",
            system="You are a helpful assistant",
            temperature=0.7
        )
        return response.text
```

## Switching Between Ollama and Anthropic

Edit your `.env` file:

### Use Ollama (Local, Free)
```bash
LLM_PROVIDER=ollama
```

### Use Anthropic (Cloud, Paid)
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_api_key_here
```

No code changes needed - the `get_llm_client()` function handles the switch automatically!

## Troubleshooting

### Error: "Could not connect to Ollama"

**Solution**: Make sure Ollama is running:
```bash
ollama serve
```

### Error: "Model 'mistral' not found"

**Solution**: Pull the model:
```bash
ollama pull mistral
```

### Error: "OLLAMA_BASE_URL not set"

**Solution**: Check your `.env` file has:
```bash
OLLAMA_BASE_URL=http://localhost:11434
```

### Slow Response Times

**Solution**: Use a smaller model:
```bash
# Pull a faster model
ollama pull phi

# Update .env
OLLAMA_MODEL=phi
```

### Out of Memory Errors

**Solution**: Close other applications or use a smaller model like `phi`.

## Performance Comparison

| Provider | Speed | Cost | Quality | Privacy |
|----------|-------|------|---------|---------|
| **Ollama (mistral)** | ~2-3s | Free | Good | 100% |
| **Anthropic (Claude)** | ~1-2s | ~$0.05/cart | Excellent | Depends on trust |

## Recommended Models for Different Tasks

| Task | Recommended Model | Why |
|------|------------------|-----|
| Ingredient Extraction | `mistral` | Good at structured output |
| Product Matching | `mistral` | Understands context well |
| Explanations | `llama2` | Natural language generation |
| Fast Prototyping | `phi` | Very fast, good enough quality |
| Best Quality | `llama2:13b` | Best reasoning (slower) |

## Next Steps

1. ✅ Ollama installed and running
2. ✅ Model pulled and tested
3. ✅ .env configured
4. ✅ Test scripts passing

**Now you can**:
- Use Ollama for all LLM features
- Develop without API costs
- Switch back to Anthropic anytime by changing `.env`

## Advanced: Using Different Models for Different Tasks

You can create specialized clients:

```python
# Fast model for ingredient extraction
from src.utils.llm_client import OllamaClient

ingredient_client = OllamaClient(model="phi")  # Fast

# Better model for explanations
explain_client = OllamaClient(model="mistral")  # Quality
```

## Files Created

- ✅ `src/utils/llm_client.py` - Unified LLM client (Ollama + Anthropic)
- ✅ `src/agents/ingredient_agent_llm.py` - Example LLM-enhanced agent
- ✅ `test_ollama_setup.py` - Automated testing script
- ✅ `.env` - Updated with Ollama configuration
- ✅ `OLLAMA_SETUP_GUIDE.md` - This guide

## Questions?

**Q: Can I use both Ollama and Anthropic?**
A: Yes! Just change `LLM_PROVIDER` in `.env` whenever you want to switch.

**Q: Which is better for production?**
A: Anthropic (Claude) has better quality, but Ollama is free and private. Test both!

**Q: Can I use GPT-4 instead?**
A: The OpenAI client is stubbed out in `llm_client.py`. You can implement it following the same pattern.

**Q: How do I know which provider is being used?**
A: Check your logs - the LLM client logs which provider is active.

---

**Happy local LLM usage! 🎉**

