"""
Facts Store - Unified SQLite database for all factual data.

Single source of truth for:
- FDA Recalls
- EWG Dirty Dozen / Clean Fifteen
- Store listings
- Crop calendar (seasonal)
- Regional sources

Agents query this store (read-only logic), refresh jobs update it.

Usage:
    from src.data.facts_store import FactsStore

    store = FactsStore()

    # Query mode (default - uses cached data)
    recalls = store.get_recalls(state="NJ")
    ewg = store.get_ewg_classification("strawberries")

    # Check freshness
    info = store.get_refresh_info()

    # Manual refresh (or use refresh_jobs.py)
    store.refresh_recalls()
"""

import csv
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

# Paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"

# Use /tmp for database on Vercel/serverless (read-only filesystem)
# Vercel sets VERCEL=1, AWS Lambda sets AWS_LAMBDA_FUNCTION_NAME
IS_SERVERLESS = (
    os.environ.get("VERCEL") or
    os.environ.get("AWS_LAMBDA_FUNCTION_NAME") or
    os.environ.get("VERCEL_ENV")
)

if IS_SERVERLESS:
    DB_PATH = Path("/tmp/facts_store.db")
else:
    DB_PATH = DATA_DIR / "facts_store.db"

# CSV source files
CSV_SOURCES = {
    "recalls": DATA_DIR / "flags" / "fda_recalls.csv",
    "ewg": DATA_DIR / "flags" / "ewg_lists.csv",
    "stores": DATA_DIR / "stores" / "nj_middlesex_stores.csv",
    "crops": DATA_DIR / "seasonal" / "nj_crop_calendar.csv",
    "sources": DATA_DIR / "seasonal" / "trusted_regional_sources.csv",
}

# Schema definitions
SCHEMA = """
-- Metadata table for tracking refresh times
CREATE TABLE IF NOT EXISTS _meta (
    table_name TEXT PRIMARY KEY,
    last_refreshed TEXT,
    source_file TEXT,
    record_count INTEGER,
    source_url TEXT,
    trust_level TEXT,
    refresh_schedule TEXT
);

-- FDA Recalls
CREATE TABLE IF NOT EXISTS recalls (
    recall_id TEXT PRIMARY KEY,
    status TEXT,
    classification TEXT,
    product_description TEXT,
    reason_for_recall TEXT,
    contaminant TEXT,
    recalling_firm TEXT,
    city TEXT,
    state TEXT,
    distribution_pattern TEXT,
    recall_initiation_date TEXT,
    termination_date TEXT,
    affected_categories TEXT,
    affected_brands TEXT,
    affected_upcs TEXT,
    voluntary INTEGER,
    source_url TEXT
);

-- EWG Dirty Dozen / Clean Fifteen
CREATE TABLE IF NOT EXISTS ewg (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rank INTEGER,
    item TEXT,
    list TEXT,
    pesticide_residue_score INTEGER,
    organic_recommendation TEXT,
    notes TEXT,
    source_url TEXT
);

-- Stores serving Middlesex County
CREATE TABLE IF NOT EXISTS stores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_name TEXT,
    store_keywords TEXT,
    store_type TEXT,
    serves_middlesex INTEGER,
    delivery_available INTEGER,
    notes TEXT
);

-- NJ Crop Calendar
CREATE TABLE IF NOT EXISTS crops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crop TEXT,
    category TEXT,
    jan TEXT, feb TEXT, mar TEXT, apr TEXT, may TEXT, jun TEXT,
    jul TEXT, aug TEXT, sep TEXT, oct TEXT, nov TEXT, dec TEXT,
    nj_rank TEXT,
    notes TEXT,
    source TEXT
);

-- Trusted Regional Sources
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT,
    source_keywords TEXT,
    state TEXT,
    distance_miles INTEGER,
    priority INTEGER,
    trust_level TEXT,
    certification_type TEXT,
    verification TEXT,
    year_established INTEGER,
    url TEXT,
    notes TEXT
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_recalls_status ON recalls(status);
CREATE INDEX IF NOT EXISTS idx_recalls_classification ON recalls(classification);
CREATE INDEX IF NOT EXISTS idx_ewg_list ON ewg(list);
CREATE INDEX IF NOT EXISTS idx_ewg_item ON ewg(item);
CREATE INDEX IF NOT EXISTS idx_stores_serves ON stores(serves_middlesex);
CREATE INDEX IF NOT EXISTS idx_crops_category ON crops(category);
"""


class FactsStore:
    """
    Unified facts store backed by SQLite.

    Provides read-only query methods for agents.
    Refresh methods update data from CSV sources.
    """

    def __init__(self, db_path: Path = None):
        # Determine database path - prefer /tmp for serverless
        if db_path:
            self.db_path = db_path
        elif IS_SERVERLESS or not DB_PATH.parent.exists():
            self.db_path = Path("/tmp/facts_store.db")
        else:
            self.db_path = DB_PATH

        # Create parent directory if needed
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError):
            # Fallback to /tmp if we can't create directory
            self.db_path = Path("/tmp/facts_store.db")

        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(SCHEMA)

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # =========================================================================
    # REFRESH METHODS (populate from CSV)
    # =========================================================================

    def refresh_all(self):
        """Refresh all tables from CSV sources."""
        self.refresh_recalls()
        self.refresh_ewg()
        self.refresh_stores()
        self.refresh_crops()
        self.refresh_sources()

    def refresh_recalls(self):
        """Refresh FDA recalls from CSV."""
        csv_path = CSV_SOURCES["recalls"]
        if not csv_path.exists():
            return

        rows = self._load_csv(csv_path)

        with self._get_conn() as conn:
            conn.execute("DELETE FROM recalls")

            for row in rows:
                if row.get("status", "").lower() == "ongoing":
                    conn.execute("""
                        INSERT INTO recalls (
                            recall_id, status, classification, product_description,
                            reason_for_recall, contaminant, recalling_firm, city, state,
                            distribution_pattern, recall_initiation_date, termination_date,
                            affected_categories, affected_brands, affected_upcs, voluntary, source_url
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row.get("recall_id", ""),
                        row.get("status", ""),
                        row.get("classification", ""),
                        row.get("product_description", ""),
                        row.get("reason_for_recall", ""),
                        row.get("contaminant", ""),
                        row.get("recalling_firm", ""),
                        row.get("city", ""),
                        row.get("state", ""),
                        row.get("distribution_pattern", ""),
                        row.get("recall_initiation_date", ""),
                        row.get("termination_date", ""),
                        row.get("affected_categories", ""),
                        row.get("affected_brands", ""),
                        row.get("affected_upcs", ""),
                        1 if row.get("voluntary", "Yes") == "Yes" else 0,
                        row.get("source_url", ""),
                    ))

            self._update_meta(conn, "recalls", csv_path, len(rows),
                              "https://api.fda.gov/food/enforcement.json",
                              "OFFICIAL (Federal Government)", "Daily")

    def refresh_ewg(self):
        """Refresh EWG lists from CSV."""
        csv_path = CSV_SOURCES["ewg"]
        if not csv_path.exists():
            return

        rows = self._load_csv(csv_path)

        with self._get_conn() as conn:
            conn.execute("DELETE FROM ewg")

            for row in rows:
                conn.execute("""
                    INSERT INTO ewg (rank, item, list, pesticide_residue_score,
                                     organic_recommendation, notes, source_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(row.get("rank", 0)),
                    row.get("item", "").lower(),
                    row.get("list", ""),
                    int(row.get("pesticide_residue_score", 50)),
                    row.get("organic_recommendation", ""),
                    row.get("notes", ""),
                    row.get("source_url", ""),
                ))

            self._update_meta(conn, "ewg", csv_path, len(rows),
                              "https://www.ewg.org/foodnews/",
                              "Research Non-profit", "Annual (March/April)")

    def refresh_stores(self):
        """Refresh stores from CSV."""
        csv_path = CSV_SOURCES["stores"]
        if not csv_path.exists():
            return

        rows = self._load_csv(csv_path)

        with self._get_conn() as conn:
            conn.execute("DELETE FROM stores")

            for row in rows:
                conn.execute("""
                    INSERT INTO stores (store_name, store_keywords, store_type,
                                        serves_middlesex, delivery_available, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    row.get("store_name", ""),
                    row.get("store_keywords", ""),
                    row.get("store_type", ""),
                    1 if row.get("serves_middlesex", "").lower() == "yes" else 0,
                    1 if row.get("delivery_available", "").lower() == "yes" else 0,
                    row.get("notes", ""),
                ))

            self._update_meta(conn, "stores", csv_path, len(rows),
                              "Manual", "Manual verification", "Monthly")

    def refresh_crops(self):
        """Refresh crop calendar from CSV."""
        csv_path = CSV_SOURCES["crops"]
        if not csv_path.exists():
            return

        rows = self._load_csv(csv_path)

        with self._get_conn() as conn:
            conn.execute("DELETE FROM crops")

            for row in rows:
                conn.execute("""
                    INSERT INTO crops (crop, category, jan, feb, mar, apr, may, jun,
                                       jul, aug, sep, oct, nov, dec, nj_rank, notes, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get("crop", ""),
                    row.get("category", ""),
                    row.get("jan", ""),
                    row.get("feb", ""),
                    row.get("mar", ""),
                    row.get("apr", ""),
                    row.get("may", ""),
                    row.get("jun", ""),
                    row.get("jul", ""),
                    row.get("aug", ""),
                    row.get("sep", ""),
                    row.get("oct", ""),
                    row.get("nov", ""),
                    row.get("dec", ""),
                    row.get("nj_rank", ""),
                    row.get("notes", ""),
                    row.get("source", ""),
                ))

            self._update_meta(conn, "crops", csv_path, len(rows),
                              "https://njaes.rutgers.edu/",
                              "Official (Rutgers/USDA)", "Annual")

    def refresh_sources(self):
        """Refresh regional sources from CSV."""
        csv_path = CSV_SOURCES["sources"]
        if not csv_path.exists():
            return

        rows = self._load_csv(csv_path)

        with self._get_conn() as conn:
            conn.execute("DELETE FROM sources")

            for row in rows:
                conn.execute("""
                    INSERT INTO sources (source_name, source_keywords, state, distance_miles,
                                         priority, trust_level, certification_type, verification,
                                         year_established, url, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get("source_name", ""),
                    row.get("source_keywords", ""),
                    row.get("state", ""),
                    int(row.get("distance_miles", 0)) if row.get("distance_miles") else 0,
                    int(row.get("priority", 99)) if row.get("priority") else 99,
                    row.get("trust_level", ""),
                    row.get("certification_type", ""),
                    row.get("verification", ""),
                    int(row.get("year_established", 0)) if row.get("year_established") else 0,
                    row.get("url", ""),
                    row.get("notes", ""),
                ))

            self._update_meta(conn, "sources", csv_path, len(rows),
                              "Various", "Verified non-profits", "Quarterly")

    def _load_csv(self, path: Path) -> list[dict]:
        """Load CSV file, skipping comment lines."""
        with open(path, newline="", encoding="utf-8") as f:
            lines = [line for line in f if not line.startswith("#")]

        if not lines:
            return []

        reader = csv.DictReader(lines)
        return list(reader)

    def _update_meta(self, conn, table_name: str, source_file: Path,
                     count: int, source_url: str, trust_level: str, refresh_schedule: str):
        """Update metadata for a table."""
        conn.execute("""
            INSERT OR REPLACE INTO _meta (table_name, last_refreshed, source_file,
                                          record_count, source_url, trust_level, refresh_schedule)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            table_name,
            datetime.now().isoformat(),
            str(source_file),
            count,
            source_url,
            trust_level,
            refresh_schedule,
        ))

    # =========================================================================
    # QUERY METHODS (read-only for agents)
    # =========================================================================

    def get_recalls(
        self,
        state: str | None = None,
        classification: str | None = None,
        stores: list[str] | None = None,
    ) -> list[dict]:
        """
        Get FDA recalls, optionally filtered.

        Args:
            state: Filter by state (e.g., "NJ")
            classification: Filter by class (e.g., "Class I")
            stores: Filter by stores (matches distribution_pattern)

        Returns:
            List of recall dicts
        """
        with self._get_conn() as conn:
            query = "SELECT * FROM recalls WHERE status = 'Ongoing'"
            params = []

            if classification:
                query += " AND classification = ?"
                params.append(classification)

            rows = conn.execute(query, params).fetchall()
            recalls = [dict(r) for r in rows]

        # Post-filter by state/stores (requires pattern matching)
        if state:
            state_upper = state.upper()
            recalls = [
                r for r in recalls
                if "nationwide" in r.get("distribution_pattern", "").lower()
                or state_upper in r.get("distribution_pattern", "").upper()
                or (state_upper == "NJ" and any(
                    region in r.get("distribution_pattern", "").lower()
                    for region in ["northeast", "mid-atlantic", "east coast"]
                ))
            ]

        if stores:
            stores_lower = [s.lower() for s in stores]
            filtered = []
            for r in recalls:
                dist_lower = r.get("distribution_pattern", "").lower()
                if "nationwide" in dist_lower:
                    filtered.append(r)
                elif any(store in dist_lower for store in stores_lower):
                    filtered.append(r)
            recalls = filtered

        return recalls

    def get_ewg_classification(self, product_name: str) -> dict:
        """
        Get EWG classification for a product.

        Uses priority matching: exact > word-boundary > substring.
        Checks all three lists: dirty_dozen, middle, clean_fifteen.

        Args:
            product_name: Product name to check

        Returns:
            Dict with list, rank, organic_required, organic_beneficial, etc.
        """
        name_lower = product_name.lower().strip()

        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM ewg ORDER BY rank"
            ).fetchall()

        # Priority matching to avoid "apple" matching "pineapple" etc.
        best_match = None
        best_priority = 999

        for row in rows:
            item = row["item"].lower()

            # Priority 0: Exact match (including singular/plural)
            if name_lower == item or name_lower + "s" == item or name_lower == item + "s":
                best_match = row
                best_priority = 0
                break

            # Priority 1: Query word found in item words
            item_words = item.replace(",", " ").replace(" and ", " ").split()
            name_words = name_lower.replace(",", " ").replace(" and ", " ").split()

            if any(nw in item_words for nw in name_words):
                if best_priority > 1:
                    best_match = row
                    best_priority = 1
                continue

            # Priority 2: Item word found in query words
            if any(iw in name_words for iw in item_words):
                if best_priority > 2:
                    best_match = row
                    best_priority = 2
                continue

            # Priority 3: Substring (only for longer queries)
            if (name_lower in item or item in name_lower) and len(name_lower) > 3:
                if best_priority > 3:
                    best_match = row
                    best_priority = 3

        if best_match:
            list_type = best_match["list"]
            return {
                "list": list_type,
                "rank": best_match["rank"],
                "pesticide_score": best_match["pesticide_residue_score"],
                "organic_required": list_type == "dirty_dozen",
                "organic_beneficial": list_type == "middle",
                "organic_optional": list_type == "clean_fifteen",
                "notes": best_match["notes"],
            }

        # Not on any list
        return {
            "list": "unknown",
            "rank": None,
            "pesticide_score": None,
            "organic_required": False,
            "organic_beneficial": False,
            "organic_optional": False,
            "notes": "Not on EWG 2025 list (not a ranked produce item)",
        }

    def get_stores(self, serves_middlesex: bool = True, delivery_only: bool = False) -> list[dict]:
        """
        Get stores, optionally filtered.

        Args:
            serves_middlesex: Only stores serving Middlesex County
            delivery_only: Only stores with delivery

        Returns:
            List of store dicts
        """
        with self._get_conn() as conn:
            query = "SELECT * FROM stores WHERE 1=1"
            params = []

            if serves_middlesex:
                query += " AND serves_middlesex = 1"
            if delivery_only:
                query += " AND delivery_available = 1"

            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def get_seasonal_crops(self, month: str | None = None) -> list[dict]:
        """
        Get crops, optionally filtered by month.

        Args:
            month: Month abbreviation (jan, feb, etc.) or None for all

        Returns:
            List of crop dicts with availability
        """
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM crops").fetchall()
            crops = [dict(r) for r in rows]

        if month:
            month_lower = month.lower()[:3]
            # Filter to crops available this month
            crops = [
                c for c in crops
                if c.get(month_lower, "").lower() in ["peak", "available", "storage"]
            ]

        return crops

    def get_in_season_now(self) -> list[dict]:
        """Get crops currently in season."""
        month_names = ["jan", "feb", "mar", "apr", "may", "jun",
                       "jul", "aug", "sep", "oct", "nov", "dec"]
        current_month = month_names[datetime.now().month - 1]
        return self.get_seasonal_crops(current_month)

    def get_regional_sources(self, trust_level: str | None = None) -> list[dict]:
        """
        Get trusted regional sources.

        Args:
            trust_level: Filter by trust level (official, verified, etc.)

        Returns:
            List of source dicts ordered by priority
        """
        with self._get_conn() as conn:
            query = "SELECT * FROM sources"
            params = []

            if trust_level:
                query += " WHERE trust_level = ?"
                params.append(trust_level)

            query += " ORDER BY priority ASC"

            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    # =========================================================================
    # METADATA & STATUS
    # =========================================================================

    def get_refresh_info(self) -> dict[str, dict]:
        """
        Get refresh info for all tables.

        Returns:
            Dict mapping table_name to metadata
        """
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM _meta").fetchall()
            return {row["table_name"]: dict(row) for row in rows}

    def get_table_counts(self) -> dict[str, int]:
        """Get record counts for all tables."""
        tables = ["recalls", "ewg", "stores", "crops", "sources"]
        counts = {}

        with self._get_conn() as conn:
            for table in tables:
                row = conn.execute(f"SELECT COUNT(*) as cnt FROM {table}").fetchone()
                counts[table] = row["cnt"] if row else 0

        return counts

    def is_stale(self, table: str, max_age_hours: int = 24) -> bool:
        """
        Check if a table's data is stale.

        Args:
            table: Table name
            max_age_hours: Maximum age in hours before considered stale

        Returns:
            True if data is stale or missing
        """
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT last_refreshed FROM _meta WHERE table_name = ?",
                (table,)
            ).fetchone()

            if not row or not row["last_refreshed"]:
                return True

            last_refreshed = datetime.fromisoformat(row["last_refreshed"])
            age_hours = (datetime.now() - last_refreshed).total_seconds() / 3600

            return age_hours > max_age_hours

    def needs_refresh(self) -> list[str]:
        """
        Get list of tables that need refreshing based on schedule.

        Returns:
            List of table names needing refresh
        """
        stale = []

        # Different staleness thresholds per table
        thresholds = {
            "recalls": 24,      # Daily
            "stores": 720,      # Monthly (30 days)
            "crops": 8760,      # Annual
            "ewg": 8760,        # Annual
            "sources": 2160,    # Quarterly (90 days)
        }

        for table, hours in thresholds.items():
            if self.is_stale(table, hours):
                stale.append(table)

        return stale


# Convenience function
def get_store() -> FactsStore:
    """Get the default facts store instance."""
    return FactsStore()
