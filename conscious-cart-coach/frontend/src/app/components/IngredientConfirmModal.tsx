import { useState } from 'react';
import { Ingredient } from '@/app/types';
import { designTokens } from '@/app/design-tokens';
import { X, Plus, Minus } from 'lucide-react';

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

  const handleEdit = (index: number, field: keyof Ingredient, value: any) => {
    setEditableIngredients(editableIngredients.map((ing, i) =>
      i === index ? { ...ing, [field]: value } : ing
    ));
  };

  const handleAdd = () => {
    if (newIngredientName.trim()) {
      const newIngredient: Ingredient = {
        name: newIngredientName.trim(),
        quantity: 1,
        unit: 'unit',
      };
      setEditableIngredients([...editableIngredients, newIngredient]);
      setNewIngredientName('');
    }
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
          <div className="space-y-2">
            {editableIngredients.map((ing, index) => (
              <div
                key={index}
                className="flex items-center gap-3 p-3 rounded border"
                style={{
                  borderColor: designTokens.colors.border.light,
                  backgroundColor: designTokens.colors.background.card,
                }}
              >
                <input
                  type="text"
                  value={ing.name}
                  onChange={(e) => handleEdit(index, 'name', e.target.value)}
                  className="flex-1 px-3 py-2 rounded border"
                  style={{
                    borderColor: designTokens.colors.border.light,
                    fontFamily: designTokens.typography.fontFamily.primary,
                  }}
                />
                <button
                  onClick={() => handleRemove(index)}
                  className="p-2 hover:bg-red-50 rounded transition-colors"
                  style={{ color: '#dc3545' }}
                  title="Remove ingredient"
                >
                  <Minus className="w-5 h-5" />
                </button>
              </div>
            ))}
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
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
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
            onClick={() => onConfirm(editableIngredients)}
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
