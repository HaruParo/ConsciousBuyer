"""
Receipt data ingestion module.
Handles loading and parsing raw receipt CSV data.
"""

import pandas as pd
from pathlib import Path


def load_receipts(filepath: str | Path) -> pd.DataFrame:
    """Load receipt data from CSV file."""
    pass


def parse_receipt_items(df: pd.DataFrame) -> pd.DataFrame:
    """Parse and normalize receipt line items."""
    pass
