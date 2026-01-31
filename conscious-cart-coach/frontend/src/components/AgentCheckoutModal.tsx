import React, { useState, useEffect } from 'react'
import { Modal } from './Modal'
import { Button } from './Button'
import { Cart, CheckoutStore } from '../types'
import { colors, spacing, fontSize, fontWeight } from '../design-system'

interface AgentCheckoutModalProps {
  isOpen: boolean
  carts: Cart[]
  onClose: () => void
}

export const AgentCheckoutModal: React.FC<AgentCheckoutModalProps> = ({
  isOpen,
  carts,
  onClose
}) => {
  const [stores, setStores] = useState<CheckoutStore[]>([])
  const [isCreating, setIsCreating] = useState(true)

  useEffect(() => {
    if (isOpen) {
      // Reset state when modal opens
      setIsCreating(true)
      setStores([])

      // Simulate cart creation with delays
      const storeList: CheckoutStore[] = carts.map(cart => ({
        name: cart.store,
        url: `https://${cart.store.toLowerCase().replace(/\s+/g, '')}.com/cart`,
        ready: false
      }))

      setStores(storeList)

      // Mark stores as ready one by one
      storeList.forEach((_store, index) => {
        setTimeout(() => {
          setStores(prev => prev.map((s, i) =>
            i === index ? { ...s, ready: true } : s
          ))

          // After last store, stop "creating" state
          if (index === storeList.length - 1) {
            setTimeout(() => setIsCreating(false), 500)
          }
        }, (index + 1) * 1000) // 1 second delay between each
      })
    }
  }, [isOpen, carts])

  const handleCheckoutAll = () => {
    stores.forEach(store => {
      if (store.ready) {
        window.open(store.url, '_blank')
      }
    })
  }

  const handleCheckoutStore = (storeUrl: string) => {
    window.open(storeUrl, '_blank')
  }

  const progressStyles: React.CSSProperties = {
    marginBottom: spacing.xl,
  }

  const progressItemStyles: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
  }

  const checkmarkStyles: React.CSSProperties = {
    fontSize: fontSize.lg,
    color: colors.successGreen,
  }

  const storeButtonContainerStyles: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.md,
    marginBottom: spacing.xl,
  }

  const disclaimerStyles: React.CSSProperties = {
    padding: spacing.md,
    backgroundColor: colors.beigeLight,
    borderRadius: '4px',
    fontSize: fontSize.sm,
    color: colors.gray,
    marginTop: spacing.lg,
  }

  const footer = (
    <>
      <Button variant="secondary" onClick={onClose}>
        Close
      </Button>
      <Button
        variant="primary"
        onClick={handleCheckoutAll}
        disabled={isCreating || stores.some(s => !s.ready)}
      >
        Checkout all (opens tabs)
      </Button>
    </>
  )

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Agent Checkout"
      footer={footer}
    >
      <div>
        {/* Progress section */}
        {isCreating && (
          <div style={progressStyles}>
            <div style={{ fontSize: fontSize.base, fontWeight: fontWeight.semibold, marginBottom: spacing.md }}>
              Creating carts...
            </div>
          </div>
        )}

        {/* Store status list */}
        <div style={progressStyles}>
          {stores.map(store => (
            <div key={store.name} style={progressItemStyles}>
              <span style={checkmarkStyles}>
                {store.ready ? '✅' : '⏳'}
              </span>
              <span style={{ flex: 1, fontSize: fontSize.base }}>
                {store.ready ? `${store.name} cart ready` : `Creating ${store.name} cart...`}
              </span>
            </div>
          ))}
        </div>

        {/* Individual checkout buttons */}
        {!isCreating && (
          <div style={storeButtonContainerStyles}>
            {stores.map(store => (
              <Button
                key={store.name}
                variant="secondary"
                fullWidth
                onClick={() => handleCheckoutStore(store.url)}
                disabled={!store.ready}
              >
                Checkout {store.name}
              </Button>
            ))}
          </div>
        )}

        {/* Disclaimer */}
        <div style={disclaimerStyles}>
          Opens store carts in new tabs. Payment happens on store sites.
        </div>
      </div>
    </Modal>
  )
}
