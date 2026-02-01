'use client';

import { useState, useEffect } from 'react';
import { MapPin, Users, Settings } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/app/components/ui/dialog';
import { Button } from '@/app/components/ui/button';
import { Input } from '@/app/components/ui/input';
import { Label } from '@/app/components/ui/label';

interface UserPreferencesLinksProps {
  location: string;
  servings: number;
  onChangeLocation?: () => void;
  onServingsChange?: (servings: number) => void;
  onPreferencesChange?: (preferences: any) => void;
}

export function UserPreferencesLinks({
  location,
  servings,
  onChangeLocation,
  onServingsChange,
  onPreferencesChange,
}: UserPreferencesLinksProps) {
  const [servingsDialogOpen, setServingsDialogOpen] = useState(false);
  const [preferencesDialogOpen, setPreferencesDialogOpen] = useState(false);

  const [tempServings, setTempServings] = useState(servings);

  // Sync tempServings with servings prop when it changes
  useEffect(() => {
    setTempServings(servings);
  }, [servings]);

  const handleServingsSave = () => {
    onServingsChange?.(tempServings);
    setServingsDialogOpen(false);
  };

  return (
    <>
      <div className="flex items-center gap-1 sm:gap-2 flex-wrap text-sm sm:text-base">
        {/* Delivery Location Link */}
        <button
          onClick={onChangeLocation}
          className="inline-flex items-center gap-1 px-2 py-1 rounded hover:bg-white/10 transition-colors"
        >
          <MapPin className="w-3 h-3 sm:w-4 sm:h-4" />
          <span>Delivery Location: {location}</span>
        </button>

        <span className="opacity-40">|</span>

        {/* Family Size Link */}
        <button
          onClick={() => setServingsDialogOpen(true)}
          className="inline-flex items-center gap-1 px-2 py-1 rounded hover:bg-white/10 transition-colors"
        >
          <Users className="w-3 h-3 sm:w-4 sm:h-4" />
          <span>Family size: {servings}</span>
        </button>

        <span className="opacity-40">|</span>

        {/* Other Preferences Link */}
        <button
          onClick={() => setPreferencesDialogOpen(true)}
          className="inline-flex items-center gap-1 px-2 py-1 rounded hover:bg-white/10 transition-colors"
        >
          <Settings className="w-3 h-3 sm:w-4 sm:h-4" />
          <span>Other Preferences</span>
        </button>
      </div>

      {/* Family Size Dialog */}
      <Dialog open={servingsDialogOpen} onOpenChange={setServingsDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Users className="w-5 h-5 text-[#6b5f3a]" />
              Family Size
            </DialogTitle>
            <DialogDescription>
              How many people are you typically shopping for?
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="servings">Number of people</Label>
              <div className="flex items-center gap-3">
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setTempServings(Math.max(1, tempServings - 1))}
                  className="h-10 w-10"
                >
                  -
                </Button>
                <Input
                  id="servings"
                  type="number"
                  value={tempServings}
                  onChange={(e) => setTempServings(Math.max(1, parseInt(e.target.value) || 1))}
                  className="text-center text-lg font-semibold border-[#c9b896] w-20"
                  min="1"
                />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setTempServings(tempServings + 1)}
                  className="h-10 w-10"
                >
                  +
                </Button>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setTempServings(servings);
                setServingsDialogOpen(false);
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleServingsSave}
              className="bg-[#6b5f3a] hover:bg-[#5a4e2f] text-white"
            >
              Save Family Size
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Other Preferences Dialog */}
      <Dialog open={preferencesDialogOpen} onOpenChange={setPreferencesDialogOpen}>
        <DialogContent className="sm:max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5 text-[#6b5f3a]" />
              Other Preferences
            </DialogTitle>
            <DialogDescription>
              Customize your shopping preferences to get personalized recommendations
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {/* Info text */}
            <p className="text-sm text-[#6b5f4a] mb-2">
              Tell us about your dietary needs, health goals, or any special requirements.
            </p>
            <div className="bg-[#e8f5e9] border border-[#4a7c59]/25 rounded-lg p-3 text-xs text-[#2d5a3d]">
              <span className="font-semibold">💡 Tip:</span> You can include preferences in your meal prompt (e.g., "vegetarian pasta for 4") or add them here for all future carts.
            </div>

            {/* Ingredient Preferences Section */}
            <div className="space-y-3">
              <div className="space-y-3">
                <div className="space-y-2">
                  <Label htmlFor="include-ingredients" className="text-sm font-semibold text-[#4a3f2a]">
                    Always Include
                  </Label>
                  <Input
                    id="include-ingredients"
                    placeholder="e.g., turmeric, ginger, garlic, organic produce"
                    className="border-[#c9b896]"
                  />
                  <p className="text-xs text-gray-500">
                    Ingredients, brands, or qualities you want to prioritize (e.g., "organic", "grass-fed", "local")
                  </p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="exclude-ingredients" className="text-sm font-semibold text-[#4a3f2a]">
                    Don't Include
                  </Label>
                  <Input
                    id="exclude-ingredients"
                    placeholder="e.g., peanuts, shellfish, dairy, gluten"
                    className="border-[#c9b896]"
                  />
                  <p className="text-xs text-gray-500">
                    Ingredients to avoid due to allergies, dietary restrictions, or preferences
                  </p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="other-preferences" className="text-sm font-semibold text-[#4a3f2a]">
                    Other Preferences
                  </Label>
                  <textarea
                    id="other-preferences"
                    placeholder="e.g., recovering from ACL surgery, need high protein, prefer sustainable seafood"
                    rows={3}
                    className="w-full px-3 py-2 border border-[#c9b896] rounded bg-white text-[#4a3f2a] placeholder:text-[#9b8f7a] focus:outline-none focus:ring-2 focus:ring-[#d9b899] text-sm resize-none"
                  />
                  <p className="text-xs text-gray-500">
                    Any other dietary needs, health goals, or preferences we should know about
                  </p>
                </div>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setPreferencesDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={() => {
                // TODO: Collect all preference values and pass to onPreferencesChange
                onPreferencesChange?.({});
                setPreferencesDialogOpen(false);
              }}
              className="bg-[#6b5f3a] hover:bg-[#5a4e2f] text-white"
            >
              Save Preferences
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
