"""
Refresh Jobs - Scheduled and on-demand data refresh.

Handles:
- Scheduled refresh (daily FDA recalls, annual EWG, etc.)
- On-demand refresh (user-triggered "live check")
- API fetching (when available) vs CSV reload

Usage:
    from src.data.refresh_jobs import RefreshManager

    manager = RefreshManager()

    # Check what needs refresh
    stale = manager.check_stale()

    # Refresh specific table
    manager.refresh("recalls")

    # Refresh all stale tables
    manager.refresh_stale()

    # Force refresh everything
    manager.refresh_all(force=True)
"""

import json
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Any

from .facts_store import FactsStore, CSV_SOURCES

# API endpoints (for live mode)
API_ENDPOINTS = {
    "recalls": "https://api.fda.gov/food/enforcement.json?search=status:Ongoing&limit=100",
    # EWG doesn't have a public API - CSV only
    # Stores are manual - CSV only
    # Crops are static - CSV only
    # Sources are manual - CSV only
}

# Refresh schedules (in hours)
REFRESH_SCHEDULES = {
    "recalls": 24,       # Daily
    "ewg": 8760,         # Annual (March/April)
    "stores": 720,       # Monthly
    "crops": 8760,       # Annual
    "sources": 2160,     # Quarterly
}


class RefreshManager:
    """
    Manages data refresh for the facts store.

    Supports two modes:
    - Snapshot (default): Reload from local CSV files
    - Live: Fetch from APIs where available, fall back to CSV
    """

    def __init__(self, store: FactsStore | None = None):
        self.store = store or FactsStore()
        self.last_api_check: dict[str, datetime] = {}
        self.api_errors: dict[str, str] = {}

    def check_stale(self) -> dict[str, dict]:
        """
        Check which tables are stale and need refresh.

        Returns:
            Dict mapping table_name to staleness info
        """
        result = {}
        refresh_info = self.store.get_refresh_info()

        for table, max_hours in REFRESH_SCHEDULES.items():
            info = refresh_info.get(table, {})
            last_refreshed = info.get("last_refreshed")

            if not last_refreshed:
                result[table] = {
                    "is_stale": True,
                    "reason": "Never refreshed",
                    "schedule": f"Every {max_hours} hours",
                }
                continue

            last_dt = datetime.fromisoformat(last_refreshed)
            age_hours = (datetime.now() - last_dt).total_seconds() / 3600

            is_stale = age_hours > max_hours
            result[table] = {
                "is_stale": is_stale,
                "age_hours": round(age_hours, 1),
                "max_hours": max_hours,
                "last_refreshed": last_refreshed,
                "schedule": info.get("refresh_schedule", "Unknown"),
            }

        return result

    def refresh(self, table: str, live: bool = False) -> dict:
        """
        Refresh a specific table.

        Args:
            table: Table name (recalls, ewg, stores, crops, sources)
            live: If True, try to fetch from API first

        Returns:
            Dict with refresh result
        """
        start_time = datetime.now()

        if live and table in API_ENDPOINTS:
            result = self._refresh_from_api(table)
            if result.get("success"):
                return result
            # Fall back to CSV on API failure

        result = self._refresh_from_csv(table)
        result["duration_ms"] = (datetime.now() - start_time).total_seconds() * 1000
        return result

    def _refresh_from_csv(self, table: str) -> dict:
        """Refresh table from local CSV file."""
        csv_path = CSV_SOURCES.get(table)

        if not csv_path or not csv_path.exists():
            return {
                "success": False,
                "table": table,
                "source": "csv",
                "error": f"CSV file not found: {csv_path}",
            }

        # Call the appropriate refresh method
        refresh_methods = {
            "recalls": self.store.refresh_recalls,
            "ewg": self.store.refresh_ewg,
            "stores": self.store.refresh_stores,
            "crops": self.store.refresh_crops,
            "sources": self.store.refresh_sources,
        }

        method = refresh_methods.get(table)
        if not method:
            return {
                "success": False,
                "table": table,
                "source": "csv",
                "error": f"Unknown table: {table}",
            }

        try:
            method()
            counts = self.store.get_table_counts()
            return {
                "success": True,
                "table": table,
                "source": "csv",
                "source_file": str(csv_path),
                "record_count": counts.get(table, 0),
                "refreshed_at": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "success": False,
                "table": table,
                "source": "csv",
                "error": str(e),
            }

    def _refresh_from_api(self, table: str) -> dict:
        """Refresh table from API (live mode)."""
        url = API_ENDPOINTS.get(table)
        if not url:
            return {"success": False, "error": "No API endpoint for this table"}

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ConsciousCartCoach/1.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))

            self.last_api_check[table] = datetime.now()

            # Process based on table type
            if table == "recalls":
                return self._process_fda_api_response(data)

            return {"success": False, "error": f"API processing not implemented for {table}"}

        except urllib.error.URLError as e:
            self.api_errors[table] = str(e)
            return {
                "success": False,
                "table": table,
                "source": "api",
                "error": f"API request failed: {e}",
            }
        except Exception as e:
            self.api_errors[table] = str(e)
            return {
                "success": False,
                "table": table,
                "source": "api",
                "error": str(e),
            }

    def _process_fda_api_response(self, data: dict) -> dict:
        """Process FDA API response and update recalls table."""
        results = data.get("results", [])

        if not results:
            return {
                "success": True,
                "table": "recalls",
                "source": "api",
                "record_count": 0,
                "note": "No ongoing recalls from FDA API",
            }

        # TODO: Parse FDA API response format and insert into SQLite
        # For now, return info about what we received
        return {
            "success": True,
            "table": "recalls",
            "source": "api",
            "record_count": len(results),
            "note": "API response received (full processing TODO)",
            "sample_fields": list(results[0].keys()) if results else [],
        }

    def refresh_stale(self, live: bool = False) -> dict[str, dict]:
        """
        Refresh all stale tables.

        Args:
            live: If True, try APIs first

        Returns:
            Dict mapping table_name to refresh result
        """
        results = {}
        stale_info = self.check_stale()

        for table, info in stale_info.items():
            if info["is_stale"]:
                results[table] = self.refresh(table, live=live)

        return results

    def refresh_all(self, force: bool = False, live: bool = False) -> dict[str, dict]:
        """
        Refresh all tables.

        Args:
            force: If True, refresh even if not stale
            live: If True, try APIs first

        Returns:
            Dict mapping table_name to refresh result
        """
        results = {}

        for table in REFRESH_SCHEDULES.keys():
            if force or self.store.is_stale(table, REFRESH_SCHEDULES[table]):
                results[table] = self.refresh(table, live=live)
            else:
                results[table] = {
                    "success": True,
                    "table": table,
                    "skipped": True,
                    "reason": "Not stale",
                }

        return results

    def get_status(self) -> dict:
        """
        Get overall refresh status.

        Returns:
            Dict with status summary
        """
        stale_info = self.check_stale()
        counts = self.store.get_table_counts()

        stale_tables = [t for t, info in stale_info.items() if info["is_stale"]]

        return {
            "total_tables": len(REFRESH_SCHEDULES),
            "stale_tables": len(stale_tables),
            "stale_list": stale_tables,
            "record_counts": counts,
            "last_api_errors": self.api_errors,
            "tables": stale_info,
        }


# CLI interface
def main():
    """CLI for refresh jobs."""
    import argparse

    parser = argparse.ArgumentParser(description="Refresh facts store data")
    parser.add_argument("command", choices=["status", "refresh", "refresh-all", "live"],
                        help="Command to run")
    parser.add_argument("--table", help="Specific table to refresh")
    parser.add_argument("--force", action="store_true", help="Force refresh even if not stale")

    args = parser.parse_args()

    manager = RefreshManager()

    if args.command == "status":
        status = manager.get_status()
        print("=" * 60)
        print("FACTS STORE REFRESH STATUS")
        print("=" * 60)
        print(f"Total tables: {status['total_tables']}")
        print(f"Stale tables: {status['stale_tables']}")
        if status["stale_list"]:
            print(f"  Need refresh: {', '.join(status['stale_list'])}")
        print()
        print("Record counts:")
        for table, count in status["record_counts"].items():
            print(f"  {table}: {count}")
        print()
        print("Table details:")
        for table, info in status["tables"].items():
            stale_marker = " [STALE]" if info["is_stale"] else ""
            age = info.get("age_hours", "N/A")
            print(f"  {table}: {age}h old (max {info.get('max_hours', '?')}h){stale_marker}")

    elif args.command == "refresh":
        if args.table:
            result = manager.refresh(args.table)
            print(f"Refresh {args.table}: {'OK' if result['success'] else 'FAILED'}")
            if not result["success"]:
                print(f"  Error: {result.get('error')}")
            else:
                print(f"  Records: {result.get('record_count')}")
        else:
            results = manager.refresh_stale()
            for table, result in results.items():
                status = "OK" if result["success"] else "FAILED"
                print(f"  {table}: {status}")

    elif args.command == "refresh-all":
        results = manager.refresh_all(force=args.force)
        print("Refresh all results:")
        for table, result in results.items():
            if result.get("skipped"):
                print(f"  {table}: SKIPPED (not stale)")
            else:
                status = "OK" if result["success"] else "FAILED"
                count = result.get("record_count", "?")
                print(f"  {table}: {status} ({count} records)")

    elif args.command == "live":
        print("Live refresh (fetching from APIs where available)...")
        results = manager.refresh_all(force=True, live=True)
        for table, result in results.items():
            source = result.get("source", "unknown")
            status = "OK" if result["success"] else "FAILED"
            print(f"  {table} ({source}): {status}")


if __name__ == "__main__":
    main()
