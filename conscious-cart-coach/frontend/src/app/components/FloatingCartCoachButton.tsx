'use client';

import { useState, useEffect } from 'react';
import { MessageSquare, X } from 'lucide-react';
import { Dialog, DialogContent } from '@/app/components/ui/dialog';
import { Button } from '@/app/components/ui/button';
import { MealPlanInput } from '@/app/components/MealPlanInput';

interface FloatingCartCoachButtonProps {
  mealPlan: string;
  onMealPlanChange: (value: string) => void;
  onCreateCart: () => void;
  isLoading: boolean;
}

export function FloatingCartCoachButton({
  mealPlan,
  onMealPlanChange,
  onCreateCart,
  isLoading
}: FloatingCartCoachButtonProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      {/* Floating Button - Only visible on mobile/tablet (< lg) */}
      <button
        onClick={() => setIsModalOpen(true)}
        className="
          fixed bottom-24 right-6 z-50
          lg:hidden
          flex items-center gap-2
          px-4 py-3
          bg-[#DD9057] hover:bg-[#C87040]
          text-white rounded-full shadow-lg
          transition-all duration-300 ease-in-out
        "
        aria-label="Open Cart Coach"
      >
        <MessageSquare className="w-5 h-5" />
        <span className="font-medium text-sm">Cart Coach</span>
      </button>

      {/* Full-Screen Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-full h-full m-0 p-0 rounded-none lg:hidden">
          <div className="h-full flex flex-col bg-[#f5e6d3]">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-4 py-3 bg-[#f5d7b1] border-b border-[#e5c7a1]">
              <h2 className="text-lg font-semibold text-[#4a3f2a]" style={{ fontFamily: 'Georgia, serif' }}>
                Cart Coach
              </h2>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsModalOpen(false)}
                className="text-[#6b5f4a] hover:text-[#4a3f2a] hover:bg-[#f5e6d3]"
              >
                <X className="w-5 h-5" />
              </Button>
            </div>

            {/* Modal Content - MealPlanInput */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6">
              <MealPlanInput
                mealPlan={mealPlan}
                onMealPlanChange={onMealPlanChange}
                onCreateCart={() => {
                  onCreateCart();
                  setIsModalOpen(false); // Close modal after creating cart
                }}
                isLoading={isLoading}
              />
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
