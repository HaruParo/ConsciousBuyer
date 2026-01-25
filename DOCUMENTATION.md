# Documentation Overview

**Last Updated**: 2026-01-24

---

## 📚 All Documentation is in `architecture/` Folder

All project documentation has been consolidated into the [`architecture/`](architecture/) folder for better organization.

---

## Quick Links

### Get Started
- 🚀 **[README.md](README.md)** - Project overview and quick start
- 📖 **[architecture/0-step.md](architecture/0-step.md)** - Complete architecture guide
- 🎯 **[architecture/3-usage-guide.md](architecture/3-usage-guide.md)** - How to use the system

### Deploy
- 🚢 **[architecture/10-deployment-guide.md](architecture/10-deployment-guide.md)** - Deploy to production (5 min)
- ✅ **[architecture/11-implementation-changelog.md](architecture/11-implementation-changelog.md)** - What's been built

### Troubleshoot
- 🔧 **[architecture/12-troubleshooting-guide.md](architecture/12-troubleshooting-guide.md)** - Fix common issues
- 🧪 **[conscious-cart-coach/tests/README.md](conscious-cart-coach/tests/README.md)** - Testing guide

### Learn More
- 🤖 **[architecture/6-llm-integration-deep-dive.md](architecture/6-llm-integration-deep-dive.md)** - AI approach
- 📊 **[architecture/9-opik-llm-evaluation.md](architecture/9-opik-llm-evaluation.md)** - Monitoring
- 🏗️ **[architecture/5-technical-architecture.md](architecture/5-technical-architecture.md)** - System design

---

## Complete Documentation Index

See **[architecture/README.md](architecture/README.md)** for the full documentation index.

**Total**: 12 comprehensive guides covering architecture, implementation, deployment, testing, and troubleshooting.

---

## What Happened to the Old Root-Level MD Files?

Previously, documentation was scattered across multiple MD files in the root directory:
- `IMPLEMENTATION_COMPLETE.md`
- `PYTEST_OPIK_INTEGRATION.md`
- `OPIK_THREADS_EXPLAINED.md`
- `ENV_LOADING_FIX.md`
- `STREAMLIT_FIX_2026-01-24.md`
- `UI_LLM_FEATURES_GUIDE.md`

**These have all been consolidated** into:
- **[architecture/11-implementation-changelog.md](architecture/11-implementation-changelog.md)** - Implementation details and testing
- **[architecture/12-troubleshooting-guide.md](architecture/12-troubleshooting-guide.md)** - All troubleshooting info

This provides a cleaner, better-organized documentation structure.

---

## Documentation Structure

```
ConsciousBuyer/
├── README.md                      # Project overview
├── DOCUMENTATION.md               # This file
├── CLAUDE.md                      # User instructions
├── architecture/                  # 📚 All documentation here
│   ├── README.md                  # Documentation index
│   ├── 0-step.md                  # Architecture overview (start here)
│   ├── 2-llm-integration-summary.md
│   ├── 3-usage-guide.md
│   ├── 4-ui-expectations.md
│   ├── 5-technical-architecture.md
│   ├── 6-llm-integration-deep-dive.md
│   ├── 7-ui-flows.md
│   ├── 8-data-flows.md
│   ├── 9-opik-llm-evaluation.md
│   ├── 10-deployment-guide.md     # Deploy to production
│   ├── 11-implementation-changelog.md  # What's built
│   └── 12-troubleshooting-guide.md     # Fix issues
└── conscious-cart-coach/
    ├── tests/
    │   └── README.md              # Testing guide
    └── ...
```

---

## Need Help?

1. **Quick question?** Check [README.md](README.md)
2. **Getting started?** Read [architecture/0-step.md](architecture/0-step.md)
3. **Stuck on something?** Check [Troubleshooting Guide](architecture/12-troubleshooting-guide.md)
4. **Want to deploy?** See [Deployment Guide](architecture/10-deployment-guide.md)
5. **Need full details?** Browse [architecture/](architecture/) folder

---

**Pro tip**: Start with [README.md](README.md), then dive into [architecture/0-step.md](architecture/0-step.md). Everything else branches from there.
