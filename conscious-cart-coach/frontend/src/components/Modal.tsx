import React from 'react'
import { colors, spacing, borderRadius, fontSize, fontWeight } from '../design-system'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
  footer?: React.ReactNode
}

export const Modal: React.FC<ModalProps> = ({ isOpen, onClose, title, children, footer }) => {
  if (!isOpen) return null

  const overlayStyles: React.CSSProperties = {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  }

  const modalStyles: React.CSSProperties = {
    backgroundColor: colors.white,
    borderRadius: borderRadius.lg,
    width: '90%',
    maxWidth: '600px',
    maxHeight: '80vh',
    display: 'flex',
    flexDirection: 'column',
    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
  }

  const headerStyles: React.CSSProperties = {
    padding: spacing.xl,
    borderBottom: `2px solid ${colors.beigeBorder}`,
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  }

  const titleStyles: React.CSSProperties = {
    fontSize: fontSize.xl,
    fontWeight: fontWeight.bold,
    color: colors.primaryBrown,
    margin: 0,
  }

  const closeButtonStyles: React.CSSProperties = {
    background: 'none',
    border: 'none',
    fontSize: fontSize.xl,
    cursor: 'pointer',
    color: colors.gray,
    padding: spacing.sm,
  }

  const contentStyles: React.CSSProperties = {
    padding: spacing.xl,
    flex: 1,
    overflowY: 'auto',
  }

  const footerStyles: React.CSSProperties = {
    padding: spacing.xl,
    borderTop: `2px solid ${colors.beigeBorder}`,
    display: 'flex',
    gap: spacing.md,
    justifyContent: 'flex-end',
  }

  return (
    <div style={overlayStyles} onClick={onClose}>
      <div style={modalStyles} onClick={(e) => e.stopPropagation()}>
        <div style={headerStyles}>
          <h2 style={titleStyles}>{title}</h2>
          <button style={closeButtonStyles} onClick={onClose}>×</button>
        </div>
        <div style={contentStyles}>
          {children}
        </div>
        {footer && <div style={footerStyles}>{footer}</div>}
      </div>
    </div>
  )
}
