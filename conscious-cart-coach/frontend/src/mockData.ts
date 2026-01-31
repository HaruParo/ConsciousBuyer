// Mock data for demo
import { Ingredient, StoreInfo, CartItem } from './types'

// Mock ingredient extraction based on prompts
export const extractIngredientsFromPrompt = (prompt: string): Ingredient[] => {
  const promptLower = prompt.toLowerCase()

  // Biryani recipe
  if (promptLower.includes('biryani')) {
    return [
      { id: '1', name: 'basmati rice', quantity: 2, unit: 'cups' },
      { id: '2', name: 'chicken', quantity: 2, unit: 'lbs' },
      { id: '3', name: 'red onions', quantity: 2, unit: 'large' },
      { id: '4', name: 'roma tomatoes', quantity: 3, unit: 'medium' },
      { id: '5', name: 'yogurt', quantity: 1, unit: 'cup' },
      { id: '6', name: 'ginger', quantity: 2, unit: 'inches' },
      { id: '7', name: 'garlic', quantity: 10, unit: 'cloves' },
      { id: '8', name: 'green chilies', quantity: 3, unit: 'whole' },
      { id: '9', name: 'cilantro', quantity: 0.5, unit: 'cup' },
      { id: '10', name: 'mint leaves', quantity: 0.5, unit: 'cup' },
      { id: '11', name: 'ghee', quantity: 4, unit: 'tbsp' },
      { id: '12', name: 'turmeric', quantity: 1, unit: 'tsp' },
      { id: '13', name: 'cumin', quantity: 2, unit: 'tsp' },
      { id: '14', name: 'coriander', quantity: 2, unit: 'tsp' },
      { id: '15', name: 'garam masala', quantity: 2, unit: 'tsp' },
      { id: '16', name: 'cardamom', quantity: 4, unit: 'pods' },
      { id: '17', name: 'cinnamon', quantity: 2, unit: 'sticks' },
      { id: '18', name: 'cloves', quantity: 5, unit: 'whole' },
      { id: '19', name: 'bay leaves', quantity: 2, unit: 'leaves' },
      { id: '20', name: 'saffron', quantity: 1, unit: 'pinch' },
      { id: '21', name: 'salt', quantity: 1, unit: 'tsp' },
    ]
  }

  // Salad recipe
  if (promptLower.includes('salad')) {
    return [
      { id: '1', name: 'lettuce', quantity: 1, unit: 'head' },
      { id: '2', name: 'tomatoes', quantity: 2, unit: 'medium' },
      { id: '3', name: 'cucumber', quantity: 1, unit: 'medium' },
      { id: '4', name: 'red onion', quantity: 1, unit: 'small' },
      { id: '5', name: 'feta cheese', quantity: 4, unit: 'oz' },
      { id: '6', name: 'olive oil', quantity: 3, unit: 'tbsp' },
      { id: '7', name: 'lemon', quantity: 1, unit: 'whole' },
    ]
  }

  // Seasonal veggies
  if (promptLower.includes('seasonal') || promptLower.includes('vegetables')) {
    return [
      { id: '1', name: 'broccoli', quantity: 2, unit: 'heads' },
      { id: '2', name: 'carrots', quantity: 1, unit: 'lb' },
      { id: '3', name: 'bell peppers', quantity: 3, unit: 'medium' },
      { id: '4', name: 'zucchini', quantity: 2, unit: 'medium' },
      { id: '5', name: 'mushrooms', quantity: 8, unit: 'oz' },
    ]
  }

  // Default
  return [
    { id: '1', name: 'tomatoes', quantity: 2, unit: 'medium' },
    { id: '2', name: 'lettuce', quantity: 1, unit: 'head' },
    { id: '3', name: 'chicken', quantity: 1, unit: 'lb' },
  ]
}

// Mock store assignment based on ingredient classification
const specialtyIngredients = [
  'basmati rice', 'ghee', 'saffron', 'turmeric', 'cumin', 'coriander',
  'garam masala', 'biryani masala', 'cardamom', 'cinnamon', 'cloves',
  'bay leaves', 'curry leaves', 'paneer', 'kashmiri chili', 'kasuri methi',
  'asafoetida', 'hing', 'fennel seeds', 'mustard seeds', 'fenugreek'
]

export const assignStores = (ingredients: Ingredient[]): StoreInfo[] => {
  const primaryItems: string[] = []
  const specialtyItems: string[] = []

  ingredients.forEach(ing => {
    if (specialtyIngredients.includes(ing.name.toLowerCase())) {
      specialtyItems.push(ing.name)
    } else {
      primaryItems.push(ing.name)
    }
  })

  const stores: StoreInfo[] = []

  // Primary store always exists
  stores.push({
    name: 'FreshDirect',
    count: primaryItems.length,
    ingredients: primaryItems,
    isPrimary: true,
    deliveryEstimate: '1-2 days'
  })

  // Add specialty store if there are specialty items
  if (specialtyItems.length > 0) {
    stores.push({
      name: 'Pure Indian Foods',
      count: specialtyItems.length,
      ingredients: specialtyItems,
      isPrimary: false,
      deliveryEstimate: '1-2 weeks'
    })
  }

  return stores
}

// Mock cart items
export const generateCartItems = (ingredients: Ingredient[], store: string): CartItem[] => {
  return ingredients.map((ing, idx) => {
    const isAvailable = Math.random() > 0.1 // 90% availability
    const basePrice = Math.random() * 10 + 2

    return {
      id: `${store}-${idx}`,
      ingredientName: ing.name,
      name: `${ing.name.charAt(0).toUpperCase()}${ing.name.slice(1)}`,
      brand: store === 'FreshDirect' ? 'FreshDirect Brand' : 'Authentic Indian',
      price: parseFloat(basePrice.toFixed(2)),
      quantity: ing.quantity || 1,
      size: ing.unit || 'unit',
      store,
      available: isAvailable,
      tags: {
        whyPick: isAvailable ? ['Fresh', 'In Season', 'No recent recalls'] : [],
        tradeOffs: isAvailable ? [] : ['Currently unavailable']
      }
    }
  })
}
