"""
Seasonal Agent - Lightweight agent for seasonal and regional data.

Returns AgentResult contract for all outputs.

Usage:
    from src.agents.seasonal_agent import SeasonalAgent

    agent = SeasonalAgent()
    result = agent.check_products([{"name": "blueberries"}, {"name": "spinach"}])
    # Returns AgentResult with seasonality facts
"""

from datetime import datetime
from typing import Any

from ..core.types import AgentResult, Evidence, make_result, make_error
from ..facts import get_facts, FactsGateway


class SeasonalAgent:
    """
    Seasonal agent that checks products for:
    - Local availability (NJ crop calendar)
    - Peak season status
    - Regional source trust levels

    All queries go through FactsGateway.
    """

    AGENT_NAME = "seasonal"

    def __init__(self, facts: FactsGateway | None = None):
        self.facts = facts or get_facts()

    def check_products(self, products: list[dict]) -> AgentResult:
        """
        Check seasonality for a list of products.

        Args:
            products: List of product dicts with at least {name}

        Returns:
            AgentResult with seasonality in facts
        """
        try:
            seasonality = {}
            explain = []
            evidence = []

            peak_count = 0
            local_count = 0
            imported_count = 0

            for product in products:
                product_id = product.get("product_id") or product.get("name", "unknown")
                name = product.get("name", "")

                # Get seasonality
                seasonal = self.facts.get_seasonality(name)

                seasonality[product_id] = {
                    "status": seasonal["status"],
                    "is_local": seasonal["is_local"],
                    "bonus": seasonal["bonus"],
                    "reasoning": seasonal["reasoning"],
                }

                if seasonal["status"] == "peak":
                    peak_count += 1
                if seasonal["is_local"]:
                    local_count += 1
                if seasonal["status"] == "imported":
                    imported_count += 1

                # Add evidence for local items
                if seasonal["is_local"]:
                    evidence.append(Evidence(
                        source="NJ Crop Calendar",
                        key=name,
                        value=seasonal["status"],
                        url="https://njaes.rutgers.edu/",
                        timestamp=datetime.now().isoformat(),
                    ))

            # Build explain bullets
            if peak_count > 0:
                explain.append(f"{peak_count} item(s) at peak season in NJ - maximum freshness")
            if local_count > 0 and local_count != peak_count:
                explain.append(f"{local_count} item(s) available locally")
            if imported_count > 0:
                explain.append(f"{imported_count} item(s) likely imported (not in NJ season)")
            if local_count == len(products):
                explain.append("All items can be sourced locally!")

            return make_result(
                agent_name=self.AGENT_NAME,
                facts={
                    "seasonality": seasonality,
                    "peak_count": peak_count,
                    "local_count": local_count,
                    "imported_count": imported_count,
                },
                explain=explain,
                evidence=evidence,
            )

        except Exception as e:
            return make_error(self.AGENT_NAME, str(e))

    def check_single_product(self, name: str) -> AgentResult:
        """
        Check seasonality for a single product.

        Args:
            name: Product name

        Returns:
            AgentResult with seasonality info
        """
        return self.check_products([{"name": name}])

    def get_in_season_now(self) -> AgentResult:
        """
        Get all items currently in season in NJ.

        Returns:
            AgentResult with list of in-season items
        """
        try:
            items = self.facts.get_in_season_now()

            explain = []
            if items:
                # Group by peak vs available
                peak_items = []
                other_items = []

                crops = self.facts.store.get_seasonal_crops()
                month_names = ["jan", "feb", "mar", "apr", "may", "jun",
                               "jul", "aug", "sep", "oct", "nov", "dec"]
                current_month = month_names[datetime.now().month - 1]

                for crop in crops:
                    if crop.get(current_month, "").lower() == "peak":
                        peak_items.append(crop.get("crop", ""))
                    elif crop.get(current_month, "").lower() in ["available", "storage"]:
                        other_items.append(crop.get("crop", ""))

                if peak_items:
                    explain.append(f"Peak season: {', '.join(peak_items[:5])}")
                if other_items:
                    explain.append(f"Also available: {', '.join(other_items[:5])}")
            else:
                explain.append("No local produce in season (winter months)")

            return make_result(
                agent_name=self.AGENT_NAME,
                facts={
                    "in_season": items,
                    "count": len(items),
                    "month": datetime.now().strftime("%B"),
                },
                explain=explain,
                evidence=[Evidence(
                    source="NJ Crop Calendar",
                    key="in_season_count",
                    value=len(items),
                    url="https://njaes.rutgers.edu/",
                )],
            )

        except Exception as e:
            return make_error(self.AGENT_NAME, str(e))

    def get_regional_sources(self) -> AgentResult:
        """
        Get trusted regional sources.

        Returns:
            AgentResult with regional source info
        """
        try:
            sources = self.facts.store.get_regional_sources()

            # Group by trust level
            official = [s for s in sources if s.get("trust_level") == "official"]
            verified = [s for s in sources if s.get("trust_level") == "verified"]

            explain = []
            if official:
                names = [s.get("source_name", "") for s in official[:3]]
                explain.append(f"Official sources: {', '.join(names)}")
            if verified:
                names = [s.get("source_name", "") for s in verified[:3]]
                explain.append(f"Verified sources: {', '.join(names)}")

            evidence = []
            for s in sources[:5]:
                evidence.append(Evidence(
                    source="Regional Sources DB",
                    key=s.get("source_name", ""),
                    value=s.get("trust_level", ""),
                    url=s.get("url"),
                ))

            return make_result(
                agent_name=self.AGENT_NAME,
                facts={
                    "sources": sources,
                    "official_count": len(official),
                    "verified_count": len(verified),
                },
                explain=explain,
                evidence=evidence,
            )

        except Exception as e:
            return make_error(self.AGENT_NAME, str(e))


# Convenience function
def get_seasonal_agent() -> SeasonalAgent:
    """Get default seasonal agent instance."""
    return SeasonalAgent()
