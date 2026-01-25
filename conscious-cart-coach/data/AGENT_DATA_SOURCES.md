# Agent Data Sources & Update Schedules

## Overview

The Conscious Cart Coach uses a multi-agent architecture where each agent maintains its own data store with different refresh schedules aligned to source update frequencies.

---

## Agent Summary

| Agent | Data Store | Refresh Schedule | Primary Sources |
|-------|-----------|------------------|-----------------|
| ProductAgent | `alternatives/*.csv` | Hourly | FreshDirect, Store APIs |
| SafetyAgent | `flags/product_flags.json` | Daily (recalls), Annual (EWG) | FDA API, EWG |
| UserAgent | `users/{user_id}/` | Real-time | User interactions |
| **Seasonal/Regional** | `seasonal_regional.py` | Annual | NJ Dept of Ag, Rutgers |

---

## 1. ProductAgent

**Purpose:** Tracks product availability, prices, and tier assignments

**Data Files:**
- `data/alternatives/alternatives_template.csv`

**Refresh:** Hourly (prices/availability change frequently)

**Source:** FreshDirect product listings

| Field | Description | Update Frequency |
|-------|-------------|------------------|
| product_name | Product display name | Hourly |
| brand | Brand name | Hourly |
| price | Current price | Hourly |
| certifications | Organic, Local, etc. | Weekly |
| selected_tier | cheaper/balanced/conscious | Manual |

---

## 2. SafetyAgent

**Purpose:** Enforces food safety rules (FDA recalls, EWG pesticide lists)

**Data Files:**
- `data/flags/product_flags.json`
- `data/flags/recall_history.csv`

### FDA Recalls

**Refresh:** Daily

**Source:** FDA Food Recall API
- URL: `https://api.fda.gov/food/enforcement.json`
- Trust Level: **OFFICIAL (Federal Government)**

| Field | Description |
|-------|-------------|
| type | "recall" |
| title | Recall title |
| severity | Class I (dangerous) / Class II / Class III |
| affected_tiers | Which product tiers affected |
| recommendation | Action to take |

### EWG Dirty Dozen / Clean Fifteen

**Refresh:** Annual (typically March/April)

**Source:** Environmental Working Group
- URL: `https://www.ewg.org/foodnews/`
- Trust Level: **Non-profit research organization**

**Current Version:** 2024

| List | Items | Organic Rule |
|------|-------|--------------|
| Dirty Dozen | strawberries, spinach, kale, grapes, peaches, pears, nectarines, apples, bell peppers, cherries, blueberries, green beans | **Required** |
| Clean Fifteen | avocados, corn, pineapple, onions, papaya, peas, asparagus, honeydew, kiwi, cabbage, watermelon, mushrooms, mangoes, sweet potatoes, carrots | Optional |

---

## 3. UserAgent

**Purpose:** Tracks user preferences, purchase history, and personalization

**Data Files:**
- `data/users/{user_id}/profile.json`
- `data/users/{user_id}/history.csv`

**Refresh:** Real-time (per interaction)

| Data Type | Description |
|-----------|-------------|
| tier_preference | User's default tier (cheaper/balanced/conscious) |
| personal_staples | Frequently purchased items |
| dietary | Restrictions (vegetarian, gluten-free, etc.) |
| category_favorites | Preferred products per category |

---

## 4. Seasonal/Regional Module

**Purpose:** Dynamic seasonality and local sourcing for NJ/Mid-Atlantic

**Data File:** `src/data_processing/seasonal_regional.py`

**Refresh:** Annual (crop calendar updates)

### Primary Data Sources

| Source | Authority | Trust Level | URL |
|--------|-----------|-------------|-----|
| Jersey Fresh Program | NJ Dept of Agriculture | **OFFICIAL (State Gov)** | https://jerseyfresh.nj.gov/ |
| Rutgers Extension | Rutgers University | **ACADEMIC** | https://njaes.rutgers.edu/ |
| USDA NASS | US Dept of Agriculture | **OFFICIAL (Federal Gov)** | https://www.nass.usda.gov/ |
| NJ Dept of Agriculture | State of New Jersey | **OFFICIAL (State Gov)** | https://www.nj.gov/agriculture/ |

### Trusted Regional Sources

| Source | State | Distance | Trust Level | Verification |
|--------|-------|----------|-------------|--------------|
| Jersey Fresh | NJ | 0 mi | **Official** | NJ Dept of Ag certified label since 1984 |
| Lancaster Farm Fresh | PA | 80 mi | **Verified** | Cooperative of 100+ PA farms, certified organic since 1998 |
| Black Dirt Region | NY | 60 mi | **Verified** | Orange County NY muckland, 26,000 acres organic soil |
| Satur Farms | NY | 100 mi | **Verified** | Long Island farm, supplies FreshDirect since 1997 |
| Ronnybrook | NY | 90 mi | **Verified** | Hudson Valley dairy, family-owned since 1941 |
| Long Island | NY | 50 mi | Generic | Cornell Cooperative Extension tracked |
| Hudson Valley | NY | 70 mi | Generic | Diverse farming region |
| "Local" | - | 50 mi | Generic | Self-declared, verify with store |

### NJ Crop Calendar (35+ crops)

**Sources:** Jersey Fresh Availability Guide + Rutgers FS1218 Planting Calendar

| Crop | Peak Season | Storage Season | NJ Rank |
|------|-------------|----------------|---------|
| Blueberry | Jun-Aug | - | #3 nationally |
| Cranberry | Sep-Nov | - | #4 nationally |
| Peach | Jul-Sep | - | #4 nationally |
| Tomato | Jul-Sep | - | "Jersey Tomato" protected term |
| Spinach | Mar-May, Sep-Nov | - | - |
| Apple | Aug-Oct | Nov-Mar | - |
| Potato | Jul-Oct | Nov-May | - |

---

## 5. Impact Scoring

**Purpose:** Multi-dimensional scoring (Health, Environmental, Social, Packaging, Animal Welfare)

**Weights:** Configurable per user preference

### Default Weights

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Health | 30% | EWG pesticides, recalls, nutrition |
| Environmental | 20% | Carbon footprint, local sourcing, seasonality |
| Social | 15% | Fair trade, labor practices, B-Corp |
| Packaging | 15% | Recyclability, plastic reduction |
| Animal Welfare | 10% | Cage-free, pasture-raised, humane |
| Price | 10% | Cost consideration |

### Presets

| Preset | Primary Focus |
|--------|---------------|
| health_focused | Health 50%, Price 10% |
| eco_warrior | Environmental 35%, Packaging 25% |
| budget_conscious | Price 55%, Health 20% |
| animal_lover | Animal Welfare 40%, Health 15% |
| balanced | Default weights |

---

## Environmental Bonuses

### Seasonal Bonuses (added to Environmental score)

| Status | Bonus | Description |
|--------|-------|-------------|
| Peak Season | +40 | Best quality, lowest transport |
| Available | +35 | In season, local |
| Storage | +25 | Local storage crops |
| Off Season | -10 | Penalty if imported |

### Regional Bonuses (added to Environmental + Social scores)

| Priority | States | Environmental | Social |
|----------|--------|---------------|--------|
| Priority 1 | NJ | +35 | +20 |
| Priority 2 | PA, NY | +25 | +15 |
| Priority 3 | Further | +15 | +10 |

---

## Data Flow

```
User Request
     │
     ▼
┌─────────────────┐
│  Orchestrator   │
└────────┬────────┘
         │
    ┌────┴────┬──────────┐
    ▼         ▼          ▼
┌───────┐ ┌───────┐ ┌───────┐
│Product│ │Safety │ │ User  │
│ Agent │ │ Agent │ │ Agent │
└───┬───┘ └───┬───┘ └───┬───┘
    │         │         │
    ▼         ▼         ▼
┌───────┐ ┌───────┐ ┌───────┐
│  CSV  │ │ JSON  │ │Profile│
│ Store │ │Flags  │ │History│
└───────┘ └───────┘ └───────┘
         │
         ▼
   ┌───────────┐
   │Impact     │◄── Seasonal/Regional
   │Scoring    │    Module
   └─────┬─────┘
         │
         ▼
   ┌───────────┐
   │Facts Pack │
   └─────┬─────┘
         │
         ▼
   ┌───────────┐
   │LLM Decision│
   │  Engine   │
   └───────────┘
```

---

## Verification Checklist

Before deploying, verify:

- [ ] FDA Recall API accessible
- [ ] EWG list version matches current year (after March)
- [ ] FreshDirect product data is current
- [ ] Crop calendar reflects current growing season
- [ ] Regional sources are still operating
- [ ] User data stores are writable

---

*Last Updated: 2024-01*
*Version: 1.0*
