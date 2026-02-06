# LLM Provider Switching Guide

**Switch between Ollama, Anthropic Claude, Google Gemini, and OpenAI GPT with just one line in `.env`!**

## Quick Switch - Just Edit `.env`

### Option 1: Ollama (Local, Free, Private)
```bash
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5-coder
```
**Perfect for**: Development, privacy, offline work, no API costs

### Option 2: Anthropic Claude (Cloud API)
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-api03-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```
**Perfect for**: Best quality responses, structured output, long context

### Option 3: Google Gemini (Cloud API)
```bash
LLM_PROVIDER=gemini
GOOGLE_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-1.5-flash
```
**Perfect for**: Fast responses, multimodal capabilities, cost-effective

### Option 4: OpenAI GPT (Cloud API)
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini
```
**Perfect for**: Fast reasoning, popular choice, good documentation

---

## Complete Configuration Reference

### Ollama (Local LLM)

**Setup**:
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start server
ollama serve

# Pull a model
ollama pull qwen2.5-coder
```

**`.env` Configuration**:
```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder
```

**Recommended Models**:
| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| `qwen2.5-coder` | 7.6GB | ⚡️⚡️⚡️ | ⭐⭐⭐⭐ | Code understanding, structured output |
| `mistral` | 4.1GB | ⚡️⚡️⚡️ | ⭐⭐⭐ | General purpose, fast |
| `llama2` | 3.8GB | ⚡️⚡️⚡️ | ⭐⭐⭐ | General purpose |
| `phi` | 2.7GB | ⚡️⚡️⚡️⚡️ | ⭐⭐ | Very fast, smaller context |
| `codellama` | 3.8GB | ⚡️⚡️⚡️ | ⭐⭐⭐⭐ | Code generation |
| `llama2:13b` | 7.3GB | ⚡️⚡️ | ⭐⭐⭐⭐ | Better quality, slower |

**Cost**: FREE
**Privacy**: 100% local
**Internet**: Not required

---

### Anthropic Claude (Cloud API)

**Setup**:
```bash
# Get API key from: https://console.anthropic.com/
# Add to .env
```

**`.env` Configuration**:
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

**Available Models**:
| Model | Context | Speed | Quality | Cost (per 1M tokens) |
|-------|---------|-------|---------|---------------------|
| `claude-3-5-sonnet-20241022` | 200K | ⚡️⚡️ | ⭐⭐⭐⭐⭐ | $3 / $15 |
| `claude-3-opus-20240229` | 200K | ⚡️ | ⭐⭐⭐⭐⭐ | $15 / $75 |
| `claude-3-sonnet-20240229` | 200K | ⚡️⚡️ | ⭐⭐⭐⭐ | $3 / $15 |
| `claude-3-haiku-20240307` | 200K | ⚡️⚡️⚡️ | ⭐⭐⭐ | $0.25 / $1.25 |

**Best for**:
- Highest quality responses
- Complex reasoning
- Structured JSON output
- Long context understanding
- Following instructions precisely

**Estimated Cost**: ~$0.05 per cart creation

---

### Google Gemini (Cloud API)

**Setup**:
```bash
# Get API key from: https://aistudio.google.com/app/apikey
# Add to .env
```

**`.env` Configuration**:
```bash
LLM_PROVIDER=gemini
GOOGLE_API_KEY=AIzaSyYour-Key-Here
GEMINI_MODEL=gemini-1.5-flash
```

**Available Models**:
| Model | Context | Speed | Quality | Cost (per 1M tokens) |
|-------|---------|-------|---------|---------------------|
| `gemini-1.5-flash` | 1M | ⚡️⚡️⚡️ | ⭐⭐⭐⭐ | $0.075 / $0.30 |
| `gemini-1.5-pro` | 2M | ⚡️⚡️ | ⭐⭐⭐⭐⭐ | $1.25 / $5.00 |
| `gemini-pro` | 32K | ⚡️⚡️⚡️ | ⭐⭐⭐ | $0.50 / $1.50 |

**Best for**:
- Fast responses
- Very long context (1M-2M tokens)
- Cost-effective API
- Multimodal capabilities (text + images)
- Google ecosystem integration

**Estimated Cost**: ~$0.01 per cart creation (cheapest!)

---

### OpenAI GPT (Cloud API)

**Setup**:
```bash
# Get API key from: https://platform.openai.com/api-keys
# Install package: pip install openai
# Add to .env
```

**`.env` Configuration**:
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

**Available Models**:
| Model | Context | Speed | Quality | Cost (per 1M tokens) |
|-------|---------|-------|---------|---------------------|
| `gpt-4o-mini` | 128K | ⚡️⚡️⚡️ | ⭐⭐⭐⭐ | $0.15 / $0.60 |
| `gpt-4o` | 128K | ⚡️⚡️ | ⭐⭐⭐⭐⭐ | $2.50 / $10.00 |
| `gpt-4-turbo` | 128K | ⚡️⚡️ | ⭐⭐⭐⭐⭐ | $10 / $30 |
| `gpt-3.5-turbo` | 16K | ⚡️⚡️⚡️ | ⭐⭐⭐ | $0.50 / $1.50 |

**Best for**:
- Fast reasoning
- Popular and well-documented
- Good ecosystem support
- Function calling
- Wide range of model options

**Estimated Cost**: ~$0.02 per cart creation

---

## Comparison Table

| Feature | Ollama | Anthropic | Gemini | OpenAI |
|---------|--------|-----------|--------|--------|
| **Cost** | FREE | ~$0.05/cart | ~$0.01/cart | ~$0.02/cart |
| **Speed** | 2-3s | 1-2s | 1-2s | 1-2s |
| **Quality** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Privacy** | 100% Local | Cloud | Cloud | Cloud |
| **Internet** | Not required | Required | Required | Required |
| **Setup** | 1 command | API key | API key | API key + pip |
| **Context** | 4K-32K | 200K | 1M-2M | 128K |

---

## How to Switch Providers

### Step 1: Edit `.env`

**Example: Switch from Ollama to Gemini**

Before:
```bash
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5-coder
```

After:
```bash
LLM_PROVIDER=gemini
GOOGLE_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-1.5-flash
```

### Step 2: Restart Backend

```bash
# Stop backend (Ctrl+C)
# Start again
python -m uvicorn api.main:app --reload
```

### Step 3: Verify

Check logs for:
```
INFO: Initializing LLM client with provider: gemini
INFO: LLM client initialized successfully: GeminiClient
```

**That's it!** No code changes needed.

---

## Testing Different Providers

Use the test script to verify any provider:

```bash
# Test Ollama
LLM_PROVIDER=ollama python test_ollama_setup.py

# Test Gemini
LLM_PROVIDER=gemini GOOGLE_API_KEY=your-key python test_ollama_setup.py

# Test OpenAI
LLM_PROVIDER=openai OPENAI_API_KEY=your-key python test_ollama_setup.py
```

---

## Recommended Use Cases

### Development & Testing
✅ **Use Ollama**
- Free unlimited usage
- Fast iteration
- No API costs while developing

### Production (Budget-Conscious)
✅ **Use Gemini Flash**
- Excellent quality/cost ratio
- Very fast
- Huge context window (1M tokens)

### Production (Best Quality)
✅ **Use Claude 3.5 Sonnet**
- Highest quality responses
- Best at following instructions
- Excellent structured output

### Production (Popular Choice)
✅ **Use GPT-4o-mini**
- Good balance of speed/quality/cost
- Well-documented
- Broad ecosystem support

---

## Cost Estimates (1000 carts/day)

| Provider | Model | Daily Cost | Monthly Cost |
|----------|-------|-----------|--------------|
| Ollama | qwen2.5-coder | $0 | $0 |
| Gemini | gemini-1.5-flash | $10 | $300 |
| OpenAI | gpt-4o-mini | $20 | $600 |
| Anthropic | claude-3.5-sonnet | $50 | $1,500 |

---

## Advanced: Mix & Match Providers

You can use different providers for different tasks:

```python
from src.utils.llm_client import get_llm_client

# Use cheap/fast model for ingredient extraction
ingredient_client = get_llm_client(provider="gemini")

# Use best model for explanations
explain_client = get_llm_client(provider="anthropic")
```

---

## Troubleshooting

### Ollama: "Connection refused"
```bash
# Make sure Ollama is running
ollama serve
```

### Anthropic: "Invalid API key"
```bash
# Check your key at: https://console.anthropic.com/
# Make sure ANTHROPIC_API_KEY is set in .env
```

### Gemini: "Invalid API key"
```bash
# Get key from: https://aistudio.google.com/app/apikey
# Make sure GOOGLE_API_KEY is set in .env
```

### OpenAI: "Module not found: openai"
```bash
# Install the package
pip install openai
```

---

## Getting API Keys

### Anthropic Claude
1. Visit https://console.anthropic.com/
2. Sign up for an account
3. Go to API Keys section
4. Create a new key
5. Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-api03-...`

### Google Gemini
1. Visit https://aistudio.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Add to `.env`: `GOOGLE_API_KEY=AIzaSy...`

### OpenAI
1. Visit https://platform.openai.com/api-keys
2. Sign up for an account
3. Click "Create new secret key"
4. Add to `.env`: `OPENAI_API_KEY=sk-proj-...`
5. Install package: `pip install openai`

---

## Summary

✅ **Four providers supported**: Ollama, Anthropic, Gemini, OpenAI
✅ **One-line switch**: Just change `LLM_PROVIDER` in `.env`
✅ **Zero code changes**: All existing code works with any provider
✅ **Backward compatible**: Drop-in replacement for existing Anthropic code

**Choose based on your needs**:
- **Budget**: Ollama (free) or Gemini ($)
- **Quality**: Claude ($$$$) or GPT-4o ($$$)
- **Speed**: Gemini Flash or GPT-4o-mini
- **Privacy**: Ollama (100% local)
- **Development**: Ollama (unlimited free testing)

