import { useState, useEffect } from 'react';
import { MealPlanInput } from '@/app/components/MealPlanInput';
import { ShoppingCart } from '@/app/components/ShoppingCart';
import { MultiStoreCart } from '@/app/components/MultiStoreCart';
import { StyleGuide } from '@/app/components/StyleGuide';
import { LocationModal } from '@/app/components/LocationModal';
import { IngredientConfirmModal } from '@/app/components/IngredientConfirmModal';
import { AgentCheckoutModal } from '@/app/components/AgentCheckoutModal';
import { LoadingOverlay } from '@/app/components/LoadingOverlay';
import {
  AppState,
  Ingredient,
  CartData,
  ExtractIngredientsResponse,
  MultiCartResponse,
  StoreSplit
} from '@/app/types';
import { extractIngredients, createMultiCart, ApiError } from '@/app/services/api';
import { BookOpen } from 'lucide-react';

export default function App() {
  // State
  const [appState, setAppState] = useState<AppState>('idle');
  const [mealPlan, setMealPlan] = useState('');
  const [servings, setServings] = useState(2);
  const [showStyleGuide, setShowStyleGuide] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('Processing...');
  const [loadingSubmessage, setLoadingSubmessage] = useState<string | undefined>();
  const [error, setError] = useState<string | null>(null);
  const [userLocation, setUserLocation] = useState<{ city: string; state: string } | null>(null);
  const [showLocationModal, setShowLocationModal] = useState(false);

  // New flow state
  const [draftIngredients, setDraftIngredients] = useState<Ingredient[]>([]);
  const [storeSplit, setStoreSplit] = useState<StoreSplit | null>(null);
  const [carts, setCarts] = useState<CartData[]>([]);
  const [multiCartData, setMultiCartData] = useState<MultiCartResponse | null>(null);

  // Check for stored location on mount
  useEffect(() => {
    const storedLocation = localStorage.getItem('userLocation');
    if (storedLocation) {
      const location = JSON.parse(storedLocation);
      setUserLocation(location);
    }
    // Don't show modal automatically - only show when user clicks "Change"
  }, []);

  const handleLocationSet = (city: string, state: string) => {
    const location = { city, state };
    setUserLocation(location);
    localStorage.setItem('userLocation', JSON.stringify(location));
    setShowLocationModal(false);
  };

  const handleChangeLocation = () => {
    setShowLocationModal(true);
  };

  // Step 1: Extract ingredients and show confirmation modal
  const handleCreateCart = async () => {
    if (!mealPlan.trim()) return;

    // If no location set, show location modal first
    if (!userLocation) {
      setShowLocationModal(true);
      return;
    }

    setIsLoading(true);
    setLoadingMessage('Analyzing your meal plan...');
    setLoadingSubmessage('Extracting ingredients and checking product availability');
    setError(null);

    const minLoadingTime = new Promise(resolve => setTimeout(resolve, 800));

    try {
      const [response] = await Promise.all([
        extractIngredients(mealPlan, servings),
        minLoadingTime
      ]);
      setDraftIngredients(response.ingredients);
      setStoreSplit(response.store_split);
      setAppState('confirmingIngredients');
    } catch (err) {
      await minLoadingTime;
      if (err instanceof ApiError) {
        setError(err.detail || err.message);
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
      console.error('Failed to extract ingredients:', err);
    } finally {
      setIsLoading(false);
      setLoadingSubmessage(undefined);
    }
  };

  // Step 2: User confirms ingredients, create multi-cart
  const handleConfirmIngredients = async (confirmedIngredients: Ingredient[]) => {
    setIsLoading(true);
    setLoadingMessage('Building your personalized cart...');
    setLoadingSubmessage('Finding the best products across stores based on quality, health, and value');
    setError(null);

    const minLoadingTime = new Promise(resolve => setTimeout(resolve, 1200));

    try {
      const [response] = await Promise.all([
        createMultiCart(mealPlan, confirmedIngredients, storeSplit, servings),
        minLoadingTime
      ]);

      setCarts(response.carts);
      setMultiCartData(response);
      setAppState('cartReady');
    } catch (err) {
      await minLoadingTime;
      if (err instanceof ApiError) {
        setError(err.detail || err.message);
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
      console.error('Failed to create cart:', err);
      setAppState('idle');
    } finally {
      setIsLoading(false);
      setLoadingSubmessage(undefined);
    }
  };

  const handleCancelConfirmation = () => {
    setAppState('idle');
    setDraftIngredients([]);
    setStoreSplit(null);
  };

  const handleAgentCheckout = () => {
    setAppState('agentCheckout');
  };

  const handleCloseAgentCheckout = () => {
    setAppState('cartReady');
  };

  const handleUpdateQuantity = (id: string, quantity: number) => {
    setCarts(prev =>
      prev.map(cart => {
        const updatedItems = cart.items.map(item =>
          item.id === id ? { ...item, quantity } : item
        );
        const newTotal = updatedItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);

        return {
          ...cart,
          items: updatedItems,
          total: Math.round(newTotal * 100) / 100
        };
      })
    );
  };

  const handleRemoveItem = (id: string) => {
    setCarts(prev => {
      // Remove the item and recalculate totals
      const updatedCarts = prev.map(cart => {
        const updatedItems = cart.items.filter(item => item.id !== id);
        const newTotal = updatedItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);

        return {
          ...cart,
          items: updatedItems,
          total: Math.round(newTotal * 100) / 100,
          item_count: updatedItems.length
        };
      });

      // Filter out carts with no items
      return updatedCarts.filter(cart => cart.items.length > 0);
    });
  };

  const handleFindSwap = (id: string) => {
    // In a real app, this would find cheaper alternatives
    const item = carts.flatMap(c => c.items).find(i => i.id === id);
    if (item) {
      alert(`Finding cheaper alternatives for ${item.name}...`);
    }
  };

  // Show style guide if requested
  if (showStyleGuide) {
    return <StyleGuide />;
  }

  const hasMultipleStores = carts.length > 1;
  const allCartItems = carts.flatMap(c => c.items);

  return (
    <>
      {showLocationModal && <LocationModal onLocationSet={handleLocationSet} />}

      <div className="min-h-screen bg-[#f5e6d3]">
        {/* Header */}
        <header className="bg-[#f5d7b1] px-4 sm:px-6 py-3 sm:py-5 border-b border-[#e5c7a1] flex justify-between items-center">
          <h1 className="text-lg sm:text-xl md:text-2xl text-[#4a3f2a]" style={{ fontFamily: 'Georgia, serif' }}>
            Conscious Cart Coach
          </h1>
          <button
            onClick={() => setShowStyleGuide(true)}
            className="flex items-center gap-1 sm:gap-2 px-2 sm:px-4 py-2 text-xs sm:text-sm text-[#6b5f4a] hover:text-[#4a3f2a] hover:bg-[#f5e6d3] rounded transition-colors"
          >
            <BookOpen className="w-4 h-4" />
            <span className="hidden sm:inline">Design System</span>
          </button>
        </header>

        {/* Main Content */}
        <div className="flex flex-col lg:flex-row min-h-[calc(100vh-57px)] sm:min-h-[calc(100vh-65px)] lg:h-[calc(100vh-73px)]">
          {/* Left Panel - Input */}
          <div className="lg:w-1/2 p-4 sm:p-6 md:p-8 lg:p-12 lg:overflow-y-auto">
            <MealPlanInput
              mealPlan={mealPlan}
              onMealPlanChange={setMealPlan}
              onCreateCart={handleCreateCart}
              isLoading={isLoading}
              error={error}
              hasItems={allCartItems.length > 0}
            />
          </div>

          {/* Right Panel - Cart */}
          <div className="lg:w-1/2 bg-white border-t lg:border-t-0 lg:border-l border-[#e5c7a1] min-h-[500px] lg:h-full">
            {hasMultipleStores ? (
              <MultiStoreCart
                carts={carts}
                onUpdateQuantity={handleUpdateQuantity}
                onRemoveItem={handleRemoveItem}
                onFindSwap={handleFindSwap}
                onAgentCheckout={handleAgentCheckout}
                location={userLocation ? `${userLocation.city}, ${userLocation.state}` : 'City, State'}
                servings={servings}
                onChangeLocation={handleChangeLocation}
              />
            ) : (
              <ShoppingCart
                items={allCartItems}
                onUpdateQuantity={handleUpdateQuantity}
                onRemoveItem={handleRemoveItem}
                onFindSwap={handleFindSwap}
                metadata={{
                  store: carts.length > 0 ? carts[0].store : 'Your Cart',
                  location: userLocation ? `${userLocation.city}, ${userLocation.state}` : 'City, State',
                  servings: servings,
                }}
                onChangeLocation={handleChangeLocation}
              />
            )}
          </div>
        </div>
      </div>

      {/* Modals */}
      {appState === 'confirmingIngredients' && (
        <IngredientConfirmModal
          ingredients={draftIngredients}
          onConfirm={handleConfirmIngredients}
          onCancel={handleCancelConfirmation}
        />
      )}

      {appState === 'agentCheckout' && carts.length > 0 && (
        <AgentCheckoutModal carts={carts} onClose={handleCloseAgentCheckout} />
      )}

      {/* Loading Overlay */}
      {isLoading && (
        <LoadingOverlay message={loadingMessage} submessage={loadingSubmessage} />
      )}
    </>
  );
}
