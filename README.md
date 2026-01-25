# Conscious Cart Coach

**A smart grocery shopping assistant that helps you make informed decisions across budget, health, and ethics.**

![Status: Production Ready](https://img.shields.io/badge/status-production%20ready-brightgreen)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue)
![Streamlit](https://img.shields.io/badge/streamlit-1.30+-red)

---

## What is This?

Conscious Cart Coach analyzes grocery products and recommends three shopping cart options:

- 💸 **Cheaper**: Budget-focused options
- ⚖️ **Balanced**: Middle ground (value + quality)
- 🌍 **Conscious**: Premium/ethical choices (organic, local, sustainable)

**Key Features**:
- 🎯 Deterministic product scoring (same inputs → same outputs)
- 🤖 Optional AI enhancement (natural language prompts, detailed explanations)
- 🔍 EWG safety classifications & FDA recall checking
- 🍂 Seasonal produce recommendations
- 📊 Real-time cost tracking with Opik

---

## Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/ConsciousBuyer.git
cd ConsciousBuyer/conscious-cart-coach

# Install dependencies
pip install -r requirements.txt

# Set up environment (optional: for AI features)
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run the app
streamlit run src/ui/app.py
```

Open http://localhost:8501 in your browser.

---

## Documentation

📚 **All documentation is in the [`architecture/`](architecture/) folder**

### Getting Started

- **[Architecture Overview](architecture/0-step.md)** - Start here! Complete system walkthrough
- **[Usage Guide](architecture/3-usage-guide.md)** - How to use the system
- **[Deployment Guide](architecture/10-deployment-guide.md)** - Deploy in 5 minutes

### For Developers

- **[Technical Architecture](architecture/5-technical-architecture.md)** - System design
- **[LLM Integration](architecture/6-llm-integration-deep-dive.md)** - AI approach
- **[Testing Guide](conscious-cart-coach/tests/README.md)** - Run tests
- **[Implementation Changelog](architecture/11-implementation-changelog.md)** - What's built
- **[Troubleshooting](architecture/12-troubleshooting-guide.md)** - Fix issues

### Full Documentation Index

See **[architecture/README.md](architecture/README.md)** for complete documentation index (12 detailed guides).

---

## Technology Stack

- **Backend**: Python 3.11
- **UI**: Streamlit
- **Database**: SQLite
- **LLM**: Anthropic Claude (optional)
- **Monitoring**: Opik
- **Testing**: Pytest (30+ tests)

---

## Cost

**Free tier** (default mode):
- ✅ No LLM = $0
- ✅ Streamlit Cloud = $0 (public repos)
- ✅ Opik monitoring = $0 (free tier)

**With AI features**:
- 🤖 Natural language prompts: $0.01/cart
- 🤖 Detailed explanations: $0.03/cart
- **Combined**: ~$0.045/cart

**For 100 carts/month**: $4.50/month

---

## Deployment

**Streamlit Cloud** (5 minutes, free) - **Recommended!**

```bash
# 1. Push to GitHub
# 2. Go to https://share.streamlit.io
# 3. Deploy: ConsciousBuyer/main/conscious-cart-coach/src/ui/app.py
# 4. Add API keys in secrets
# 5. Done!
```

**Quick Start**: See **[DEPLOY.md](DEPLOY.md)** (1-page guide)
**Full Guide**: See **[Deployment Guide](architecture/10-deployment-guide.md)** (detailed + alternatives)

---

## Testing

```bash
cd conscious-cart-coach

# All tests (30+ tests)
pytest

# Only LLM tests
pytest -m llm

# Environment check
pytest tests/test_env_loading.py -v -s
```

**Cost per test run**: ~$0.14

---

## Project Structure

```
ConsciousBuyer/
├── architecture/                  # 📚 All documentation
│   ├── 0-step.md                  # Start here
│   ├── 10-deployment-guide.md
│   ├── 11-implementation-changelog.md
│   ├── 12-troubleshooting-guide.md
│   └── ... (8 more guides)
├── conscious-cart-coach/          # Main application
│   ├── src/
│   │   ├── ui/                    # Streamlit interface
│   │   ├── agents/                # Multi-agent system
│   │   ├── llm/                   # AI integration
│   │   └── ...
│   ├── tests/                     # Test suite
│   └── requirements.txt
└── README.md                      # This file
```

---

## License

MIT License

---

## Support

- 📖 **Documentation**: See [`architecture/`](architecture/) folder
- 🐛 **Issues**: Open on GitHub
- ❓ **Questions**: Check [Troubleshooting Guide](architecture/12-troubleshooting-guide.md)

---

**Last Updated**: 2026-01-24 | **Status**: ✅ Production Ready | **Version**: 1.0.0
