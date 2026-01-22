"""
Safety Agent v2 - Lightweight agent that queries the Facts Gateway.

Returns AgentResult contract for all outputs.

Usage:
    from src.agents.safety_agent_v2 import SafetyAgent

    agent = SafetyAgent()
    result = agent.check_products([{"name": "spinach", "brand": "Fresh Express"}])
    # Returns AgentResult with facts, explain, evidence
"""

from datetime import datetime
from typing import Any

from ..core.types import AgentResult, Evidence, make_result, make_error
from ..facts import get_facts, FactsGateway


class SafetyAgent:
    """
    Safety agent that checks products for:
    - EWG Dirty Dozen / Clean Fifteen classification
    - FDA recall status
    - Organic requirements

    All queries go through FactsGateway (no direct file loading).
    """

    AGENT_NAME = "safety"

    def __init__(self, facts: FactsGateway | None = None):
        self.facts = facts or get_facts()

    def check_products(self, products: list[dict]) -> AgentResult:
        """
        Check safety for a list of products.

        Args:
            products: List of product dicts with at least {name, brand?}

        Returns:
            AgentResult with product_flags in facts
        """
        try:
            product_flags = {}
            ewg_results = {}
            explain = []
            evidence = []

            organic_required_count = 0
            organic_beneficial_count = 0
            recall_count = 0

            for product in products:
                product_id = product.get("product_id") or product.get("name", "unknown")
                name = product.get("name", "")
                brand = product.get("brand", "")
                is_organic = product.get("is_organic", False) or "organic" in name.lower()

                # Get EWG classification
                ewg = self.facts.get_ewg_bucket(name)
                ewg_bucket = ewg["bucket"]
                organic_required = ewg["organic_required"] and not is_organic
                organic_beneficial = ewg.get("organic_beneficial", False) and not is_organic

                if organic_required:
                    organic_required_count += 1
                if organic_beneficial:
                    organic_beneficial_count += 1

                # Store EWG result for decision engine
                ewg_results[name] = {
                    "bucket": ewg_bucket,
                    "rank": ewg["rank"],
                    "organic_required": ewg["organic_required"],
                    "organic_beneficial": ewg.get("organic_beneficial", False),
                    "pesticide_score": ewg.get("pesticide_score"),
                    "has_organic_option": is_organic,
                }

                # Check recalls
                recall_status = self.facts.check_recall_status(name, brand)
                has_recall = recall_status["status"] == "recalled"

                if has_recall:
                    recall_count += 1

                # Build flags for this product
                product_flags[product_id] = {
                    "ewg_bucket": ewg_bucket,
                    "ewg_rank": ewg["rank"],
                    "organic_required": organic_required,
                    "organic_beneficial": organic_beneficial,
                    "is_organic": is_organic,
                    "recall_status": recall_status["status"],
                    "recall_classification": recall_status["classification"],
                    "recall_details": recall_status["recalls"],
                    "red_flags": self._build_red_flags(ewg, recall_status, is_organic),
                }

                # Add evidence for known items
                if ewg_bucket != "unknown":
                    evidence.append(Evidence(
                        source="EWG 2025",
                        key=name,
                        value=f"{ewg_bucket} (rank {ewg['rank']})",
                        url="https://www.ewg.org/foodnews/full-list.php",
                        timestamp=datetime.now().isoformat(),
                    ))

                if has_recall:
                    for recall in recall_status["recalls"]:
                        evidence.append(Evidence(
                            source="FDA",
                            key=recall.get("recall_id", "unknown"),
                            value=recall.get("classification", ""),
                            url=recall.get("source_url"),
                            timestamp=recall.get("recall_initiation_date"),
                        ))

            # Build explain bullets
            if organic_required_count > 0:
                explain.append(f"{organic_required_count} item(s) are Dirty Dozen - organic required")
            if organic_beneficial_count > 0:
                explain.append(f"{organic_beneficial_count} item(s) are EWG Middle - organic beneficial")
            if recall_count > 0:
                explain.append(f"WARNING: {recall_count} item(s) have active FDA recalls")
            if organic_required_count == 0 and recall_count == 0:
                explain.append("All items pass safety checks")

            # Add EWG data freshness warning if stale
            if self.facts.is_data_stale("ewg"):
                explain.append("Note: EWG data may be outdated")
            if self.facts.is_data_stale("recalls"):
                explain.append("Note: Recall data may be outdated")

            return make_result(
                agent_name=self.AGENT_NAME,
                facts={
                    "product_flags": product_flags,
                    "ewg_results": ewg_results,
                    "organic_required_count": organic_required_count,
                    "organic_beneficial_count": organic_beneficial_count,
                    "recall_count": recall_count,
                },
                explain=explain,
                evidence=evidence,
            )

        except Exception as e:
            return make_error(
                agent_name=self.AGENT_NAME,
                error_message=str(e),
            )

    def _build_red_flags(self, ewg: dict, recall_status: dict, is_organic: bool) -> list[str]:
        """Build list of red flags for a product."""
        flags = []

        if ewg["bucket"] == "dirty_dozen" and not is_organic:
            flags.append(f"EWG Dirty Dozen #{ewg['rank']} - non-organic")

        if recall_status["status"] == "recalled":
            cls = recall_status["classification"]
            if cls == "Class I":
                flags.append("CRITICAL: Class I recall - serious health risk")
            elif cls == "Class II":
                flags.append("WARNING: Class II recall - potential health issue")
            else:
                flags.append(f"NOTICE: {cls} recall")

        return flags

    def check_single_product(
        self,
        name: str,
        brand: str = "",
        is_organic: bool = False,
    ) -> AgentResult:
        """
        Convenience method to check a single product.

        Args:
            name: Product name
            brand: Brand name
            is_organic: Whether product is organic

        Returns:
            AgentResult for the single product
        """
        return self.check_products([{
            "name": name,
            "brand": brand,
            "is_organic": is_organic,
        }])

    def get_ewg_info(self, product_name: str) -> AgentResult:
        """
        Get EWG classification for a single product.

        Args:
            product_name: Product to check

        Returns:
            AgentResult with EWG info
        """
        try:
            ewg = self.facts.get_ewg_bucket(product_name)

            explain = []
            if ewg["bucket"] == "dirty_dozen":
                explain.append(f"Dirty Dozen #{ewg['rank']} - organic strongly recommended")
            elif ewg["bucket"] == "clean_fifteen":
                explain.append(f"Clean Fifteen #{ewg['rank']} - conventional acceptable")
            else:
                explain.append("Not on EWG lists - moderate pesticide levels")

            return make_result(
                agent_name=self.AGENT_NAME,
                facts={
                    "product": product_name,
                    "ewg_bucket": ewg["bucket"],
                    "ewg_rank": ewg["rank"],
                    "organic_required": ewg["organic_required"],
                    "pesticide_score": ewg["pesticide_score"],
                },
                explain=explain,
                evidence=[Evidence(
                    source="EWG",
                    key=product_name,
                    value=ewg["bucket"],
                    url="https://www.ewg.org/foodnews/",
                )],
            )

        except Exception as e:
            return make_error(self.AGENT_NAME, str(e))

    def get_recall_summary(self, stores: list[str] | None = None) -> AgentResult:
        """
        Get summary of active recalls for user's region/stores.

        Args:
            stores: Optional list of stores user shops at

        Returns:
            AgentResult with recall summary
        """
        try:
            recalls = self.facts.get_recalls()

            # Filter by stores if provided
            if stores:
                store_keywords = self.facts.get_store_keywords()
                stores_lower = set(s.lower() for s in stores)

                filtered = []
                for r in recalls:
                    dist = r.get("distribution_pattern", "").lower()
                    if "nationwide" in dist:
                        filtered.append(r)
                    elif any(s in dist for s in stores_lower):
                        filtered.append(r)
                recalls = filtered

            # Categorize
            class_i = [r for r in recalls if r.get("classification") == "Class I"]
            class_ii = [r for r in recalls if r.get("classification") == "Class II"]
            class_iii = [r for r in recalls if r.get("classification") == "Class III"]

            # Build explain
            explain = []
            if class_i:
                explain.append(f"URGENT: {len(class_i)} Class I recall(s) - serious health risk")
            if class_ii:
                explain.append(f"CAUTION: {len(class_ii)} Class II recall(s) - check pantry")
            if not class_i and not class_ii:
                explain.append("No critical recalls for your region")

            # Build evidence
            evidence = []
            for r in (class_i + class_ii)[:5]:  # Limit evidence to top 5
                evidence.append(Evidence(
                    source="FDA",
                    key=r.get("recall_id", ""),
                    value=r.get("product_description", "")[:50],
                    url=r.get("source_url"),
                ))

            return make_result(
                agent_name=self.AGENT_NAME,
                facts={
                    "total_recalls": len(recalls),
                    "class_i_count": len(class_i),
                    "class_ii_count": len(class_ii),
                    "class_iii_count": len(class_iii),
                    "class_i_recalls": class_i,
                    "class_ii_recalls": class_ii,
                },
                explain=explain,
                evidence=evidence,
            )

        except Exception as e:
            return make_error(self.AGENT_NAME, str(e))


# Convenience function
def get_safety_agent() -> SafetyAgent:
    """Get default safety agent instance."""
    return SafetyAgent()
