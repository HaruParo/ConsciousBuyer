#!/usr/bin/env python3
"""
Conscious Cart Coach CLI - Data inspection and management.

Commands:
  inspect     Inspect facts store data (SQLite or CSV)
  refresh     Refresh data from sources
  status      Show system status
  query       Run sample queries

Usage:
  python -m src.cli inspect [table]
  python -m src.cli refresh [--live]
  python -m src.cli status
  python -m src.cli query <product>
"""

import argparse
from datetime import datetime
from pathlib import Path

from .data.facts_store import FactsStore
from .data.refresh_jobs import RefreshManager
from .agents.safety_agent_v2 import SafetyAgent
from .agents.seasonal_agent import SeasonalAgent


def print_table(headers: list[str], rows: list[list], max_width: int = 40):
    """Print a formatted table."""
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            cell_str = str(cell)[:max_width]
            if i < len(widths):
                widths[i] = max(widths[i], len(cell_str))

    header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    print(header_line)
    print("-" * len(header_line))

    for row in rows:
        row_strs = [str(cell)[:max_width].ljust(widths[i]) if i < len(widths) else str(cell)
                    for i, cell in enumerate(row)]
        print(" | ".join(row_strs))


def cmd_inspect(args):
    """Inspect facts store data."""
    store = FactsStore()

    if args.table == "all" or not args.table:
        print("=" * 70)
        print("FACTS STORE SUMMARY")
        print(f"Database: {store.db_path}")
        print(f"Generated: {datetime.now().isoformat()}")
        print("=" * 70)
        print()

        counts = store.get_table_counts()
        refresh_info = store.get_refresh_info()

        print("TABLES:")
        for table, count in counts.items():
            info = refresh_info.get(table, {})
            last = info.get("last_refreshed", "Never")[:19] if info.get("last_refreshed") else "Never"
            trust = info.get("trust_level", "Unknown")
            print(f"  {table:12} {count:4} records | Last refresh: {last} | Trust: {trust}")

        print()
        stale = store.needs_refresh()
        if stale:
            print(f"NEEDS REFRESH: {', '.join(stale)}")
        else:
            print("All tables are fresh.")

    elif args.table == "recalls":
        recalls = store.get_recalls()
        print(f"ONGOING FDA RECALLS ({len(recalls)})")
        print("=" * 70)

        headers = ["ID", "Class", "Product", "Contaminant", "Distribution"]
        rows = []
        for r in recalls:
            rows.append([
                r.get("recall_id", "")[:13],
                r.get("classification", ""),
                r.get("product_description", "")[:25],
                r.get("contaminant", "")[:18],
                r.get("distribution_pattern", "")[:20],
            ])
        print_table(headers, rows)

    elif args.table == "ewg":
        print("EWG DIRTY DOZEN / CLEAN FIFTEEN")
        print("=" * 70)

        # Dirty Dozen
        print("\nDIRTY DOZEN (Organic Required):")
        ewg_data = store._get_conn().execute(
            "SELECT * FROM ewg WHERE list = 'dirty_dozen' ORDER BY rank"
        ).fetchall()

        headers = ["Rank", "Item", "Score", "Notes"]
        rows = [[r["rank"], r["item"], r["pesticide_residue_score"], r["notes"][:35]]
                for r in ewg_data]
        print_table(headers, rows)

        # Clean Fifteen
        print("\nCLEAN FIFTEEN (Conventional OK):")
        ewg_data = store._get_conn().execute(
            "SELECT * FROM ewg WHERE list = 'clean_fifteen' ORDER BY rank"
        ).fetchall()

        rows = [[r["rank"], r["item"], r["pesticide_residue_score"], r["notes"][:35]]
                for r in ewg_data]
        print_table(headers, rows)

    elif args.table == "stores":
        stores = store.get_stores()
        print(f"STORES SERVING MIDDLESEX COUNTY ({len(stores)})")
        print("=" * 70)

        headers = ["Store", "Type", "Delivery", "Notes"]
        rows = []
        for s in stores:
            rows.append([
                s.get("store_name", ""),
                s.get("store_type", ""),
                "Yes" if s.get("delivery_available") else "No",
                s.get("notes", "")[:30],
            ])
        print_table(headers, rows)

    elif args.table == "seasonal":
        month_names = ["jan", "feb", "mar", "apr", "may", "jun",
                       "jul", "aug", "sep", "oct", "nov", "dec"]
        current_month = month_names[datetime.now().month - 1]

        crops = store.get_in_season_now()
        print(f"IN SEASON NOW ({current_month.upper()}) - {len(crops)} crops")
        print("=" * 70)

        peak = [c for c in crops if c.get(current_month, "").lower() == "peak"]
        available = [c for c in crops if c.get(current_month, "").lower() == "available"]
        storage = [c for c in crops if c.get(current_month, "").lower() == "storage"]

        print(f"\nPEAK ({len(peak)}):")
        if peak:
            print("  " + ", ".join(c["crop"] for c in peak))

        print(f"\nAVAILABLE ({len(available)}):")
        if available:
            print("  " + ", ".join(c["crop"] for c in available))

        print(f"\nSTORAGE ({len(storage)}):")
        if storage:
            print("  " + ", ".join(c["crop"] for c in storage))

    elif args.table == "sources":
        sources = store.get_regional_sources()
        print(f"TRUSTED REGIONAL SOURCES ({len(sources)})")
        print("=" * 70)

        headers = ["Source", "State", "Trust", "Distance"]
        rows = []
        for s in sources:
            rows.append([
                s.get("source_name", ""),
                s.get("state", ""),
                s.get("trust_level", ""),
                f"{s.get('distance_miles', 0)} mi",
            ])
        print_table(headers, rows)


def cmd_refresh(args):
    """Refresh data from sources."""
    manager = RefreshManager()

    if args.live:
        print("Live refresh (fetching from APIs)...")
        results = manager.refresh_all(force=args.force, live=True)
    elif args.force:
        print("Force refresh from CSV...")
        results = manager.refresh_all(force=True)
    else:
        print("Refreshing stale tables from CSV...")
        results = manager.refresh_stale()

    if not results:
        print("Nothing to refresh - all tables are fresh.")
        return

    for table, result in results.items():
        if result.get("skipped"):
            print(f"  {table}: SKIPPED (not stale)")
        elif result["success"]:
            source = result.get("source", "csv")
            count = result.get("record_count", "?")
            print(f"  {table}: OK ({count} records from {source})")
        else:
            print(f"  {table}: FAILED - {result.get('error')}")


def cmd_status(args):
    """Show system status."""
    store = FactsStore()
    manager = RefreshManager(store)

    status = manager.get_status()

    print("=" * 70)
    print("CONSCIOUS CART COACH - SYSTEM STATUS")
    print("=" * 70)
    print()

    print(f"Database: {store.db_path}")
    print(f"Tables: {status['total_tables']}")
    print(f"Stale: {status['stale_tables']}")
    print()

    print("RECORD COUNTS:")
    for table, count in status["record_counts"].items():
        print(f"  {table:12} {count:4} records")
    print()

    print("FRESHNESS:")
    for table, info in status["tables"].items():
        stale = " [NEEDS REFRESH]" if info["is_stale"] else ""
        age = info.get("age_hours", 0)
        max_h = info.get("max_hours", "?")
        print(f"  {table:12} {age:6.1f}h old (max {max_h}h){stale}")

    if status["last_api_errors"]:
        print()
        print("API ERRORS:")
        for table, error in status["last_api_errors"].items():
            print(f"  {table}: {error}")


def cmd_query(args):
    """Run sample queries."""
    safety = SafetyAgent()
    seasonal = SeasonalAgent()

    product = args.product

    print("=" * 70)
    print(f"QUERY: {product}")
    print("=" * 70)

    # Safety check
    print("\nSAFETY:")
    result = safety.check_product(product)
    print(f"  Safe: {result['is_safe']}")
    print(f"  EWG List: {result['ewg']['list']}")
    if result['ewg']['rank']:
        print(f"  EWG Rank: #{result['ewg']['rank']}")
    if result["warnings"]:
        print(f"  Warnings: {', '.join(result['warnings'])}")
    if result["recommendations"]:
        print(f"  Recommendations: {', '.join(result['recommendations'])}")

    # Seasonal check
    print("\nSEASONAL:")
    seasonal_info = seasonal.check_seasonal(product)
    print(f"  In Season: {seasonal_info['is_in_season']}")
    print(f"  Availability: {seasonal_info['availability']}")
    print(f"  Bonus: +{seasonal_info['bonus']} points")
    if seasonal_info.get("notes"):
        print(f"  Notes: {seasonal_info['notes']}")


def main():
    parser = argparse.ArgumentParser(
        description="Conscious Cart Coach CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Inspect command
    inspect_parser = subparsers.add_parser("inspect", help="Inspect facts store data")
    inspect_parser.add_argument(
        "table",
        nargs="?",
        default="all",
        choices=["all", "recalls", "ewg", "stores", "seasonal", "sources"],
        help="Table to inspect"
    )

    # Refresh command
    refresh_parser = subparsers.add_parser("refresh", help="Refresh data")
    refresh_parser.add_argument("--live", action="store_true", help="Fetch from APIs")
    refresh_parser.add_argument("--force", action="store_true", help="Force refresh all")

    # Status command
    subparsers.add_parser("status", help="Show system status")

    # Query command
    query_parser = subparsers.add_parser("query", help="Query a product")
    query_parser.add_argument("product", help="Product name to query")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    commands = {
        "inspect": cmd_inspect,
        "refresh": cmd_refresh,
        "status": cmd_status,
        "query": cmd_query,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
