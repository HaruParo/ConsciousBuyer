#!/usr/bin/env python3
"""
Facts Inspector - CLI tool to verify and inspect all data in the facts store.

Run: python -m src.data_processing.facts_inspector [command]

Commands:
  all         Show summary of all data tables
  recalls     Show FDA recalls data
  ewg         Show EWG Dirty Dozen / Clean Fifteen
  stores      Show stores serving Middlesex County
  seasonal    Show NJ crop calendar
  sources     Show all data sources with trust levels
  export      Export all data to CSV for manual review
"""

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

# Data directories
DATA_DIR = Path(__file__).parent.parent.parent / "data"
FLAGS_DIR = DATA_DIR / "flags"
STORES_DIR = DATA_DIR / "stores"
SEASONAL_DIR = DATA_DIR / "seasonal"
EXPORT_DIR = DATA_DIR / "exports"


def load_csv_with_comments(filepath: Path) -> tuple[list[str], list[dict]]:
    """Load CSV file, returning comments and data separately."""
    comments = []
    data = []

    if not filepath.exists():
        return comments, data

    with open(filepath, newline="", encoding="utf-8") as f:
        lines = f.readlines()

    # Separate comments from data
    data_lines = []
    for line in lines:
        if line.startswith("#"):
            comments.append(line.strip("# \n"))
        else:
            data_lines.append(line)

    if data_lines:
        reader = csv.DictReader(data_lines)
        data = list(reader)

    return comments, data


def print_table(headers: list[str], rows: list[list], max_width: int = 40):
    """Print a formatted table."""
    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            cell_str = str(cell)[:max_width]
            if i < len(widths):
                widths[i] = max(widths[i], len(cell_str))

    # Print header
    header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    print(header_line)
    print("-" * len(header_line))

    # Print rows
    for row in rows:
        row_strs = [str(cell)[:max_width].ljust(widths[i]) if i < len(widths) else str(cell)
                    for i, cell in enumerate(row)]
        print(" | ".join(row_strs))


def show_recalls():
    """Display FDA recalls data."""
    filepath = FLAGS_DIR / "fda_recalls.csv"
    comments, data = load_csv_with_comments(filepath)

    print("=" * 80)
    print("FDA RECALLS DATA")
    print("=" * 80)
    print(f"File: {filepath}")
    print()

    # Show metadata from comments
    print("METADATA (from file header):")
    for comment in comments[:10]:  # First 10 comment lines
        if comment:
            print(f"  {comment}")
    print()

    # Count by status
    ongoing = [r for r in data if r.get("status", "").lower() == "ongoing"]
    terminated = [r for r in data if r.get("status", "").lower() == "terminated"]

    print(f"SUMMARY:")
    print(f"  Total records: {len(data)}")
    print(f"  Ongoing recalls: {len(ongoing)}")
    print(f"  Terminated recalls: {len(terminated)}")
    print()

    # Count by classification
    class_counts = {}
    for r in ongoing:
        cls = r.get("classification", "Unknown")
        class_counts[cls] = class_counts.get(cls, 0) + 1

    print("ONGOING BY CLASSIFICATION:")
    for cls, count in sorted(class_counts.items()):
        print(f"  {cls}: {count}")
    print()

    # Show ongoing recalls
    if ongoing:
        print("ONGOING RECALLS:")
        headers = ["ID", "Classification", "Product", "Contaminant", "Distribution"]
        rows = []
        for r in ongoing:
            rows.append([
                r.get("recall_id", ""),
                r.get("classification", ""),
                r.get("product_description", "")[:35],
                r.get("contaminant", "")[:20],
                r.get("distribution_pattern", "")[:25],
            ])
        print_table(headers, rows)
    print()


def show_ewg():
    """Display EWG lists data."""
    filepath = FLAGS_DIR / "ewg_lists.csv"
    comments, data = load_csv_with_comments(filepath)

    print("=" * 80)
    print("EWG DIRTY DOZEN / CLEAN FIFTEEN")
    print("=" * 80)
    print(f"File: {filepath}")
    print()

    # Show metadata
    print("METADATA (from file header):")
    for comment in comments[:15]:
        if comment:
            print(f"  {comment}")
    print()

    # Separate lists
    dirty_dozen = [r for r in data if r.get("list") == "dirty_dozen"]
    clean_fifteen = [r for r in data if r.get("list") == "clean_fifteen"]

    print(f"SUMMARY:")
    print(f"  Dirty Dozen items: {len(dirty_dozen)}")
    print(f"  Clean Fifteen items: {len(clean_fifteen)}")
    print()

    # Show Dirty Dozen
    print("DIRTY DOZEN (Organic STRONGLY recommended):")
    headers = ["Rank", "Item", "Pesticide Score", "Notes"]
    rows = []
    for r in sorted(dirty_dozen, key=lambda x: int(x.get("rank", 0))):
        rows.append([
            r.get("rank", ""),
            r.get("item", ""),
            r.get("pesticide_residue_score", ""),
            r.get("notes", "")[:40],
        ])
    print_table(headers, rows)
    print()

    # Show Clean Fifteen
    print("CLEAN FIFTEEN (Conventional OK):")
    rows = []
    for r in sorted(clean_fifteen, key=lambda x: int(x.get("rank", 0))):
        rows.append([
            r.get("rank", ""),
            r.get("item", ""),
            r.get("pesticide_residue_score", ""),
            r.get("notes", "")[:40],
        ])
    print_table(headers, rows)
    print()


def show_stores():
    """Display stores data."""
    filepath = STORES_DIR / "nj_middlesex_stores.csv"
    comments, data = load_csv_with_comments(filepath)

    print("=" * 80)
    print("STORES SERVING MIDDLESEX COUNTY, NJ")
    print("=" * 80)
    print(f"File: {filepath}")
    print()

    # Show metadata
    print("METADATA (from file header):")
    for comment in comments:
        if comment:
            print(f"  {comment}")
    print()

    # Count by type
    serves = [r for r in data if r.get("serves_middlesex", "").lower() == "yes"]
    delivery = [r for r in serves if r.get("delivery_available", "").lower() == "yes"]

    type_counts = {}
    for r in serves:
        t = r.get("store_type", "Unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    print(f"SUMMARY:")
    print(f"  Total stores serving Middlesex: {len(serves)}")
    print(f"  With delivery: {len(delivery)}")
    print()

    print("BY TYPE:")
    for t, count in sorted(type_counts.items()):
        print(f"  {t}: {count}")
    print()

    # Show all stores
    print("ALL STORES:")
    headers = ["Store", "Type", "Delivery", "Notes"]
    rows = []
    for r in serves:
        rows.append([
            r.get("store_name", ""),
            r.get("store_type", ""),
            r.get("delivery_available", ""),
            r.get("notes", "")[:35],
        ])
    print_table(headers, rows)
    print()


def show_seasonal():
    """Display seasonal/regional data."""
    crop_file = SEASONAL_DIR / "nj_crop_calendar.csv"
    sources_file = SEASONAL_DIR / "trusted_regional_sources.csv"

    print("=" * 80)
    print("NJ SEASONAL & REGIONAL DATA")
    print("=" * 80)

    # Crop calendar
    if crop_file.exists():
        comments, data = load_csv_with_comments(crop_file)
        print(f"\nCROP CALENDAR: {crop_file}")
        print(f"  Total crops: {len(data)}")

        # Show what's in season now
        month_names = ["jan", "feb", "mar", "apr", "may", "jun",
                       "jul", "aug", "sep", "oct", "nov", "dec"]
        current_month = month_names[datetime.now().month - 1]

        in_season = []
        for r in data:
            availability = r.get(current_month, "").lower()
            if availability in ["peak", "available", "storage"]:
                in_season.append((r.get("crop", ""), availability))

        print(f"\n  IN SEASON NOW ({current_month.upper()}):")
        for crop, status in sorted(in_season):
            print(f"    {crop}: {status}")

    # Regional sources
    if sources_file.exists():
        comments, data = load_csv_with_comments(sources_file)
        print(f"\nTRUSTED REGIONAL SOURCES: {sources_file}")
        print(f"  Total sources: {len(data)}")

        headers = ["Source", "State", "Trust Level", "Distance"]
        rows = []
        for r in data:
            rows.append([
                r.get("source_name", ""),
                r.get("state", ""),
                r.get("trust_level", ""),
                r.get("distance_miles", "") + " mi",
            ])
        print()
        print_table(headers, rows)
    print()


def show_sources():
    """Show all data sources with trust levels and refresh schedules."""
    print("=" * 80)
    print("ALL DATA SOURCES")
    print("=" * 80)
    print()

    sources = [
        {
            "name": "FDA Recalls",
            "file": str(FLAGS_DIR / "fda_recalls.csv"),
            "trust": "OFFICIAL (Federal Government)",
            "refresh": "Daily",
            "url": "https://api.fda.gov/food/enforcement.json",
        },
        {
            "name": "EWG Lists",
            "file": str(FLAGS_DIR / "ewg_lists.csv"),
            "trust": "Research Non-profit",
            "refresh": "Annual (March/April)",
            "url": "https://www.ewg.org/foodnews/",
        },
        {
            "name": "NJ Stores",
            "file": str(STORES_DIR / "nj_middlesex_stores.csv"),
            "trust": "Manual verification",
            "refresh": "Monthly",
            "url": "N/A",
        },
        {
            "name": "NJ Crop Calendar",
            "file": str(SEASONAL_DIR / "nj_crop_calendar.csv"),
            "trust": "Official (Rutgers/USDA)",
            "refresh": "Annual",
            "url": "https://njaes.rutgers.edu/",
        },
        {
            "name": "Regional Sources",
            "file": str(SEASONAL_DIR / "trusted_regional_sources.csv"),
            "trust": "Verified non-profits",
            "refresh": "Quarterly",
            "url": "Various",
        },
    ]

    headers = ["Source", "Trust Level", "Refresh", "File"]
    rows = []
    for s in sources:
        exists = "✓" if Path(s["file"]).exists() else "✗"
        rows.append([
            f"{exists} {s['name']}",
            s["trust"],
            s["refresh"],
            Path(s["file"]).name,
        ])

    print_table(headers, rows, max_width=50)
    print()

    # Show URLs
    print("SOURCE URLS:")
    for s in sources:
        print(f"  {s['name']}: {s['url']}")
    print()


def show_all():
    """Show summary of all data."""
    print("=" * 80)
    print("FACTS STORE SUMMARY")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 80)
    print()

    # Quick counts
    files_info = [
        ("FDA Recalls", FLAGS_DIR / "fda_recalls.csv"),
        ("EWG Lists", FLAGS_DIR / "ewg_lists.csv"),
        ("NJ Stores", STORES_DIR / "nj_middlesex_stores.csv"),
        ("Crop Calendar", SEASONAL_DIR / "nj_crop_calendar.csv"),
        ("Regional Sources", SEASONAL_DIR / "trusted_regional_sources.csv"),
    ]

    print("DATA FILES:")
    for name, path in files_info:
        if path.exists():
            _, data = load_csv_with_comments(path)
            print(f"  ✓ {name}: {len(data)} records")
        else:
            print(f"  ✗ {name}: NOT FOUND")

    print()
    print("Run with specific command for details:")
    print("  python -m src.data_processing.facts_inspector recalls")
    print("  python -m src.data_processing.facts_inspector ewg")
    print("  python -m src.data_processing.facts_inspector stores")
    print("  python -m src.data_processing.facts_inspector seasonal")
    print("  python -m src.data_processing.facts_inspector sources")
    print()


def export_all():
    """Export all data to timestamped CSV files for review."""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("=" * 80)
    print(f"EXPORTING ALL DATA TO: {EXPORT_DIR}")
    print("=" * 80)
    print()

    files_to_export = [
        ("fda_recalls", FLAGS_DIR / "fda_recalls.csv"),
        ("ewg_lists", FLAGS_DIR / "ewg_lists.csv"),
        ("nj_stores", STORES_DIR / "nj_middlesex_stores.csv"),
        ("crop_calendar", SEASONAL_DIR / "nj_crop_calendar.csv"),
        ("regional_sources", SEASONAL_DIR / "trusted_regional_sources.csv"),
    ]

    for name, src_path in files_to_export:
        if src_path.exists():
            dst_path = EXPORT_DIR / f"{name}_{timestamp}.csv"
            # Copy without comments for clean export
            _, data = load_csv_with_comments(src_path)
            if data:
                with open(dst_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                print(f"  ✓ Exported: {dst_path.name} ({len(data)} rows)")
            else:
                print(f"  ✗ Skipped {name}: no data")
        else:
            print(f"  ✗ Skipped {name}: file not found")

    print()
    print(f"Export complete. Review files in: {EXPORT_DIR}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Inspect and verify facts store data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="all",
        choices=["all", "recalls", "ewg", "stores", "seasonal", "sources", "export"],
        help="What to inspect (default: all)"
    )

    args = parser.parse_args()

    commands = {
        "all": show_all,
        "recalls": show_recalls,
        "ewg": show_ewg,
        "stores": show_stores,
        "seasonal": show_seasonal,
        "sources": show_sources,
        "export": export_all,
    }

    commands[args.command]()


if __name__ == "__main__":
    main()
