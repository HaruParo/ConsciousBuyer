import React, { useState } from 'react'
import { AppState, Ingredient, Cart } from './types'
import { Button } from './components/Button'
import { IngredientConfirmModal } from './components/IngredientConfirmModal'
import { CartView } from './components/CartView'
import { AgentCheckoutModal } from './components/AgentCheckoutModal'
import { extractIngredientsFromPrompt, assignStores, generateCartItems } from './mockData'
import { colors, spacing, borderRadius, fontSize, fontWeight } from './design-system'

export const App: React.FC = () => {
  const [appState, setAppState] = useState<AppState>('idle')
  const [prompt, setPrompt] = useState('chicken biryani for 4')
  const [draftIngredients, setDraftIngredients] = useState<Ingredient[]>([])
  const [carts, setCarts] = useState<Cart[]>([])

  const handleCreateCart = () => {
    // Extract ingredients from prompt
    const ingredients = extractIngredientsFromPrompt(prompt)
    setDraftIngredients(ingredients)
    setAppState('confirmingIngredients')
  }

  const handleConfirmIngredients = (confirmedIngredients: Ingredient[]) => {
    // Assign ingredients to stores
    const stores = assignStores(confirmedIngredients)

    // Create carts for each store
    const newCarts: Cart[] = stores.map(store => {
      const storeIngredients = confirmedIngredients.filter(ing =>
        store.ingredients.includes(ing.name)
      )
      const items = generateCartItems(storeIngredients, store.name)
      const total = items.reduce((sum, item) => sum + (item.price * item.quantity), 0)

      return {
        store: store.name,
        items,
        total,
        isPrimary: store.isPrimary,
        deliveryEstimate: store.deliveryEstimate
      }
    })

    setCarts(newCarts)
    setAppState('cartReady')
  }

  const handleCancelConfirmation = () => {
    setAppState('idle')
    setDraftIngredients([])
  }

  const handleAgentCheckout = () => {
    setAppState('agentCheckout')
  }

  const handleCloseAgentCheckout = () => {
    setAppState('cartReady')
  }

  const containerStyles: React.CSSProperties = {
    minHeight: '100vh',
    backgroundColor: colors.cream,
    padding: spacing.xxxl,
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  }

  const maxWidthStyles: React.CSSProperties = {
    maxWidth: '900px',
    margin: '0 auto',
  }

  const headerStyles: React.CSSProperties = {
    marginBottom: spacing.xxl,
  }

  const titleStyles: React.CSSProperties = {
    fontSize: fontSize.xxl,
    fontWeight: fontWeight.bold,
    color: colors.primaryBrown,
    marginBottom: spacing.sm,
  }

  const subtitleStyles: React.CSSProperties = {
    fontSize: fontSize.base,
    color: colors.grayLight,
  }

  const promptSectionStyles: React.CSSProperties = {
    backgroundColor: colors.white,
    padding: spacing.xl,
    borderRadius: borderRadius.lg,
    border: `2px solid ${colors.beigeBorder}`,
    marginBottom: spacing.xl,
  }

  const labelStyles: React.CSSProperties = {
    display: 'block',
    fontWeight: fontWeight.semibold,
    color: colors.primaryBrown,
    marginBottom: spacing.sm,
    fontSize: fontSize.base,
  }

  const textareaStyles: React.CSSProperties = {
    width: '100%',
    padding: spacing.md,
    border: `2px solid ${colors.beigeBorder}`,
    borderRadius: borderRadius.md,
    fontSize: fontSize.base,
    fontFamily: 'inherit',
    resize: 'vertical',
    minHeight: '100px',
    boxSizing: 'border-box',
  }

  const examplesStyles: React.CSSProperties = {
    marginTop: spacing.md,
    fontSize: fontSize.sm,
    color: colors.gray,
  }

  const exampleLinkStyles: React.CSSProperties = {
    color: colors.primaryBrown,
    textDecoration: 'underline',
    cursor: 'pointer',
    marginRight: spacing.md,
  }

  return (
    <div style={containerStyles}>
      <div style={maxWidthStyles}>
        <div style={headerStyles}>
          <h1 style={titleStyles}>🛒 Conscious Cart Coach</h1>
          <p style={subtitleStyles}>Multi-store cart planning with ingredient confirmation</p>
        </div>

        {/* Prompt Section - Always visible */}
        <div style={promptSectionStyles}>
          <label style={labelStyles}>What would you like to cook?</label>
          <textarea
            style={textareaStyles}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="E.g., chicken biryani for 4, fresh salad, seasonal vegetables..."
          />
          <div style={examplesStyles}>
            Try:{' '}
            <span style={exampleLinkStyles} onClick={() => setPrompt('chicken biryani for 4')}>
              chicken biryani for 4
            </span>
            <span style={exampleLinkStyles} onClick={() => setPrompt('fresh salad for 2')}>
              fresh salad for 2
            </span>
            <span style={exampleLinkStyles} onClick={() => setPrompt('seasonal vegetables')}>
              seasonal vegetables
            </span>
          </div>
          <div style={{ marginTop: spacing.lg }}>
            <Button
              variant="primary"
              fullWidth
              onClick={handleCreateCart}
              disabled={!prompt.trim()}
            >
              Create my cart
            </Button>
          </div>
        </div>

        {/* Cart View - Only shows after confirmation */}
        {appState === 'cartReady' && carts.length > 0 && (
          <CartView carts={carts} onAgentCheckout={handleAgentCheckout} />
        )}

        {/* Modals */}
        <IngredientConfirmModal
          isOpen={appState === 'confirmingIngredients'}
          ingredients={draftIngredients}
          onConfirm={handleConfirmIngredients}
          onCancel={handleCancelConfirmation}
        />

        <AgentCheckoutModal
          isOpen={appState === 'agentCheckout'}
          carts={carts}
          onClose={handleCloseAgentCheckout}
        />
      </div>
    </div>
  )
}
