import { Minus, Plus, Info, ImageOff } from 'lucide-react';
import { Button } from '@/app/components/ui/button';
import { CartItem } from '@/app/types';
import { Badge } from '@/app/components/ui/badge';
import { UnavailableCard } from './UnavailableCard';
import {
  formatProductName,
  sanitizeChipText
} from '@/app/utils/ingredientHelpers';

interface CartItemCardProps {
  item: CartItem;
  onUpdateQuantity?: (quantity: number) => void;
  onRemove?: () => void;
  onFindSwap?: () => void;
  showStoreChip?: boolean;
  useCheaperSwap?: boolean; // V2: Whether cheaper swap is currently active
  ingredientForm?: string | null; // NEW: Optional ingredient form (powder, seeds, etc.)
  universalChips?: Set<string>; // NEW: Universal chips to filter out
}

export function CartItemCard({
  item,
  onUpdateQuantity,
  onRemove,
  onFindSwap,
  showStoreChip = false,
  useCheaperSwap = false,
  ingredientForm = null,
  universalChips = new Set()
}: CartItemCardProps) {
  // CRITICAL: Render compact unavailable card if item is unavailable
  const isUnavailable = item.available === false || item.price === 0 || item.brand === 'N/A';

  if (isUnavailable) {
    return (
      <UnavailableCard
        ingredientName={item.ingredientName || item.name}
        storeName={item.store}
        reason={item.catalogueName?.includes('Not Available') ? item.catalogueName : undefined}
        onRemove={onRemove}
      />
    );
  }

  const handleDecrement = () => {
    if (item.quantity > 1) {
      onUpdateQuantity(item.quantity - 1);
    }
  };

  const handleIncrement = () => {
    onUpdateQuantity(item.quantity + 1);
  };

  // Use backend reason if available, otherwise fallback to default
  const reasonLine = item.reasonLine || "Good match";
  const reasonDetails = item.reasonDetails || ["Matches ingredient requirements for this recipe."];

  // Filter distinctive chips (max 3)
  const distinctiveWhyPick = item.tags?.whyPick
    ? item.tags.whyPick.filter(chip => !universalChips.has(chip)).slice(0, 3)
    : [];

  // Use backend tradeoffs (already limited to max 2 in backend)
  const allTradeoffs = item.tags?.tradeOffs
    ? item.tags.tradeOffs
        .filter(chip => !universalChips.has(chip))
        .map(chip => sanitizeChipText(chip))
    : [];

  return (
    <div className="border border-[#e5d5b8] rounded-lg overflow-hidden bg-white">
      <div className="flex gap-2 sm:gap-3 md:gap-4 p-2 sm:p-3 md:p-4">
        {/* Product Image Placeholder */}
        <div className="w-16 h-16 sm:w-20 sm:h-20 flex-shrink-0 rounded bg-gray-100 flex flex-col items-center justify-center">
          <ImageOff className="w-6 h-6 sm:w-8 sm:h-8 text-gray-400 mb-1" />
          <span className="text-[8px] sm:text-[10px] text-gray-500 text-center px-1">Image Unavailable</span>
        </div>

        {/* Product Info */}
        <div className="flex-1 min-w-0">
          {/* 1. Top row: Product title as main heading */}
          <div className="mb-1">
            <h3 className="text-sm sm:text-base font-semibold text-[#4a3f2a] mb-1">
              {formatProductName(item.catalogueName, item.brand)}
            </h3>
          </div>

          {/* 2. Badges row: Store chip and swap indicator */}
          {(showStoreChip || useCheaperSwap) && (
            <div className="mb-2 flex items-center gap-2 flex-wrap">
              {showStoreChip && (
                <Badge
                  variant="secondary"
                  className={`text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 rounded font-semibold ${
                    item.store.toLowerCase().includes('freshdirect')
                      ? 'bg-[#d4976c] text-white'
                      : 'bg-[#8b7ba8] text-white'
                  }`}
                >
                  {item.store}
                </Badge>
              )}
              {useCheaperSwap && (
                <Badge
                  variant="secondary"
                  className="bg-[#e8f5e9] text-[#2d5a3d] border border-[#4a7c59]/25 text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 rounded font-semibold"
                >
                  💸 Swap active
                </Badge>
              )}
            </div>
          )}

          {/* 3. Price + size row */}
          <div className="flex items-center gap-2 mb-2">
            <p className="text-sm sm:text-base font-semibold text-[#4a3f2a]">
              ${item.price.toFixed(2)}
            </p>
            <span className="text-xs sm:text-sm text-[#6b5f4a]">
              · {item.size || 'not specified'}
            </span>
          </div>

          {/* 4. Reason line + ⓘ details (from backend) */}
          {reasonDetails.length > 0 && (
            <div className="mb-2 group relative inline-block">
              <div className="flex items-center gap-1 text-xs sm:text-sm text-[#6b5f4a]">
                <span className="font-medium">{reasonLine}</span>
                <Info className="w-3 h-3 sm:w-3.5 sm:h-3.5 text-[#8b7a5a] cursor-help" />
              </div>
              {/* Hover tooltip with details */}
              <div className="absolute left-0 top-full mt-1 w-64 p-2 bg-[#4a3f2a] text-white text-xs rounded shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-opacity z-10">
                <ul className="list-disc list-inside space-y-1">
                  {reasonDetails.map((detail, idx) => (
                    <li key={idx}>{detail}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* 5. Chips (max 3, soft pills, distinctive only) */}
          {distinctiveWhyPick.length > 0 && (
            <div className="mb-2 flex flex-wrap gap-1 sm:gap-1.5">
              {distinctiveWhyPick.map((tag, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] sm:text-xs bg-[#e8f5e9] text-[#2d5a3d]"
                >
                  {sanitizeChipText(tag)}
                </span>
              ))}
            </div>
          )}

          {/* 6. Tradeoffs (max 2, from backend) */}
          {allTradeoffs.length > 0 && (
            <div className="mb-2 flex flex-wrap gap-1 sm:gap-1.5">
              {allTradeoffs.map((tradeoff, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] sm:text-xs bg-[#fff4e6] text-[#8b5e2b] opacity-75"
                >
                  {tradeoff}
                </span>
              ))}
            </div>
          )}

          {/* Quantity controls */}
          <div className="flex items-center gap-2 mb-2">
            {onUpdateQuantity ? (
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
            ) : (
              <span className="px-2 sm:px-3 py-1 sm:py-1.5 text-xs sm:text-sm font-medium text-[#4a3f2a] bg-white border border-[#d5c5a8] rounded">
                Qty: {item.quantity}
              </span>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-2 mt-2 sm:mt-3">
            {onFindSwap ? (
              <Button
                onClick={onFindSwap}
                variant="outline"
                size="sm"
                className={`${
                  useCheaperSwap
                    ? 'border-[#4a7c59] bg-[#e8f5e9] text-[#2d5a3d] hover:bg-[#d4ead9]'
                    : 'border-[#8b7a5a] text-[#6b5f4a] hover:bg-[#f5e6d3]'
                } text-[10px] sm:text-xs py-2 sm:py-3 touch-manipulation`}
              >
                {useCheaperSwap ? '✓ Using Cheaper Swap' : 'Find Cheaper Swap'}
              </Button>
            ) : item.available === false ? (
              <div className="text-[10px] sm:text-xs text-[#6b5f4a] italic py-2">
                No alternative available
              </div>
            ) : null}
            {onRemove && (
              <Button
                onClick={onRemove}
                variant="outline"
                size="sm"
                className="border-[#8b7a5a] text-[#6b5f4a] hover:bg-[#f5e6d3] text-[10px] sm:text-xs py-2 sm:py-3 touch-manipulation"
              >
                Remove Cart Item
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}