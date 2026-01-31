import React from 'react'
import { colors, spacing, borderRadius, fontWeight, fontSize } from '../design-system'

interface ChipProps {
  children: React.ReactNode
  variant: 'primary' | 'specialty' | 'unavailable'
}

export const Chip: React.FC<ChipProps> = ({ children, variant }) => {
  const getColors = () => {
    switch (variant) {
      case 'primary':
        return { bg: '#fef3e6', color: colors.accentOrange }
      case 'specialty':
        return { bg: '#f3f0f7', color: colors.accentPurple }
      case 'unavailable':
        return { bg: colors.beigeBorder, color: colors.unavailableBeige }
    }
  }

  const { bg, color } = getColors()

  const styles: React.CSSProperties = {
    display: 'inline-block',
    padding: `${spacing.xs} ${spacing.sm}`,
    backgroundColor: bg,
    color: color,
    borderRadius: borderRadius.sm,
    fontSize: fontSize.xs,
    fontWeight: fontWeight.semibold,
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  }

  return <span style={styles}>{children}</span>
}
