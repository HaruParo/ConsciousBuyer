# Data Directory

> **Purpose**: All data sources for Conscious Cart Coach
> **Last Updated**: 2026-01-29

---

## 📁 Directory Structure

```
data/
├── facts_store.db              # SQLite database (auto-generated)
├── AGENT_DATA_SOURCES.md      # Data source documentation
├── agent_data_sources.csv      # Agent data mappings
├── scoring_bonuses.csv         # Scoring bonus rules
│
├── alternatives/               # Product alternatives
│   ├── alternatives_template.csv
│   ├── source_listings.csv
│   ├── CSV_INSTRUCTIONS.md
│   └── RESEARCH_GUIDE.md
│
├── flags/                      # Safety data
│   ├── ewg_lists.csv          # EWG Dirty Dozen/Clean 15
│   └── fda_recalls.csv        # FDA recall data
│
├── seasonal/                   # Seasonality data
│   ├── nj_crop_calendar.csv
│   └── trusted_regional_sources.csv
│
├── stores/                     # Store inventory
│   └── nj_middlesex_stores.csv
│
├── processed/                  # Processed purchase history
│   ├── items.csv
│   ├── purchases.csv
│   └── categories.csv
│
└── users/                      # User preferences
    └── (user data storage)
```

---

## 📊 Data Sources

### Safety Data (`flags/`)

**EWG Lists** (`ewg_lists.csv`):
- Dirty Dozen (high pesticide)
- Clean Fifteen (low pesticide)
- **Refresh**: Annual
- **Used By**: SafetyAgent

**FDA Recalls** (`fda_recalls.csv`):
- Active recalls
- Advisory notices
- **Refresh**: Daily
- **Used By**: SafetyAgent

### Seasonality (`seasonal/`)

**NJ Crop Calendar** (`nj_crop_calendar.csv`):
- Peak seasons by month
- Local availability
- **Refresh**: Annual
- **Used By**: SeasonalAgent

**Regional Sources** (`trusted_regional_sources.csv`):
- Local farms
- Farmers markets
- **Refresh**: As needed

### Store Data (`stores/`)

**Store Inventory** (`nj_middlesex_stores.csv`):
- Store locations
- Product availability
- Store types (primary/specialty)
- **Refresh**: Monthly

### Product Alternatives (`alternatives/`)

**Templates** (`alternatives_template.csv`):
- Product substitution rules
- Alternative suggestions
- **Used By**: ProductAgent

**Source Listings** (`source_listings.csv`):
- Where to source specialty items
- Store-product mappings

### Purchase History (`processed/`)

**User Data**:
- `items.csv` - Item details
- `purchases.csv` - Purchase records
- `categories.csv` - Category mappings
- **Privacy**: Anonymized
- **Used By**: UserHistoryAgent

---

## 🔄 Data Refresh

### Auto-Refresh System
- **Module**: `src/data/refresh_jobs.py`
- **Checks**: On startup
- **Sources**: CSV files in this directory

### Refresh Schedule

| Data | Frequency | Auto-Refresh |
|------|-----------|--------------|
| FDA Recalls | Daily | ✅ Yes |
| EWG Lists | Annual | ✅ Yes |
| Crop Calendar | Annual | ✅ Yes |
| Store Inventory | Monthly | ⚠️ Manual |
| Alternatives | As needed | ⚠️ Manual |

---

## 🗄️ Database

### facts_store.db (SQLite)

**Purpose**: In-memory cache of CSV data for fast querying

**Auto-Generated**: Creates/updates from CSV files on startup

**Tables**:
- ewg_lists
- fda_recalls
- crop_calendar
- store_inventory
- (and more)

**Management**:
```bash
# Delete and regenerate
rm data/facts_store.db
python -c "from src.data.facts_store import FactsStore; FactsStore()"
```

---

## 📝 Data Format

### CSV Standards
- **Encoding**: UTF-8
- **Delimiter**: Comma (`,`)
- **Headers**: Required
- **Dates**: ISO 8601 (YYYY-MM-DD)

See `alternatives/CSV_INSTRUCTIONS.md` for detailed format specs.

---

## ⚠️ Important Notes

### Do Not Commit
- ❌ `facts_store.db` (auto-generated)
- ❌ User purchase history (privacy)
- ⚠️ Large CSV files (use Git LFS if needed)

### Always Commit
- ✅ EWG lists
- ✅ FDA recalls (sample/test data)
- ✅ Crop calendars
- ✅ Template files
- ✅ Documentation

---

## 🔍 Finding Data

| Need | Location | File |
|------|----------|------|
| Pesticide data | `flags/` | `ewg_lists.csv` |
| Recall info | `flags/` | `fda_recalls.csv` |
| Seasonality | `seasonal/` | `nj_crop_calendar.csv` |
| Store locations | `stores/` | `nj_middlesex_stores.csv` |
| Product alternatives | `alternatives/` | `alternatives_template.csv` |

---

**Navigation**: [↑ Project Root](../) | [Architecture Docs →](../docs/architecture/)
