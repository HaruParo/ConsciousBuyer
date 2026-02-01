import { useState } from 'react';
import { CartData, CartItem as CartItemType } from '@/app/types';
import { CartItemCard } from '@/app/components/CartItemCard';
import { designTokens } from '@/app/design-tokens';
import { Button } from '@/app/components/ui/button';
import { ArrowRight } from 'lucide-react';
import { UserPreferencesLinks } from '@/app/components/UserPreferencesLinks';

interface MultiStoreCartProps {
  carts: CartData[];
  onUpdateQuantity: (id: string, quantity: number) => void;
  onRemoveItem: (id: string) => void;
  onFindSwap: (id: string) => void;
  onAgentCheckout: () => void;
  location: string;
  servings: number;
  onChangeLocation?: () => void;
  onServingsChange?: (servings: number) => void;
  onPreferencesChange?: (preferences: any) => void;
}

export function MultiStoreCart({
  carts,
  onUpdateQuantity,
  onRemoveItem,
  onFindSwap,
  onAgentCheckout,
  location,
  servings,
  onChangeLocation,
  onServingsChange,
  onPreferencesChange
}: MultiStoreCartProps) {
  const [activeTab, setActiveTab] = useState<string>('all');

  const totalStores = carts.length;
  const totalItems = carts.reduce((sum, cart) => sum + cart.item_count, 0);

  // Calculate total from actual item prices instead of using backend total
  const allItems = carts.flatMap(cart => cart.items);
  const totalCost = Math.round(allItems.reduce((sum, item) => sum + (item.price * item.quantity), 0) * 100) / 100;

  // Get filtered items based on active tab
  const getFilteredItems = (): CartItemType[] => {
    if (activeTab === 'all') {
      return carts.flatMap(cart => cart.items);
    }
    const selectedCart = carts.find(c => c.store === activeTab);
    return selectedCart ? selectedCart.items : [];
  };

  const filteredItems = getFilteredItems();
  const currentTotal = Math.round(filteredItems.reduce((sum, item) => sum + (item.price * item.quantity), 0) * 100) / 100;

  return (
    <div className="h-full flex flex-col">
      {/* Multi-Store Header */}
      <div className="bg-[#6b5f3a] text-white px-4 sm:px-6 py-3 sm:py-4">
        <div className="flex items-baseline justify-between gap-3 mb-1">
          <div className="min-w-0 flex-1">
            <h2 className="text-base sm:text-lg md:text-xl font-semibold truncate mb-1">
              {totalStores > 1 ? `Multi-store cart: ${totalStores} stores` : '1 store selected'}
            </h2>
            <UserPreferencesLinks
              location={location}
              servings={servings}
              onChangeLocation={onChangeLocation}
              onServingsChange={onServingsChange}
              onPreferencesChange={onPreferencesChange}
            />
          </div>
          <div className="text-right flex-shrink-0">
            <p className="text-xs opacity-75 mb-0.5">est. total</p>
            <p className="text-lg sm:text-xl font-semibold">
              ${totalCost.toFixed(2)}
            </p>
          </div>
        </div>
      </div>

      {/* Cart Items with Tabs */}
      <div className="flex-1 overflow-y-auto p-3 sm:p-4 md:p-6">
        {/* Tabs */}
        <div className="flex gap-3 sm:gap-4 mb-4 sm:mb-6 border-b pb-0 overflow-x-auto" style={{ borderColor: designTokens.colors.border.light }}>
          <button
            onClick={() => setActiveTab('all')}
            className="px-3 sm:px-4 py-2 sm:py-3 font-semibold whitespace-nowrap transition-colors text-xs sm:text-sm"
            style={{
              borderBottom: activeTab === 'all' ? `3px solid ${designTokens.colors.brand.primary}` : '3px solid transparent',
              color: activeTab === 'all' ? designTokens.colors.brand.primary : designTokens.colors.text.secondary,
              marginBottom: '-1px'
            }}
          >
            All items ({totalItems})
          </button>
          {carts.map(cart => (
            <button
              key={cart.store}
              onClick={() => setActiveTab(cart.store)}
              className="px-3 sm:px-4 py-2 sm:py-3 font-semibold whitespace-nowrap transition-colors text-xs sm:text-sm"
              style={{
                borderBottom: activeTab === cart.store ? `3px solid ${designTokens.colors.brand.primary}` : '3px solid transparent',
                color: activeTab === cart.store ? designTokens.colors.brand.primary : designTokens.colors.text.secondary,
                marginBottom: '-1px'
              }}
            >
              {cart.store}
              {cart.delivery_estimate && <span className="opacity-60"> · {cart.delivery_estimate}</span>}
              {' '}({cart.item_count})
            </button>
          ))}
        </div>

        {/* Items */}
        {filteredItems.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-center text-sm sm:text-base" style={{ color: designTokens.colors.text.tertiary }}>
              No items in this view
            </p>
          </div>
        ) : (
          <div className="space-y-3 sm:space-y-4 md:space-y-6">
            {filteredItems.map((item) => (
              <CartItemCard
                key={item.id}
                item={item}
                onUpdateQuantity={(quantity) => onUpdateQuantity(item.id, quantity)}
                onRemove={() => onRemoveItem(item.id)}
                onFindSwap={() => onFindSwap(item.id)}
                showStoreChip={true}
              />
            ))}
          </div>
        )}
      </div>

      {/* Sticky Footer with Checkout and Download Buttons */}
      <div className="p-3 sm:p-4 md:p-6 border-t border-[#e5d5b8] bg-white">
        <div className="flex gap-2 sm:gap-3">
          <Button
            variant="outline"
            className="flex-1 border-[#8b7a5a] text-[#6b5f4a] hover:bg-[#f5e6d3] text-xs sm:text-sm py-3 sm:py-4 md:py-5"
          >
            Download<span className="hidden sm:inline"> list</span>
          </Button>
          <Button
            onClick={onAgentCheckout}
            className="flex-1 bg-[#6b5f3a] hover:bg-[#5b4f2a] text-white py-3 sm:py-4 md:py-5 text-xs sm:text-sm md:text-base"
          >
            <span className="hidden sm:inline">Agent </span>Checkout
            <ArrowRight className="w-3 h-3 sm:w-4 sm:h-4 md:w-5 md:h-5 ml-1 sm:ml-2" />
          </Button>
        </div>
      </div>
    </div>
  );
}
