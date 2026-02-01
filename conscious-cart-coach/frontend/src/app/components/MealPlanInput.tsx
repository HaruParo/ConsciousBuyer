import { Check } from 'lucide-react';
import { Button } from '@/app/components/ui/button';

interface MealPlanInputProps {
  mealPlan: string;
  onMealPlanChange: (value: string) => void;
  onCreateCart: () => void;
  isLoading?: boolean;
  error?: string | null;
  hasItems?: boolean;
}

export function MealPlanInput({
  mealPlan,
  onMealPlanChange,
  onCreateCart,
  isLoading = false,
  error = null,
  hasItems = false
}: MealPlanInputProps) {
  const isDisabled = !mealPlan.trim() || isLoading;
  const buttonText = hasItems ? 'Update cart' : 'Create my cart';
  const loadingText = hasItems ? 'Updating your cart...' : 'Creating your cart...';

  return (
    <div className="max-w-xl mx-auto">
      <h2 className="text-xl sm:text-2xl mb-2 sm:mb-3 text-[#4a3f2a]">
        Turn any meal idea into a smart shopping cart
      </h2>
      <p className="text-sm sm:text-base text-[#6b5f4a] mb-4 sm:mb-6">
        Just tell me what you want to cook or buy. I'll build your cart with products from local stores near you.
      </p>

      <div className="mb-4 sm:mb-6">
        <h3 className="mb-2 sm:mb-3 text-base sm:text-lg text-[#4a3f2a]">What you get:</h3>
        <ul className="space-y-1.5 sm:space-y-2">
          <li className="flex items-start gap-2 text-sm sm:text-base text-[#6b5f4a]">
            <Check className="w-4 h-4 sm:w-5 sm:h-5 text-[#7a6f4a] flex-shrink-0 mt-0.5" />
            <span>Products from stores in your area</span>
          </li>
          <li className="flex items-start gap-2 text-sm sm:text-base text-[#6b5f4a]">
            <Check className="w-4 h-4 sm:w-5 sm:h-5 text-[#7a6f4a] flex-shrink-0 mt-0.5" />
            <span>Smart alternatives for health, cost, and quality</span>
          </li>
          <li className="flex items-start gap-2 text-sm sm:text-base text-[#6b5f4a]">
            <Check className="w-4 h-4 sm:w-5 sm:h-5 text-[#7a6f4a] flex-shrink-0 mt-0.5" />
            <span>FDA recall alerts and safety checks</span>
          </li>
          <li className="flex items-start gap-2 text-sm sm:text-base text-[#6b5f4a]">
            <Check className="w-4 h-4 sm:w-5 sm:h-5 text-[#7a6f4a] flex-shrink-0 mt-0.5" />
            <span>Seasonal produce and sustainable options</span>
          </li>
        </ul>
      </div>

      <div className="mb-3">
        <span className="text-xs sm:text-sm text-[#6b5f4a]">e.g. </span>
        <span className="text-xs sm:text-sm text-[#6b5f4a]">
          "chicken biryani for 4", "stir fry with tofu", "chicken tikka for 2"
        </span>
      </div>

      <div className="space-y-3">
        <div className="bg-[#fef4e6] border border-[#e5d5b8] rounded p-3 sm:p-4">
          <textarea
            id="meal-plan-input"
            value={mealPlan}
            onChange={(e) => onMealPlanChange(e.target.value)}
            placeholder="Enter your meal plan or shopping needs..."
            className="w-full bg-transparent border-none outline-none text-[#4a3f2a] text-sm sm:text-base resize-none min-h-[80px] sm:min-h-[100px]"
            style={{ fontFamily: 'inherit' }}
            disabled={isLoading}
          />
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-3 sm:px-4 py-2 sm:py-3 rounded text-xs sm:text-sm">
            {error}
          </div>
        )}

        <Button
          onClick={onCreateCart}
          disabled={isDisabled}
          className="w-full bg-[#DD9057] hover:bg-[#C87040] text-white py-4 sm:py-6 rounded text-sm sm:text-base disabled:bg-[#EDD4C0] disabled:opacity-70 disabled:cursor-not-allowed"
        >
          {isLoading ? loadingText : buttonText}
        </Button>
      </div>
    </div>
  );
}