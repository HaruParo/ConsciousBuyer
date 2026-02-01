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
