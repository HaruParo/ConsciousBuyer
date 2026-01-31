import React, { useState } from 'react'
import { Cart, CartItem as CartItemType } from '../types'
import { Chip } from './Chip'
import { Button } from './Button'
import { colors, spacing, borderRadius, fontSize, fontWeight } from '../design-system'

interface CartViewProps {
  carts: Cart[]
  onAgentCheckout: () => void
}

export const CartView: React.FC<CartViewProps> = ({ carts, onAgentCheckout }) => {
  const [activeTab, setActiveTab] = useState<string>('all')

  const totalStores = carts.length
  const totalItems = carts.reduce((sum, cart) => sum + cart.items.length, 0)
  const totalCost = carts.reduce((sum, cart) => sum + cart.total, 0)

  const headerStyles: React.CSSProperties = {
    backgroundColor: colors.white,
    padding: spacing.xl,
    borderRadius: borderRadius.lg,
    border: `2px solid ${colors.beigeBorder}`,
    marginBottom: spacing.xl,
  }

  const headerTitleStyles: React.CSSProperties = {
    fontSize: fontSize.xl,
    fontWeight: fontWeight.bold,
    color: colors.primaryBrown,
    marginBottom: spacing.md,
  }

  const storeBreakdownStyles: React.CSSProperties = {
    fontSize: fontSize.base,
    color: colors.gray,
    marginBottom: spacing.lg,
  }

  const tabsContainerStyles: React.CSSProperties = {
    display: 'flex',
    gap: spacing.md,
    marginBottom: spacing.xl,
    borderBottom: `2px solid ${colors.beigeBorder}`,
  }

  const getTabStyles = (isActive: boolean): React.CSSProperties => ({
    padding: `${spacing.md} ${spacing.lg}`,
    background: 'none',
    border: 'none',
    borderBottom: isActive ? `3px solid ${colors.primaryBrown}` : '3px solid transparent',
    color: isActive ? colors.primaryBrown : colors.gray,
    fontWeight: isActive ? fontWeight.bold : fontWeight.normal,
    fontSize: fontSize.base,
    cursor: 'pointer',
    marginBottom: '-2px',
    fontFamily: 'inherit',
  })

  const getFilteredItems = (): { cart: Cart; item: CartItemType }[] => {
    const allItems: { cart: Cart; item: CartItemType }[] = []

    carts.forEach(cart => {
      if (activeTab === 'all' || activeTab === cart.store) {
        cart.items.forEach(item => {
          allItems.push({ cart, item })
        })
      }
    })

    return allItems
  }

  return (
    <div>
      {/* Header with multi-store info */}
      <div style={headerStyles}>
        <div style={headerTitleStyles}>
          {totalStores > 1 ? `Multi-store cart: ${totalStores} stores selected` : '1 store selected'}
        </div>
        <div style={storeBreakdownStyles}>
          {carts.map((cart, idx) => (
            <span key={cart.store}>
              {cart.store} ({cart.items.length})
              {idx < carts.length - 1 && ' • '}
            </span>
          ))}
        </div>
        <Button variant="primary" onClick={onAgentCheckout}>
          Agent Checkout
        </Button>
      </div>

      {/* Tabs */}
      <div style={tabsContainerStyles}>
        <button
          style={getTabStyles(activeTab === 'all')}
          onClick={() => setActiveTab('all')}
        >
          All items ({totalItems})
        </button>
        {carts.map(cart => (
          <button
            key={cart.store}
            style={getTabStyles(activeTab === cart.store)}
            onClick={() => setActiveTab(cart.store)}
          >
            {cart.store}
            {cart.deliveryEstimate && <span style={{ opacity: 0.6 }}> · {cart.deliveryEstimate}</span>}
            {' '}({cart.items.length})
          </button>
        ))}
      </div>

      {/* Cart items */}
      <div>
        {getFilteredItems().map(({ cart, item }) => (
          <CartItemCard key={item.id} item={item} cart={cart} />
        ))}
      </div>

      {/* Total */}
      <div style={{
        ...headerStyles,
        marginTop: spacing.xl,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <span style={{ fontSize: fontSize.lg, fontWeight: fontWeight.bold }}>
          Total ({activeTab === 'all' ? 'all stores' : activeTab})
        </span>
        <span style={{ fontSize: fontSize.xl, fontWeight: fontWeight.bold, color: colors.primaryBrown }}>
          ${activeTab === 'all'
            ? totalCost.toFixed(2)
            : carts.find(c => c.store === activeTab)?.total.toFixed(2) || '0.00'}
        </span>
      </div>
    </div>
  )
}

// Cart Item Card Component
const CartItemCard: React.FC<{ item: CartItemType; cart: Cart }> = ({ item, cart }) => {
  const cardStyles: React.CSSProperties = {
    backgroundColor: colors.white,
    padding: spacing.lg,
    borderRadius: borderRadius.md,
    border: `2px solid ${colors.beigeBorder}`,
    marginBottom: spacing.md,
  }

  const headerRowStyles: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing.sm,
  }

  const nameStyles: React.CSSProperties = {
    fontSize: fontSize.md,
    fontWeight: fontWeight.semibold,
    color: colors.black,
    marginBottom: spacing.xs,
  }

  const brandStyles: React.CSSProperties = {
    fontSize: fontSize.sm,
    color: colors.gray,
  }

  const chipContainerStyles: React.CSSProperties = {
    display: 'flex',
    gap: spacing.sm,
    flexWrap: 'wrap',
    marginTop: spacing.md,
  }

  const priceStyles: React.CSSProperties = {
    fontSize: fontSize.lg,
    fontWeight: fontWeight.bold,
    color: colors.primaryBrown,
  }

  // Determine store chip variant
  const getStoreVariant = () => {
    if (!item.available) return 'unavailable'
    return cart.isPrimary ? 'primary' : 'specialty'
  }

  return (
    <div style={cardStyles}>
      <div style={headerRowStyles}>
        <div style={{ flex: 1 }}>
          <div style={nameStyles}>{item.name}</div>
          <div style={brandStyles}>{item.brand} • {item.size}</div>
        </div>
        <div style={priceStyles}>
          ${(item.price * item.quantity).toFixed(2)}
        </div>
      </div>

      <div style={chipContainerStyles}>
        <Chip variant={getStoreVariant()}>{item.store}</Chip>
        {!item.available && <Chip variant="unavailable">Unavailable</Chip>}
        {item.tags.whyPick.slice(0, 3).map(tag => (
          <span
            key={tag}
            style={{
              padding: `${spacing.xs} ${spacing.sm}`,
              backgroundColor: colors.beigeLight,
              borderRadius: borderRadius.sm,
              fontSize: fontSize.xs,
              color: colors.gray,
            }}
          >
            {tag}
          </span>
        ))}
      </div>

      {!item.available && (
        <div style={{
          marginTop: spacing.md,
          padding: spacing.sm,
          backgroundColor: '#fff3cd',
          borderRadius: borderRadius.sm,
          fontSize: fontSize.sm,
          color: '#856404',
        }}>
          This item is currently unavailable.{' '}
          <a href="#" style={{ color: colors.primaryBrown, textDecoration: 'underline' }}>
            Try another store
          </a>
        </div>
      )}
    </div>
  )
}
