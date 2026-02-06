# Documentation

> **Last Updated**: 2026-01-29
> **Current Version**: v2.0 (React + FastAPI)

Quick navigation for all project documentation.

---

## 📁 Active Documentation

### architecture/ - System Architecture & Guides

**Core Documentation** (12 files):
- **[architecture-overview.md](architecture/architecture-overview.md)** - Complete system overview (START HERE)
- **[STORE_CLASSIFICATION_SYSTEM.md](architecture/STORE_CLASSIFICATION_SYSTEM.md)** - v2.0 store classification (NEW)
- **[MULTI_STORE_CART_SYSTEM.md](architecture/MULTI_STORE_CART_SYSTEM.md)** - Multi-store cart design
- **[implementation-status.md](architecture/implementation-status.md)** - What's been built
- **[DATA_SOURCE_STRATEGY.md](architecture/DATA_SOURCE_STRATEGY.md)** - Data sources and refresh schedule

**Technical Deep Dives**:
- [technical-stack.md](architecture/technical-stack.md) - System architecture
- [llm-integration.md](architecture/llm-integration.md) - LLM integration details
- [ui-user-flows.md](architecture/ui-user-flows.md) - UI user flows
- [data-pipeline.md](architecture/data-pipeline.md) - Data flow diagrams
- [llm-monitoring-opik.md](architecture/llm-monitoring-opik.md) - LLM monitoring

**Demo & Quick Start**:
Run `python demo_api.py` then visit http://localhost:8000 for interactive demo

### Root Docs - Quick Reference

**Development**:
- **[DEVELOPMENT_PRINCIPLES.md](DEVELOPMENT_PRINCIPLES.md)** - Coding standards & principles
- **[TESTING_CHEAT_SHEET.md](TESTING_CHEAT_SHEET.md)** - Testing quick reference
- **[CLAUDE.md](CLAUDE.md)** - Instructions for documentation

---

## 📦 Archived Documentation

**All archives moved to single location**: `/archive/`

See [../archive/README.md](../archive/README.md) for all historical documentation (32 docs):
- v1.0 design docs (8 files)
- v1.0 implementation guides (14 files)
- Early project history (10 files)

---

## 🎯 Quick Start

### New to the Project?
1. Read [architecture/architecture-overview.md](architecture/architecture-overview.md) - Complete overview
2. Check [../PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md) - File navigation
3. See [architecture/implementation-status.md](architecture/implementation-status.md) - What's built

### Want to Understand Store Classification?
1. [architecture/STORE_CLASSIFICATION_SYSTEM.md](architecture/STORE_CLASSIFICATION_SYSTEM.md) - How it works
2. [architecture/STORE_CLASSIFICATION_VERSION_HISTORY.md](architecture/STORE_CLASSIFICATION_VERSION_HISTORY.md) - Why we built it this way
3. Run the demo: `python demo_api.py` then visit http://localhost:8000

### Looking for Specific Topics?

| Topic | Document |
|-------|----------|
| System Architecture | [architecture/technical-stack.md](architecture/technical-stack.md) |
| LLM Integration | [architecture/llm-integration.md](architecture/llm-integration.md) |
| UI Flows | [architecture/ui-user-flows.md](architecture/ui-user-flows.md) |
| Data Pipeline | [architecture/data-pipeline.md](architecture/data-pipeline.md) |
| LLM Monitoring | [architecture/llm-monitoring-opik.md](architecture/llm-monitoring-opik.md) |
| Data Sources | [architecture/DATA_SOURCE_STRATEGY.md](architecture/DATA_SOURCE_STRATEGY.md) |
| Testing | [TESTING_CHEAT_SHEET.md](TESTING_CHEAT_SHEET.md) |
| Demo | Run `python demo_api.py` then visit http://localhost:8000 |

---

## 📊 Documentation Summary

| Category | Files | Status |
|----------|-------|--------|
| Active Architecture Docs | 12 | ✅ Current |
| Root Quick References | 3 | ✅ Current |
| Archived Historical Docs | 32 | 📦 Reference |

**Total**: 47 documentation files

---

## 🔄 Documentation Structure

```
docs/
├── README.md                    ✨ This file
├── DEVELOPMENT_PRINCIPLES.md   📚 Active
├── TESTING_CHEAT_SHEET.md     📚 Active
├── CLAUDE.md                   📚 Active
│
└── architecture/               ✅ Active (12 files)
    ├── architecture-overview.md   🎯 START HERE
    ├── STORE_CLASSIFICATION_*.md  🆕 v2.0
    ├── technical-stack.md         📚 Technical guides
    ├── llm-*.md                   🤖 LLM docs
    └── README.md                  📖 Architecture index

All archives → /archive/ (see ../archive/README.md)
```

---

**Navigation**: [↑ Project Root](../) | [Architecture →](architecture/) | [Archive →](archive/)
