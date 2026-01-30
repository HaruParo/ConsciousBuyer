Generate data/alternatives/alternatives_template.json for manual filling.

For TOP 10 most-purchased categories from baseline_stats.json:

Structure per category:
{
  "category_name": {
    "cheaper": {
      "brand": "",
      "est_price": null,
      "packaging": "",
      "why_cheaper": "",
      "trade_offs": "",
      "source_url": ""
    },
    "balanced": {
      "brand": "",
      "est_price": null,
      "packaging": "",
      "notes": "",
      "source_url": ""
    },
    "conscious": {
      "brand": "",
      "est_price": null,
      "packaging": "",
      "why_conscious": "",
      "certifications": [],
      "source_url": ""
    }
  }
}

Also create data/alternatives/RESEARCH_GUIDE.md with:
- Instructions for researching each tier
- What to look for (certifications, packaging, sourcing)
- Where to search (brand websites, specialty retailers)
- Example entries for miso_paste

NOTE: User will manually fill this - create empty template only


----------------Response----------------


Files Created
data/alternatives/alternatives_template.json
Empty template for top 10 most-purchased categories:

produce_greens (43 purchases)
produce_onions (40 purchases)
produce_root_veg (39 purchases)
fruit_tropical (33 purchases)
produce_tomatoes (18 purchases)
milk (18 purchases)
fruit_berries (17 purchases)
produce_peppers (15 purchases)
produce_squash (15 purchases)
produce_beans (14 purchases)
Each category has three tiers: cheaper, balanced, conscious

data/alternatives/RESEARCH_GUIDE.md
Research guide including:

Tier definitions and what to look for
Certification reference table (USDA Organic, Fair Trade, B-Corp, etc.)
Where to research (retailers, brand sites, directories)
Complete example entry for fermented/miso_paste
Research checklist
Category-specific notes for produce, milk, berries
