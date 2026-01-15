"""
Baseline metrics calculation module.
Computes statistics per category for establishing user's baseline purchasing patterns.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import func, text

from .ingest import (
    Category,
    Item,
    ItemCategory,
    Purchase,
    get_engine,
    get_session,
)

logger = logging.getLogger(__name__)


def calculate_category_stats(engine=None) -> dict:
    """
    Calculate statistics for each category using SQL aggregations.

    Returns:
        Dictionary with category statistics
    """
    if engine is None:
        engine = get_engine()

    # Use raw SQL for complex aggregations (PERCENTILE_CONT, MODE)
    query = text("""
        SELECT
            c.category_name,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY p.price) as median_price,
            MIN(p.price) as min_price,
            MAX(p.price) as max_price,
            STDDEV(p.price) as price_volatility,
            MODE() WITHIN GROUP (ORDER BY i.brand) as usual_brand,
            MODE() WITHIN GROUP (ORDER BY i.packaging_type) as common_packaging,
            COUNT(*) as purchase_count,
            AVG(p.quantity) as avg_quantity,
            SUM(p.price * p.quantity) as total_spend,
            MIN(p.timestamp) as first_purchase,
            MAX(p.timestamp) as last_purchase
        FROM purchases p
        JOIN items i ON p.item_id = i.item_id
        JOIN item_categories ic ON i.item_id = ic.item_id
        JOIN categories c ON ic.category_id = c.category_id
        GROUP BY c.category_name
        ORDER BY purchase_count DESC
    """)

    with engine.connect() as conn:
        result = conn.execute(query)
        rows = result.fetchall()
        columns = result.keys()

    stats = {}
    for row in rows:
        row_dict = dict(zip(columns, row))
        category_name = row_dict["category_name"]

        stats[category_name] = {
            "median_price": float(row_dict["median_price"]) if row_dict["median_price"] else None,
            "price_range": [
                float(row_dict["min_price"]) if row_dict["min_price"] else None,
                float(row_dict["max_price"]) if row_dict["max_price"] else None,
            ],
            "usual_brand": row_dict["usual_brand"],
            "common_packaging": row_dict["common_packaging"],
            "volatility": float(row_dict["price_volatility"]) if row_dict["price_volatility"] else 0.0,
            "purchase_count": int(row_dict["purchase_count"]),
            "avg_quantity": float(row_dict["avg_quantity"]) if row_dict["avg_quantity"] else 1.0,
            "total_spend": float(row_dict["total_spend"]) if row_dict["total_spend"] else 0.0,
            "first_purchase": row_dict["first_purchase"].isoformat() if row_dict["first_purchase"] else None,
            "last_purchase": row_dict["last_purchase"].isoformat() if row_dict["last_purchase"] else None,
        }

    return stats


def calculate_summary_stats(engine=None) -> dict:
    """
    Calculate overall summary statistics.

    Returns:
        Dictionary with summary stats
    """
    if engine is None:
        engine = get_engine()

    query = text("""
        SELECT
            COUNT(DISTINCT c.category_id) as total_categories,
            COUNT(DISTINCT i.item_id) as total_items,
            COUNT(*) as total_purchases,
            SUM(p.price * p.quantity) as total_spend,
            AVG(p.price) as avg_price,
            MIN(p.timestamp) as date_range_start,
            MAX(p.timestamp) as date_range_end
        FROM purchases p
        JOIN items i ON p.item_id = i.item_id
        JOIN item_categories ic ON i.item_id = ic.item_id
        JOIN categories c ON ic.category_id = c.category_id
    """)

    with engine.connect() as conn:
        result = conn.execute(query)
        row = result.fetchone()
        columns = result.keys()

    row_dict = dict(zip(columns, row))

    return {
        "total_categories": int(row_dict["total_categories"]) if row_dict["total_categories"] else 0,
        "total_items": int(row_dict["total_items"]) if row_dict["total_items"] else 0,
        "total_purchases": int(row_dict["total_purchases"]) if row_dict["total_purchases"] else 0,
        "total_spend": float(row_dict["total_spend"]) if row_dict["total_spend"] else 0.0,
        "avg_price": float(row_dict["avg_price"]) if row_dict["avg_price"] else 0.0,
        "date_range": {
            "start": row_dict["date_range_start"].isoformat() if row_dict["date_range_start"] else None,
            "end": row_dict["date_range_end"].isoformat() if row_dict["date_range_end"] else None,
        },
        "generated_at": datetime.now().isoformat(),
    }


def calculate_baseline(engine=None) -> dict:
    """
    Calculate complete baseline metrics from historical purchases.

    Returns:
        Dictionary with summary and per-category statistics
    """
    if engine is None:
        engine = get_engine()

    logger.info("Calculating baseline statistics...")

    summary = calculate_summary_stats(engine)
    categories = calculate_category_stats(engine)

    baseline = {
        "summary": summary,
        "categories": categories,
    }

    logger.info(
        f"Baseline calculated: {summary['total_categories']} categories, "
        f"{summary['total_purchases']} purchases, "
        f"${summary['total_spend']:.2f} total spend"
    )

    return baseline


def get_baseline(category_name: str, engine=None) -> Optional[dict]:
    """
    Get baseline statistics for a specific category.

    Args:
        category_name: Name of the category
        engine: SQLAlchemy engine (optional)

    Returns:
        Dictionary with category statistics or None if not found
    """
    if engine is None:
        engine = get_engine()

    stats = calculate_category_stats(engine)
    return stats.get(category_name)


def get_category_breakdown(engine=None) -> dict:
    """
    Get spending breakdown by product category.

    Returns:
        Dictionary with category spending breakdown
    """
    if engine is None:
        engine = get_engine()

    query = text("""
        SELECT
            c.category_name,
            SUM(p.price * p.quantity) as total_spend,
            COUNT(*) as purchase_count
        FROM purchases p
        JOIN items i ON p.item_id = i.item_id
        JOIN item_categories ic ON i.item_id = ic.item_id
        JOIN categories c ON ic.category_id = c.category_id
        GROUP BY c.category_name
        ORDER BY total_spend DESC
    """)

    with engine.connect() as conn:
        result = conn.execute(query)
        rows = result.fetchall()

    total_spend = sum(row[1] for row in rows if row[1])

    breakdown = {}
    for row in rows:
        category_name, spend, count = row
        breakdown[category_name] = {
            "total_spend": float(spend) if spend else 0.0,
            "purchase_count": int(count),
            "percentage": (float(spend) / total_spend * 100) if spend and total_spend else 0.0,
        }

    return breakdown


def get_top_categories(n: int = 10, by: str = "spend", engine=None) -> list:
    """
    Get top N categories by spend or purchase count.

    Args:
        n: Number of categories to return
        by: Sort by "spend" or "count"
        engine: SQLAlchemy engine (optional)

    Returns:
        List of top categories with stats
    """
    breakdown = get_category_breakdown(engine)

    sort_key = "total_spend" if by == "spend" else "purchase_count"
    sorted_categories = sorted(
        breakdown.items(),
        key=lambda x: x[1][sort_key],
        reverse=True
    )

    return [
        {"category": name, **stats}
        for name, stats in sorted_categories[:n]
    ]


def get_price_comparison(category_name: str, price: float, engine=None) -> dict:
    """
    Compare a price against baseline for a category.

    Args:
        category_name: Category to compare against
        price: Price to compare
        engine: SQLAlchemy engine (optional)

    Returns:
        Dictionary with comparison results
    """
    baseline = get_baseline(category_name, engine)

    if not baseline:
        return {"error": f"Category not found: {category_name}"}

    median = baseline["median_price"]
    min_price, max_price = baseline["price_range"]

    if median:
        diff_from_median = price - median
        pct_diff = (diff_from_median / median) * 100 if median else 0
    else:
        diff_from_median = 0
        pct_diff = 0

    return {
        "category": category_name,
        "input_price": price,
        "median_price": median,
        "price_range": baseline["price_range"],
        "difference_from_median": round(diff_from_median, 2),
        "percent_difference": round(pct_diff, 1),
        "assessment": _assess_price(price, median, min_price, max_price),
    }


def _assess_price(price: float, median: float, min_price: float, max_price: float) -> str:
    """Assess if a price is low, typical, or high for a category."""
    if not median:
        return "unknown"

    pct_diff = ((price - median) / median) * 100

    if pct_diff < -20:
        return "significantly_below_median"
    elif pct_diff < -5:
        return "below_median"
    elif pct_diff <= 5:
        return "typical"
    elif pct_diff <= 20:
        return "above_median"
    else:
        return "significantly_above_median"


def export_baseline(output_path: Path = None, engine=None) -> dict:
    """
    Export baseline statistics to JSON file.

    Args:
        output_path: Path to output JSON file
        engine: SQLAlchemy engine (optional)

    Returns:
        The baseline dictionary that was exported
    """
    if output_path is None:
        output_path = Path("data/processed/baseline_stats.json")

    baseline = calculate_baseline(engine)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(baseline, f, indent=2)

    logger.info(f"Exported baseline statistics to {output_path}")
    return baseline


def main():
    """CLI entry point for baseline calculation."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Calculate baseline statistics per category"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/baseline_stats.json",
        help="Output path for baseline stats JSON"
    )
    parser.add_argument(
        "--category",
        type=str,
        help="Show stats for a specific category"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=0,
        help="Show top N categories by spend"
    )

    args = parser.parse_args()

    try:
        if args.category:
            stats = get_baseline(args.category)
            if stats:
                print(f"\nBaseline for '{args.category}':")
                print("-" * 40)
                for key, value in stats.items():
                    print(f"  {key}: {value}")
            else:
                print(f"Category not found: {args.category}")

        elif args.top > 0:
            top = get_top_categories(args.top)
            print(f"\nTop {args.top} Categories by Spend:")
            print("-" * 50)
            for i, cat in enumerate(top, 1):
                print(f"  {i}. {cat['category']}: ${cat['total_spend']:.2f} ({cat['purchase_count']} purchases)")

        else:
            baseline = export_baseline(args.output)
            summary = baseline["summary"]

            print(f"\nBaseline Statistics Generated:")
            print("=" * 50)
            print(f"  Total Categories: {summary['total_categories']}")
            print(f"  Total Items: {summary['total_items']}")
            print(f"  Total Purchases: {summary['total_purchases']}")
            print(f"  Total Spend: ${summary['total_spend']:.2f}")
            print(f"  Average Price: ${summary['avg_price']:.2f}")
            print(f"  Date Range: {summary['date_range']['start'][:10]} to {summary['date_range']['end'][:10]}")
            print(f"\nExported to: {args.output}")

            print(f"\nTop 10 Categories by Spend:")
            print("-" * 50)
            sorted_cats = sorted(
                baseline["categories"].items(),
                key=lambda x: x[1]["total_spend"],
                reverse=True
            )[:10]
            for cat_name, stats in sorted_cats:
                print(f"  {cat_name}: ${stats['total_spend']:.2f} ({stats['purchase_count']} purchases)")

    except Exception as e:
        logger.error(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
