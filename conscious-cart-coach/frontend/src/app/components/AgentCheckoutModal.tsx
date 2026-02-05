import { useState, useEffect } from 'react';
import { CartData, CartPlan } from '@/app/types';
import { designTokens } from '@/app/design-tokens';
import { X, Check } from 'lucide-react';

interface CheckoutStore {
  name: string;
  url: string;
  ready: boolean;
}

interface AgentCheckoutModalProps {
  carts?: CartData[];
  cartPlan?: CartPlan;
  onClose: () => void;
}

export function AgentCheckoutModal({ carts, cartPlan, onClose }: AgentCheckoutModalProps) {
  const [stores, setStores] = useState<CheckoutStore[]>([]);
  const [isCreating, setIsCreating] = useState(true);

  useEffect(() => {
    // Initialize stores from either cartPlan or carts
    let storeList: CheckoutStore[];

    if (cartPlan) {
      // V2: Use CartPlan stores
      storeList = (cartPlan.store_plan?.stores || []).map(store => ({
        name: store.store_name,
        url: store.checkout_url_template || `https://${store.store_name.toLowerCase().replace(/\s+/g, '')}.com/cart`,
        ready: false
      }));
    } else if (carts) {
      // Old format: Use CartData[]
      storeList = carts.map(cart => ({
        name: cart.store,
        url: `https://${cart.store.toLowerCase().replace(/\s+/g, '')}.com/cart`,
        ready: false
      }));
    } else {
      storeList = [];
    }

    setStores(storeList);

    // Mark stores as ready one by one
    storeList.forEach((_store, index) => {
      setTimeout(() => {
        setStores(prev => prev.map((s, i) =>
          i === index ? { ...s, ready: true } : s
        ));

        // After last store, stop "creating" state
        if (index === storeList.length - 1) {
          setTimeout(() => setIsCreating(false), 500);
        }
      }, (index + 1) * 1000); // 1 second delay between each
    });
  }, [carts]);

  const handleCheckoutAll = () => {
    stores.forEach(store => {
      if (store.ready) {
        window.open(store.url, '_blank');
      }
    });
  };

  const handleCheckoutStore = (storeUrl: string) => {
    window.open(storeUrl, '_blank');
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-md w-full"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between p-6 border-b"
          style={{ borderColor: designTokens.colors.border.light }}
        >
          <h2
            className="text-2xl font-bold"
            style={{
              color: designTokens.colors.text.primary,
              fontFamily: designTokens.typography.fontFamily.heading
            }}
          >
            Agent Checkout
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded transition-colors"
            style={{ color: designTokens.colors.text.secondary }}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Progress header */}
          {isCreating && (
            <div className="mb-4 font-semibold" style={{ color: designTokens.colors.text.primary }}>
              Creating carts...
            </div>
          )}

          {/* Store status list */}
          <div className="space-y-3 mb-6">
            {stores.map(store => (
              <div key={store.name} className="flex items-center gap-3">
                <div
                  className="w-6 h-6 flex items-center justify-center rounded-full"
                  style={{
                    backgroundColor: store.ready ? '#28a745' : '#e5d5b8',
                    color: 'white'
                  }}
                >
                  {store.ready ? <Check className="w-4 h-4" /> : '⏳'}
                </div>
                <span style={{ color: designTokens.colors.text.primary }}>
                  {store.ready ? `${store.name} cart ready` : `Creating ${store.name} cart...`}
                </span>
              </div>
            ))}
          </div>

          {/* Individual checkout buttons */}
          {!isCreating && (
            <div className="space-y-3 mb-6">
              {stores.map(store => (
                <button
                  key={store.name}
                  onClick={() => handleCheckoutStore(store.url)}
                  disabled={!store.ready}
                  className="w-full px-4 py-3 rounded border-2 transition-colors disabled:opacity-50"
                  style={{
                    borderColor: designTokens.colors.border.medium,
                    color: designTokens.colors.text.primary,
                    backgroundColor: designTokens.colors.background.card,
                  }}
                >
                  Checkout {store.name}
                </button>
              ))}
            </div>
          )}

          {/* Disclaimer */}
          <div
            className="p-3 rounded text-sm mb-6"
            style={{
              backgroundColor: designTokens.colors.background.lightAccent,
              color: designTokens.colors.text.secondary,
            }}
          >
            Opens store carts in new tabs. Payment happens on store sites.
          </div>

          {/* Footer buttons */}
          <div className="flex items-center justify-end gap-3">
            <button
              onClick={onClose}
              className="px-6 py-3 rounded border-2 transition-colors"
              style={{
                borderColor: designTokens.colors.border.medium,
                color: designTokens.colors.text.primary,
                backgroundColor: designTokens.colors.background.card,
              }}
            >
              Close
            </button>
            <button
              onClick={handleCheckoutAll}
              disabled={isCreating || stores.some(s => !s.ready)}
              className="px-6 py-3 rounded transition-colors font-semibold disabled:opacity-50"
              style={{
                backgroundColor: designTokens.colors.brand.primary,
                color: designTokens.colors.text.white,
              }}
            >
              Checkout all (opens tabs)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
