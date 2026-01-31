import { ArrowRight } from 'lucide-react';
import { Button } from '@/app/components/ui/button';
import { CartItem as CartItemType } from '@/app/types';
import { CartItemCard } from '@/app/components/CartItemCard';

interface ShoppingCartProps {
  items: CartItemType[];
  onUpdateQuantity: (id: string, quantity: number) => void;
  onRemoveItem: (id: string) => void;
  onFindSwap: (id: string) => void;
  metadata?: { store: string; location: string; servings: number } | null;
  onChangeLocation?: () => void;
}

export function ShoppingCart({ items, onUpdateQuantity, onRemoveItem, onFindSwap, metadata, onChangeLocation }: ShoppingCartProps) {
  const totalPrice = items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  const store = metadata?.store || items[0]?.store || 'Store Name';
  const location = metadata?.location || items[0]?.location || 'City, State';
  const servings = metadata?.servings || 2;
  const isEmpty = items.length === 0;

  return (
    <div className="h-full flex flex-col">
      {/* Cart Header */}
      <div className="bg-[#6b5f3a] text-white px-4 sm:px-6 py-3 sm:py-4">
        <div className="flex items-baseline justify-between gap-3 mb-1">
          <div className="min-w-0 flex-1">
            <h2 className="text-base sm:text-lg md:text-xl font-semibold truncate mb-1">
              {store} ({items.length})
            </h2>
            <div className="flex items-center gap-2">
              <p className="text-sm sm:text-base opacity-90">
                Family size: {servings} <span className="opacity-40">|</span> Delivery Location: {location}
              </p>
              {onChangeLocation && (
                <button
                  onClick={onChangeLocation}
                  className="text-xs px-2 py-0.5 bg-white/20 hover:bg-white/30 rounded transition-colors flex-shrink-0"
                >
                  Change
                </button>
              )}
            </div>
          </div>
          <div className="text-right flex-shrink-0">
            <p className="text-xs opacity-75 mb-0.5">est. total</p>
            <p className="text-lg sm:text-xl font-semibold">
              ${totalPrice.toFixed(2)}
            </p>
          </div>
        </div>
      </div>

      {/* Cart Items or Empty State */}
      <div className="flex-1 overflow-y-auto p-3 sm:p-4 md:p-6">
        {isEmpty ? (
          <div className="flex flex-col items-center justify-center h-full px-4">
            <p className="text-[#9b8f7a] text-center text-sm sm:text-base">
              Ask cart coach to fill up your cart!
            </p>
          </div>
        ) : (
          <div className="space-y-3 sm:space-y-4 md:space-y-6">
            {items.map((item) => (
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

      {/* Sticky Footer with 3 Buttons */}
      <div className="p-3 sm:p-4 md:p-6 border-t border-[#e5d5b8] bg-white space-y-2 sm:space-y-3">
        <Button
          disabled={isEmpty}
          className="w-full bg-[#6b5f3a] hover:bg-[#5b4f2a] text-white py-4 sm:py-5 md:py-6 text-sm sm:text-base disabled:bg-[#c5baa8] disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Continue to store checkout
          <ArrowRight className="w-4 h-4 sm:w-5 sm:h-5 ml-2" />
        </Button>
        <div className="flex gap-2 sm:gap-3">
          <Button
            variant="outline"
            disabled={isEmpty}
            className="flex-1 border-[#8b7a5a] text-[#6b5f4a] hover:bg-[#f5e6d3] text-xs sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed py-3 sm:py-4"
          >
            Preferences
          </Button>
          <Button
            variant="outline"
            disabled={isEmpty}
            className="flex-1 border-[#8b7a5a] text-[#6b5f4a] hover:bg-[#f5e6d3] text-xs sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed py-3 sm:py-4"
          >
            Download list
          </Button>
        </div>
      </div>
    </div>
  );
}