"""
PlannerEngine: Deterministic shopping cart planning

4-step process:
1. retrieve_candidates() - Get product options for each ingredient
2. enrich_signals() - Add seasonality, EWG, recalls
3. choose_store_plan() - Multi-store optimization
4. select_products() - Pick ethical default + cheaper swap per ingredient

Output: Single CartPlan contract (no UI inference needed)
"""

import time
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from ..contracts.cart_plan import (
    CartPlan, CartItem, ProductChoice, Product, ProductChips,
    StorePlan, StoreInfo, StoreAssignment, CartTotals
)
from .product_index import ProductIndex, ProductCandidate
from ..facts import get_facts, FactsGateway
from ..agents.ingredient_forms import canonicalize_ingredient, get_ingredient_key, format_ingredient_label


class PlannerEngine:
    """
    Deterministic planner engine

    Core principle: All decisions made here, output as CartPlan.
    UI just renders. No transformation, no inference, no reassignment.
    """

    def __init__(
        self,
        product_index: Optional[ProductIndex] = None,
        facts_gateway: Optional[FactsGateway] = None
    ):
        """
        Initialize planner engine

        Args:
            product_index: Product retrieval index (or None for default)
            facts_gateway: Facts gateway for enrichment (or None for default)
        """
        self.product_index = product_index or ProductIndex()
        self.facts_gateway = facts_gateway or get_facts()

    def create_plan(
        self,
        prompt: str,
        ingredients: List[str],
        servings: int = 2
    ) -> CartPlan:
        """
        Create complete shopping cart plan

        CORRECTED FLOW (fixes store/product mismatch bug):
        1. Retrieve candidates for all ingredients
        2. Choose store plan FIRST (based on candidate coverage)
        3. Select products FILTERED by assigned store
        4. Build cart items (never drop ingredients)

        Args:
            prompt: Original user prompt
            ingredients: Extracted ingredient names
            servings: Number of servings

        Returns:
            CartPlan with all decisions made
        """
        start_time = time.time()

        # Step 0: Detect recipe type and canonicalize ingredients with forms
        recipe_type = self._detect_recipe_type(prompt)
        ingredient_forms = self._canonicalize_ingredients(ingredients, recipe_type)

        # Step 1: Retrieve candidates (all stores)
        candidates_by_ingredient = self._retrieve_candidates_with_forms(ingredient_forms)

        # Step 2: Enrich with signals
        enriched = self._enrich_signals(candidates_by_ingredient, ingredients)

        # Step 3: Choose store plan FIRST (based on candidate availability)
        store_plan = self._choose_store_plan(enriched, ingredients)

        # Step 4: Select products (filtered by assigned store)
        selections = self._select_products(enriched, store_plan, servings)

        # Step 5: Build cart items with chips (NEVER drop ingredients)
        cart_items = self._build_cart_items(selections, store_plan, ingredients, ingredient_forms)

        # Step 6: Calculate totals
        totals = self._calculate_totals(cart_items)

        # Build ingredient list with forms (use ingredient_label from cart_items)
        # This shows "fresh ginger", "coriander powder", "cumin seeds" instead of just "ginger", "coriander", "cumin"
        ingredients_with_forms = [item.ingredient_label for item in cart_items]

        # Build final plan
        plan = CartPlan(
            prompt=prompt,
            servings=servings,
            ingredients=ingredients_with_forms,
            store_plan=store_plan,
            items=cart_items,
            totals=totals,
            created_at=time.strftime("%Y-%m-%d %H:%M:%S")
        )

        # Validate store assignments
        plan.validate_store_assignments()

        execution_time = (time.time() - start_time) * 1000
        print(f"✓ CartPlan created in {execution_time:.0f}ms")

        return plan

    # ========================================================================
    # Step 0: Ingredient Canonicalization & Forms
    # ========================================================================

    def _detect_recipe_type(self, prompt: str) -> Optional[str]:
        """Detect recipe type from prompt for form canonicalization"""
        prompt_lower = prompt.lower()
        if "biryani" in prompt_lower:
            return "biryani"
        # Add more recipe types as needed
        return None

    def _canonicalize_ingredients(
        self,
        ingredients: List[str],
        recipe_type: Optional[str]
    ) -> Dict[str, Tuple[str, Optional[str]]]:
        """
        Canonicalize ingredients and determine forms

        Returns:
            Dict mapping original ingredient -> (canonical_name, form)
            Example: {"coriander": ("coriander", "powder")}
        """
        result = {}
        for ingredient in ingredients:
            canonical_name, form = canonicalize_ingredient(ingredient, recipe_type)
            result[ingredient] = (canonical_name, form)
            if form:
                print(f"  {ingredient} → {canonical_name} ({form})")
        return result

    # ========================================================================
    # Step 1: Retrieve Candidates
    # ========================================================================

    def _retrieve_candidates_with_forms(
        self,
        ingredient_forms: Dict[str, Tuple[str, Optional[str]]]
    ) -> Dict[str, List[ProductCandidate]]:
        """
        Retrieve product candidates for each ingredient using canonical names

        Args:
            ingredient_forms: Dict mapping original -> (canonical, form)

        Returns:
            Dict mapping original ingredient -> candidates
        """
        candidates = {}

        for original_ing, (canonical_name, form) in ingredient_forms.items():
            # Use canonical name for matching
            candidate_list = self.product_index.retrieve(canonical_name, max_candidates=6)

            candidates[original_ing] = candidate_list

            if not candidate_list:
                print(f"⚠️  No candidates found for: {canonical_name} ({form or 'any form'})")
            else:
                print(f"✓ Found {len(candidate_list)} candidates for {canonical_name}")

        return candidates

    def _retrieve_candidates(
        self,
        ingredients: List[str]
    ) -> Dict[str, List[ProductCandidate]]:
        """
        Retrieve product candidates for each ingredient

        P0 FIX: ProductIndex handles fresh produce merge automatically
        """
        candidates = {}

        for ingredient in ingredients:
            # ProductIndex handles the fresh produce merge
            candidate_list = self.product_index.retrieve(ingredient, max_candidates=6)

            if candidate_list:
                candidates[ingredient] = candidate_list
                print(f"  ✓ {ingredient}: {len(candidate_list)} candidates")
            else:
                print(f"  ⚠️  {ingredient}: No candidates found")

        return candidates

    # ========================================================================
    # Step 2: Enrich Signals
    # ========================================================================

    def _enrich_signals(
        self,
        candidates_by_ingredient: Dict[str, List[ProductCandidate]],
        all_ingredients: List[str]
    ) -> Dict[str, List[Dict]]:
        """
        Enrich candidates with signals from FactsGateway

        Adds: seasonality, EWG category, recall status

        IMPORTANT: Returns enriched dict for ALL ingredients (even if no candidates)
        """
        enriched = {}

        # Process all ingredients (not just those with candidates)
        for ingredient in all_ingredients:
            candidates = candidates_by_ingredient.get(ingredient, [])
            enriched_list = []

            for candidate in candidates:
                # Get enrichment data
                ewg_category = self._get_ewg_category(ingredient)
                recall_status = self._get_recall_status(candidate)
                seasonality = "available"  # TODO: Add seasonality lookup

                enriched_list.append({
                    "candidate": candidate,
                    "ewg_category": ewg_category,
                    "recall_status": recall_status,
                    "seasonality": seasonality
                })

            # Include even if empty (will be marked unavailable later)
            enriched[ingredient] = enriched_list

        return enriched

    def _get_ewg_category(self, ingredient: str) -> Optional[str]:
        """Check if ingredient is in EWG Dirty Dozen or Clean Fifteen"""
        # EWG lists (simplified)
        dirty_dozen = [
            "strawberries", "spinach", "kale", "peaches", "pears",
            "nectarines", "apples", "grapes", "bell peppers", "cherries"
        ]
        clean_fifteen = [
            "avocados", "onions", "pineapple", "papaya", "asparagus"
        ]

        ingredient_lower = ingredient.lower()

        if any(item in ingredient_lower for item in dirty_dozen):
            return "dirty_dozen"
        elif any(item in ingredient_lower for item in clean_fifteen):
            return "clean_fifteen"
        else:
            return None

    def _get_recall_status(self, candidate: ProductCandidate) -> str:
        """Check recall status (simplified for now)"""
        # TODO: Query facts_gateway for actual recalls
        return "safe"

    # ========================================================================
    # Step 4: Select Products (REORDERED - after store plan, with filtering)
    # ========================================================================

    def _select_products(
        self,
        enriched: Dict[str, List[Dict]],
        store_plan: StorePlan,
        servings: int
    ) -> Dict[str, Dict]:
        """
        Select products for each ingredient, FILTERED by assigned store

        CRITICAL FIX (Bug B): Enforce store exclusivity
        - Only select products where candidate.source_store_id matches assigned store_id
        - Apply brand backstop rules (365 → wholefoods only, etc.)

        Selection logic:
        - ethical_default: Best organic/safety choice from assigned store
        - cheaper_swap: Cheapest viable alternative from assigned store (if exists)
        """
        selections = {}

        # Build store assignment lookup
        store_by_ingredient = {}
        for assignment in store_plan.assignments:
            for ingredient_name in assignment.ingredient_names:
                store_by_ingredient[ingredient_name] = assignment.store_id

        for ingredient, enriched_list in enriched.items():
            # Get assigned store for this ingredient
            assigned_store_id = store_by_ingredient.get(ingredient)

            if not assigned_store_id:
                # Ingredient is unavailable (no store assignment)
                selections[ingredient] = None
                continue

            # FILTER candidates by assigned store
            store_filtered = [
                e for e in enriched_list
                if e["candidate"].source_store_id == assigned_store_id
            ]

            # Apply brand backstop rules
            backstop_filtered = []
            for e in store_filtered:
                candidate = e["candidate"]
                if self._validate_brand_backstop(candidate.brand, assigned_store_id):
                    backstop_filtered.append(e)
                else:
                    print(f"  ⚠️  Brand backstop violation: {candidate.brand} cannot be in {assigned_store_id}")

            # Apply price sanity filters (CRITICAL: prevent absurd prices)
            price_valid_candidates = []
            for e in backstop_filtered:
                candidate = e["candidate"]
                if self._validate_price_sanity(candidate, ingredient):
                    price_valid_candidates.append(e)
                else:
                    print(f"  ⚠️  Price sanity violation: {candidate.title} @ ${candidate.price:.2f} for {candidate.size}")

            # Apply unit-price consistency validation
            valid_candidates = []
            for e in price_valid_candidates:
                candidate = e["candidate"]
                if self._validate_unit_price_consistency(candidate):
                    valid_candidates.append(e)
                # Warning already printed in validation method

            if not valid_candidates:
                # No valid candidates from assigned store
                selections[ingredient] = None
                continue

            # NEW: Apply relative price outlier penalty to avoid premium-only picks
            # Compute median unit_price
            unit_prices = [e["candidate"].unit_price for e in valid_candidates]
            unit_prices.sort()
            n = len(unit_prices)
            median_unit_price = unit_prices[n // 2] if n % 2 == 1 else (unit_prices[n // 2 - 1] + unit_prices[n // 2]) / 2

            # Penalize outliers (unit_price > 2x median)
            for e in valid_candidates:
                candidate = e["candidate"]
                if candidate.unit_price > 2 * median_unit_price:
                    e["price_outlier_penalty"] = 1  # Penalize in sorting
                else:
                    e["price_outlier_penalty"] = 0

            # Sort by ethical score (organic > form_score > NOT price outlier > price)
            sorted_candidates = sorted(
                valid_candidates,
                key=lambda e: (
                    not e["candidate"].organic,  # Organic first
                    e.get("price_outlier_penalty", 0),  # Penalize outliers
                    e["candidate"].form_score,  # Fresh over dried
                    e["candidate"].price  # Cheaper is better (tie-breaker)
                )
            )

            # Ethical default = best scored (winner)
            ethical_default = sorted_candidates[0]

            # Runner-up = 2nd best candidate (for comparison in reason generation)
            runner_up = sorted_candidates[1] if len(sorted_candidates) > 1 else None

            # Cheaper swap = nearest cheaper viable option (if exists)
            # Must be at least 10% cheaper to be meaningful
            cheaper_swap = None
            if len(valid_candidates) > 1:
                ethical_price = ethical_default["candidate"].price

                # Find cheaper alternatives (at least 10% savings)
                cheaper_options = [
                    e for e in valid_candidates
                    if e["candidate"].price < ethical_price * 0.9  # At least 10% cheaper
                ]

                if cheaper_options:
                    # Pick the cheapest among cheaper options
                    cheaper_swap = min(cheaper_options, key=lambda e: e["candidate"].price)

            selections[ingredient] = {
                "ethical_default": ethical_default,
                "runner_up": runner_up,  # NEW: Track 2nd best for reason generation
                "cheaper_swap": cheaper_swap,
                "all_candidates": sorted_candidates
            }

        return selections

    def _validate_brand_backstop(self, brand: str, store_id: str) -> bool:
        """
        Brand backstop rules: Validate private label brand matches store

        Private label rules:
        - "365" → must be wholefoods
        - "FreshDirect" → must be freshdirect
        - "Bowl & Basket" → must be shoprite
        - "Pure Indian Foods" → must be pure_indian_foods
        """
        brand_lower = brand.lower()

        # 365 brand check
        if "365" in brand_lower:
            return store_id == "wholefoods"

        # FreshDirect brand check
        if "freshdirect" in brand_lower:
            return store_id == "freshdirect"

        # Bowl & Basket (ShopRite private label)
        if "bowl" in brand_lower and "basket" in brand_lower:
            return store_id == "shoprite"

        # Pure Indian Foods
        if "pure indian" in brand_lower:
            return store_id == "pure_indian_foods"

        # No private label detected, allow any store
        return True

    def _validate_price_sanity(self, candidate: ProductCandidate, ingredient: str) -> bool:
        """
        Price sanity filter: Reject candidates with unrealistic prices

        Plausible price ranges by category and size:
        - basmati rice 10lb: $18-$45
        - basmati rice 5lb: $9-$25
        - basmati rice 2lb: $3-$12
        - ghee 16oz: $8-$25, 32oz: $15-$40
        - spice jars (1.5-3oz): $2-$12
        - herbs per bunch: $1-$4
        - chicken per lb: $2-$12
        """
        price = candidate.price
        category = candidate.category.lower()
        size = candidate.size.lower()

        # Parse size value and unit
        import re
        size_match = re.search(r'(\d+\.?\d*)\s*(\w+)', size)
        if not size_match:
            return True  # Can't parse size, allow

        size_value = float(size_match.group(1))
        size_unit = size_match.group(2).lower()

        # Rice pricing bounds
        if category == "rice" or "rice" in ingredient.lower():
            if "lb" in size_unit:
                if size_value >= 10:
                    return 18 <= price <= 50
                elif size_value >= 5:
                    return 9 <= price <= 35  # Allow up to $35 for 5lb (includes premium organic)
                elif size_value >= 2:
                    return 3 <= price <= 15
                else:
                    return 2 <= price <= 10

        # Ghee pricing bounds
        if category == "oil" or "ghee" in ingredient.lower():
            if "oz" in size_unit:
                if size_value >= 32:
                    return 15 <= price <= 60
                elif size_value >= 16:
                    return 8 <= price <= 30
            elif "l" in size_unit:
                return 20 <= price <= 70

        # Spice pricing bounds
        if category == "spices":
            if "oz" in size_unit:
                if 1.5 <= size_value <= 3.5:
                    return 2 <= price <= 15
            elif "g" in size_unit:
                if 40 <= size_value <= 120:
                    return 2 <= price <= 15

        # Herbs pricing bounds
        if category == "herbs" or ingredient.lower() in ["mint", "cilantro", "parsley", "basil"]:
            if "bunch" in size_unit:
                return 1 <= price <= 5

        # Chicken pricing bounds (per lb)
        if category == "protein_poultry" or "chicken" in ingredient.lower():
            if "lb" in size_unit:
                # Price per lb should be reasonable
                price_per_lb = price / size_value if size_value > 0 else price
                return 2 <= price_per_lb <= 15

        # General produce bounds
        if category == "produce":
            if "lb" in size_unit:
                price_per_lb = price / size_value if size_value > 0 else price
                return 0.5 <= price_per_lb <= 20  # Very broad for produce

        # Default: allow if no specific rule
        return True

    def _validate_unit_price_consistency(self, candidate: ProductCandidate) -> bool:
        """
        Unit-price consistency validation: Ensure size_unit and unit_price_unit agree

        Expected mappings:
        - size_unit: "lb" → unit_price_unit: "oz" (per oz)
        - size_unit: "oz" → unit_price_unit: "oz"
        - size_unit: "g" → unit_price_unit: "g"
        - size_unit: "ct" or "bunch" → unit_price_unit: "ea"
        - size_unit: "L" → unit_price_unit: "oz"

        Returns False if inconsistent (drop candidate)
        """
        size = candidate.size.lower()
        actual_unit_price_unit = candidate.unit_price_unit.lower()

        # Parse size unit from candidate.size (format: "5 lb" or "16 oz")
        import re
        size_match = re.search(r'(\d+\.?\d*)\s*(\w+)', size)
        if not size_match:
            return True  # Can't parse, allow

        size_unit = size_match.group(2).lower()

        # Expected unit_price_unit based on size_unit
        expected_unit_price_units = {
            "lb": ["oz"],
            "oz": ["oz"],
            "g": ["g"],
            "ct": ["ea"],
            "bunch": ["ea"],
            "l": ["oz"]
        }

        expected = expected_unit_price_units.get(size_unit)
        if not expected:
            return True  # Unknown size unit, allow

        # Check if actual unit_price_unit matches expected
        if actual_unit_price_unit not in expected:
            print(f"  ⚠️  Unit-price inconsistency: {candidate.title} has size_unit={size_unit} but unit_price_unit={actual_unit_price_unit} (expected: {expected[0]})")
            return False

        return True

    # ========================================================================
    # Step 3: Choose Store Plan (REORDERED - before product selection)
    # ========================================================================

    def _choose_store_plan(
        self,
        enriched: Dict[str, List[Dict]],
        all_ingredients: List[str]
    ) -> StorePlan:
        """
        Choose optimal store plan based on candidate coverage

        CORRECTED LOGIC:
        1. Analyze which stores have candidates for each ingredient
        2. Choose stores that maximize coverage
        3. Assign ingredients to stores based on coverage
        4. Support multi-store: freshdirect + wholefoods + specialty

        Returns:
            StorePlan with store assignments (single source of truth)
        """
        # Track coverage: which stores can fulfill which ingredients
        store_coverage: Dict[str, List[str]] = {
            "freshdirect": [],
            "wholefoods": [],
            "pure_indian_foods": [],
            "shoprite": []
        }

        unavailable_ingredients = []

        for ingredient in all_ingredients:
            candidates = enriched.get(ingredient, [])

            if not candidates:
                unavailable_ingredients.append(ingredient)
                continue

            # Track which stores have candidates for this ingredient
            stores_with_candidates = set()
            for enriched_item in candidates:
                candidate = enriched_item["candidate"]
                stores_with_candidates.add(candidate.source_store_id)

            # Add to coverage for each store
            for store_id in stores_with_candidates:
                if store_id in store_coverage:
                    store_coverage[store_id].append(ingredient)

        # Choose stores to use based on coverage + quality
        stores = []
        assignments = []

        # Count specialty items (for threshold check)
        specialty_count = len(store_coverage["pure_indian_foods"])

        # Strategy: Use primary store + specialty if needed
        # Primary: Choose between freshdirect and wholefoods based on:
        # 1. Coverage count
        # 2. Fresh protein quality (for meat/poultry)
        # 3. Brand variety (penalize stores with only private label)

        freshdirect_score = self._score_store_for_primary(enriched, store_coverage["freshdirect"], "freshdirect")
        wholefoods_score = self._score_store_for_primary(enriched, store_coverage["wholefoods"], "wholefoods")

        print(f"\n  Store Scores: FreshDirect={freshdirect_score:.2f}, Whole Foods={wholefoods_score:.2f}")

        primary_store_id = "freshdirect"
        primary_store_name = "FreshDirect"

        if wholefoods_score > freshdirect_score:
            primary_store_id = "wholefoods"
            primary_store_name = "Whole Foods Market"

        # Add primary store
        stores.append(StoreInfo(
            store_id=primary_store_id,
            store_name=primary_store_name,
            store_type="primary",
            delivery_estimate="1-2 days"
        ))

        # Add specialty store if >=3 specialty items
        use_specialty = specialty_count >= 3

        if use_specialty:
            stores.append(StoreInfo(
                store_id="pure_indian_foods",
                store_name="Pure Indian Foods",
                store_type="specialty",
                delivery_estimate="3-5 days"
            ))

        # Assign ingredients to stores
        primary_ingredients = []
        specialty_ingredients = []

        for ingredient in all_ingredients:
            if ingredient in unavailable_ingredients:
                continue

            # Check if available in specialty store
            if use_specialty and ingredient in store_coverage["pure_indian_foods"]:
                specialty_ingredients.append(ingredient)
            else:
                # Assign to primary store
                primary_ingredients.append(ingredient)

        # Create assignments
        assignments.append(StoreAssignment(
            store_id=primary_store_id,
            ingredient_names=primary_ingredients,
            item_count=len(primary_ingredients),
            estimated_total=0.0  # Calculate later
        ))

        if use_specialty:
            assignments.append(StoreAssignment(
                store_id="pure_indian_foods",
                ingredient_names=specialty_ingredients,
                item_count=len(specialty_ingredients),
                estimated_total=0.0  # Calculate later
            ))

        return StorePlan(
            stores=stores,
            assignments=assignments,
            unavailable=unavailable_ingredients
        )

    def _score_store_for_primary(
        self,
        enriched: Dict[str, List[Dict]],
        covered_ingredients: List[str],
        store_id: str
    ) -> float:
        """
        Score a store for primary selection based on:
        - Coverage count (base score)
        - Fresh protein quality (+bonus for good chicken brands)
        - Brand variety (+bonus for non-private-label options)
        """
        # Base score: coverage count
        score = float(len(covered_ingredients))

        # Fresh protein quality bonus (for chicken, beef, fish)
        fresh_proteins = ["chicken", "beef", "fish", "pork"]
        for protein in fresh_proteins:
            if protein in covered_ingredients:
                # Check quality of protein candidates in this store
                protein_candidates = enriched.get(protein, [])
                store_protein_candidates = [
                    c for c in protein_candidates
                    if c["candidate"].source_store_id == store_id
                ]

                if store_protein_candidates:
                    # Bonus for premium brands (not private label only)
                    premium_brands = ["farmer focus", "mary's free range", "murray's organic", "bell & evans"]
                    has_premium = any(
                        any(brand in c["candidate"].brand.lower() for brand in premium_brands)
                        for c in store_protein_candidates
                    )

                    if has_premium:
                        score += 2.0  # Significant bonus for premium fresh protein

                    # Small bonus for variety (more than 2 options)
                    if len(store_protein_candidates) >= 3:
                        score += 0.5

        # Brand variety penalty: if >70% of covered items are private label, reduce score
        if covered_ingredients:
            private_label_count = 0
            total_checked = 0

            for ingredient in covered_ingredients[:10]:  # Sample first 10 ingredients
                ingredient_candidates = enriched.get(ingredient, [])
                store_candidates = [
                    c for c in ingredient_candidates
                    if c["candidate"].source_store_id == store_id
                ]

                if store_candidates and len(store_candidates) > 0:
                    # Check if top candidate is private label
                    top_candidate = sorted(
                        store_candidates,
                        key=lambda c: (not c["candidate"].organic, c["candidate"].price)
                    )[0]

                    if self._is_private_label(top_candidate["candidate"].brand, store_id):
                        private_label_count += 1
                    total_checked += 1

            if total_checked > 0 and private_label_count / total_checked > 0.7:
                score -= 1.0  # Penalty for lack of brand variety

        return score

    def _is_private_label(self, brand: str, store_id: str) -> bool:
        """Check if brand is the store's private label"""
        brand_lower = brand.lower()
        if store_id == "freshdirect" and "freshdirect" in brand_lower:
            return True
        if store_id == "wholefoods" and "365" in brand_lower:
            return True
        if store_id == "shoprite" and ("bowl" in brand_lower and "basket" in brand_lower):
            return True
        return False

    # ========================================================================
    # Step 5: Build Cart Items (NEVER drop ingredients)
    # ========================================================================

    def _build_cart_items(
        self,
        selections: Dict[str, Dict],
        store_plan: StorePlan,
        all_ingredients: List[str],
        ingredient_forms: Dict[str, Tuple[str, Optional[str]]]
    ) -> List[CartItem]:
        """
        Build cart items with chips

        CRITICAL FIX (Bug C): NEVER drop ingredients
        - Always create a CartItem for EVERY ingredient
        - If no selection available, create unavailable item

        P1 FIX: store_id assigned from store_plan, never changed
        P2 FIX: All data in CartItem, no lookup needed
        """
        cart_items = []

        # Build store assignment lookup
        store_by_ingredient = {}
        for assignment in store_plan.assignments:
            for ingredient_name in assignment.ingredient_names:
                store_by_ingredient[ingredient_name] = assignment.store_id

        # Process EVERY ingredient (not just those with selections)
        for ingredient in all_ingredients:
            selection = selections.get(ingredient)

            # Get canonical name and form
            canonical_name, form = ingredient_forms.get(ingredient, (ingredient, None))

            # Get assigned store (or primary if unavailable)
            primary_store_id = store_plan.stores[0].store_id if store_plan.stores else "freshdirect"
            store_id = store_by_ingredient.get(ingredient, primary_store_id)

            if selection is None or selection.get("ethical_default") is None:
                # UNAVAILABLE: Create placeholder item
                cart_item = self._build_unavailable_item(
                    ingredient_name=canonical_name,  # Use canonical name
                    store_id=store_id,
                    reason="No candidates found in store inventory",
                    ingredient_form=form
                )
            else:
                # AVAILABLE: Build normal item
                ethical = selection["ethical_default"]
                runner_up = selection.get("runner_up")  # NEW: Get 2nd best for comparison
                cheaper = selection.get("cheaper_swap")

                # Build ethical default product choice
                ethical_choice = self._build_product_choice(ethical)

                # Build cheaper swap if exists
                cheaper_choice = None
                if cheaper:
                    cheaper_choice = self._build_product_choice(cheaper)

                # Generate ingredient label
                ingredient_label = format_ingredient_label(canonical_name, form)

                # Generate reason and tradeoffs (NEW: pass runner_up for comparison)
                reason_line, reason_details, chips = self._generate_reason_and_tradeoffs(
                    ethical, runner_up, cheaper, canonical_name, form
                )

                # Build decision trace for scoring drawer
                all_candidates = selection.get("all_candidates", [])
                decision_trace = self._build_decision_trace(
                    winner=ethical,
                    runner_up=runner_up,
                    all_candidates=all_candidates,
                    reason_line=reason_line
                )

                # Create cart item
                cart_item = CartItem(
                    ingredient_name=canonical_name,  # Use canonical name
                    ingredient_label=ingredient_label,  # NEW: Combined name + form
                    ingredient_quantity="1",  # TODO: Extract from ingredients
                    ingredient_form=form,  # Include form for matching
                    store_id=store_id,
                    ethical_default=ethical_choice,
                    cheaper_swap=cheaper_choice,
                    status="available",
                    reason_line=reason_line,  # NEW: Single sentence reason
                    reason_details=reason_details,  # NEW: Hover details
                    chips=chips,
                    ewg_category=ethical.get("ewg_category"),
                    recall_status=ethical.get("recall_status", "safe"),
                    seasonality=ethical.get("seasonality", "available"),
                    decision_trace=decision_trace  # NEW: For scoring drawer
                )

            cart_items.append(cart_item)

        return cart_items

    def _build_unavailable_item(
        self,
        ingredient_name: str,
        store_id: str,
        reason: str,
        ingredient_form: Optional[str] = None
    ) -> CartItem:
        """
        Build a CartItem for an unavailable ingredient

        CRITICAL: CartItem.ethical_default is required, so we create a placeholder product
        """
        # Create a placeholder product for unavailable item
        placeholder_product = Product(
            product_id="unavailable",
            title=f"{ingredient_name.title()} (Not Available)",
            brand="N/A",
            price=0.0,
            size="N/A",
            unit="ea",
            organic=False,
            unit_price=0.0,
            unit_price_unit="oz",
            source_store_id=store_id
        )

        placeholder_choice = ProductChoice(
            product=placeholder_product,
            quantity=0.0,
            reasoning=reason
        )

        # Generate ingredient label for unavailable item
        ingredient_label = format_ingredient_label(ingredient_name, ingredient_form)

        return CartItem(
            ingredient_name=ingredient_name,
            ingredient_label=ingredient_label,  # NEW: Include label
            ingredient_quantity="as needed",
            ingredient_form=ingredient_form,
            store_id=store_id,
            ethical_default=placeholder_choice,
            cheaper_swap=None,
            status="unavailable",
            reason_line="Not found in selected stores",  # NEW: Clear unavailable reason
            reason_details=[],  # No details for unavailable items
            chips=ProductChips(
                why_pick=[],
                tradeoffs=[]  # No tradeoffs for unavailable items
            ),
            ewg_category=None,
            recall_status="safe",
            seasonality=None
        )

    def _build_product_choice(self, enriched_data: Dict) -> ProductChoice:
        """Convert enriched candidate to ProductChoice"""
        candidate = enriched_data["candidate"]

        product = Product(
            product_id=candidate.product_id,
            title=candidate.title,
            brand=candidate.brand,
            price=candidate.price,
            size=candidate.size,
            unit=candidate.unit,
            organic=candidate.organic,
            unit_price=candidate.unit_price,
            unit_price_unit="oz",
            source_store_id=candidate.source_store_id  # CRITICAL: Include provenance
        )

        return ProductChoice(
            product=product,
            quantity=1.0,
            reasoning=self._get_reasoning(enriched_data)
        )

    def _get_reasoning(self, enriched_data: Dict) -> str:
        """Generate reasoning for product selection"""
        candidate = enriched_data["candidate"]
        reasons = []

        if candidate.organic:
            reasons.append("organic")
        if candidate.form_score == 0:
            reasons.append("fresh")
        if enriched_data["recall_status"] == "safe":
            reasons.append("no recalls")

        return ", ".join(reasons) if reasons else "available"

    def _generate_reason_and_tradeoffs(
        self,
        winner: Dict,
        runner_up: Optional[Dict],
        cheaper: Optional[Dict],
        ingredient_name: str,
        ingredient_form: Optional[str]
    ) -> Tuple[str, List[str], ProductChips]:
        """
        Generate rule-based explanation (NO competitor mentions)

        CRITICAL REQUIREMENTS:
        - NO "Picked X over Y" language
        - Rule-based explanations only (e.g., "Organic recommended (EWG Dirty Dozen)")
        - NO vague phrases ("fresh pick", "optimal flavor", "good match")
        - NO standalone price chips ("+$1.00 more")
        - Cost only shown as part of tradeoff sentence when relevant
        - Tooltips must be specific and non-moralizing
        - NO invented facts in tooltips

        Allowed explanations:
        1. "Organic recommended (EWG Dirty Dozen)"
        2. "Conventional is OK (EWG Clean Fifteen)"
        3. "Wash/peel recommended (EWG guidance)"
        4. "Lower plastic packaging"
        5. "In-season in NJ"
        6. "Faster delivery"
        7. "Better value per unit"
        8. "Convenient form (powder/paste/peeled)"

        Returns:
            Tuple of (reason_line, reason_details, ProductChips)
        """
        winner_candidate = winner["candidate"]
        ewg_category = winner.get("ewg_category")

        # NO why_pick chips - removed for clarity
        why_pick = []

        # ========================================================================
        # RULE-BASED EXPLANATION (NO Competitor Mentions)
        # ========================================================================

        runner_up_candidate = runner_up["candidate"] if runner_up else None
        reason_code = None
        reason_line = ""
        reason_details = []
        tradeoffs = []

        # Priority 1: EWG Dirty Dozen (organic recommended)
        if ewg_category == "dirty_dozen" and winner_candidate.organic:
            reason_code = "ewg_dirty_dozen"
            reason_line = "Organic recommended (EWG Dirty Dozen)"
            reason_details = [
                "EWG Dirty Dozen: conventionally grown versions tend to have higher pesticide residues",
                f"Selected organic option at ${winner_candidate.price:.2f} for {winner_candidate.size}",
                "Wash thoroughly before use"
            ]

        # Priority 2: EWG Clean Fifteen (conventional is OK)
        elif ewg_category == "clean_fifteen":
            reason_code = "ewg_clean_fifteen"
            reason_line = "Conventional is OK (EWG Clean Fifteen)"
            reason_details = [
                "EWG Clean Fifteen: conventionally grown versions have low pesticide residues",
                f"${winner_candidate.price:.2f} for {winner_candidate.size}",
                "Organic option available if preferred"
            ]

        # Priority 3: Wash/peel recommended (EWG guidance for non-dirty-dozen produce)
        elif ewg_category and ewg_category not in ["dirty_dozen", "clean_fifteen"] and not winner_candidate.organic:
            reason_code = "ewg_wash_peel"
            reason_line = "Wash/peel recommended (EWG guidance)"
            reason_details = [
                "Not in EWG Dirty Dozen or Clean Fifteen",
                "Wash thoroughly and peel if applicable",
                f"${winner_candidate.price:.2f} for {winner_candidate.size}"
            ]

        # Priority 4: Lower plastic packaging (only if packaging known and better)
        elif not reason_code and runner_up_candidate:
            winner_pkg = self._detect_packaging(winner_candidate)
            runner_up_pkg = self._detect_packaging(runner_up_candidate)
            if winner_pkg != "Unknown" and runner_up_pkg != "Unknown" and winner_pkg != runner_up_pkg:
                pkg_score = {
                    "No packaging": 4,
                    "Glass jar": 3,
                    "Metal can": 3,
                    "Paper box": 2,
                    "Plastic bag": 1,
                    "Plastic clamshell": 1,
                    "Unknown": 0
                }
                if pkg_score.get(winner_pkg, 0) > pkg_score.get(runner_up_pkg, 0):
                    reason_code = "lower_plastic"
                    reason_line = "Lower plastic packaging"
                    reason_details = [
                        f"Packaging: {winner_pkg}",
                        f"Alternative had: {runner_up_pkg}",
                        "Less plastic waste"
                    ]

        # Priority 5: Convenient form (powder/paste/peeled vs whole/seeds)
        if not reason_code:
            title_lower = winner_candidate.title.lower()
            winner_form = ingredient_form or "unknown"

            # Check if convenient form
            is_powder = "powder" in title_lower or winner_form == "powder"
            is_paste = "paste" in title_lower or winner_form == "paste"
            is_peeled = "peeled" in title_lower or "chopped" in title_lower or "minced" in title_lower

            if is_powder or is_paste or is_peeled:
                reason_code = "convenient_form"
                if is_powder:
                    reason_line = "Convenient form (powder)"
                    reason_details = [
                        "Powder form - no grinding needed",
                        "Ready to use directly in cooking",
                        f"${winner_candidate.price:.2f} for {winner_candidate.size}"
                    ]
                elif is_paste:
                    reason_line = "Convenient form (paste)"
                    reason_details = [
                        "Paste form - saves prep time",
                        "No chopping or grinding needed",
                        f"${winner_candidate.price:.2f} for {winner_candidate.size}"
                    ]
                elif is_peeled:
                    reason_line = "Convenient form (pre-prepped)"
                    reason_details = [
                        "Already peeled/chopped - saves prep time",
                        "Ready to use",
                        f"${winner_candidate.price:.2f} for {winner_candidate.size}"
                    ]

        # Priority 6: Better value per unit (only if significantly better, >15%)
        if not reason_code and runner_up_candidate:
            winner_unit_price = winner_candidate.unit_price
            runner_up_unit_price = runner_up_candidate.unit_price

            if winner_unit_price < runner_up_unit_price * 0.85:
                reason_code = "better_unit_value"
                unit_savings = ((runner_up_unit_price - winner_unit_price) / runner_up_unit_price) * 100
                reason_line = "Better value per unit"
                reason_details = [
                    f"Unit price: ${winner_unit_price:.3f}/oz",
                    f"Saves {unit_savings:.0f}% per ounce vs alternatives",
                    f"${winner_candidate.price:.2f} for {winner_candidate.size}"
                ]

        # Priority 7: No alternative (store-only match)
        if not reason_code and runner_up is None:
            reason_code = "store_only"
            reason_line = "Available in selected stores"
            reason_details = [
                "Only option in current store selection",
                f"${winner_candidate.price:.2f} for {winner_candidate.size}"
            ]

        # Fallback: Generic selection (avoid this if possible)
        if not reason_code:
            reason_code = "selected"
            reason_line = "Selected for this recipe"
            reason_details = [
                f"${winner_candidate.price:.2f} for {winner_candidate.size}"
            ]

        # ========================================================================
        # TRADEOFF (embedded cost context, NO standalone price chips)
        # ========================================================================

        # NO standalone price chips like "+$1.00 more"
        # Cost only shown as part of explanation when it's a meaningful tradeoff

        # Check if cost needs to be mentioned as tradeoff
        if runner_up_candidate:
            price_diff = winner_candidate.price - runner_up_candidate.price
            # Only mention cost if it's significant AND not already explained by EWG/quality reason
            if price_diff > 0.5 and reason_code in ["ewg_dirty_dozen", "lower_plastic", "convenient_form"]:
                cost_context = f"Costs ~${price_diff:.0f} more upfront; chosen because {reason_line.split('(')[0].strip().lower()}."
                # Add cost context to reason_details if not already mentioned
                if not any("$" in detail and "more" in detail.lower() for detail in reason_details):
                    reason_details.append(cost_context)

        return reason_line, reason_details, ProductChips(why_pick=why_pick, tradeoffs=tradeoffs)

    def _detect_packaging(self, candidate) -> str:
        """
        Detect packaging type from product title keywords (dummy-proof)

        Returns one of:
        - No packaging
        - Plastic bag
        - Plastic clamshell
        - Glass jar
        - Metal can
        - Paper box
        - Unknown packaging
        """
        title_lower = candidate.title.lower()

        # Check for explicit keywords (order matters - more specific first)
        if any(kw in title_lower for kw in ["no packaging", "bulk", "loose"]):
            return "No packaging"
        elif any(kw in title_lower for kw in ["glass jar", "jar"]):
            return "Glass jar"
        elif any(kw in title_lower for kw in ["metal can", "can", "tin"]):
            return "Metal can"
        elif any(kw in title_lower for kw in ["paper box", "box", "carton"]):
            return "Paper box"
        elif any(kw in title_lower for kw in ["clamshell", "container", "tray"]):
            return "Plastic clamshell"
        elif any(kw in title_lower for kw in ["bag", "pouch", "packaged"]):
            return "Plastic bag"
        else:
            return "Unknown"

    def _needs_prep(self, candidate, ingredient_form: Optional[str], ingredient_name: str) -> bool:
        """Check if product needs prep (chopping, grinding, etc.)"""
        title_lower = candidate.title.lower()
        form_lower = ingredient_form.lower() if ingredient_form else ""
        ingredient_lower = ingredient_name.lower()

        # Already processed - no prep needed
        is_processed = any(kw in title_lower for kw in ["powder", "paste", "minced", "chopped", "ground", "diced", "sliced"])
        if is_processed:
            return False

        # Check if needs prep
        if "whole chicken" in title_lower:
            return True
        elif form_lower in ["seeds", "pods", "whole_spice"]:
            return True
        elif ingredient_lower in ["onion", "onions", "tomato", "tomatoes", "ginger", "garlic"]:
            # Check if whole/fresh (needs chopping)
            if "whole" in title_lower or form_lower in ["whole", "fresh"]:
                return True

        return False

    def _build_decision_trace(
        self,
        winner: Dict,
        runner_up: Optional[Dict],
        all_candidates: List[Dict],
        reason_line: str
    ) -> Dict:
        """
        Build decision trace for scoring drawer

        Returns dict with:
        - winner_score, runner_up_score
        - candidates list (all considered + filtered)
        - filtered_out_summary
        - score_drivers
        """
        winner_candidate = winner["candidate"]
        runner_up_candidate = runner_up["candidate"] if runner_up else None

        # Simple scoring: organic=40, form_score_bonus=30, unit_price_bonus=30
        winner_score = self._calculate_simple_score(winner_candidate)
        runner_up_score = self._calculate_simple_score(runner_up_candidate) if runner_up_candidate else None

        # Build candidates list
        candidates = []
        for idx, c_dict in enumerate(all_candidates[:10]):  # Top 10
            c = c_dict["candidate"]
            score = self._calculate_simple_score(c)

            # Determine status
            if c.product_id == winner_candidate.product_id:
                status = "Winner"
            elif runner_up_candidate and c.product_id == runner_up_candidate.product_id:
                status = "Runner-up"
            else:
                status = "Considered"

            candidates.append({
                "product": c.title,
                "brand": c.brand,
                "store": c.source_store_id,
                "price": c.price,
                "unit_price": round(c.unit_price, 3),
                "organic": c.organic,
                "form_score": c.form_score,
                "packaging": self._detect_packaging(c),
                "status": status,
                "score": score
            })

        # Score drivers (based on reason_line)
        drivers = []
        if "EWG Dirty Dozen" in reason_line or "EWG Clean Fifteen" in reason_line:
            drivers.append({"rule": "EWG guidance applied", "delta": 15})
        if "Lower plastic" in reason_line:
            drivers.append({"rule": "Better packaging", "delta": 5})
        if "Convenient form" in reason_line:
            drivers.append({"rule": "Time-saving form", "delta": 5})
        if "Better value" in reason_line:
            drivers.append({"rule": "Unit price advantage", "delta": 10})
        if winner_candidate.organic:
            drivers.append({"rule": "Organic certification", "delta": 10})

        # Top 2 drivers
        drivers = sorted(drivers, key=lambda d: d["delta"], reverse=True)[:2]

        return {
            "winner_score": winner_score,
            "runner_up_score": runner_up_score,
            "score_margin": winner_score - (runner_up_score or 0),
            "candidates": candidates,
            "filtered_out_summary": {},  # TODO: Track elimination reasons
            "drivers": drivers
        }

    def _calculate_simple_score(self, candidate) -> int:
        """Calculate simple 0-100 score for candidate"""
        if candidate is None:
            return 0

        score = 50  # Base score

        # Organic bonus
        if candidate.organic:
            score += 20

        # Form score bonus (lower form_score is better)
        if candidate.form_score == 0:
            score += 15  # Fresh/whole
        elif candidate.form_score <= 5:
            score += 10  # Seeds/pods
        elif candidate.form_score <= 10:
            score += 5   # Dried
        # Powder/granules get no bonus

        # Unit price bonus (relative, capped)
        # Lower unit price is better, but cap at +15
        if candidate.unit_price > 0:
            # Normalize to a 0-15 scale (assuming $0.10/oz is excellent, $1.00/oz is poor)
            price_score = max(0, 15 - int(candidate.unit_price * 15))
            score += min(15, price_score)

        return min(100, score)  # Cap at 100

    # ========================================================================
    # Step 6: Calculate Totals
    # ========================================================================

    def _calculate_totals(self, cart_items: List[CartItem]) -> CartTotals:
        """Calculate cart totals"""
        ethical_total = sum(
            item.ethical_default.product.price * item.ethical_default.quantity
            for item in cart_items
        )

        cheaper_total = sum(
            (item.cheaper_swap.product.price * item.cheaper_swap.quantity
             if item.cheaper_swap else
             item.ethical_default.product.price * item.ethical_default.quantity)
            for item in cart_items
        )

        # Per-store totals
        store_totals = {}
        for item in cart_items:
            if item.store_id not in store_totals:
                store_totals[item.store_id] = 0.0
            store_totals[item.store_id] += item.ethical_default.product.price * item.ethical_default.quantity

        return CartTotals(
            ethical_total=round(ethical_total, 2),
            cheaper_total=round(cheaper_total, 2),
            savings_potential=round(ethical_total - cheaper_total, 2),
            store_totals=store_totals
        )


# ============================================================================
# CLI Test
# ============================================================================

if __name__ == "__main__":
    print("=== Testing PlannerEngine ===\n")

    engine = PlannerEngine()

    # Test: Chicken biryani for 4
    print("TEST: Chicken biryani for 4")
    print("-" * 60)

    ingredients = [
        "chicken", "rice", "onions", "tomatoes", "yogurt",
        "ginger", "garlic", "ghee", "garam masala", "turmeric"
    ]

    plan = engine.create_plan(
        prompt="chicken biryani for 4",
        ingredients=ingredients,
        servings=4
    )

    print(f"\n✓ CartPlan created")
    print(f"  - Items: {len(plan.items)}")
    print(f"  - Stores: {[s.store_name for s in plan.store_plan.stores]}")
    print(f"  - Ethical total: ${plan.totals.ethical_total}")
    print(f"  - Cheaper total: ${plan.totals.cheaper_total}")
    print(f"  - Savings: ${plan.totals.savings_potential}")

    # Check P0 fix: Ginger should be fresh
    ginger_item = next((item for item in plan.items if item.ingredient_name == "ginger"), None)
    if ginger_item:
        print(f"\n✓ Ginger selected: {ginger_item.ethical_default.product.title}")
        print(f"  Form score should be 0 (fresh)")

    # Check P1 fix: Store assignments preserved
    print(f"\n✓ Store assignments:")
    for item in plan.items[:5]:
        print(f"  - {item.ingredient_name} → {item.store_id}")

    # Check P2 fix: Tradeoff tags present
    items_with_tradeoffs = [item for item in plan.items if item.chips.tradeoffs]
    print(f"\n✓ Items with tradeoff tags: {len(items_with_tradeoffs)}/{len(plan.items)}")
    for item in items_with_tradeoffs[:3]:
        print(f"  - {item.ingredient_name}: {item.chips.tradeoffs}")
