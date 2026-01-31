import React, { useState } from 'react'
import { Modal } from './Modal'
import { Button } from './Button'
import { Ingredient } from '../types'
import { colors, spacing, borderRadius, fontSize } from '../design-system'

interface IngredientConfirmModalProps {
  isOpen: boolean
  ingredients: Ingredient[]
  onConfirm: (ingredients: Ingredient[]) => void
  onCancel: () => void
}

export const IngredientConfirmModal: React.FC<IngredientConfirmModalProps> = ({
  isOpen,
  ingredients,
  onConfirm,
  onCancel
}) => {
  const [editableIngredients, setEditableIngredients] = useState<Ingredient[]>(ingredients)
  const [newIngredientName, setNewIngredientName] = useState('')

  const handleRemove = (id: string) => {
    setEditableIngredients(editableIngredients.filter(ing => ing.id !== id))
  }

  const handleEdit = (id: string, newName: string) => {
    setEditableIngredients(editableIngredients.map(ing =>
      ing.id === id ? { ...ing, name: newName } : ing
    ))
  }

  const handleAdd = () => {
    if (newIngredientName.trim()) {
      const newIngredient: Ingredient = {
        id: `new-${Date.now()}`,
        name: newIngredientName.trim(),
        quantity: 1,
        unit: 'unit'
      }
      setEditableIngredients([...editableIngredients, newIngredient])
      setNewIngredientName('')
    }
  }

  const handleConfirm = () => {
    onConfirm(editableIngredients)
  }

  const itemStyles: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.md,
    padding: spacing.md,
    borderBottom: `1px solid ${colors.beigeBorder}`,
  }

  const inputStyles: React.CSSProperties = {
    flex: 1,
    padding: spacing.sm,
    border: `2px solid ${colors.beigeBorder}`,
    borderRadius: borderRadius.sm,
    fontSize: fontSize.base,
    fontFamily: 'inherit',
  }

  const removeButtonStyles: React.CSSProperties = {
    background: 'none',
    border: 'none',
    color: colors.errorRed,
    cursor: 'pointer',
    fontSize: fontSize.lg,
    padding: spacing.sm,
  }

  const addContainerStyles: React.CSSProperties = {
    display: 'flex',
    gap: spacing.md,
    marginTop: spacing.lg,
  }

  const footer = (
    <>
      <Button variant="secondary" onClick={onCancel}>
        Cancel
      </Button>
      <Button variant="primary" onClick={handleConfirm}>
        Confirm ingredients
      </Button>
    </>
  )

  return (
    <Modal
      isOpen={isOpen}
      onClose={onCancel}
      title="Confirm ingredients"
      footer={footer}
    >
      <div>
        {editableIngredients.map((ing) => (
          <div key={ing.id} style={itemStyles}>
            <input
              style={inputStyles}
              value={ing.name}
              onChange={(e) => handleEdit(ing.id, e.target.value)}
            />
            <span style={{ color: colors.grayLight, fontSize: fontSize.sm }}>
              {ing.quantity} {ing.unit}
            </span>
            <button
              style={removeButtonStyles}
              onClick={() => handleRemove(ing.id)}
              title="Remove ingredient"
            >
              ×
            </button>
          </div>
        ))}

        <div style={addContainerStyles}>
          <input
            style={inputStyles}
            placeholder="Add new ingredient..."
            value={newIngredientName}
            onChange={(e) => setNewIngredientName(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleAdd()
              }
            }}
          />
          <Button variant="secondary" onClick={handleAdd}>
            Add
          </Button>
        </div>
      </div>
    </Modal>
  )
}
