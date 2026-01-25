"""
Typed contracts for the Conscious Cart Coach pipeline.

These dataclasses define the structured data flowing between agents,
the DecisionEngine, and the Orchestrator. Using typed models ensures
determinism, testability, and clear interfaces.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


# =============================================================================
# Tier Symbols
# =============================================================================

class TierSymbol(str, Enum):
    """Tier symbols for UI display."""
    CHEAPER = "cheaper"
    BALANCED = "balanced"
    CONSCIOUS = "conscious"

    @property
    def emoji(self) -> str:
        return {
            "cheaper": "\U0001f4b8",      # 💸
            "balanced": "\u2696\ufe0f",    # ⚖️
            "conscious": "\U0001f30d",     # 🌍
        }[self.value]

    @property
    def label(self) -> str:
        return self.value.capitalize()


# =============================================================================
# Ingredient Models
# =============================================================================

@dataclass
class IngredientSpec:
    """A single ingredient extracted from user prompt."""
    name: str                          # Canonical name (e.g., "spinach")
    quantity: str = ""                 # e.g., "2 bunches", "1 lb"
    unit: str = ""                     # Normalized unit (e.g., "bunch", "lb", "oz")
    category: str = ""                 # e.g., "produce_greens", "protein", "spice"
    optional: bool = False             # Whether ingredient is optional
    confidence: float = 1.0            # 0.0-1.0 extraction confidence
    source_text: str = ""              # Original text that produced this


# =============================================================================
# Product Models
# =============================================================================

@dataclass
class ProductCandidate:
    """
    A candidate product that could fulfill an ingredient.

    ProductAgent produces these WITHOUT tier labels.
    DecisionEngine assigns tiers later.
    """
    product_id: str
    ingredient_name: str               # Which ingredient this fulfills
    title: str                         # e.g., "Organic Baby Spinach"
    brand: str                         # e.g., "Earthbound Farm"
    size: str                          # e.g., "5oz", "1 lb"
    price: float                       # Shelf price in dollars
    unit_price: float                  # Price per normalized unit (e.g., per oz)
    unit_price_unit: str = "oz"        # Unit for unit_price normalization
    organic: bool = False
    in_stock: bool = True
    metadata: dict = field(default_factory=dict)  # Extra attributes (packaging, origin, etc.)

    @property
    def price_label(self) -> str:
        return f"${self.price:.2f}/{self.size}"


# =============================================================================
# Safety / Recall Models
# =============================================================================

@dataclass
class RecallSignal:
    """
    Structured recall assessment for a product or category.

    Replaces the old clear|recalled binary with nuanced taxonomy.
    """
    product_match: bool = False           # Direct product/brand recall match
    category_advisory: Literal[
        "none", "recent", "elevated"
    ] = "none"                            # Category-level advisory
    confidence: Literal[
        "high", "medium", "low"
    ] = "low"                             # How confident is this assessment
    data_gap: bool = False                # True if insufficient data to assess
    details: list[str] = field(default_factory=list)   # Human-readable details
    sources: list[str] = field(default_factory=list)   # Source identifiers


@dataclass
class SafetySignals:
    """Safety signals aggregated for a product candidate."""
    ewg_bucket: Literal[
        "dirty_dozen", "middle", "clean_fifteen", "unknown"
    ] = "unknown"
    ewg_rank: int | None = None
    pesticide_score: int | None = None
    organic_recommended: bool = False     # True if EWG says organic matters here
    recall: RecallSignal = field(default_factory=RecallSignal)
    safety_notes: list[str] = field(default_factory=list)
    attributes: list[str] = field(default_factory=list)  # e.g., ["USDA Organic", "Local"]


@dataclass
class SeasonalitySignal:
    """Seasonality assessment for an ingredient."""
    status: Literal[
        "peak", "available", "storage", "imported", "unknown"
    ] = "unknown"
    is_local: bool = False
    notes: str = ""


# =============================================================================
# User Preferences
# =============================================================================

@dataclass
class UserPrefs:
    """User preference model for decision-making."""
    budget_limit: float | None = None     # Max total cart in dollars
    dietary_restrictions: list[str] = field(default_factory=list)  # e.g., ["vegetarian", "gluten-free"]
    preferred_brands: list[str] = field(default_factory=list)
    avoided_brands: list[str] = field(default_factory=list)
    default_tier: TierSymbol = TierSymbol.BALANCED
    strict_safety: bool = False           # If True, organic_recommended becomes hard constraint
    ingredient_overrides: dict[str, str] = field(default_factory=dict)  # ingredient -> tier


# =============================================================================
# Decision Output Models
# =============================================================================

@dataclass
class DecisionItem:
    """
    A single ingredient's decision output.

    Contains the recommended product plus neighbors for the stepper UI.
    """
    ingredient_name: str
    selected_product_id: str
    tier_symbol: TierSymbol
    reason_short: str                    # 3-4 word reason (e.g., "Organic recommended (EWG)")
    attributes: list[str] = field(default_factory=list)  # e.g., ["Organic", "Local"]
    safety_notes: list[str] = field(default_factory=list)
    cheaper_neighbor_id: str | None = None   # Product ID of next-cheaper viable option
    conscious_neighbor_id: str | None = None # Product ID of next-more-conscious option
    score: int = 50                      # 0-100 score
    evidence_refs: list[str] = field(default_factory=list)  # Source identifiers
    reason_llm: str | None = None        # Optional LLM-generated explanation (1-2 sentences)


@dataclass
class DecisionBundle:
    """
    Complete decision output from the engine.

    Contains all items plus cart-level totals and tier deltas.
    """
    items: list[DecisionItem] = field(default_factory=list)
    totals: dict[str, float] = field(default_factory=dict)  # tier -> total
    deltas: dict[str, float] = field(default_factory=dict)  # tier -> delta from recommended
    data_gaps: list[str] = field(default_factory=list)       # Missing data warnings
    constraint_notes: list[str] = field(default_factory=list)  # Hard constraints applied

    @property
    def recommended_total(self) -> float:
        return self.totals.get("recommended", 0.0)

    @property
    def item_count(self) -> int:
        return len(self.items)
