import React from 'react'
import { colors, spacing, borderRadius, fontWeight, fontSize } from '../design-system'

interface ButtonProps {
  children: React.ReactNode
  onClick?: () => void
  variant?: 'primary' | 'secondary'
  fullWidth?: boolean
  disabled?: boolean
}

export const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  fullWidth = false,
  disabled = false
}) => {
  const isPrimary = variant === 'primary'

  const styles: React.CSSProperties = {
    padding: `${spacing.lg} ${spacing.xl}`,
    backgroundColor: isPrimary ? colors.primaryBrown : colors.white,
    color: isPrimary ? colors.white : colors.primaryBrown,
    border: isPrimary ? 'none' : `2px solid ${colors.beigeBorder}`,
    borderRadius: borderRadius.md,
    fontSize: fontSize.md,
    fontWeight: fontWeight.semibold,
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.5 : 1,
    width: fullWidth ? '100%' : 'auto',
    transition: 'all 0.2s',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  }

  return (
    <button
      style={styles}
      onClick={onClick}
      disabled={disabled}
      onMouseEnter={(e) => {
        if (!disabled) {
          e.currentTarget.style.backgroundColor = isPrimary ? '#5a4f2f' : colors.beigeLight
        }
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = isPrimary ? colors.primaryBrown : colors.white
      }}
    >
      {children}
    </button>
  )
}
