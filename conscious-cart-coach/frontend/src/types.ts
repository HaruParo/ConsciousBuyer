// Type definitions for Conscious Cart Coach

export type AppState = 'idle' | 'confirmingIngredients' | 'cartReady' | 'agentCheckout'

export interface Ingredient {
  id: string
  name: string
  quantity?: number
  unit?: string
}

export interface StoreInfo {
  name: string
  count: number
  ingredients: string[]
  isPrimary: boolean
  deliveryEstimate?: string
}

export interface CartItem {
  id: string
  ingredientName: string
  name: string
  brand: string
  price: number
  quantity: number
  size: string
  store: string
  available: boolean
  tags: {
    whyPick: string[]
    tradeOffs: string[]
  }
}

export interface Cart {
  store: string
  items: CartItem[]
  total: number
  isPrimary: boolean
  deliveryEstimate?: string
}

export interface CheckoutStore {
  name: string
  url: string
  ready: boolean
}
