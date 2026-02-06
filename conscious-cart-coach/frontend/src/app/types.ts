export interface CartItem {
  id: string;
  name: string;
  brand: string;
  catalogueName: string;
  price: number;
  quantity: number;
  size: string;
  image: string;
  tags: {
    whyPick: string[];
    tradeOffs: string[];
  };
  store: string;
  location: string;
  unitPrice?: number;
  unitPriceUnit?: string;
  ingredientName?: string;
  available?: boolean;
  // NEW: V2 fields (from backend reason generation)
  reasonLine?: string;
  reasonDetails?: string[];
  decisionTrace?: DecisionTrace; // For scoring drawer
}

export interface MealPlanData {
  input: string;
  items: CartItem[];
}

// New types for multi-store flow
export interface Ingredient {
  name: string;
  quantity: number;
  unit: string;
  category?: string;
}

export interface StoreInfo {
  store: string;
  ingredients: string[];
  count: number;
  is_primary: boolean;
  delivery_estimate?: string; // e.g., "1-2 days" or "1-2 weeks"
}

export interface UnavailableItem {
  ingredient: string;
  quantity: string;
  reason: string;
  external_sources: any[];
}

export interface StoreSplit {
  available_stores: StoreInfo[];
  unavailable_items: UnavailableItem[];
  total_stores_needed: number;
}

export interface ExtractIngredientsResponse {
  ingredients: Ingredient[];
  servings: number;
  store_split: StoreSplit;
  primary_store: string;
}

export interface CartData {
  store: string;
  is_primary: boolean;
  items: CartItem[];
  total: number;
  item_count: number;
  delivery_estimate?: string; // e.g., "1-2 days" or "1-2 weeks"
}

export interface MultiCartResponse {
  carts: CartData[];
  current_cart: string;
  total_all_carts: number;
  servings: number;
  confirmed_ingredients: Ingredient[];
  unavailable_items: UnavailableItem[];
}

export type AppState = 'idle' | 'confirmingIngredients' | 'cartReady' | 'agentCheckout';

// ============================================================================
// V2 CartPlan Types (matches backend src/contracts/cart_plan.py)
// ============================================================================

export interface ProductV2 {
  product_id: string;
  title: string;
  brand: string;
  price: number;
  size: string;
  unit: string;
  organic: boolean;
  unit_price: number;
  unit_price_unit: string;
  image_url: string | null;
}

export interface ProductChoice {
  product: ProductV2;
  quantity: number;
  reasoning: string;
}

export interface ProductChips {
  why_pick: string[];
  tradeoffs: string[];
}

export interface CandidatePoolSummary {
  store_id: string;
  store_name: string;
  retrieved_count: number;
  considered_count: number;
}

export interface DecisionTrace {
  query_key: string; // NEW: Normalized ingredient key used for retrieval
  retrieved_summary: CandidatePoolSummary[]; // NEW: Retrieved from ProductIndex by store
  considered_summary: CandidatePoolSummary[]; // NEW: After filters by store
  winner_score: number;
  runner_up_score: number | null;
  score_margin: number;
  candidates: Array<{
    product: string;
    brand: string;
    store: string;
    price: number;
    unit_price: number;
    organic: boolean;
    form_score: number;
    packaging: string;
    status: string;
    score_total: number;
    score_breakdown?: {  // NEW: Component score breakdown
      base: number;
      ewg: number;
      form_fit: number;
      packaging: number;
      delivery: number;
      unit_value: number;
      outlier_penalty: number;
    };
    elimination_reasons: string[];
    elimination_explanation?: string; // NEW: Human-readable explanation
    elimination_stage?: string; // NEW: Stage where eliminated
  }>;
  filtered_out_summary: Record<string, number>;
  drivers: Array<{
    rule: string;
    delta: number;
  }>;
  tradeoffs_accepted: string[]; // NEW: Tradeoffs accepted on winner
}

export interface CartItemV2 {
  ingredient_name: string;
  ingredient_label: string; // NEW: Combined name + form ("fresh ginger", "cumin seeds", etc.)
  ingredient_quantity: string;
  ingredient_form: string | null; // powder, seeds, pods, leaves, whole, etc. (used for matching)
  store_id: string;
  ethical_default: ProductChoice;
  cheaper_swap: ProductChoice | null;
  status: string;
  reason_line: string; // NEW: Single sentence explaining selection ("Fresh pick for optimal flavor", etc.)
  reason_details: string[]; // NEW: Bullets for ⓘ hover (1-2 details)
  chips: ProductChips;
  seasonality: string | null;
  ewg_category: string | null;
  recall_status: string;
  decision_trace?: DecisionTrace; // Optional decision trace for scoring drawer
}

export interface StoreInfoV2 {
  store_id: string;
  store_name: string;
  store_type: string;
  delivery_estimate: string;
  checkout_url_template: string | null;
  selection_reason?: string; // NEW: Why this store was chosen
}

export interface StoreAssignment {
  store_id: string;
  ingredient_names: string[];
  item_count: number;
  estimated_total: number;
  assignment_reason?: string; // NEW: Why these ingredients were assigned to this store
}

export interface StorePlan {
  stores: StoreInfoV2[];
  assignments: StoreAssignment[];
  unavailable: string[];
}

export interface CartTotals {
  ethical_total: number;
  cheaper_total: number;
  savings_potential: number;
  store_totals: { [store_id: string]: number };
}

export interface CartPlan {
  prompt: string;
  servings: number;
  ingredients: string[];
  store_plan: StorePlan;
  items: CartItemV2[];
  totals: CartTotals;
  created_at: string | null;
  planner_version: string;
}
