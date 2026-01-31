import { CartItem } from '@/app/types';

// Mock data for different meal plan scenarios
const mealPlanDatabase: Record<string, Partial<CartItem>[]> = {
  'seasonal veggies': [
    {
      name: 'Organic Spinach',
      brand: 'Green Valley Farms',
      catalogueName: 'Organic Baby Spinach',
      price: 4.99,
      size: '5 oz',
      image: 'https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400&h=300&fit=crop',
      tags: {
        whyPick: ['Organic', 'Local', 'Best value', 'Farmer\'s co-op', 'Recyclable packaging'],
        tradeOffs: ['Plastic clamshell (5oz, thicker plastic per oz)', 'Part of EWG Dirty Dozen (Organic recommended)', 'Costlier than conventional']
      },
      store: 'Whole Foods Market',
      location: 'San Francisco, CA'
    },
    {
      name: 'Rainbow Carrots',
      brand: 'Farm Fresh',
      catalogueName: 'Heritage Rainbow Carrots',
      price: 3.49,
      size: '1 lb',
      image: 'https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?w=400&h=300&fit=crop',
      tags: {
        whyPick: ['Local', 'Seasonal', 'Best value', 'Farmer\'s co-op'],
        tradeOffs: ['No supplier transparency', 'Fair trade']
      },
      store: 'Whole Foods Market',
      location: 'San Francisco, CA'
    },
    {
      name: 'Brussels Sprouts',
      brand: 'Seasonal Harvest',
      catalogueName: 'Fresh Brussels Sprouts',
      price: 5.99,
      size: '12 oz',
      image: 'https://images.unsplash.com/photo-1599818101570-447ae8e93480?w=400&h=300&fit=crop',
      tags: {
        whyPick: ['Organic', 'Local', 'Seasonal', 'Human Packed'],
        tradeOffs: ['Higher price point', 'Limited availability']
      },
      store: 'Whole Foods Market',
      location: 'San Francisco, CA'
    }
  ],
  'tofu miso soup': [
    {
      name: 'Organic Firm Tofu',
      brand: 'House Foods',
      catalogueName: 'Organic Firm Tofu 14oz',
      price: 3.99,
      size: '14 oz',
      image: 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=300&fit=crop',
      tags: {
        whyPick: ['Organic', 'High protein', 'Recyclable packaging'],
        tradeOffs: ['Imported', 'Plastic tray packaging']
      },
      store: 'Trader Joe\'s',
      location: 'Berkeley, CA'
    },
    {
      name: 'White Miso Paste',
      brand: 'Hikari',
      catalogueName: 'Organic White Miso',
      price: 6.99,
      size: '17.6 oz',
      image: 'https://images.unsplash.com/photo-1589621316382-008455b857cd?w=400&h=300&fit=crop',
      tags: {
        whyPick: ['Organic', 'Traditional fermented', 'Long shelf life'],
        tradeOffs: ['Imported from Japan', 'Plastic container']
      },
      store: 'Trader Joe\'s',
      location: 'Berkeley, CA'
    },
    {
      name: 'Green Onions',
      brand: 'Fresh Valley',
      catalogueName: 'Organic Green Onions Bunch',
      price: 1.99,
      size: '1 bunch',
      image: 'https://images.unsplash.com/photo-1603569283847-aa295f0d016a?w=400&h=300&fit=crop',
      tags: {
        whyPick: ['Organic', 'Local', 'Low cost'],
        tradeOffs: ['Rubber band bundling', 'Short shelf life']
      },
      store: 'Trader Joe\'s',
      location: 'Berkeley, CA'
    },
    {
      name: 'Shiitake Mushrooms',
      brand: 'Organic Valley',
      catalogueName: 'Fresh Shiitake Mushrooms',
      price: 4.99,
      size: '8 oz',
      image: 'https://images.unsplash.com/photo-1618639149721-92c6b0c69004?w=400&h=300&fit=crop',
      tags: {
        whyPick: ['Organic', 'Local grower', 'Recyclable packaging'],
        tradeOffs: ['Premium price', 'Cardboard tray with plastic wrap']
      },
      store: 'Trader Joe\'s',
      location: 'Berkeley, CA'
    }
  ],
  'pasta': [
    {
      name: 'Organic Pasta',
      brand: 'Bionaturae',
      catalogueName: 'Organic Spaghetti',
      price: 3.49,
      size: '16 oz',
      image: 'https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?w=400&h=300&fit=crop',
      tags: {
        whyPick: ['Organic', 'Cardboard packaging', 'Fair trade'],
        tradeOffs: ['Imported', 'Higher price than conventional']
      },
      store: 'Safeway',
      location: 'Portland, OR'
    },
    {
      name: 'Cherry Tomatoes',
      brand: 'Nature\'s Pride',
      catalogueName: 'Organic Cherry Tomatoes',
      price: 4.99,
      size: '10 oz',
      image: 'https://images.unsplash.com/photo-1592841200221-a6898f307baa?w=400&h=300&fit=crop',
      tags: {
        whyPick: ['Organic', 'Local', 'Sweet variety'],
        tradeOffs: ['Plastic clamshell packaging']
      },
      store: 'Safeway',
      location: 'Portland, OR'
    }
  ],
  'stir fry': [
    {
      name: 'Bell Peppers Mix',
      brand: 'Farm Stand',
      catalogueName: 'Organic Bell Peppers Trio',
      price: 6.99,
      size: '3 pack',
      image: 'https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?w=400&h=300&fit=crop',
      tags: {
        whyPick: ['Organic', 'Color variety', 'Local'],
        tradeOffs: ['Plastic wrap', 'Premium pricing']
      },
      store: 'Local Market',
      location: 'Seattle, WA'
    },
    {
      name: 'Broccoli Crowns',
      brand: 'Green Fields',
      catalogueName: 'Fresh Broccoli Crowns',
      price: 2.99,
      size: '12 oz',
      image: 'https://images.unsplash.com/photo-1459411621453-7b03977f4baa?w=400&h=300&fit=crop',
      tags: {
        whyPick: ['Local', 'Seasonal', 'Best value'],
        tradeOffs: ['Not organic', 'Rubber band bundling']
      },
      store: 'Local Market',
      location: 'Seattle, WA'
    }
  ]
};

export function convertMealPlanToCart(mealPlan: string): CartItem[] {
  const input = mealPlan.toLowerCase();
  
  // Find matching meal plan items
  let selectedItems: Partial<CartItem>[] = [];
  
  for (const [key, items] of Object.entries(mealPlanDatabase)) {
    if (input.includes(key)) {
      selectedItems = [...selectedItems, ...items];
    }
  }
  
  // If no specific match, provide default veggies
  if (selectedItems.length === 0) {
    selectedItems = mealPlanDatabase['seasonal veggies'];
  }
  
  // Convert to full CartItem objects with IDs and default quantity
  return selectedItems.map((item, index) => ({
    id: `item-${Date.now()}-${index}`,
    name: item.name || 'Product',
    brand: item.brand || 'Brand',
    catalogueName: item.catalogueName || 'Item',
    price: item.price || 0,
    quantity: 1,
    size: item.size || '1 unit',
    image: item.image || 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=400&h=300&fit=crop',
    tags: item.tags || { whyPick: [], tradeOffs: [] },
    store: item.store || 'Local Store',
    location: item.location || 'Nearby'
  }));
}