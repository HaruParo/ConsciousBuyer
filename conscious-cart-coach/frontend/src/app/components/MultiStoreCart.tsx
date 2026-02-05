import { useState, useMemo } from 'react';
import { CartData, CartItem as CartItemType, CartPlan } from '@/app/types';
import { CartItemCard } from '@/app/components/CartItemCard';
import { designTokens } from '@/app/design-tokens';
import { Button } from '@/app/components/ui/button';
import { Badge } from '@/app/components/ui/badge';
import { ArrowRight, Download, AlertTriangle } from 'lucide-react';
import { UserPreferencesLinks } from '@/app/components/UserPreferencesLinks';
import { detectUniversalChips } from '@/app/utils/ingredientHelpers';

interface MultiStoreCartProps {
  carts?: CartData[];
  cartPlan?: CartPlan;
  onUpdateQuantity?: (id: string, quantity: number) => void;
  onRemoveItem?: (id: string) => void;
  onFindSwap?: (id: string) => void;
  onAgentCheckout: () => void;
  location: string;
  servings: number;
  onChangeLocation?: () => void;
  onServingsChange?: (servings: number) => void;
  onPreferencesChange?: (preferences: any) => void;
}

export function MultiStoreCart({
  carts,
  cartPlan,
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
  // Track which items use cheaper swap (V2 feature)
  const [cheaperSwapEnabled, setCheaperSwapEnabled] = useState<Record<string, boolean>>({});

  // Normalize ingredient name for consistent state keys (case-insensitive, trimmed)
  const normalizeKey = (name: string): string => {
    return name.trim().toLowerCase();
  };

  // V2 CartPlan rendering
  if (cartPlan) {
    // Defensive guards for missing data
    const stores = cartPlan.store_plan?.stores ?? [];
    const items = cartPlan.items ?? [];
    const totalStores = stores.length;
    const totalItems = items.length;

    // Compute current total based on swap selections
    const ethicalTotal = cartPlan.totals?.ethical_total || 0;
    const cheaperTotal = cartPlan.totals?.cheaper_total || 0;
    const maxSavingsPotential = cartPlan.totals?.savings_potential || 0;

    // Count unavailable items (status === 'unavailable' OR price === 0)
    const unavailableItems = items.filter(item =>
      item.status === 'unavailable' ||
      item.ethical_default?.product?.price === 0 ||
      item.ethical_default?.product?.brand === 'N/A'
    );
    const unavailableCount = unavailableItems.length;
    const availableItems = items.filter(item => !unavailableItems.includes(item));

    // Robust total calculation - guards against NaN and EXCLUDES unavailable items
    const currentTotal = availableItems.reduce((sum, item) => {
      const useSwap = cheaperSwapEnabled[normalizeKey(item.ingredient_name)] === true;
      const selected = (useSwap && item.cheaper_swap) ? item.cheaper_swap : item.ethical_default;
      const price = selected?.product?.price ?? 0;
      const quantity = typeof selected?.quantity === 'number' ? selected.quantity : 1;
      return sum + (price * quantity);
    }, 0);

    const savingsSoFar = ethicalTotal - currentTotal;

    // Detect universal chips (appear on most items) to move to cart-level header
    const universalChips = useMemo(() => {
      const allChips = availableItems.map(item => item.chips?.why_pick || []);
      return detectUniversalChips(allChips);
    }, [availableItems]);

    // Get items for active tab (V2)
    const getFilteredItemsV2 = () => {
      if (activeTab === 'all') return items;
      return items.filter(item => item.store_id === activeTab);
    };

    const filteredItemsV2 = getFilteredItemsV2();

    // CSV Export handler
    const handleDownloadCSV = () => {
      if (items.length === 0) return;

      const csvRows = [
        ['Ingredient', 'Product', 'Store', 'Qty', 'Price', 'Organic', 'Status', 'Total'].join(',')
      ];

      for (const item of items) {
        const useSwap = cheaperSwapEnabled[normalizeKey(item.ingredient_name)];
        const product = useSwap && item.cheaper_swap
          ? item.cheaper_swap.product
          : item.ethical_default.product;
        const quantity = useSwap && item.cheaper_swap
          ? item.cheaper_swap.quantity
          : item.ethical_default.quantity;
        const store = stores.find(s => s.store_id === item.store_id)?.store_name || item.store_id;
        const status = item.status === 'unavailable' ? 'Unavailable' : 'Available';

        csvRows.push([
          item.ingredient_name,
          `"${product.title}"`,
          store,
          quantity,
          product.price.toFixed(2),
          product.organic ? 'Yes' : 'No',
          status,
          (product.price * quantity).toFixed(2)
        ].join(','));
      }

      const csv = csvRows.join('\n');
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cart-${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    };

    // Toggle cheaper swap for an item
    const toggleCheaperSwap = (ingredientName: string) => {
      const key = normalizeKey(ingredientName);
      setCheaperSwapEnabled(prev => ({
        ...prev,
        [key]: !prev[key]
      }));
    };

    return (
      <div className="h-full flex flex-col">
        {/* Multi-Store Header (V2) */}
        <div className="bg-[#6b5f3a] text-white px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex items-baseline justify-between gap-3 mb-1">
            <div className="min-w-0 flex-1">
              <h2 className="text-base sm:text-lg md:text-xl font-semibold truncate mb-1">
                {totalStores > 1
                  ? `Multi-store cart: ${stores.map(s => `${s.store_name} (${items.filter(i => i.store_id === s.store_id).length})`).join(' • ')}`
                  : `Store: ${stores[0]?.store_name || 'Cart'}`}
              </h2>
              {totalStores > 1 && (
                <p className="text-xs opacity-75 mb-1">
                  Items are split by store. Checkout opens each store cart.
                </p>
              )}
              <UserPreferencesLinks
                location={location}
                servings={servings}
                onChangeLocation={onChangeLocation}
                onServingsChange={onServingsChange}
                onPreferencesChange={onPreferencesChange}
              />
            </div>
            <div className="text-right flex-shrink-0">
              <p className="text-xs opacity-75 mb-0.5">
                {availableItems.length} items{unavailableCount > 0 && ` (${unavailableCount} unavailable)`}
              </p>
              <p className="text-lg sm:text-xl font-semibold">
                ${currentTotal.toFixed(2)}
              </p>
              {unavailableCount > 0 && (
                <p className="text-xs opacity-75">
                  Excludes unavailable items
                </p>
              )}
              {maxSavingsPotential > 0.01 && (
                <p className="text-xs opacity-75">
                  Cheaper swaps available{' '}
                  <span className="text-[#e8f5e9]">–${maxSavingsPotential.toFixed(2)}</span>
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Unavailable Items Warning */}
        {cartPlan.store_plan?.unavailable && cartPlan.store_plan.unavailable.length > 0 && (
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mx-4 mt-4">
            <div className="flex items-start">
              <AlertTriangle className="w-5 h-5 text-yellow-600 mr-2 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-yellow-800">
                  {cartPlan.store_plan.unavailable.length} item(s) unavailable
                </p>
                <p className="text-xs text-yellow-700 mt-1">
                  {cartPlan.store_plan.unavailable.join(', ')}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Cart-level recall signals check */}
        {universalChips.size > 0 && (
          <div className="bg-[#f9f5f0] border-l-4 border-[#e5d5b8] px-4 py-2 mx-4 mt-4">
            <p className="text-xs text-[#6b5f4a]">
              {Array.from(universalChips).some(chip => chip.toLowerCase().includes('recall')) && (
                <span>✓ Recall signals checked for all items</span>
              )}
              {Array.from(universalChips).filter(chip => !chip.toLowerCase().includes('recall')).map((chip, index) => (
                <span key={index}>
                  {index > 0 && ' · '}
                  {chip}
                </span>
              ))}
            </p>
          </div>
        )}

        {/* Cart Items with Tabs (V2) */}
        <div className="flex-1 overflow-y-auto p-3 sm:p-4 md:p-6">
          {/* Tabs */}
          {totalStores > 1 && (
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
              {stores.map(store => {
                const storeItemCount = items.filter(item => item.store_id === store.store_id).length;
                return (
                  <button
                    key={store.store_id}
                    onClick={() => setActiveTab(store.store_id)}
                    className="px-3 sm:px-4 py-2 sm:py-3 font-semibold whitespace-nowrap transition-colors text-xs sm:text-sm"
                    style={{
                      borderBottom: activeTab === store.store_id ? `3px solid ${designTokens.colors.brand.primary}` : '3px solid transparent',
                      color: activeTab === store.store_id ? designTokens.colors.brand.primary : designTokens.colors.text.secondary,
                      marginBottom: '-1px'
                    }}
                  >
                    {store.store_name}
                    {store.delivery_estimate && <span className="opacity-60"> · {store.delivery_estimate}</span>}
                    {' '}({storeItemCount})
                  </button>
                );
              })}
            </div>
          )}

          {/* Items (V2 CartItemV2 rendering) */}
          {filteredItemsV2.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <p className="text-center text-sm sm:text-base" style={{ color: designTokens.colors.text.tertiary }}>
                No items in this view
              </p>
            </div>
          ) : (
            <div className="space-y-3 sm:space-y-4 md:space-y-6">
              {filteredItemsV2.map((itemV2) => {
                const useSwap = cheaperSwapEnabled[normalizeKey(itemV2.ingredient_name)];
                const productChoice = useSwap && itemV2.cheaper_swap
                  ? itemV2.cheaper_swap
                  : itemV2.ethical_default;
                const store = stores.find(s => s.store_id === itemV2.store_id);

                // Convert CartItemV2 to old CartItemType for rendering
                const cartItem: CartItemType = {
                  id: itemV2.ingredient_name,
                  name: productChoice.product.title,
                  brand: productChoice.product.brand,
                  catalogueName: productChoice.product.title,
                  price: productChoice.product.price,
                  quantity: productChoice.quantity,
                  size: productChoice.product.size,
                  image: productChoice.product.image_url || '',
                  tags: {
                    whyPick: itemV2.chips.why_pick,
                    tradeOffs: itemV2.chips.tradeoffs
                  },
                  store: store?.store_name || itemV2.store_id,
                  location: location,
                  unitPrice: productChoice.product.unit_price,
                  unitPriceUnit: productChoice.product.unit_price_unit,
                  ingredientName: itemV2.ingredient_name,
                  available: itemV2.status !== 'unavailable',
                  // NEW: Pass reason from backend
                  reasonLine: itemV2.reason_line,
                  reasonDetails: itemV2.reason_details
                };

                return (
                  <div key={itemV2.ingredient_name}>
                    <CartItemCard
                      item={cartItem}
                      onUpdateQuantity={() => {}} // V2 doesn't support quantity updates yet
                      onRemove={() => {}} // V2 doesn't support removal yet
                      onFindSwap={itemV2.cheaper_swap ? () => toggleCheaperSwap(itemV2.ingredient_name) : undefined}
                      showStoreChip={totalStores > 1}
                      useCheaperSwap={useSwap}
                      ingredientForm={itemV2.ingredient_form}
                      universalChips={universalChips}
                    />
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Sticky Footer with Checkout and Download Buttons */}
        <div className="p-3 sm:p-4 md:p-6 border-t border-[#e5d5b8] bg-white">
          <div className="flex gap-2 sm:gap-3">
            <Button
              onClick={handleDownloadCSV}
              variant="outline"
              className="flex-1 border-[#8b7a5a] text-[#6b5f4a] hover:bg-[#f5e6d3] text-xs sm:text-sm py-3 sm:py-4 md:py-5"
            >
              <Download className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
              Download<span className="hidden sm:inline"> CSV</span>
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

  // Old format (CartData[]) rendering
  if (!carts || carts.length === 0) {
    return null;
  }

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
