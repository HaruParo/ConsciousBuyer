# Changelog

All notable changes to Conscious Cart Coach will be documented here.

---

## [2.1.0] - 2026-01-29

### 📝 Changed - File Renaming for Better Scanability

**Architecture Files Renamed** (removed confusing numbers):
- `0-step.md` → `architecture-overview.md`
- `5-technical-architecture.md` → `technical-stack.md`
- `6-llm-integration-deep-dive.md` → `llm-integration.md`
- `7-ui-flows.md` → `ui-user-flows.md`
- `8-data-flows.md` → `data-pipeline.md`
- `9-opik-llm-evaluation.md` → `llm-monitoring-opik.md`
- `11-implementation-changelog.md` → `implementation-status.md`

**Root Files Renamed** (clearer naming):
- `START.md` → `QUICKSTART.md`
- `DEV_NOTE.md` → `DEV_SETUP.md`
- `UI_NOTE.md` → `UI_DEVELOPMENT.md`

**Cleanup Logs Consolidated**:
- Combined 3 separate cleanup files into `CLEANUP_HISTORY.md`
- Removed: `CLEANUP_SUMMARY.md`, `ARCHITECTURE_CLEANUP_LOG.md`, `FINAL_CLEANUP_LOG.md`

**Documentation Updated**:
- All references updated in `docs/README.md` and `docs/architecture/README.md`
- Created `RENAME_LOG.md` - Complete renaming audit

**Benefits**:
- Files now sort alphabetically by topic
- LLM docs grouped together (`llm-*.md`)
- Names indicate content at a glance
- Easier scanning and retrieval

---

## [2.0.0] - 2026-01-29

### 🎯 Added - Store Classification System

**Major Feature: Multi-Store Cart Splitting**
- Dynamic ingredient classification (primary/specialty/both)
- Implements 1-item efficiency rule (don't add 2nd store for just 1 item)
- Urgency-aware store selection:
  - Planning mode → Pure Indian Foods (high transparency)
  - Urgent mode → Kesar Grocery (fast delivery)
- Handles NEW ingredients automatically via pattern matching
- No manual intervention needed

**Files Added**:
- `src/orchestrator/ingredient_classifier.py` - Classification logic
- `src/orchestrator/store_split.py` - Store splitting algorithm
- `tests/test_store_split_demo.py` - Complete test suite (4 tests, all passing)
- `demo_api.py` - Interactive demo at localhost:8000
- `docs/architecture/STORE_CLASSIFICATION_SYSTEM.md` - Documentation
- `docs/architecture/STORE_CLASSIFICATION_VERSION_HISTORY.md` - Version history

**Design System Integration**:
- Primary Store: `#d4976c` (orange)
- Specialty Store: `#8b7ba8` (purple)
- Unavailable: `#e5d5b8` (beige)

### 🧹 Changed - Project Organization

**Consolidated Structure**:
- Renamed `Figma_files/` → `frontend/` (clearer naming)
- Merged duplicate `architecture/` folders
- Single documentation location: `docs/architecture/`
- Removed all Python cache files

**Archived**:
- Old Streamlit UI → `archive/v1.0-streamlit/`
- Unused v1.0 scripts → `archive/unused-scripts/`

**Documentation**:
- Created `PROJECT_STRUCTURE.md` - Navigation guide
- Created `CLEANUP_SUMMARY.md` - What was cleaned and why
- Updated `11-implementation-changelog.md` - Today's changes

### 🔧 Fixed

- Import issues in store split modules (standalone import support)
- Test file now uses direct module loading to bypass package `__init__` issues

---

## [1.0.0] - 2026-01-24

### Initial Release

**Core Features**:
- Multi-agent architecture (6 agents)
- Three-tier cart system (Cheaper/Balanced/Conscious)
- Streamlit UI
- LLM integration (optional)
- Deterministic scoring engine
- EWG + FDA safety checks
- Seasonality scoring
- Opik monitoring integration

**Documentation**:
- Complete architecture documentation (13 files)
- LLM integration guide
- UI flows and data flows
- Deployment guide

---

## Version Naming Convention

- **Major (X.0.0)**: New features, breaking changes, architecture changes
- **Minor (0.X.0)**: New features, backwards compatible
- **Patch (0.0.X)**: Bug fixes, documentation updates

---

## Quick Links

- [Latest Changes](docs/architecture/implementation-status.md)
- [Project Structure](PROJECT_STRUCTURE.md)
- [Store Classification Docs](docs/architecture/STORE_CLASSIFICATION_SYSTEM.md)
- [Version History](docs/architecture/STORE_CLASSIFICATION_VERSION_HISTORY.md)
- [Rename Log](RENAME_LOG.md)

---

**Current Version**: 2.1.0
**Last Updated**: 2026-01-29
