import { MapPin, Store, Loader2, Check, ArrowRight } from 'lucide-react';
import { Button } from '@/app/components/ui/button';
import { useState, useEffect } from 'react';

interface LocationModalProps {
  onLocationSet: (city: string, state: string) => void;
}

// Simple zipcode to city/state lookup (mock data for demo)
const zipcodeDatabase: Record<string, { city: string; state: string }> = {
  '08830': { city: 'Iselin', state: 'NJ' }, // Hackathon demo zipcode
  '10001': { city: 'New york', state: 'NY' },
  '10002': { city: 'New york', state: 'NY' },
  '07102': { city: 'Newark', state: 'NJ' },
  '07103': { city: 'Newark', state: 'NJ' },
  '90001': { city: 'Los angeles', state: 'CA' },
  '90002': { city: 'Los angeles', state: 'CA' },
  '60601': { city: 'Chicago', state: 'IL' },
  '60602': { city: 'Chicago', state: 'IL' },
  '94102': { city: 'San francisco', state: 'CA' },
  '94103': { city: 'San francisco', state: 'CA' },
  '02108': { city: 'Boston', state: 'MA' },
  '02109': { city: 'Boston', state: 'MA' },
  '75201': { city: 'Dallas', state: 'TX' },
  '75202': { city: 'Dallas', state: 'TX' },
  '98101': { city: 'Seattle', state: 'WA' },
  '98102': { city: 'Seattle', state: 'WA' },
};

// Store type colors
const STORE_TYPE_COLORS = {
  primary: '#6ba567',    // Green for primary stores
  specialty: '#8b7ba8'   // Purple for specialty stores
};

// Available stores with types
const AVAILABLE_STORES = [
  {
    id: 'freshdirect',
    name: 'FreshDirect',
    type: 'primary' as const,
    description: 'Wide selection, competitive prices',
    color: STORE_TYPE_COLORS.primary
  },
  {
    id: 'whole_foods',
    name: 'Whole Foods',
    type: 'primary' as const,
    description: 'Organic & natural products',
    color: STORE_TYPE_COLORS.primary
  },
  {
    id: 'indian_grocer',
    name: 'Pure Indian Foods',
    type: 'specialty' as const,
    description: 'Authentic Indian ingredients',
    color: STORE_TYPE_COLORS.specialty
  },
  {
    id: 'asian_market',
    name: 'H Mart',
    type: 'specialty' as const,
    description: 'Asian grocery specialists',
    color: STORE_TYPE_COLORS.specialty
  }
];

export function LocationModal({ onLocationSet }: LocationModalProps) {
  const [step, setStep] = useState<'zipcode' | 'loading' | 'store'>('zipcode');
  const [zipcode, setZipcode] = useState('');
  const [location, setLocation] = useState<{ city: string; state: string } | null>(null);
  const [selectedStores, setSelectedStores] = useState<string[]>([]);
  const [showSuggestionInput, setShowSuggestionInput] = useState(false);
  const [storeSuggestion, setStoreSuggestion] = useState('');

  // Load saved favorite stores from localStorage
  useEffect(() => {
    const savedStores = localStorage.getItem('favoriteStores');
    if (savedStores) {
      try {
        setSelectedStores(JSON.parse(savedStores));
      } catch (e) {
        console.error('Failed to load favorite stores:', e);
      }
    }
  }, []);

  const handleZipcodeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!zipcode.trim() || zipcode.length !== 5) return;

    // Show loading state
    setStep('loading');

    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1500));

    // Look up city/state from zipcode
    const locationData = zipcodeDatabase[zipcode] || { city: 'Your City', state: 'XX' };
    setLocation(locationData);

    // Show store selection
    setStep('store');
  };

  const toggleStore = (storeId: string) => {
    setSelectedStores(prev => {
      const newSelection = prev.includes(storeId)
        ? prev.filter(id => id !== storeId)
        : [...prev, storeId];

      // Save to localStorage
      localStorage.setItem('favoriteStores', JSON.stringify(newSelection));
      return newSelection;
    });
  };

  const handleStoreConfirm = () => {
    if (location) {
      // Save selected stores to localStorage
      localStorage.setItem('favoriteStores', JSON.stringify(selectedStores));
      onLocationSet(location.city, location.state);
    }
  };

  const handleSuggestionSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (storeSuggestion.trim()) {
      // In a real app, this would send the suggestion to the backend
      alert(`Thank you! We'll consider adding ${storeSuggestion} in the future.`);
      setStoreSuggestion('');
      setShowSuggestionInput(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 sm:p-8">
        {/* Zipcode Step */}
        {step === 'zipcode' && (
          <>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-[#f5e6d3] rounded-full flex items-center justify-center">
                <MapPin className="w-5 h-5 text-[#6b5f4a]" />
              </div>
              <h2 className="text-xl sm:text-2xl font-semibold text-[#4a3f2a]">
                Where are you shopping?
              </h2>
            </div>

            <p className="text-sm sm:text-base text-[#6b5f4a] mb-4">
              Enter your zipcode to find stores and products available near you.
            </p>

            <div className="bg-[#e8f5e9] border border-[#4a7c59]/25 rounded-lg p-3 mb-6">
              <p className="text-xs sm:text-sm text-[#2d5a3d]">
                <span className="font-semibold">Demo Note:</span> For this hackathon demo, please use zipcode <span className="font-mono font-semibold">08830</span>
              </p>
            </div>

            <form onSubmit={handleZipcodeSubmit} className="space-y-4">
              <div>
                <label htmlFor="zipcode" className="block text-sm font-medium text-[#4a3f2a] mb-2">
                  Zipcode
                </label>
                <input
                  id="zipcode"
                  type="text"
                  value={zipcode}
                  onChange={(e) => setZipcode(e.target.value.replace(/\D/g, '').slice(0, 5))}
                  placeholder="e.g., 10001"
                  maxLength={5}
                  className="w-full px-3 sm:px-4 py-2 sm:py-3 border border-[#d5c5a8] rounded bg-white text-[#4a3f2a] placeholder:text-[#9b8f7a] focus:outline-none focus:ring-2 focus:ring-[#d9b899] text-sm sm:text-base"
                  required
                />
              </div>

              <Button
                type="submit"
                disabled={zipcode.length !== 5}
                className="w-full bg-[#DD9057] hover:bg-[#C87040] text-white py-3 sm:py-4 rounded text-sm sm:text-base disabled:bg-[#EDD4C0] disabled:opacity-70 disabled:cursor-not-allowed"
              >
                Find Stores
              </Button>
            </form>

            <p className="text-xs text-[#9b8f7a] mt-4 text-center">
              Your location helps us show you products available in your area
            </p>
          </>
        )}

        {/* Loading Step */}
        {step === 'loading' && (
          <div className="flex flex-col items-center justify-center py-8">
            <Loader2 className="w-12 h-12 text-[#d9b899] animate-spin mb-4" />
            <h3 className="text-lg sm:text-xl font-semibold text-[#4a3f2a] mb-2">
              Finding stores near you...
            </h3>
            <p className="text-sm text-[#6b5f4a] text-center">
              We're checking product availability in {zipcode}
            </p>
          </div>
        )}

        {/* Store Selection Step */}
        {step === 'store' && location && (
          <>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-[#f5e6d3] rounded-full flex items-center justify-center">
                <Store className="w-5 h-5 text-[#6b5f4a]" />
              </div>
              <h2 className="text-xl sm:text-2xl font-semibold text-[#4a3f2a]">
                Stores Available
              </h2>
            </div>

            <p className="text-sm sm:text-base text-[#6b5f4a] mb-4">
              Select your favorite stores near {location.city}, {location.state}. Cart Coach will find the best deals across all selected stores.
            </p>

            {/* Store Cards */}
            <div className="space-y-3 mb-4 max-h-[300px] overflow-y-auto">
              {AVAILABLE_STORES.map((store) => (
                <button
                  key={store.id}
                  onClick={() => toggleStore(store.id)}
                  className="w-full flex items-start gap-3 p-3 border-2 rounded-lg transition-all hover:border-[#d4976c]"
                  style={{
                    borderColor: selectedStores.includes(store.id) ? store.color : '#e5d5b8',
                    backgroundColor: selectedStores.includes(store.id) ? `${store.color}10` : 'white'
                  }}
                >
                  <div
                    className="w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 transition-colors"
                    style={{
                      borderColor: selectedStores.includes(store.id) ? store.color : '#d5c5a8',
                      backgroundColor: selectedStores.includes(store.id) ? store.color : 'white'
                    }}
                  >
                    {selectedStores.includes(store.id) && (
                      <Check className="w-3 h-3 text-white" />
                    )}
                  </div>
                  <div className="flex-1 text-left">
                    <div className="flex items-center gap-2 mb-0.5">
                      <h3 className="font-semibold text-[#4a3f2a] text-sm">
                        {store.name}
                      </h3>
                      <span
                        className="text-[10px] px-1.5 py-0.5 rounded-full text-white font-medium"
                        style={{ backgroundColor: store.color }}
                      >
                        {store.type}
                      </span>
                    </div>
                    <p className="text-xs text-[#6b5f4a]">
                      {store.description}
                    </p>
                  </div>
                </button>
              ))}
            </div>

            <Button
              onClick={handleStoreConfirm}
              className="w-full bg-[#6b5f3a] hover:bg-[#5b4f2a] text-white py-3 sm:py-4 rounded text-sm sm:text-base mb-3"
            >
              Continue
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>

            {/* Store Suggestion */}
            {!showSuggestionInput ? (
              <button
                onClick={() => setShowSuggestionInput(true)}
                className="w-full text-sm text-[#6b5f4a] hover:text-[#4a3f2a] underline"
              >
                Don't see your store? Suggest one for future
              </button>
            ) : (
              <form onSubmit={handleSuggestionSubmit} className="space-y-2">
                <input
                  type="text"
                  value={storeSuggestion}
                  onChange={(e) => setStoreSuggestion(e.target.value)}
                  placeholder="Enter store name..."
                  className="w-full px-3 py-2 border border-[#d5c5a8] rounded bg-white text-[#4a3f2a] placeholder:text-[#9b8f7a] focus:outline-none focus:ring-2 focus:ring-[#d9b899] text-sm"
                />
                <div className="flex gap-2">
                  <Button
                    type="submit"
                    className="flex-1 bg-[#6b5f4a] hover:bg-[#5b4f3a] text-white py-2 text-xs sm:text-sm"
                  >
                    Submit Suggestion
                  </Button>
                  <Button
                    type="button"
                    onClick={() => setShowSuggestionInput(false)}
                    variant="outline"
                    className="flex-1 border-[#8b7a5a] text-[#6b5f4a] hover:bg-[#f5e6d3] py-2 text-xs sm:text-sm"
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            )}
          </>
        )}
      </div>
    </div>
  );
}
