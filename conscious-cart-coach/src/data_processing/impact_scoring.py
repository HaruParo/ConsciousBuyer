"""
Multi-dimensional impact scoring for conscious shopping decisions.

Scores products across multiple dimensions beyond just health/price:
- Health: EWG pesticides, recalls, nutrition
- Environmental: Carbon footprint, water usage, local sourcing, seasonality
- Social: Fair trade, labor practices, B-Corp status
- Packaging: Recyclability, plastic reduction, bulk options
- Animal Welfare: Cage-free, pasture-raised, humane certifications

Each dimension scored 0-100, with weights configurable per user preference.

Integrates with seasonal_regional.py for dynamic NJ/Mid-Atlantic seasonality
and regional source bonuses.
"""

from dataclasses import dataclass
from typing import Any

# Import seasonal/regional module
try:
    from .seasonal_regional import (
        get_seasonal_status,
        is_regional_source,
        TRUSTED_REGIONAL_SOURCES,
    )
    SEASONAL_AVAILABLE = True
except ImportError:
    SEASONAL_AVAILABLE = False


# Certification mappings to impact dimensions
CERTIFICATION_IMPACTS = {
    # Health certifications
    "usda organic": {"health": 30, "environmental": 20},
    "non-gmo": {"health": 10},

    # Environmental certifications
    "local": {"environmental": 40, "social": 10},  # Reduced transport + supports local economy
    "fair trade": {"social": 50, "environmental": 10},
    "rainforest alliance": {"environmental": 40, "social": 20},
    "b-corp": {"social": 30, "environmental": 20},
    "carbon neutral": {"environmental": 50},

    # Animal welfare certifications
    "grass-fed": {"animal_welfare": 40, "health": 15, "environmental": 10},
    "pasture-raised": {"animal_welfare": 50, "environmental": 15},
    "cage-free": {"animal_welfare": 20},
    "free-range": {"animal_welfare": 30},
    "certified humane": {"animal_welfare": 60},
    "animal welfare approved": {"animal_welfare": 70},

    # Packaging certifications
    "recyclable": {"packaging": 20},
    "compostable": {"packaging": 40},
    "plastic-free": {"packaging": 50},
    "bulk": {"packaging": 30, "environmental": 10},  # Less packaging per unit
    "glass": {"packaging": 25},  # Reusable/recyclable
    "aluminum": {"packaging": 30},  # Highly recyclable
}

# Negative impacts (deductions)
NEGATIVE_IMPACTS = {
    "conventional": {"health": -10, "environmental": -10},  # For Dirty Dozen items
    "imported": {"environmental": -15},  # Long transport
    "plastic bottle": {"packaging": -20},
    "single-use": {"packaging": -15},
    "factory farmed": {"animal_welfare": -50, "environmental": -20},
}

# Default weights (user can customize)
DEFAULT_WEIGHTS = {
    "health": 0.30,
    "environmental": 0.20,
    "social": 0.15,
    "packaging": 0.15,
    "animal_welfare": 0.10,
    "price": 0.10,
}

# User preference presets
PREFERENCE_PRESETS = {
    "health_focused": {
        "health": 0.50,
        "environmental": 0.15,
        "social": 0.10,
        "packaging": 0.10,
        "animal_welfare": 0.05,
        "price": 0.10,
    },
    "eco_warrior": {
        "health": 0.15,
        "environmental": 0.35,
        "social": 0.15,
        "packaging": 0.25,
        "animal_welfare": 0.05,
        "price": 0.05,
    },
    "budget_conscious": {
        "health": 0.20,
        "environmental": 0.10,
        "social": 0.05,
        "packaging": 0.05,
        "animal_welfare": 0.05,
        "price": 0.55,
    },
    "animal_lover": {
        "health": 0.15,
        "environmental": 0.15,
        "social": 0.10,
        "packaging": 0.10,
        "animal_welfare": 0.40,
        "price": 0.10,
    },
    "balanced": DEFAULT_WEIGHTS,
}


@dataclass
class ImpactScore:
    """Multi-dimensional impact score for a product."""
    health: int = 50  # Base score
    environmental: int = 50
    social: int = 50
    packaging: int = 50
    animal_welfare: int = 50  # N/A for produce, relevant for dairy/meat

    # Metadata
    certifications_found: list = None
    warnings: list = None

    def __post_init__(self):
        if self.certifications_found is None:
            self.certifications_found = []
        if self.warnings is None:
            self.warnings = []

    def weighted_score(self, weights: dict = None) -> float:
        """Calculate weighted overall score."""
        weights = weights or DEFAULT_WEIGHTS

        # Normalize weights
        total_weight = sum(weights.values())
        normalized = {k: v / total_weight for k, v in weights.items()}

        score = (
            self.health * normalized.get("health", 0) +
            self.environmental * normalized.get("environmental", 0) +
            self.social * normalized.get("social", 0) +
            self.packaging * normalized.get("packaging", 0) +
            self.animal_welfare * normalized.get("animal_welfare", 0)
        )

        return round(score, 1)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "dimensions": {
                "health": self.health,
                "environmental": self.environmental,
                "social": self.social,
                "packaging": self.packaging,
                "animal_welfare": self.animal_welfare,
            },
            "certifications_found": self.certifications_found,
            "warnings": self.warnings,
        }


def score_product(
    product: dict,
    category: str,
    ewg_classification: dict = None,
    has_recall: bool = False,
) -> ImpactScore:
    """
    Score a product across all impact dimensions.

    Args:
        product: Product dict with certifications, brand, etc.
        category: Product category for context
        ewg_classification: EWG dirty dozen/clean fifteen classification
        has_recall: Whether product has active recall

    Returns:
        ImpactScore with all dimension scores
    """
    score = ImpactScore()

    # Parse certifications
    cert_str = (product.get("certifications") or "").lower()
    notes = (product.get("notes") or "").lower()
    selection_reason = (product.get("selection_reason") or "").lower()

    # Combine text for searching
    all_text = f"{cert_str} {notes} {selection_reason}"

    # Apply positive certification impacts
    for cert, impacts in CERTIFICATION_IMPACTS.items():
        if cert in all_text:
            score.certifications_found.append(cert)
            for dimension, points in impacts.items():
                current = getattr(score, dimension)
                setattr(score, dimension, min(100, current + points))

    # Apply negative impacts
    for negative, impacts in NEGATIVE_IMPACTS.items():
        if negative in all_text:
            for dimension, points in impacts.items():
                current = getattr(score, dimension)
                setattr(score, dimension, max(0, current + points))  # points are negative

    # EWG classification adjustments
    if ewg_classification:
        ewg_list = ewg_classification.get("list", "")

        if ewg_list == "dirty_dozen":
            if "organic" not in cert_str:
                score.health = max(0, score.health - 30)
                score.warnings.append("Dirty Dozen item without organic certification")
            else:
                score.health = min(100, score.health + 20)

        elif ewg_list == "clean_fifteen":
            # No penalty for conventional on clean fifteen
            pass

    # Recall impact
    if has_recall:
        score.health = max(0, score.health - 40)
        score.warnings.append("Active recall on this product")

    # Category-specific adjustments
    if category.startswith("milk") or category.startswith("dairy"):
        # Animal welfare is relevant for dairy
        if "grass" not in all_text and "pasture" not in all_text:
            score.animal_welfare = max(0, score.animal_welfare - 20)
    elif category.startswith("produce") or category.startswith("fruit"):
        # Animal welfare less relevant for produce
        score.animal_welfare = 50  # Neutral

    # Packaging heuristics
    if "plastic" in all_text and "bottle" in all_text:
        score.packaging = max(0, score.packaging - 15)
    if "carton" in all_text:
        score.packaging = min(100, score.packaging + 10)  # Often more recyclable
    if "case" in all_text or "bulk" in all_text:
        score.packaging = min(100, score.packaging + 15)  # Less packaging per unit

    # Local sourcing bonus (basic)
    if "local" in all_text or "lancaster" in all_text.lower():
        score.environmental = min(100, score.environmental + 25)
        score.social = min(100, score.social + 15)

    # Enhanced seasonal/regional scoring if available
    if SEASONAL_AVAILABLE:
        product_name = product.get("product_name", "")
        brand = product.get("brand", "")

        # Check regional source
        regional = is_regional_source(brand, notes, cert_str)
        if regional:
            source_name = regional.get("source", "")
            priority = regional.get("priority", 3)
            score.certifications_found.append(f"regional:{source_name}")

            # Higher priority = closer/more trusted
            if priority == 1:  # NJ sources
                score.environmental = min(100, score.environmental + 35)
                score.social = min(100, score.social + 20)
            elif priority == 2:  # PA, NY nearby
                score.environmental = min(100, score.environmental + 25)
                score.social = min(100, score.social + 15)
            else:  # Further regional
                score.environmental = min(100, score.environmental + 15)
                score.social = min(100, score.social + 10)

        # Check seasonality
        seasonal = get_seasonal_status(product_name, category)
        if seasonal.is_in_season:
            env_bonus = seasonal.environmental_bonus
            score.environmental = min(100, score.environmental + env_bonus)

            if seasonal.quality == "peak":
                score.certifications_found.append("peak_season")
            elif seasonal.quality == "storage":
                score.certifications_found.append("local_storage")

        elif seasonal.quality == "off_season" and not regional:
            # Penalty for imported out-of-season items
            score.environmental = max(0, score.environmental - 10)
            score.warnings.append(f"Out of season - likely imported")

    return score


def compare_products(
    products: list[dict],
    category: str,
    ewg_classification: dict = None,
    user_weights: dict = None,
) -> list[dict]:
    """
    Compare multiple products and rank by weighted score.

    Args:
        products: List of product dicts
        category: Product category
        ewg_classification: EWG classification for category
        user_weights: User's dimension weights

    Returns:
        List of products with scores, sorted by weighted score descending
    """
    weights = user_weights or DEFAULT_WEIGHTS
    scored = []

    for product in products:
        impact = score_product(product, category, ewg_classification)
        weighted = impact.weighted_score(weights)

        scored.append({
            "product": product,
            "impact_score": impact.to_dict(),
            "weighted_score": weighted,
        })

    # Sort by weighted score descending
    scored.sort(key=lambda x: x["weighted_score"], reverse=True)

    return scored


def get_dimension_leaders(
    products: list[dict],
    category: str,
    ewg_classification: dict = None,
) -> dict[str, dict]:
    """
    Find the best product for each dimension.

    Useful for showing "Best for environment", "Best for health", etc.

    Returns:
        Dict mapping dimension name to best product for that dimension
    """
    dimensions = ["health", "environmental", "social", "packaging", "animal_welfare"]
    leaders = {}

    for dim in dimensions:
        best_product = None
        best_score = -1

        for product in products:
            impact = score_product(product, category, ewg_classification)
            dim_score = getattr(impact, dim)

            if dim_score > best_score:
                best_score = dim_score
                best_product = {
                    "product": product,
                    "score": dim_score,
                }

        if best_product:
            leaders[dim] = best_product

    return leaders


def explain_score(impact: ImpactScore, weights: dict = None) -> str:
    """
    Generate human-readable explanation of the score.

    Args:
        impact: ImpactScore to explain
        weights: User's dimension weights

    Returns:
        Explanation string
    """
    weights = weights or DEFAULT_WEIGHTS

    lines = []
    lines.append(f"Overall Score: {impact.weighted_score(weights)}/100")
    lines.append("")
    lines.append("Dimension Breakdown:")

    dimensions = [
        ("health", "Health & Safety", impact.health),
        ("environmental", "Environmental", impact.environmental),
        ("social", "Social/Ethics", impact.social),
        ("packaging", "Packaging", impact.packaging),
        ("animal_welfare", "Animal Welfare", impact.animal_welfare),
    ]

    for key, name, score in dimensions:
        weight_pct = int(weights.get(key, 0) * 100)
        bar = "█" * (score // 10) + "░" * (10 - score // 10)
        lines.append(f"  {name}: {bar} {score}/100 (weight: {weight_pct}%)")

    if impact.certifications_found:
        lines.append("")
        lines.append(f"Certifications: {', '.join(impact.certifications_found)}")

    if impact.warnings:
        lines.append("")
        lines.append("Warnings:")
        for w in impact.warnings:
            lines.append(f"  ⚠️  {w}")

    return "\n".join(lines)
