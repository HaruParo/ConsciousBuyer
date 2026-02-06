#!/usr/bin/env python3
"""
Add packaging column to source_listings.csv with intelligent inference.

Uses patterns from alternatives_template.csv to infer packaging based on:
- Category (produce, dairy, spices, etc.)
- Product type (loose, bunched, packaged, etc.)
- Product name keywords (clamshell, bag, jar, bottle, etc.)
"""

import csv
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).parent.parent
source_path = PROJECT_ROOT / "data" / "alternatives" / "source_listings.csv"
backup_path = PROJECT_ROOT / "data" / "alternatives" / "source_listings_backup.csv"


# Packaging inference rules based on category and product characteristics
PACKAGING_RULES = {
    # Produce categories
    "produce_greens": {
        "default": "Loose bunch in produce bag + plastic twist-tie",
        "patterns": {
            "baby": "Clear plastic clamshell (recyclable #1 PET)",
            "organic baby": "Clear plastic clamshell (recyclable #1 PET)",
            "clamshell": "Clear plastic clamshell (recyclable #1 PET)",
            "5oz": "Clear plastic clamshell (recyclable #1 PET)",
            "chopped": "Plastic bag",
            "shredded": "Plastic bag",
            "blend": "Clear plastic clamshell (recyclable #1 PET)",
            "mix": "Clear plastic clamshell (recyclable #1 PET)",
        }
    },
    "produce_onions": {
        "default": "Loose bulk in produce bag",
        "patterns": {
            "bag": "Mesh bag",
            "(bag)": "Mesh bag",
            "scallions": "Bunched with twist-tie",
            "garlic": "Loose bulk in produce bag",
            "peeled": "Plastic bag",
            "diced": "Plastic bag",
        }
    },
    "produce_roots": {
        "default": "Loose bulk in produce bag",
        "patterns": {
            "baby": "Plastic bag",
            "peeled": "Plastic bag",
            "shredded": "Plastic bag",
            "(bag)": "Mesh bag",
        }
    },
    "produce_mushrooms": {
        "default": "Clear plastic clamshell (recyclable #1 PET)",
        "patterns": {
            "bulk": "Loose bulk in paper bag",
            "sliced": "Clear plastic clamshell (recyclable #1 PET)",
        }
    },
    "produce_tomatoes": {
        "default": "Loose bulk in produce bag",
        "patterns": {
            "cherry": "Clear plastic clamshell (recyclable #1 PET)",
            "grape": "Clear plastic clamshell (recyclable #1 PET)",
            "clamshell": "Clear plastic clamshell (recyclable #1 PET)",
            "package": "Clear plastic clamshell (recyclable #1 PET)",
        }
    },

    # Dairy categories
    "milk_whole": {
        "default": "Plastic gallon jug (HDPE #2 recyclable)",
        "patterns": {
            "carton": "Gable-top carton (paper/plastic laminate)",
            "half": "Gable-top carton (paper/plastic laminate)",
            "half-gallon": "Gable-top carton (paper/plastic laminate)",
            "bottle": "Plastic bottle (HDPE #2 recyclable)",
        }
    },
    "dairy_yogurt": {
        "default": "Recyclable plastic tub",
        "patterns": {
            "glass": "Glass jar",
            "jar": "Glass jar",
        }
    },
    "dairy_butter": {
        "default": "Paper-wrapped sticks in box",
        "patterns": {
            "tub": "Recyclable plastic tub",
            "spread": "Recyclable plastic tub",
        }
    },
    "dairy_cheese": {
        "default": "Plastic wrap",
        "patterns": {
            "shredded": "Plastic bag",
            "grated": "Recyclable plastic tub",
            "jar": "Glass jar",
        }
    },

    # Proteins
    "chicken": {
        "default": "Vacuum-sealed recyclable packaging",
        "patterns": {
            "tray": "Plastic-wrapped foam tray",
            "fresh": "Plastic-wrapped foam tray",
        }
    },
    "seafood": {
        "default": "Vacuum-sealed recyclable packaging",
        "patterns": {
            "tray": "Plastic-wrapped foam tray",
            "fresh": "Plastic-wrapped foam tray",
        }
    },

    # Grains and rice
    "rice": {
        "default": "Paper bag or plastic bag",
        "patterns": {
            "jar": "Glass jar",
            "bulk": "Loose bulk (sold by pound)",
        }
    },
    "grains": {
        "default": "Paper bag or plastic bag",
        "patterns": {
            "jar": "Glass jar",
            "bulk": "Loose bulk (sold by pound)",
        }
    },

    # Spices and condiments
    "spices_whole": {
        "default": "Glass jar with plastic cap",
        "patterns": {
            "bag": "Opaque white plastic bag",
            "bulk": "Loose bulk, whole pods",
            "pure indian": "Glass jar with plastic cap",  # Small spice jars
        }
    },
    "spices_ground": {
        "default": "Glass jar with plastic cap",
        "patterns": {
            "bag": "Opaque white plastic bag",
            "pure indian": "Glass jar with plastic cap",  # Small spice jars
        }
    },
    "condiments_asian": {
        "default": "Glass bottle",
        "patterns": {
            "jar": "Glass jar",
            "tub": "Recyclable plastic tub",
            "paste": "Glass jar with plastic lid",
            "sauce": "Glass bottle",
            "bottle": "Glass bottle",
        }
    },
    "condiments_oils": {
        "default": "Glass bottle",
        "patterns": {
            "jar": "Glass jar",
            "plastic": "Plastic bottle",
        }
    },

    # Ghee and oils (Pure Indian Foods)
    "ghee": {
        "default": "Glass jar with aluminum cap",
        "patterns": {
            "coconut oil": "Glass jar with aluminum cap",
        }
    },
}


def infer_packaging(category: str, product_name: str, brand: str, size: str) -> str:
    """
    Infer packaging based on category and product characteristics.

    Returns packaging description following alternatives_template.csv patterns.
    """
    # Brand-specific packaging rules
    if "Pure Indian Foods" in brand:
        # Pure Indian Foods packaging
        if category == "dairy_ghee" or "coconut oil" in product_name.lower() or "oil" in product_name.lower():
            return "Glass jar with aluminum cap"
        elif "spice" in category or category == "spices":
            # Check if it's a bag or jar
            if "bag" in product_name.lower() or "blend" in product_name.lower():
                return "Opaque white plastic bag"
            else:
                return "Glass jar with plastic cap"

    # Get category rules
    rules = PACKAGING_RULES.get(category, {"default": "Plastic bag"})

    # Check for pattern matches in product name (case-insensitive)
    name_lower = product_name.lower()
    brand_lower = brand.lower()
    size_lower = size.lower()

    combined_text = f"{name_lower} {brand_lower} {size_lower}"

    # Check each pattern
    for pattern, packaging in rules.get("patterns", {}).items():
        if pattern.lower() in combined_text:
            return packaging

    # Return default packaging for category
    return rules["default"]


def add_packaging_column():
    """Add packaging column to source_listings.csv"""

    # Backup original file
    import shutil
    shutil.copy(source_path, backup_path)
    print(f"✓ Created backup: {backup_path}")

    # Read all rows
    rows = []
    comments = []
    header = None

    with open(source_path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip().strip('"')
            if stripped.startswith('#'):
                comments.append(line.rstrip('\n'))
            elif header is None:
                header = line.rstrip('\n').split(',')
            else:
                rows.append(line.rstrip('\n'))

    print(f"✓ Read {len(rows)} products")
    print(f"✓ Current columns: {', '.join(header)}")

    # Add packaging column after certifications
    if 'packaging' in header:
        print("⚠️  Packaging column already exists!")
        return

    # Insert packaging column after 'certifications' (index 6)
    cert_idx = header.index('certifications')
    new_header = header[:cert_idx+1] + ['packaging'] + header[cert_idx+1:]

    print(f"✓ New columns: {', '.join(new_header)}")

    # Process each row and add packaging
    new_rows = []
    stats = {}

    for row_str in rows:
        # Parse CSV row (handle quotes)
        parts = []
        current = []
        in_quotes = False

        for char in row_str:
            if char == '"':
                in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                parts.append(''.join(current))
                current = []
            else:
                current.append(char)

        if current:
            parts.append(''.join(current))

        # Ensure we have enough columns
        while len(parts) < len(header):
            parts.append('')

        # Extract product info
        category = parts[0] if len(parts) > 0 else ''
        product_name = parts[1] if len(parts) > 1 else ''
        brand = parts[2] if len(parts) > 2 else ''
        size = parts[5] if len(parts) > 5 else ''

        # Infer packaging
        packaging = infer_packaging(category, product_name, brand, size)

        # Track stats
        stats[packaging] = stats.get(packaging, 0) + 1

        # Insert packaging after certifications
        new_parts = parts[:cert_idx+1] + [packaging] + parts[cert_idx+1:]
        new_rows.append(new_parts)

    # Write new CSV
    with open(source_path, 'w', encoding='utf-8', newline='') as f:
        # Write comments
        for comment in comments:
            f.write(comment + '\n')

        # Write header
        writer = csv.writer(f)
        writer.writerow(new_header)

        # Write rows
        for row in new_rows:
            writer.writerow(row)

    print(f"\n✓ Updated {source_path}")
    print(f"\n📊 Packaging Distribution:")
    for packaging, count in sorted(stats.items(), key=lambda x: -x[1])[:15]:
        print(f"  {count:3}x  {packaging}")

    print(f"\nTotal unique packaging types: {len(stats)}")


if __name__ == '__main__':
    add_packaging_column()
