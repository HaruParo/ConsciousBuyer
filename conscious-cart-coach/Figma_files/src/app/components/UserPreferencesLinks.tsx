'use client';

import { useState } from 'react';
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
  onLocationChange?: (location: string) => void;
  onServingsChange?: (servings: number) => void;
  onPreferencesChange?: (preferences: any) => void;
}

export function UserPreferencesLinks({
  location,
  servings,
  onLocationChange,
  onServingsChange,
  onPreferencesChange,
}: UserPreferencesLinksProps) {
  const [locationDialogOpen, setLocationDialogOpen] = useState(false);
  const [servingsDialogOpen, setServingsDialogOpen] = useState(false);
  const [preferencesDialogOpen, setPreferencesDialogOpen] = useState(false);

  const [tempLocation, setTempLocation] = useState(location);
  const [tempServings, setTempServings] = useState(servings);

  const handleLocationSave = () => {
    onLocationChange?.(tempLocation);
    setLocationDialogOpen(false);
  };

  const handleServingsSave = () => {
    onServingsChange?.(tempServings);
    setServingsDialogOpen(false);
  };

  return (
    <>
      <div className="flex items-center gap-2 flex-wrap text-sm sm:text-base opacity-90">
        {/* Delivery Location Link */}
        <button
          onClick={() => setLocationDialogOpen(true)}
          className="underline hover:opacity-75 transition-opacity inline-flex items-center gap-1"
        >
          <MapPin className="w-3 h-3 sm:w-4 sm:h-4" />
          <span>Delivery Location: {location}</span>
        </button>

        <span className="opacity-40">|</span>

        {/* Family Size Link */}
        <button
          onClick={() => setServingsDialogOpen(true)}
          className="underline hover:opacity-75 transition-opacity inline-flex items-center gap-1"
        >
          <Users className="w-3 h-3 sm:w-4 sm:h-4" />
          <span>Family size: {servings}</span>
        </button>

        <span className="opacity-40">|</span>

        {/* Other Preferences Link */}
        <button
          onClick={() => setPreferencesDialogOpen(true)}
          className="underline hover:opacity-75 transition-opacity inline-flex items-center gap-1"
        >
          <Settings className="w-3 h-3 sm:w-4 sm:h-4" />
          <span>Other Preferences</span>
        </button>
      </div>

      {/* Delivery Location Dialog */}
      <Dialog open={locationDialogOpen} onOpenChange={setLocationDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <MapPin className="w-5 h-5 text-[#6b5f3a]" />
              Delivery Location
            </DialogTitle>
            <DialogDescription>
              Update your delivery address for accurate availability and timing.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="location">City, State or ZIP Code</Label>
              <Input
                id="location"
                value={tempLocation}
                onChange={(e) => setTempLocation(e.target.value)}
                placeholder="e.g., Iselin, NJ or 08830"
                className="border-[#c9b896]"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setTempLocation(location);
                setLocationDialogOpen(false);
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleLocationSave}
              className="bg-[#6b5f3a] hover:bg-[#5a4e2f] text-white"
            >
              Save Location
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

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
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5 text-[#6b5f3a]" />
              Other Preferences
            </DialogTitle>
            <DialogDescription>
              Customize your shopping preferences
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="organic">Prefer Organic</Label>
                <input
                  id="organic"
                  type="checkbox"
                  className="w-4 h-4 accent-[#6b5f3a]"
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="local">Prefer Local Products</Label>
                <input
                  id="local"
                  type="checkbox"
                  className="w-4 h-4 accent-[#6b5f3a]"
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="seasonal">Prefer Seasonal Items</Label>
                <input
                  id="seasonal"
                  type="checkbox"
                  className="w-4 h-4 accent-[#6b5f3a]"
                />
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
                // TODO: Handle preferences save
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
