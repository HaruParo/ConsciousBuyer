"""
CartPlan: Single source of truth for shopping cart UI

This contract is the ONLY output from the planner engine.
UI must render this directly without inference or transformation.

Key principles:
- store_id assigned ONCE in planner, never reassigned
- All product data included (no lookup needed)
- Chips computed in planner (no UI calculation)
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Product Data
# ============================================================================

class Product(BaseModel):
    """Complete product information"""
    product_id: str
    title: str
    brand: str
    price: float
    size: str
    unit: str  # lb, oz, ea, bunch
    organic: bool = False
    unit_price: float  # normalized per oz
    unit_price_unit: str = "oz"
    image_url: Optional[str] = None
    source_store_id: str  # MANDATORY: Which store this product comes from

    # Enhanced metadata for decision summaries
    packaging: str = ""
    nutrition: str = ""
    labels: str = ""


class ProductChoice(BaseModel):
    """Product selection with metadata"""
    product: Product
    quantity: float = 1.0
    reasoning: str  # Why this product was chosen


# ============================================================================
# Chips (Tags)
# ============================================================================

class ProductChips(BaseModel):
    """Evidence-based tags for product choice"""
    why_pick: List[str] = Field(default_factory=list, max_length=5)  # DEPRECATED: Use reason_line instead
    tradeoffs: List[str] = Field(default_factory=list, max_length=2)  # Max 2 tradeoffs

    @field_validator('why_pick', 'tradeoffs')
    @classmethod
    def validate_chip_count(cls, v):
        """Ensure reasonable chip counts"""
        if len(v) > 5:
            return v[:5]
        return v


# ============================================================================
# Decision Trace (for scoring drawer)
# ============================================================================

class CandidateTrace(BaseModel):
    """Single candidate in decision trace"""
    product: str
    brand: str
    store: str
    price: float
    unit_price: float
    organic: bool
    form_score: int
    packaging: str
    nutrition: str = ""
    labels: str = ""
    status: str  # winner, runner_up, considered, filtered_out
    score_total: Optional[int] = None
    score_breakdown: Optional[Dict[str, int]] = None  # Component breakdown
    elimination_reasons: List[str] = Field(default_factory=list)
    elimination_explanation: Optional[str] = None  # Human-readable explanation
    elimination_stage: Optional[str] = None  # STORE_ENFORCEMENT, FORM_CONSTRAINTS, etc.


class ScoreDriver(BaseModel):
    """Single score driver (reason why winner won)"""
    rule: str  # e.g., "Organic (EWG Dirty Dozen)", "Lower plastic packaging"
    delta: int  # Score delta vs runner-up or median


class CandidatePoolSummary(BaseModel):
    """Summary of retrieved vs considered candidates by store"""
    store_id: str
    store_name: str
    retrieved_count: int  # Retrieved from ProductIndex
    considered_count: int  # After hard filters


class DecisionTrace(BaseModel):
    """Complete decision trace for scoring drawer"""
    # Query info
    query_key: str  # Normalized ingredient key used for retrieval

    # Candidate pools
    retrieved_summary: List[CandidatePoolSummary] = Field(default_factory=list)
    considered_summary: List[CandidatePoolSummary] = Field(default_factory=list)

    # Scores
    winner_score: int
    runner_up_score: Optional[int] = None
    score_margin: int = 0

    # Candidates
    candidates: List[CandidateTrace] = Field(default_factory=list)

    # Explanations
    drivers: List[ScoreDriver] = Field(default_factory=list)  # Why winner won
    tradeoffs_accepted: List[str] = Field(default_factory=list)  # Negative components on winner

    # Filtered out summary
    filtered_out_summary: Dict[str, int] = Field(default_factory=dict)


# ============================================================================
# Cart Items
# ============================================================================

class CartItem(BaseModel):
    """Single ingredient with product selection"""
    ingredient_name: str
    ingredient_label: str  # NEW: Combined name + form ("fresh ginger", "cumin seeds", "coriander powder")
    ingredient_quantity: str  # "2 lbs", "1 bunch"
    ingredient_form: Optional[str] = None  # powder, seeds, pods, leaves, whole, paste, chopped, other (used for matching)

    # Store assignment (SINGLE SOURCE OF TRUTH)
    store_id: str  # Must match StoreInfo.store_id

    # Product selections
    ethical_default: ProductChoice  # Recommended choice
    cheaper_swap: Optional[ProductChoice] = None  # Budget alternative

    # Status
    status: str = "available"  # available, unavailable, out_of_stock

    # Reason for selection (NEW)
    reason_line: str = "Good match"  # Single sentence explaining why this product was chosen
    reason_details: List[str] = Field(default_factory=list)  # Bullets for ⓘ hover (1-2 details)

    # Chips (computed in planner)
    chips: ProductChips = Field(default_factory=ProductChips)

    # Enrichment data (for display/explanation)
    seasonality: Optional[str] = None  # "peak", "available", "off_season"
    ewg_category: Optional[str] = None  # "dirty_dozen", "clean_fifteen"
    recall_status: str = "safe"  # "safe", "advisory", "recalled"

    # Decision trace (for scoring drawer) - Optional, only included if include_trace=True
    decision_trace: Optional[DecisionTrace] = None


# ============================================================================
# Store Plan
# ============================================================================

class StoreInfo(BaseModel):
    """Store metadata"""
    store_id: str  # Unique ID (e.g., "freshdirect", "whole_foods")
    store_name: str  # Display name
    store_type: str  # "primary", "specialty"
    delivery_estimate: str = "1-2 days"
    checkout_url_template: Optional[str] = None
    selection_reason: Optional[str] = None  # NEW: Why this store was chosen (e.g., "Best coverage (10 items) + fresh protein quality")


class StoreAssignment(BaseModel):
    """Which ingredients go to which store"""
    store_id: str
    ingredient_names: List[str]
    item_count: int
    estimated_total: float
    assignment_reason: Optional[str] = None  # NEW: Why these ingredients were assigned to this store


class StorePlan(BaseModel):
    """Multi-store optimization result"""
    stores: List[StoreInfo]
    assignments: List[StoreAssignment]
    unavailable: List[str] = Field(default_factory=list)  # Ingredients not found

    @property
    def total_stores(self) -> int:
        return len(self.stores)

    @property
    def primary_store_id(self) -> str:
        """Return the primary store (most items)"""
        if not self.assignments:
            return self.stores[0].store_id if self.stores else "unknown"
        return max(self.assignments, key=lambda a: a.item_count).store_id


# ============================================================================
# Totals
# ============================================================================

class CartTotals(BaseModel):
    """Price summaries"""
    ethical_total: float  # Total if all ethical defaults
    cheaper_total: float  # Total if all cheaper swaps
    savings_potential: float  # ethical - cheaper

    # Per-store breakdowns
    store_totals: Dict[str, float] = Field(default_factory=dict)


# ============================================================================
# Main CartPlan Contract
# ============================================================================

class CartPlan(BaseModel):
    """
    Complete shopping cart plan - SINGLE SOURCE OF TRUTH

    This is the only output from planner engine.
    UI renders this directly.
    """

    # Input context
    prompt: str
    servings: int = 2

    # Extracted ingredients
    ingredients: List[str]  # Simple list for display

    # Store optimization
    store_plan: StorePlan

    # Cart items (ONE per ingredient)
    items: List[CartItem]

    # Totals
    totals: CartTotals

    # Metadata
    created_at: Optional[str] = None
    planner_version: str = "2.0"

    def validate_store_assignments(self) -> bool:
        """Verify all items have valid store_ids"""
        valid_store_ids = {s.store_id for s in self.store_plan.stores}
        for item in self.items:
            if item.store_id not in valid_store_ids:
                raise ValueError(
                    f"Item '{item.ingredient_name}' assigned to invalid store '{item.store_id}'. "
                    f"Valid stores: {valid_store_ids}"
                )
        return True

    def get_items_by_store(self, store_id: str) -> List[CartItem]:
        """Get all items for a specific store"""
        return [item for item in self.items if item.store_id == store_id]

    def get_store_total(self, store_id: str, use_cheaper: bool = False) -> float:
        """Calculate total for a specific store"""
        items = self.get_items_by_store(store_id)
        total = 0.0
        for item in items:
            if use_cheaper and item.cheaper_swap:
                total += item.cheaper_swap.product.price * item.cheaper_swap.quantity
            else:
                total += item.ethical_default.product.price * item.ethical_default.quantity
        return round(total, 2)


# ============================================================================
# Debug Output
# ============================================================================

class CandidateDebugInfo(BaseModel):
    """Debug info for a single candidate"""
    title: str
    brand: str
    price: float
    store: str
    form_score: int
    organic: bool
    unit_price: float


class PlannerDebugInfo(BaseModel):
    """Debug information from planner execution"""
    ingredient_name: str
    candidates_found: int
    candidate_titles: List[str]
    candidate_stores: List[str]  # NEW: source_store_id for each candidate

    # NEW: Detailed candidate info
    winner: Optional[CandidateDebugInfo] = None
    runner_up: Optional[CandidateDebugInfo] = None
    all_candidates: List[CandidateDebugInfo] = []

    # Winner/runner-up comparison
    reason_code: Optional[str] = None  # ewg_guidance, less_plastic, fewer_prep, better_unit_value, etc.
    reason_line: Optional[str] = None

    # Legacy fields (keep for compatibility)
    chosen_product_id: str
    chosen_title: str
    chosen_store_id: str  # NEW: source_store_id of chosen product
    store_assignment_reason: str


class CartPlanDebug(BaseModel):
    """Extended plan with debug info"""
    plan: CartPlan
    debug_info: List[PlannerDebugInfo]
    execution_time_ms: float


# ============================================================================
# Validation Example
# ============================================================================

if __name__ == "__main__":
    # Example: Create a minimal valid CartPlan
    plan = CartPlan(
        prompt="chicken and rice",
        servings=2,
        ingredients=["chicken", "rice"],
        store_plan=StorePlan(
            stores=[
                StoreInfo(
                    store_id="freshdirect",
                    store_name="FreshDirect",
                    store_type="primary"
                )
            ],
            assignments=[
                StoreAssignment(
                    store_id="freshdirect",
                    ingredient_names=["chicken", "rice"],
                    item_count=2,
                    estimated_total=15.98
                )
            ]
        ),
        items=[
            CartItem(
                ingredient_name="chicken",
                ingredient_quantity="1 lb",
                store_id="freshdirect",
                ethical_default=ProductChoice(
                    product=Product(
                        product_id="prod001",
                        title="Organic Chicken Breast",
                        brand="FreshDirect",
                        price=8.99,
                        size="1 lb",
                        unit="lb",
                        organic=True,
                        unit_price=0.56,
                        source_store_id="freshdirect"
                    ),
                    quantity=1.0,
                    reasoning="Organic, no recalls"
                ),
                chips=ProductChips(
                    why_pick=["USDA Organic", "No Active Recalls"],
                    tradeoffs=[]
                )
            ),
            CartItem(
                ingredient_name="rice",
                ingredient_quantity="2 cups",
                store_id="freshdirect",
                ethical_default=ProductChoice(
                    product=Product(
                        product_id="prod002",
                        title="Organic Basmati Rice",
                        brand="Lundberg",
                        price=6.99,
                        size="2 lb",
                        unit="lb",
                        organic=True,
                        unit_price=0.22,
                        source_store_id="freshdirect"
                    ),
                    quantity=1.0,
                    reasoning="Organic, good value"
                )
            )
        ],
        totals=CartTotals(
            ethical_total=15.98,
            cheaper_total=12.50,
            savings_potential=3.48,
            store_totals={"freshdirect": 15.98}
        )
    )

    # Validate
    assert plan.validate_store_assignments()
    print(f"✓ Valid CartPlan with {len(plan.items)} items")
    print(f"✓ Stores: {[s.store_name for s in plan.store_plan.stores]}")
    print(f"✓ Total: ${plan.totals.ethical_total}")
    print(f"✓ Savings potential: ${plan.totals.savings_potential}")
