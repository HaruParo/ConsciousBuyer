"""
CSV Exporter - Exports 3 files for debugging and UI handoff.

Output files (to /outputs/):
1. ingredients_confirmed.csv  - Confirmed ingredient list
2. candidates_by_ingredient.csv - All candidates with unit_price
3. final_cart_bundle.csv - DecisionBundle items with neighbors

Usage:
    from src.exporters import CSVExporter

    exporter = CSVExporter()
    paths = exporter.export_all(
        ingredients=orchestrator.state.ingredients,
        candidates=orchestrator.state.candidates_by_ingredient,
        bundle=bundle,
    )
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from ..contracts.models import DecisionBundle


# Output directory
OUTPUTS_DIR = Path(__file__).parent.parent.parent / "outputs"


class CSVExporter:
    """Exports pipeline data to 3 CSV files."""

    def __init__(self, output_dir: Path | None = None):
        self.output_dir = output_dir or OUTPUTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _write_csv(self, filename: str, rows: list[dict], fieldnames: list[str] | None = None) -> Path:
        if not rows:
            return Path()
        filepath = self.output_dir / filename
        fieldnames = fieldnames or list(rows[0].keys())
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return filepath

    def export_all(
        self,
        ingredients: list[dict],
        candidates: dict[str, list[dict]],
        bundle: DecisionBundle,
        prefix: str = "",
    ) -> dict[str, Path]:
        """
        Export all 3 files.

        Returns:
            Dict mapping file type to path
        """
        ts = self._timestamp()
        pfx = f"{prefix}_" if prefix else ""

        paths = {}
        paths["ingredients"] = self.export_ingredients(ingredients, f"{pfx}ingredients_confirmed_{ts}.csv")
        paths["candidates"] = self.export_candidates(candidates, f"{pfx}candidates_by_ingredient_{ts}.csv")
        paths["bundle"] = self.export_bundle(bundle, f"{pfx}final_cart_bundle_{ts}.csv")
        return paths

    def export_ingredients(self, ingredients: list[dict], filename: str | None = None) -> Path:
        """Export confirmed ingredients."""
        rows = []
        for i, ing in enumerate(ingredients):
            rows.append({
                "index": i + 1,
                "name": ing.get("name", ""),
                "quantity": ing.get("quantity", ""),
                "unit": ing.get("unit", ""),
                "category": ing.get("category", ""),
                "optional": ing.get("optional", False),
            })
        filename = filename or f"ingredients_confirmed_{self._timestamp()}.csv"
        return self._write_csv(filename, rows)

    def export_candidates(self, candidates: dict[str, list[dict]], filename: str | None = None) -> Path:
        """Export all candidates by ingredient."""
        rows = []
        for ingredient, cands in candidates.items():
            for c in cands:
                rows.append({
                    "ingredient": ingredient,
                    "product_id": c.get("product_id", ""),
                    "title": c.get("title", ""),
                    "brand": c.get("brand", ""),
                    "size": c.get("size", ""),
                    "price": c.get("price", 0),
                    "unit_price": c.get("unit_price", 0),
                    "unit_price_unit": c.get("unit_price_unit", "oz"),
                    "organic": c.get("organic", False),
                    "in_stock": c.get("in_stock", True),
                })
        filename = filename or f"candidates_by_ingredient_{self._timestamp()}.csv"
        return self._write_csv(filename, rows)

    def export_bundle(self, bundle: DecisionBundle, filename: str | None = None) -> Path:
        """Export the final DecisionBundle."""
        rows = []
        for item in bundle.items:
            rows.append({
                "ingredient": item.ingredient_name,
                "selected_product_id": item.selected_product_id,
                "tier": item.tier_symbol.value,
                "reason_short": item.reason_short,
                "score": item.score,
                "attributes": "; ".join(item.attributes),
                "safety_notes": "; ".join(item.safety_notes),
                "cheaper_neighbor_id": item.cheaper_neighbor_id or "",
                "conscious_neighbor_id": item.conscious_neighbor_id or "",
            })

        # Add totals row
        rows.append({
            "ingredient": "---TOTALS---",
            "selected_product_id": "",
            "tier": "",
            "reason_short": "",
            "score": "",
            "attributes": f"recommended=${bundle.totals.get('recommended', 0):.2f}",
            "safety_notes": f"cheaper=${bundle.totals.get('cheaper', 0):.2f}; conscious=${bundle.totals.get('conscious', 0):.2f}",
            "cheaper_neighbor_id": f"delta={bundle.deltas.get('cheaper_vs_recommended', 0):.2f}",
            "conscious_neighbor_id": f"delta={bundle.deltas.get('conscious_vs_recommended', 0):.2f}",
        })

        filename = filename or f"final_cart_bundle_{self._timestamp()}.csv"
        return self._write_csv(filename, rows)


# Convenience function
def get_csv_exporter() -> CSVExporter:
    """Get default CSV exporter instance."""
    return CSVExporter()
