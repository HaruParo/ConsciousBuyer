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
