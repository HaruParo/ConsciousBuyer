"""
Receipt data ingestion module.
Handles loading, parsing, and storing receipt data into PostgreSQL.

Run with: python -m src.data_processing.ingest data/raw/receipts.csv
"""

import logging
import os
import re
from pathlib import Path
from typing import Optional

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# SQLAlchemy setup
Base = declarative_base()


# =============================================================================
# Database Models
# =============================================================================


class Category(Base):
    """Category model for product categorization."""

    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(String(255), unique=True, nullable=False)

    items = relationship("Item", secondary="item_categories", back_populates="categories")

    def __repr__(self):
        return f"<Category(category_id={self.category_id}, name='{self.category_name}')>"


class Item(Base):
    """Item model for products."""

    __tablename__ = "items"

    item_id = Column(Integer, primary_key=True)
    name = Column(String(500), nullable=False)
    brand = Column(String(255))
    size = Column(String(255))
    packaging_type = Column(String(255))

    purchases = relationship("Purchase", back_populates="item")
    categories = relationship("Category", secondary="item_categories", back_populates="items")

    def __repr__(self):
        return f"<Item(item_id={self.item_id}, name='{self.name}', brand='{self.brand}')>"


class ItemCategory(Base):
    """Association table for items and categories (many-to-many)."""

    __tablename__ = "item_categories"

    item_id = Column(Integer, ForeignKey("items.item_id"), primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.category_id"), primary_key=True)


class Purchase(Base):
    """Purchase model for transaction records."""

    __tablename__ = "purchases"

    price_id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("items.item_id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Float)

    item = relationship("Item", back_populates="purchases")

    def __repr__(self):
        return f"<Purchase(price_id={self.price_id}, item_id={self.item_id}, price={self.price})>"


# =============================================================================
# Database Connection
# =============================================================================


def get_database_url() -> str:
    """Get database URL from environment."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError(
            "DATABASE_URL environment variable is not set. "
            "Please set it in your .env file."
        )
    return database_url


def get_engine(database_url: Optional[str] = None):
    """Create SQLAlchemy engine."""
    url = database_url or get_database_url()
    return create_engine(url, echo=False)


def get_session(engine=None):
    """Create a database session."""
    if engine is None:
        engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def create_tables(engine=None):
    """Create all tables in the database."""
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(engine)
    logger.info("Database tables created successfully")


def drop_tables(engine=None):
    """Drop all tables from the database."""
    if engine is None:
        engine = get_engine()
    Base.metadata.drop_all(engine)
    logger.info("Database tables dropped")


# =============================================================================
# Data Parsing & Transformation
# =============================================================================

# Common packaging type patterns
PACKAGING_PATTERNS = [
    (r"plastic\s+clamshell", "plastic clamshell"),
    (r"glass\s+jar", "glass jar"),
    (r"glass\s+bottle", "glass bottle"),
    (r"plastic\s+bag", "plastic bag"),
    (r"plastic\s+bottle", "plastic bottle"),
    (r"paperboard\s+box", "paperboard box"),
    (r"paperboard\s+(?:pint\s+)?tub", "paperboard tub"),
    (r"metal\s+(?:lid|cap)", "metal lid/cap"),
    (r"carton", "carton"),
    (r"bunch", "bunch"),
    (r"plastic\s+twist\s+tie", "plastic twist tie"),
    (r"plastic\s+produce\s+bag", "plastic produce bag"),
    (r"resealable", "resealable bag"),
]


def extract_packaging_type(size_str: str) -> Optional[str]:
    """
    Extract packaging type from the size column.

    Args:
        size_str: The size string that may contain packaging info

    Returns:
        Extracted packaging type or None
    """
    if pd.isna(size_str) or not size_str:
        return None

    size_lower = str(size_str).lower()
    packaging_types = []

    for pattern, packaging_name in PACKAGING_PATTERNS:
        if re.search(pattern, size_lower):
            packaging_types.append(packaging_name)

    if packaging_types:
        return ", ".join(sorted(set(packaging_types)))
    return None


def normalize_brand_name(brand: str) -> Optional[str]:
    """
    Normalize brand names for consistency.

    Args:
        brand: Raw brand name

    Returns:
        Normalized brand name
    """
    if pd.isna(brand) or not brand:
        return None

    # Strip whitespace and normalize
    normalized = str(brand).strip()

    # Handle common variations
    if normalized.lower() in ("store brand", "store_brand", "generic"):
        return "Store Brand"

    # Remove trailing/leading special characters
    normalized = re.sub(r"^[^\w]+|[^\w]+$", "", normalized)

    # Title case if all lowercase or all uppercase
    if normalized.islower() or normalized.isupper():
        normalized = normalized.title()

    return normalized if normalized else None


def validate_row(row: pd.Series) -> list[str]:
    """
    Validate a single row of data.

    Args:
        row: A pandas Series representing a row

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Required fields
    if pd.isna(row.get("price_id")):
        errors.append("Missing price_id")
    if pd.isna(row.get("item_id")):
        errors.append("Missing item_id")
    if pd.isna(row.get("ts")):
        errors.append("Missing timestamp")
    if pd.isna(row.get("price")):
        errors.append("Missing price")

    # Type validations
    try:
        if not pd.isna(row.get("price")):
            float(row["price"])
    except (ValueError, TypeError):
        errors.append(f"Invalid price value: {row.get('price')}")

    try:
        if not pd.isna(row.get("qty")):
            float(row["qty"])
    except (ValueError, TypeError):
        errors.append(f"Invalid quantity value: {row.get('qty')}")

    return errors


# =============================================================================
# CSV Loading & Processing
# =============================================================================


def load_receipts(filepath: str | Path) -> pd.DataFrame:
    """
    Load receipt data from CSV file.

    Args:
        filepath: Path to the CSV file

    Returns:
        DataFrame with receipt data

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is empty or has invalid format
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"Receipt file not found: {filepath}")

    logger.info(f"Loading receipts from {filepath}")

    try:
        df = pd.read_csv(filepath)
    except pd.errors.EmptyDataError:
        raise ValueError(f"CSV file is empty: {filepath}")
    except pd.errors.ParserError as e:
        raise ValueError(f"Error parsing CSV file: {e}")

    required_columns = {"price_id", "item_id", "ts", "price"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    logger.info(f"Loaded {len(df)} rows from {filepath}")
    return df


def parse_receipt_items(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Parse and normalize receipt line items.

    Args:
        df: Raw receipt DataFrame

    Returns:
        Tuple of (items_df, purchases_df)
    """
    logger.info("Parsing receipt items...")

    # Validate all rows and collect errors
    validation_errors = []
    for idx, row in df.iterrows():
        errors = validate_row(row)
        if errors:
            validation_errors.append((idx, errors))

    if validation_errors:
        logger.warning(f"Found {len(validation_errors)} rows with validation issues")
        for idx, errors in validation_errors[:5]:
            logger.warning(f"  Row {idx}: {errors}")
        if len(validation_errors) > 5:
            logger.warning(f"  ... and {len(validation_errors) - 5} more")

    # Extract unique items
    items_data = []
    seen_items = set()

    for _, row in df.iterrows():
        item_id = row.get("item_id")
        if pd.isna(item_id) or item_id in seen_items:
            continue

        seen_items.add(item_id)

        items_data.append({
            "item_id": int(item_id),
            "name": row.get("raw_product_line", "Unknown"),
            "brand": normalize_brand_name(row.get("brand_name")),
            "size": row.get("size"),
            "packaging_type": extract_packaging_type(row.get("size")),
        })

    items_df = pd.DataFrame(items_data)
    logger.info(f"Extracted {len(items_df)} unique items")

    # Extract purchases
    purchases_data = []
    skipped_purchases = 0
    for _, row in df.iterrows():
        if pd.isna(row.get("price_id")) or pd.isna(row.get("item_id")):
            continue

        # Skip rows with missing timestamps
        timestamp = pd.to_datetime(row["ts"], errors="coerce")
        if pd.isna(timestamp):
            skipped_purchases += 1
            logger.debug(f"Skipping purchase {row['price_id']} due to missing timestamp")
            continue

        purchases_data.append({
            "price_id": int(row["price_id"]),
            "item_id": int(row["item_id"]),
            "timestamp": timestamp,
            "price": float(row["price"]) if not pd.isna(row["price"]) else None,
            "quantity": float(row["qty"]) if not pd.isna(row.get("qty")) else 1.0,
        })

    if skipped_purchases > 0:
        logger.warning(f"Skipped {skipped_purchases} purchases due to missing timestamps")

    purchases_df = pd.DataFrame(purchases_data)
    logger.info(f"Extracted {len(purchases_df)} purchases")

    return items_df, purchases_df


# =============================================================================
# Database Operations
# =============================================================================


def ingest_to_database(
    items_df: pd.DataFrame,
    purchases_df: pd.DataFrame,
    engine=None,
    drop_existing: bool = False,
) -> dict:
    """
    Ingest parsed data into the database.

    Args:
        items_df: DataFrame with item data
        purchases_df: DataFrame with purchase data
        engine: SQLAlchemy engine (optional)
        drop_existing: Whether to drop existing tables first

    Returns:
        Dictionary with ingestion statistics
    """
    if engine is None:
        engine = get_engine()

    if drop_existing:
        drop_tables(engine)

    create_tables(engine)

    session = get_session(engine)
    stats = {"items_inserted": 0, "purchases_inserted": 0, "errors": []}

    try:
        # Insert items
        logger.info("Inserting items...")
        for _, row in items_df.iterrows():
            try:
                item = Item(
                    item_id=row["item_id"],
                    name=row["name"],
                    brand=row["brand"],
                    size=row["size"],
                    packaging_type=row["packaging_type"],
                )
                session.merge(item)  # Use merge to handle duplicates
                stats["items_inserted"] += 1
            except Exception as e:
                stats["errors"].append(f"Item {row['item_id']}: {e}")
                logger.error(f"Error inserting item {row['item_id']}: {e}")

        session.commit()
        logger.info(f"Inserted {stats['items_inserted']} items")

        # Insert purchases
        logger.info("Inserting purchases...")
        for _, row in purchases_df.iterrows():
            try:
                purchase = Purchase(
                    price_id=row["price_id"],
                    item_id=row["item_id"],
                    timestamp=row["timestamp"],
                    price=row["price"],
                    quantity=row["quantity"],
                )
                session.merge(purchase)  # Use merge to handle duplicates
                stats["purchases_inserted"] += 1
            except Exception as e:
                stats["errors"].append(f"Purchase {row['price_id']}: {e}")
                logger.error(f"Error inserting purchase {row['price_id']}: {e}")

        session.commit()
        logger.info(f"Inserted {stats['purchases_inserted']} purchases")

    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        session.close()

    return stats


def ingest_csv(filepath: str | Path, drop_existing: bool = False) -> dict:
    """
    Main ingestion function - loads CSV and inserts into database.

    Args:
        filepath: Path to the CSV file
        drop_existing: Whether to drop existing tables first

    Returns:
        Dictionary with ingestion statistics
    """
    logger.info(f"Starting ingestion from {filepath}")

    # Load and parse
    df = load_receipts(filepath)
    items_df, purchases_df = parse_receipt_items(df)

    # Ingest to database
    stats = ingest_to_database(items_df, purchases_df, drop_existing=drop_existing)

    logger.info(
        f"Ingestion complete: {stats['items_inserted']} items, "
        f"{stats['purchases_inserted']} purchases"
    )

    return stats


# =============================================================================
# Query Functions
# =============================================================================


def get_purchase_history(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    brand: Optional[str] = None,
    engine=None,
) -> pd.DataFrame:
    """
    Get purchase history as a DataFrame.

    Args:
        start_date: Filter purchases from this date (YYYY-MM-DD)
        end_date: Filter purchases until this date (YYYY-MM-DD)
        brand: Filter by brand name
        engine: SQLAlchemy engine (optional)

    Returns:
        DataFrame with purchase history including item details
    """
    if engine is None:
        engine = get_engine()

    session = get_session(engine)

    try:
        query = session.query(
            Purchase.price_id,
            Purchase.timestamp,
            Purchase.price,
            Purchase.quantity,
            Item.item_id,
            Item.name,
            Item.brand,
            Item.size,
            Item.packaging_type,
        ).join(Item)

        # Apply filters
        if start_date:
            query = query.filter(Purchase.timestamp >= pd.to_datetime(start_date))
        if end_date:
            query = query.filter(Purchase.timestamp <= pd.to_datetime(end_date))
        if brand:
            query = query.filter(Item.brand.ilike(f"%{brand}%"))

        # Execute query and convert to DataFrame
        results = query.all()

        df = pd.DataFrame(
            results,
            columns=[
                "price_id",
                "timestamp",
                "price",
                "quantity",
                "item_id",
                "name",
                "brand",
                "size",
                "packaging_type",
            ],
        )

        logger.info(f"Retrieved {len(df)} purchase records")
        return df

    finally:
        session.close()


def get_items_by_packaging(packaging_type: str, engine=None) -> pd.DataFrame:
    """
    Get all items with a specific packaging type.

    Args:
        packaging_type: The packaging type to filter by
        engine: SQLAlchemy engine (optional)

    Returns:
        DataFrame with matching items
    """
    if engine is None:
        engine = get_engine()

    session = get_session(engine)

    try:
        query = session.query(Item).filter(
            Item.packaging_type.ilike(f"%{packaging_type}%")
        )

        results = query.all()

        df = pd.DataFrame(
            [
                {
                    "item_id": item.item_id,
                    "name": item.name,
                    "brand": item.brand,
                    "size": item.size,
                    "packaging_type": item.packaging_type,
                }
                for item in results
            ]
        )

        logger.info(f"Found {len(df)} items with packaging type '{packaging_type}'")
        return df

    finally:
        session.close()


# =============================================================================
# CLI Entry Point
# =============================================================================


def main():
    """CLI entry point for the ingestion script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Ingest receipt CSV data into PostgreSQL database"
    )
    parser.add_argument(
        "filepath",
        type=str,
        help="Path to the receipt CSV file",
    )
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop existing tables before ingestion",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate the CSV without inserting into database",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        if args.validate_only:
            logger.info("Running in validation-only mode")
            df = load_receipts(args.filepath)
            items_df, purchases_df = parse_receipt_items(df)
            print(f"\nValidation Results:")
            print(f"  Total rows: {len(df)}")
            print(f"  Unique items: {len(items_df)}")
            print(f"  Total purchases: {len(purchases_df)}")
            print(f"\nSample items:")
            print(items_df.head(10).to_string(index=False))
        else:
            stats = ingest_csv(args.filepath, drop_existing=args.drop_existing)
            print(f"\nIngestion Complete:")
            print(f"  Items inserted: {stats['items_inserted']}")
            print(f"  Purchases inserted: {stats['purchases_inserted']}")
            if stats["errors"]:
                print(f"  Errors: {len(stats['errors'])}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
