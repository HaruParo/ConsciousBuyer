import { useState } from 'react';
import { Ingredient } from '@/app/types';
import { designTokens } from '@/app/design-tokens';
import { X, Plus, Minus, Info } from 'lucide-react';
import { getIngredientGuidanceChips } from '@/app/utils/ingredientHelpers';
import { Badge } from '@/app/components/ui/badge';

interface IngredientConfirmModalProps {
  ingredients: Ingredient[];
  onConfirm: (ingredients: Ingredient[]) => void;
  onCancel: () => void;
}

export function IngredientConfirmModal({ ingredients, onConfirm, onCancel }: IngredientConfirmModalProps) {
  const [editableIngredients, setEditableIngredients] = useState<Ingredient[]>(ingredients);
  const [newIngredientName, setNewIngredientName] = useState('');

  const handleRemove = (index: number) => {
    setEditableIngredients(editableIngredients.filter((_, i) => i !== index));
  };

  const handleEditName = (index: number, newName: string) => {
    setEditableIngredients(editableIngredients.map((ing, i) =>
      i === index ? { ...ing, name: newName } : ing
    ));
  };

  const handleAdd = () => {
    const trimmedName = newIngredientName.trim();
    if (trimmedName) {
      const newIngredient: Ingredient = {
        name: trimmedName,
        quantity: 1,
        unit: 'unit',
      };
      setEditableIngredients([...editableIngredients, newIngredient]);
      setNewIngredientName('');
    }
  };

  const handleConfirm = () => {
    // Filter out empty names and trim all before confirming
    const cleanedIngredients = editableIngredients
      .map(ing => ({ ...ing, name: ing.name.trim() }))
      .filter(ing => ing.name.length > 0);
    onConfirm(cleanedIngredients);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
      onClick={onCancel}
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col"
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
            Confirm ingredients
          </h2>
          <button
            onClick={onCancel}
            className="p-2 hover:bg-gray-100 rounded transition-colors"
            style={{ color: designTokens.colors.text.secondary }}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <p className="text-sm mb-4" style={{ color: designTokens.colors.text.secondary }}>
            Review and edit the ingredient list. Add or remove items as needed.
          </p>
          <div className="space-y-3">
            {editableIngredients.map((ing, index) => {
              const guidanceChips = getIngredientGuidanceChips(ing.name, null, null);

              return (
                <div
                  key={index}
                  className="p-3 rounded border"
                  style={{
                    borderColor: designTokens.colors.border.light,
                    backgroundColor: designTokens.colors.background.card,
                  }}
                >
                  {/* Ingredient name (user can type "fresh ginger", "cumin seeds", etc.) */}
                  <div className="flex items-center gap-2 mb-2">
                    <input
                      type="text"
                      value={ing.name}
                      onChange={(e) => handleEditName(index, e.target.value)}
                      className="flex-1 px-3 py-2 rounded border"
                      placeholder="Ingredient name (e.g., fresh ginger, cumin seeds)"
                      style={{
                        borderColor: designTokens.colors.border.light,
                        fontFamily: designTokens.typography.fontFamily.primary,
                      }}
                    />
                    <button
                      onClick={() => handleRemove(index)}
                      className="p-2 hover:bg-red-50 rounded transition-colors flex-shrink-0"
                      style={{ color: '#dc3545' }}
                      title="Remove ingredient"
                    >
                      <Minus className="w-5 h-5" />
                    </button>
                  </div>

                  {/* Guidance chips */}
                  {guidanceChips.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 ml-1">
                      {guidanceChips.map((chip, chipIndex) => (
                        <div key={chipIndex} className="group relative">
                          <Badge
                            variant="outline"
                            className={`text-xs px-2 py-0.5 rounded-full flex items-center gap-1 cursor-help ${
                              chip.type === 'organic'
                                ? 'bg-[#e8f5e9] text-[#2d5a3d] border-[#4a7c59]/25'
                                : chip.type === 'conventional'
                                  ? 'bg-[#f0f4f8] text-[#4a5568] border-[#718096]/25'
                                  : chip.type === 'fresh'
                                    ? 'bg-[#e6f7ff] text-[#0369a1] border-[#0369a1]/25'
                                    : 'bg-[#fef9f5] text-[#8b5e2b] border-[#8b5e2b]/25'
                            }`}
                          >
                            <Info className="w-3 h-3" />
                            {chip.label}
                          </Badge>
                          {/* Tooltip */}
                          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                            {chip.tooltip}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Add new ingredient */}
          <div
            className="mt-4 flex items-center gap-3 p-3 rounded border-2 border-dashed"
            style={{ borderColor: designTokens.colors.border.medium }}
          >
            <input
              type="text"
              value={newIngredientName}
              onChange={(e) => setNewIngredientName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleAdd();
                }
              }}
              placeholder="Add new ingredient..."
              className="flex-1 px-3 py-2 rounded border"
              style={{
                borderColor: designTokens.colors.border.light,
                fontFamily: designTokens.typography.fontFamily.primary,
              }}
            />
            <button
              onClick={handleAdd}
              className="px-4 py-2 rounded flex items-center gap-2 transition-colors"
              style={{
                backgroundColor: designTokens.colors.brand.accent,
                color: designTokens.colors.text.primary,
              }}
            >
              <Plus className="w-5 h-5" />
              Add
            </button>
          </div>
        </div>

        {/* Footer */}
        <div
          className="flex items-center justify-end gap-3 p-6 border-t"
          style={{ borderColor: designTokens.colors.border.light }}
        >
          <button
            onClick={onCancel}
            className="px-6 py-3 rounded border-2 transition-colors"
            style={{
              borderColor: designTokens.colors.border.medium,
              color: designTokens.colors.text.primary,
              backgroundColor: designTokens.colors.background.card,
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            className="px-6 py-3 rounded transition-colors font-semibold"
            style={{
              backgroundColor: designTokens.colors.brand.primary,
              color: designTokens.colors.text.white,
            }}
          >
            Confirm ingredients
          </button>
        </div>
      </div>
    </div>
  );
}
