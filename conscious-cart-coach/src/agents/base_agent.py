"""
Base Data Agent class for the hybrid multi-agent architecture.

Each agent:
- Maintains its own CSV/JSON data store
- Learns from interactions and updates
- Provides query interface for the decision engine
- Tracks confidence and data freshness

Update schedules aligned with data sources:
- ProductAgent: Real-time (per session) for prices/availability
- SafetyAgent: Daily for FDA recalls, Annual for EWG lists
- UserAgent: Real-time (per interaction)
"""

import csv
import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


# Refresh schedule constants (in hours)
REFRESH_SCHEDULES = {
    "product": 1,       # Hourly - prices/availability change frequently
    "safety": 24,       # Daily - FDA recalls checked daily
    "user": 0,          # Real-time - always fresh from user actions
    "ewg": 8760,        # Annual - EWG updates once per year (March/April)
}

# Data source URLs for reference
DATA_SOURCES = {
    "fda_recalls": "https://api.fda.gov/food/enforcement.json",
    "ewg_lists": "https://www.ewg.org/foodnews/",
    "freshdirect": "https://www.freshdirect.com/",
}


class DataAgent(ABC):
    """Base class for all data agents."""

    def __init__(self, name: str, data_dir: Path):
        self.name = name
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.last_updated: datetime | None = None
        self.metadata_path = self.data_dir / f"{name}_metadata.json"
        self._load_metadata()

    def _load_metadata(self):
        """Load agent metadata (last updated, stats, etc.)."""
        if self.metadata_path.exists():
            with open(self.metadata_path) as f:
                meta = json.load(f)
                self.last_updated = datetime.fromisoformat(meta.get("last_updated", ""))
                self.stats = meta.get("stats", {})
        else:
            self.last_updated = None
            self.stats = {}

    def _save_metadata(self):
        """Save agent metadata."""
        with open(self.metadata_path, "w") as f:
            json.dump({
                "last_updated": datetime.now().isoformat(),
                "stats": self.stats,
                "agent_name": self.name,
            }, f, indent=2)

    @abstractmethod
    def query(self, **kwargs) -> dict[str, Any]:
        """Query the agent for relevant data."""
        pass

    @abstractmethod
    def learn(self, interaction: dict) -> None:
        """Learn from an interaction and update data store."""
        pass

    @abstractmethod
    def refresh(self) -> None:
        """Refresh data from external sources."""
        pass

    def get_freshness(self) -> str:
        """Return data freshness status."""
        if not self.last_updated:
            return "never_updated"

        age = datetime.now() - self.last_updated
        if age.days == 0:
            return "fresh"
        elif age.days <= 1:
            return "recent"
        elif age.days <= 7:
            return "stale"
        else:
            return "outdated"

    def _get_agent_type(self) -> str:
        """Get the base agent type for schedule lookup."""
        # Handle user agents with user_id suffix (e.g., "user_default" -> "user")
        if self.name.startswith("user_"):
            return "user"
        return self.name

    def needs_refresh(self) -> bool:
        """Check if agent data needs refresh based on schedule."""
        if not self.last_updated:
            return True

        # Get refresh interval for this agent type
        agent_type = self._get_agent_type()
        refresh_hours = REFRESH_SCHEDULES.get(agent_type, 24)
        if refresh_hours == 0:  # Real-time agents never "need" refresh
            return False

        age = datetime.now() - self.last_updated
        return age > timedelta(hours=refresh_hours)

    def get_refresh_schedule(self) -> dict:
        """Get refresh schedule info for this agent."""
        agent_type = self._get_agent_type()
        refresh_hours = REFRESH_SCHEDULES.get(agent_type, 24)

        schedule_description = {
            0: "Real-time (per interaction)",
            1: "Hourly",
            24: "Daily",
            168: "Weekly",
            8760: "Annual",
        }.get(refresh_hours, f"Every {refresh_hours} hours")

        next_refresh = None
        if self.last_updated and refresh_hours > 0:
            next_refresh = self.last_updated + timedelta(hours=refresh_hours)

        return {
            "agent": self.name,
            "interval_hours": refresh_hours,
            "schedule": schedule_description,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "next_refresh": next_refresh.isoformat() if next_refresh else "now",
            "needs_refresh": self.needs_refresh(),
        }

    def read_csv(self, path: Path) -> list[dict]:
        """Read CSV file, skipping comment lines."""
        rows = []
        if not path.exists():
            return rows

        with open(path, newline="", encoding="utf-8") as f:
            # Skip comment lines
            lines = [line for line in f if not line.startswith("#")]

        if not lines:
            return rows

        reader = csv.DictReader(lines)
        for row in reader:
            rows.append(row)
        return rows

    def write_csv(self, path: Path, rows: list[dict], fieldnames: list[str] | None = None):
        """Write CSV file with optional header comments."""
        if not rows:
            return

        if fieldnames is None:
            fieldnames = list(rows[0].keys())

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def append_csv(self, path: Path, row: dict):
        """Append a single row to CSV."""
        file_exists = path.exists()

        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
