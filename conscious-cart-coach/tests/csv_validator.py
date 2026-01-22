#!/usr/bin/env python3
"""
CSV Validator for alternatives_template.csv

Validates the product alternatives CSV file for:
- Format compliance (required columns, data types)
- EWG Dirty Dozen / Clean Fifteen compliance
- Recall safety (loads from product_flags.json)
- Tier logic (price ordering, certification requirements)

Supports three use cases:
1. CI/Build-time: Exit codes (0=pass, 1=fail) for automated pipelines
2. Runtime: Import validate_csv_row() for facts_pack validation
3. Manual QA: --verbose flag for detailed human-readable output

Usage:
    # CI mode (default)
    python csv_validator.py

    # Verbose mode for QA
    python csv_validator.py --verbose

    # Validate specific file
    python csv_validator.py --file /path/to/alternatives.csv

    # As module import
    from tests.csv_validator import validate_csv_row, validate_csv_file
"""

import argparse
import csv
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from data_processing.ewg_lists import (
        is_dirty_dozen,
        is_clean_fifteen,
        get_ewg_classification,
        DIRTY_DOZEN_ITEMS,
        CLEAN_FIFTEEN_ITEMS,
    )
except ImportError:
    # Fallback if ewg_lists not available - define locally
    DIRTY_DOZEN_ITEMS = {
        "strawberries", "strawberry", "spinach",
        "kale", "collard greens", "mustard greens",
        "grapes", "grape", "peaches", "peach",
        "pears", "pear", "nectarines", "nectarine",
        "apples", "apple", "bell peppers", "hot peppers", "peppers", "pepper",
        "cherries", "cherry", "blueberries", "blueberry",
        "green beans", "green bean",
    }
    CLEAN_FIFTEEN_ITEMS = {
        "avocados", "avocado", "sweet corn", "corn",
        "pineapple", "pineapples", "onions", "onion",
        "papaya", "papayas", "sweet peas", "peas",
        "asparagus", "honeydew melon", "honeydew",
        "kiwi", "kiwis", "cabbage", "watermelon",
        "mushrooms", "mushroom", "mangoes", "mango",
        "sweet potatoes", "sweet potato", "carrots", "carrot",
    }

    def is_dirty_dozen(product_name: str) -> bool:
        name_lower = product_name.lower()
        for item in DIRTY_DOZEN_ITEMS:
            if item in name_lower or name_lower in item:
                return True
        return False

    def is_clean_fifteen(product_name: str) -> bool:
        name_lower = product_name.lower()
        for item in CLEAN_FIFTEEN_ITEMS:
            if item in name_lower or name_lower in item:
                return True
        return False

    def get_ewg_classification(product_name: str) -> dict:
        if is_dirty_dozen(product_name):
            return {"list": "dirty_dozen", "organic_required": True}
        elif is_clean_fifteen(product_name):
            return {"list": "clean_fifteen", "organic_required": False}
        return {"list": "middle", "organic_required": False}


# Required CSV columns (after skipping header rows)
REQUIRED_COLUMNS = [
    "category",
    "tier",
    "brand",
    "product_name",
    "est_price",
    "packaging",
    "why_this_tier",
    "certifications",
    "trade_offs",
    "source_url",
    "source_reasoning",
]

VALID_TIERS = {"cheaper", "balanced", "conscious"}

# Categories that are produce (EWG rules apply)
PRODUCE_CATEGORIES = {
    "produce_greens", "produce_onions", "produce_roots", "produce_tomatoes",
    "produce_peppers", "produce_squash", "produce_beans", "produce_cucumbers",
    "produce_mushrooms", "produce_aromatics",
    "fruit_tropical", "fruit_berries", "fruit_citrus", "fruit_other",
}


@dataclass
class ValidationError:
    """Represents a validation error."""
    row_num: int
    column: str
    message: str
    severity: str = "error"  # error, warning, info

    def __str__(self):
        icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(self.severity, "•")
        return f"{icon} Row {self.row_num}, {self.column}: {self.message}"


@dataclass
class ValidationResult:
    """Result of validating a CSV file."""
    is_valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)
    info: list[ValidationError] = field(default_factory=list)
    rows_validated: int = 0
    categories_found: set = field(default_factory=set)

    def add_error(self, row_num: int, column: str, message: str):
        self.errors.append(ValidationError(row_num, column, message, "error"))
        self.is_valid = False

    def add_warning(self, row_num: int, column: str, message: str):
        self.warnings.append(ValidationError(row_num, column, message, "warning"))

    def add_info(self, row_num: int, column: str, message: str):
        self.info.append(ValidationError(row_num, column, message, "info"))


def load_product_flags(flags_path: Optional[str] = None) -> dict:
    """
    Load product flags (recalls, advisories) from JSON file.

    Args:
        flags_path: Path to product_flags.json, or None for default

    Returns:
        Dict of category -> list of flags
    """
    if flags_path is None:
        # Try default locations
        possible_paths = [
            Path(__file__).parent.parent / "data" / "flags" / "product_flags.json",
            Path(__file__).parent.parent.parent / "conscious-cart-coach" / "data" / "flags" / "product_flags.json",
        ]
        for path in possible_paths:
            if path.exists():
                flags_path = str(path)
                break

    if flags_path is None or not Path(flags_path).exists():
        return {}

    try:
        with open(flags_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def parse_price(price_str: str) -> Optional[float]:
    """
    Parse price string like "$4.99/lb" or "$6.99/ea" to float.

    Args:
        price_str: Price string with $ and optional unit

    Returns:
        Float price or None if unparseable
    """
    if not price_str:
        return None

    # Extract first dollar amount
    match = re.search(r'\$(\d+(?:\.\d{1,2})?)', price_str)
    if match:
        return float(match.group(1))
    return None


def has_organic_certification(certifications: str) -> bool:
    """Check if certifications string includes organic."""
    if not certifications:
        return False
    return "organic" in certifications.lower()


def validate_csv_row(
    row: dict,
    row_num: int,
    product_flags: dict,
    result: ValidationResult,
    category_prices: dict[str, dict[str, float]],
) -> None:
    """
    Validate a single CSV row.

    Args:
        row: Dict of column -> value
        row_num: Row number for error reporting
        product_flags: Dict of category -> flags from product_flags.json
        result: ValidationResult to accumulate errors
        category_prices: Dict to track prices per category per tier
    """
    category = row.get("category", "").strip()
    tier = row.get("tier", "").strip()
    brand = row.get("brand", "").strip()
    product_name = row.get("product_name", "").strip()
    est_price = row.get("est_price", "").strip()
    certifications = row.get("certifications", "").strip()
    why_this_tier = row.get("why_this_tier", "").strip()
    trade_offs = row.get("trade_offs", "").strip()

    # Basic required field checks
    if not category:
        result.add_error(row_num, "category", "Missing category")
        return

    if not tier:
        result.add_error(row_num, "tier", "Missing tier")
        return

    if tier not in VALID_TIERS:
        result.add_error(row_num, "tier", f"Invalid tier '{tier}'. Must be one of: {VALID_TIERS}")

    if not product_name:
        result.add_error(row_num, "product_name", "Missing product name")

    if not est_price:
        result.add_error(row_num, "est_price", "Missing price")

    if not why_this_tier:
        result.add_warning(row_num, "why_this_tier", "Missing tier justification")

    if not trade_offs:
        result.add_warning(row_num, "trade_offs", "Missing trade-offs description")

    result.categories_found.add(category)

    # Parse and track price
    price = parse_price(est_price)
    if price is not None:
        if category not in category_prices:
            category_prices[category] = {}
        category_prices[category][tier] = price

    # EWG Dirty Dozen / Clean Fifteen checks (produce only)
    if category in PRODUCE_CATEGORIES:
        ewg_info = get_ewg_classification(category)

        if ewg_info.get("list") == "dirty_dozen":
            # Dirty Dozen items: organic REQUIRED at cheaper tier
            if tier == "cheaper" and not has_organic_certification(certifications):
                result.add_error(
                    row_num,
                    "certifications",
                    f"EWG Dirty Dozen item '{category}' at 'cheaper' tier MUST be organic. "
                    f"Current certifications: {certifications or 'None'}"
                )
            # Info: Dirty Dozen at any tier should ideally be organic
            if tier != "cheaper" and not has_organic_certification(certifications):
                result.add_warning(
                    row_num,
                    "certifications",
                    f"EWG Dirty Dozen item '{category}' - organic recommended even at '{tier}' tier"
                )

        elif ewg_info.get("list") == "clean_fifteen":
            # Clean Fifteen: organic optional, note if present
            if has_organic_certification(certifications):
                result.add_info(
                    row_num,
                    "certifications",
                    f"Clean Fifteen item '{category}' is organic (optional but nice)"
                )

    # Check for active recalls
    if category in product_flags:
        for flag in product_flags[category]:
            flag_type = flag.get("type", "").lower()
            affected_tiers = flag.get("affected_tiers", [])
            severity = flag.get("severity", "")
            recall_title = flag.get("title", "Unknown")

            if flag_type == "recall":
                # Check if this tier is affected
                if not affected_tiers or tier in affected_tiers:
                    # Check if the recall is already documented in trade_offs or why_this_tier
                    recall_documented = (
                        "recall" in trade_offs.lower() or
                        "recall" in why_this_tier.lower()
                    )

                    if recall_documented:
                        # Recall is documented - just informational
                        result.add_info(
                            row_num,
                            "category",
                            f"RECALL DOCUMENTED ({severity}): {recall_title}"
                        )
                    elif severity == "Class I":
                        # Class I undocumented recall - error
                        result.add_error(
                            row_num,
                            "category",
                            f"UNDOCUMENTED RECALL (Class I): {recall_title} - {flag.get('recommendation', '')}. "
                            f"Add recall warning to trade_offs column."
                        )
                    else:
                        # Other severity undocumented - warning
                        result.add_warning(
                            row_num,
                            "category",
                            f"UNDOCUMENTED RECALL ({severity}): {recall_title} - {flag.get('recommendation', '')}"
                        )

            elif flag_type == "info" or flag_type == "seasonal":
                result.add_info(
                    row_num,
                    "category",
                    f"{flag.get('title', 'Advisory')}: {flag.get('description', '')}"
                )


def validate_tier_price_ordering(
    category_prices: dict[str, dict[str, float]],
    result: ValidationResult,
) -> None:
    """
    Validate that prices generally follow tier ordering (cheaper < balanced < conscious).

    Note: Some exceptions are acceptable (e.g., organic cheaper than conventional).

    Args:
        category_prices: Dict of category -> tier -> price
        result: ValidationResult to accumulate errors
    """
    for category, tier_prices in category_prices.items():
        cheaper = tier_prices.get("cheaper")
        balanced = tier_prices.get("balanced")
        conscious = tier_prices.get("conscious")

        # Check if conscious is cheaper than cheaper (unusual)
        if cheaper is not None and conscious is not None:
            if conscious < cheaper:
                result.add_info(
                    0,
                    "price_ordering",
                    f"Category '{category}': conscious (${conscious:.2f}) < cheaper (${cheaper:.2f}) - unusual but may be valid"
                )

        # Missing tiers
        if cheaper is None:
            result.add_warning(0, "tier_coverage", f"Category '{category}' missing 'cheaper' tier")
        if balanced is None:
            result.add_warning(0, "tier_coverage", f"Category '{category}' missing 'balanced' tier")
        if conscious is None:
            result.add_warning(0, "tier_coverage", f"Category '{category}' missing 'conscious' tier")


def validate_csv_file(
    csv_path: str,
    flags_path: Optional[str] = None,
) -> ValidationResult:
    """
    Validate an entire CSV file.

    Args:
        csv_path: Path to the alternatives CSV file
        flags_path: Path to product_flags.json (optional)

    Returns:
        ValidationResult with errors, warnings, and info
    """
    result = ValidationResult(is_valid=True)
    product_flags = load_product_flags(flags_path)
    category_prices: dict[str, dict[str, float]] = {}

    if not Path(csv_path).exists():
        result.add_error(0, "file", f"CSV file not found: {csv_path}")
        return result

    try:
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            # Skip the first two header rows (empty row + column labels)
            lines = f.readlines()

            # Find the actual header row (contains "category")
            header_row_idx = None
            for i, line in enumerate(lines):
                if "category" in line.lower() and "tier" in line.lower():
                    header_row_idx = i
                    break

            if header_row_idx is None:
                result.add_error(0, "format", "Could not find header row with 'category' and 'tier'")
                return result

            # Parse CSV from header row
            csv_content = "".join(lines[header_row_idx:])
            reader = csv.DictReader(csv_content.splitlines())

            # Validate columns
            if reader.fieldnames:
                # Handle the special CSV format with row numbers in first column
                fieldnames = [f for f in reader.fieldnames if f and f.strip()]
                missing_cols = set(REQUIRED_COLUMNS) - set(fieldnames)
                if missing_cols:
                    result.add_error(
                        0,
                        "columns",
                        f"Missing required columns: {missing_cols}"
                    )

            # Validate each row
            for row_num, row in enumerate(reader, start=header_row_idx + 2):
                # Skip empty rows
                if not any(row.values()):
                    continue

                # Skip rows that are just row numbers
                category = row.get("category", "").strip()
                if not category or category.isdigit():
                    continue

                result.rows_validated += 1
                validate_csv_row(row, row_num, product_flags, result, category_prices)

        # After all rows, check tier price ordering
        validate_tier_price_ordering(category_prices, result)

    except csv.Error as e:
        result.add_error(0, "format", f"CSV parsing error: {e}")
    except IOError as e:
        result.add_error(0, "file", f"Could not read file: {e}")

    return result


def print_result_verbose(result: ValidationResult) -> None:
    """Print detailed validation results for manual QA."""
    print("\n" + "=" * 60)
    print("CSV VALIDATION REPORT")
    print("=" * 60)

    print(f"\nRows validated: {result.rows_validated}")
    print(f"Categories found: {len(result.categories_found)}")
    print(f"  {', '.join(sorted(result.categories_found))}")

    if result.errors:
        print(f"\n{'='*60}")
        print(f"ERRORS ({len(result.errors)})")
        print("=" * 60)
        for error in result.errors:
            print(f"  {error}")

    if result.warnings:
        print(f"\n{'='*60}")
        print(f"WARNINGS ({len(result.warnings)})")
        print("=" * 60)
        for warning in result.warnings:
            print(f"  {warning}")

    if result.info:
        print(f"\n{'='*60}")
        print(f"INFO ({len(result.info)})")
        print("=" * 60)
        for info in result.info:
            print(f"  {info}")

    print("\n" + "=" * 60)
    if result.is_valid:
        print("✅ VALIDATION PASSED")
    else:
        print("❌ VALIDATION FAILED")
    print("=" * 60 + "\n")


def print_result_ci(result: ValidationResult) -> None:
    """Print concise CI-friendly output."""
    if result.is_valid:
        print(f"✅ CSV validation passed ({result.rows_validated} rows, {len(result.categories_found)} categories)")
        if result.warnings:
            print(f"   ⚠️ {len(result.warnings)} warnings")
    else:
        print(f"❌ CSV validation failed ({len(result.errors)} errors)")
        for error in result.errors[:5]:  # Show first 5 errors
            print(f"   {error}")
        if len(result.errors) > 5:
            print(f"   ... and {len(result.errors) - 5} more errors")


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Validate alternatives_template.csv",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--file", "-f",
        help="Path to CSV file (default: data/alternatives/alternatives_template.csv)",
        default=None,
    )
    parser.add_argument(
        "--flags",
        help="Path to product_flags.json (default: auto-detect)",
        default=None,
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output for manual QA",
    )
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Treat warnings as errors (stricter validation)",
    )

    args = parser.parse_args()

    # Find CSV file
    csv_path = args.file
    if csv_path is None:
        possible_paths = [
            Path(__file__).parent.parent / "data" / "alternatives" / "alternatives_template.csv",
            Path(__file__).parent.parent.parent / "conscious-cart-coach" / "data" / "alternatives" / "alternatives_template.csv",
        ]
        for path in possible_paths:
            if path.exists():
                csv_path = str(path)
                break

    if csv_path is None:
        print("❌ Could not find alternatives_template.csv")
        sys.exit(1)

    # Validate
    result = validate_csv_file(csv_path, args.flags)

    # Apply --warnings-as-errors
    if args.warnings_as_errors and result.warnings:
        result.is_valid = False

    # Output
    if args.verbose:
        print_result_verbose(result)
    else:
        print_result_ci(result)

    # Exit code for CI
    sys.exit(0 if result.is_valid else 1)


if __name__ == "__main__":
    main()
