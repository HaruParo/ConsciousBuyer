import { Minus, Plus, ChevronDown, ImageOff } from 'lucide-react';
import { Button } from '@/app/components/ui/button';
import { CartItem } from '@/app/types';
import { Badge } from '@/app/components/ui/badge';

interface CartItemCardProps {
  item: CartItem;
  onUpdateQuantity: (quantity: number) => void;
  onRemove: () => void;
  onFindSwap: () => void;
  showStoreChip?: boolean;
}

export function CartItemCard({ item, onUpdateQuantity, onRemove, onFindSwap, showStoreChip = false }: CartItemCardProps) {
  const handleDecrement = () => {
    if (item.quantity > 1) {
      onUpdateQuantity(item.quantity - 1);
    }
  };

  const handleIncrement = () => {
    onUpdateQuantity(item.quantity + 1);
  };

  return (
    <div className="border border-[#e5d5b8] rounded-lg overflow-hidden bg-white">
      <div className="flex gap-2 sm:gap-3 md:gap-4 p-2 sm:p-3 md:p-4">
        {/* Product Image Unavailable */}
        <div className="w-16 h-16 sm:w-20 sm:h-20 flex-shrink-0 rounded bg-gray-100 flex flex-col items-center justify-center">
          <ImageOff className="w-6 h-6 sm:w-8 sm:h-8 text-gray-400 mb-1" />
          <span className="text-[8px] sm:text-[10px] text-gray-500 text-center px-1">Image Unavailable</span>
        </div>

        {/* Product Info */}
        <div className="flex-1 min-w-0">
          {/* Store chip and availability */}
          <div className="mb-1 sm:mb-2 flex flex-wrap gap-1 sm:gap-1.5">
            {showStoreChip && (
              <Badge
                variant="secondary"
                className={`text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 rounded font-semibold ${
                  item.available === false
                    ? 'bg-[#c5baa8] text-[#6b5f3a]'
                    : item.store.toLowerCase().includes('freshdirect')
                      ? 'bg-[#d4976c] text-white'
                      : 'bg-[#8b7ba8] text-white'
                }`}
              >
                {item.store}
              </Badge>
            )}
            {item.available === false && (
              <Badge
                variant="secondary"
                className="bg-[#c5baa8] text-[#6b5f3a] text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 rounded font-semibold"
              >
                Unavailable
              </Badge>
            )}
          </div>

          <div className="flex items-start justify-between gap-1 sm:gap-2 mb-1 sm:mb-2">
            <div className="flex-1 min-w-0">
              <h3 className="text-sm sm:text-base font-semibold text-[#4a3f2a] truncate">
                {item.brand}, <span className="font-normal text-[#6b5f4a]">{item.catalogueName}</span>
              </h3>
            </div>
            <p className="text-sm sm:text-base font-semibold text-[#4a3f2a] flex-shrink-0">
              ${item.price.toFixed(2)}
            </p>
          </div>

          {/* Quantity and Size Controls */}
          <div className="flex items-center gap-2 sm:gap-3 mb-2 sm:mb-3">
            <div className="flex items-center gap-0.5 sm:gap-1 bg-white border border-[#d5c5a8] rounded">
              <button
                onClick={handleDecrement}
                className="p-1 sm:p-1.5 hover:bg-[#f5e6d3] transition-colors touch-manipulation"
                aria-label="Decrease quantity"
              >
                <Minus className="w-3 h-3 sm:w-4 sm:h-4 text-[#6b5f4a]" />
              </button>
              <span className="px-2 sm:px-3 text-xs sm:text-sm font-medium text-[#4a3f2a] min-w-[1.5rem] sm:min-w-[2rem] text-center">
                {item.quantity}
              </span>
              <button
                onClick={handleIncrement}
                className="p-1 sm:p-1.5 hover:bg-[#f5e6d3] transition-colors touch-manipulation"
                aria-label="Increase quantity"
              >
                <Plus className="w-3 h-3 sm:w-4 sm:h-4 text-[#6b5f4a]" />
              </button>
            </div>

            <button className="flex items-center gap-0.5 sm:gap-1 px-2 sm:px-3 py-1 sm:py-1.5 text-xs sm:text-sm text-[#6b5f4a] bg-white border border-[#d5c5a8] rounded hover:bg-[#f5e6d3] transition-colors touch-manipulation">
              Size: {item.size || 'not specified'}
              <ChevronDown className="w-3 h-3 sm:w-4 sm:h-4" />
            </button>
          </div>

          {/* Why this pick tags */}
          <div className="mb-2 sm:mb-3 bg-[#f9f5f0] p-2 sm:p-3 rounded">
            <p className="text-xs font-semibold text-[#6b5f4a] mb-1 sm:mb-1.5">
              Why this pick?
            </p>
            <div className="flex flex-wrap gap-1 sm:gap-1.5">
              {item.tags.whyPick.map((tag, index) => (
                <Badge
                  key={index}
                  variant="secondary"
                  className="bg-[#e8f5e9] text-[#2d5a3d] border border-[#4a7c59]/25 text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 rounded-full"
                >
                  ✓ {tag}
                </Badge>
              ))}
            </div>
          </div>

          {/* Unavailable warning */}
          {item.available === false && (
            <div className="mb-2 sm:mb-3 p-2 sm:p-3 bg-[#fff3cd] rounded text-xs sm:text-sm text-[#856404]">
              This item is currently unavailable.{' '}
              <a href="#" className="text-[#6b5f3a] underline">
                Try another store
              </a>
            </div>
          )}

          {/* Trade-offs tags */}
          {item.tags.tradeOffs.length > 0 && (
            <div className="mb-2 sm:mb-3 bg-[#fef9f5] p-2 sm:p-3 rounded">
              <p className="text-xs font-semibold text-[#6b5f4a] mb-1 sm:mb-1.5">
                Trade-offs
              </p>
              <div className="flex flex-wrap gap-1 sm:gap-1.5">
                {item.tags.tradeOffs.map((tag, index) => (
                  <Badge
                    key={index}
                    variant="outline"
                    className="bg-[#fff4e6] text-[#8b5e2b] border border-[#8b5e2b]/35 text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 rounded-full"
                  >
                    ⓘ {tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-2 mt-2 sm:mt-3">
            <Button
              onClick={onFindSwap}
              variant="outline"
              size="sm"
              className="border-[#8b7a5a] text-[#6b5f4a] hover:bg-[#f5e6d3] text-[10px] sm:text-xs py-2 sm:py-3 touch-manipulation"
            >
              Find Cheaper Swap
            </Button>
            <Button
              onClick={onRemove}
              variant="outline"
              size="sm"
              className="border-[#8b7a5a] text-[#6b5f4a] hover:bg-[#f5e6d3] text-[10px] sm:text-xs py-2 sm:py-3 touch-manipulation"
            >
              Remove Cart Item
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}