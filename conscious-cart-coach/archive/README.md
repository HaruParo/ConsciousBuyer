# Archive - All Historical & Deprecated Content

> **Purpose**: Single location for all archived content
> **Last Updated**: 2026-01-29
> **Policy**: Reference only - never deploy

---

## 📁 Archive Structure

```
archive/
├── README.md (this file)
│
├── v1.0-streamlit/          # Code: Old Streamlit UI (3 files)
├── unused-scripts/          # Code: Abandoned scripts (2 files)
│
├── v1.0-design-docs/        # Docs: UI/UX & aspirational (8 files)
├── v1.0-implementation/     # Docs: Streamlit guides (14 files)
├── project-history/         # Docs: Early designs (10 files)
│
├── test-outputs-jan2026/    # Data: Test CSVs (10 files)
└── data-archive/            # Data: Old folders (2 folders)
```

**Total**: 47 archived items in single location

---

## 📂 Archive Categories

### CODE/ - Deprecated Code

**v1.0-streamlit/** (Deprecated UI)
- Old Streamlit web interface
- **Date**: 2026-01-24
- **Status**: ❌ Replaced by React + FastAPI
- **Files**: app.py, components.py, styles.py

**unused-scripts/** (Abandoned Approach)
- Static store_type classification scripts
- **Date**: 2026-01-29 (never deployed)
- **Status**: ❌ Abandoned
- **Files**: add_store_types.py, add_store_types_bulk.py
- **Why**: Couldn't handle new ingredients dynamically

**empty-folders/** (Cleanup)
- Cleaned up empty directories
- **Files**: scripts/, ui/

---

### DOCS/ - Historical Documentation

**v1.0-design-docs/** (Feature Proposals & Aspirational)
- UI/UX design specifications from v1.0
- Aspirational features that were never implemented
- **Count**: 8 files
- **Topics**: Ingredient confirmation, cart panels, multi-store flow, conscious buying philosophy

**v1.0-implementation/** (Implementation Guides)
- Streamlit-specific implementation docs
- **Count**: 14 files
- **Topics**: Streamlit fixes, Opik testing, LLM features, UI workflows, demo guides, usage, deployment, troubleshooting

**project-history/** (Early Designs)
- Original design evolution (PromptsResponses)
- **Count**: 10 files
- **Topics**: App structure, ingestion, validation, decision UI

---

### DATA/ - Old Data & Outputs

**test-outputs-jan2026/** (Test Data)
- CSV exports from v1.0 testing
- **Date**: 2026-01-22 to 2026-01-23
- **Count**: 10 files
- **Status**: ❌ Test data only

**data-archive/** (Old Data Folders)
- Unused data directories (raw/, opik_logs/)
- **Status**: ❌ Not used in current system

---

## 📊 Quick Stats

| Category | Items | Status | Location |
|----------|-------|--------|----------|
| Code | 7 items | Deprecated/Abandoned | CODE/ |
| Documentation | 32 files | Historical | DOCS/ |
| Data | 12+ items | Old test data | DATA/ |

**Total**: 51+ archived items

---

## 🎯 For Active Content

### Active Code
- **Backend**: `/src/` (orchestrator, agents, engine)
- **Frontend**: `/frontend/` (React UI)
- **Demo**: `/demo_api.py` (FastAPI)
- **Tests**: `/tests/`

### Active Documentation
- **Architecture**: `/docs/architecture/` (21 files)
- **Guides**: `/docs/` (DEVELOPMENT_PRINCIPLES, TESTING_CHEAT_SHEET)
- **Reference**: `/PROJECT_STRUCTURE.md`, `/CHANGELOG.md`

### Active Data
- **Sources**: `/data/` (flags, seasonal, stores, alternatives)
- **Outputs**: `/outputs/` (empty - on-demand only)

---

## 🔍 Finding Archived Content

### Looking for v1.0 Streamlit Code?
→ `CODE/v1.0-streamlit/`

### Looking for Design Docs?
→ `DOCS/v1.0-design-docs/`

### Looking for Old Test Data?
→ `DATA/test-outputs-jan2026/`

### Looking for Early Project History?
→ `DOCS/project-history/`

---

## ⚠️ Archive Policy

### What's Here
- ✅ Deprecated code (v1.0)
- ✅ Abandoned approaches
- ✅ Historical documentation
- ✅ Old test data
- ✅ Empty/cleaned folders

### What's Not Here
- ❌ Active/current code
- ❌ Current documentation
- ❌ Production data
- ❌ Sensitive information

### Usage Rules
- **Reference Only**: For historical context
- **Never Deploy**: Code is outdated and unmaintained
- **No Updates**: Archive is frozen (read-only)
- **Ask First**: Before using anything, check current alternatives

---

## 📚 Related Documentation

| Document | Purpose |
|----------|---------|
| [PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md) | Current project navigation |
| [CLEANUP_SUMMARY.md](../CLEANUP_SUMMARY.md) | What was cleaned and why |
| [CHANGELOG.md](../CHANGELOG.md) | Version history |
| [docs/architecture/STORE_CLASSIFICATION_VERSION_HISTORY.md](../docs/architecture/STORE_CLASSIFICATION_VERSION_HISTORY.md) | System evolution |

---

## 🗂️ Archive Index

For detailed listings of what's in each folder, see:
- [CODE/v1.0-streamlit/](v1.0-streamlit/) - Streamlit UI files
- [CODE/unused-scripts/](unused-scripts/) - Abandoned scripts
- [DOCS/v1.0-design-docs/](v1.0-design-docs/) - Design proposals
- [DOCS/v1.0-implementation/](v1.0-implementation/) - Implementation guides
- [DOCS/project-history/](project-history/) - Early designs
- [DATA/test-outputs-jan2026/README.md](test-outputs-jan2026/README.md) - Test data guide
- [DATA/data-archive/README.md](data-archive/README.md) - Old data folders

---

**Last Updated**: 2026-01-29
**Archive Location**: `/archive/` (single consolidated location)
**Questions?** See [PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md)
